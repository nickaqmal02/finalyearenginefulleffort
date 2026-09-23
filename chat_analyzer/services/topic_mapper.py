# topicmapper.py
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from chat_analyzer.services.malay_normalizer import MalayNormalizer

class TopicMapper:
    """"
    Maps BERTopic clusters to the 12 predefined therapy topics
    """

    def __init__(self, threshold=1.5, min_gap=1.0):
        self.stemmer = StemmerFactory().create_stemmer()
        self.threshold = threshold # min match required to accept a mapping
        self.min_gap = min_gap
        self.normalizer = MalayNormalizer()

    def stem(self, word):
        return self.stemmer.stem(word.lower().strip())

    def normalize(self, word):
        return self.normalizer.normalize(word)
    #
    #  CLUSTER LEVEL MAPPING FOR BERTOPIC PRODUCED CLUSTER  
    #
    def map_cluster(self, bertopic_keywords, defined_topics):
        # 1. kito stem BERTopic keywords (top 10 ignore the score)
        cluster_words = []
        for i, (word, _) in enumerate(bertopic_keywords[:10]):
            normalized = self.normalize(word)
            if normalized:
            # fuzzy weight by rank: #1 = strongest evidence, floor 0.5
                weight = max(2.0 - 0.5 * i, 0.5)
                cluster_words.append((normalized, weight))

        best_topic = None
        best_score = 0

        # declaring all scores list first so then we can append it
        for topic in defined_topics:
            topic_words = {self.normalize(k) for k in topic.keywords}
            score = sum(weight for word, weight in cluster_words if word in topic_words)

            if score > best_score:
                best_score = score
                best_topic = topic

        if best_score >= self.threshold:
            return best_topic, best_score

        return None, 0.0


# ╔════════════════════════════════════════════╗ 
# ║MAPPING THIS CLUSTER LEVEL WITH ALTERNATIVES║ 
# ╚════════════════════════════════════════════╝ 
    def map_cluster_with_alternatives(self, bertopic_keywords, defined_topics, threshold=0.5):
        """
            This is one of our enhancement 
            the difference we already set lower threshold for this method
            Map cluster to all matching topics not just the best
            return:list of dicts wih topic, score, confidence is_primary or not
        """
        # 1.Process cluster keywords with weight
        cluster_words = []
        for i, (word, _) in enumerate(bertopic_keywords[:10]):
            normalized = self.normalize(word)
            if normalized:
                weight = max(2.0 - 0.5 * i, 0.5)
                cluster_words.append((normalized, weight))
        
        all_scores = []
        # 2.score againts all defined_topics
        for topic in defined_topics:
            topic_words = {self.normalize(k) for k in topic.keywords}
            score = sum(weight for word, weight in cluster_words if word in topic_words)
            
            if score > 0:
                all_scores.append({
                    'topic': topic,
                    'score': score,
                    'confidence': min(score / 10, 1.0),
                    'is_primary': False
                })

        # 3. sort score by descending to take highest score
        all_scores.sort(key=lambda x: x['score'], reverse=True)

        # 4. apply threshold and gap for primary topic
        if all_scores:
            best = all_scores[0]
            second_score = all_scores[1]['score'] if len(all_scores) > 1 else 0

            gap = best['score'] - second_score

            #primaru topic: must meet the threshold + gap if wanna be primary
            if best['score'] >= self.threshold:
                best['is_primary'] = True
            else:
                best['is_primary'] = False

            # alternative topics section just need to meet lowest threshdold
            for score in all_scores[1:]:
                if score['score'] >= self.threshold * 0.5:
                    score['is_primary'] = False

            # return all topics that passed thre threshold
            return [s for s in all_scores if s['score'] >= self.threshold * 0.5]
            
        return []

# ╔════════════════════════════════════════════╗ 
# ║MESSAGE-LEVEL MAPPING ( FOR INDIVIDUAL MESSA║ 
# ╚════════════════════════════════════════════╝ 
    def map_message(self, text, defined_topics):
        """ Original single messsage mapping """
        tokens = [self.stem(t) for t in text.split() if self.stem(t)]
        
        if not tokens:
            return None, 0.0

        best_topic = None
        best_score = 0
        
        for topic in defined_topics:
            topic_words = {self.stem(k) for k in topic.keywords}
            score = sum(
                max(2.0 - 0.5 * i, 0.5)
                for i, t in enumerate(tokens)
                if t in topic_words
            )
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_score >= self.threshold:
            return best_topic, best_score
        
        return None, 0.0
# ╔════════════════════════════════════════════╗ 
# ║       MAP MESSAGE WITH ALTERNATIVES        ║ 
# ╚════════════════════════════════════════════╝ 
    def map_message_with_alternatives(
        self,
        text: str,
        defined_topics: list[Topic],
        threshold: float = 0.5,
    ) -> list[dict[str, object]]:
        """
        Map a single message to All matching topics above threshold
        """
        # 1. stem all tokens in the message
        tokens = [self.stem(t) for t in text.split() if self.stem(t)]
        # but
        if not tokens:
            return []
        # 2. score againts all defined topics
        results = []
        for topic in defined_topics:
            topic_words = {self.stem(k) for k in topic.keywords}

            # calculate score w rank-based weighting
            score = sum(
                max(2.0 - 0.5 * i, 0.5)
                for i, t in enumerate(tokens)
                if t in topic_words
            )

            if score >= threshold:
                results.append({
                    'topic': topic,
                    'score': score,
                    'confidence': min(score / 10, 1.0)
                })
        
        # 3. sort the score by descendinf order
        results.sort(key=lambda x: x['score'], reverse=True)

        # 4. mark the best as a primary
        if results:
            results[0]['is_primary'] = True
            for r in results[1:]:
                r['is_primary'] = False

        return results



