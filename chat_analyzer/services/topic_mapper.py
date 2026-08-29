from Sastrawi.Stemmer.StemmerFactory import StemmerFactory


class TopicMapper:
    """"
    Maps BERTopic clusters to the 12 predefined therapy topics
    """

    def __init__(self, threshold=2):
        self.stemmer = StemmerFactory().create_stemmer()
        self.threshold = threshold # min match required to accept a mapping

    def stem(self, word):
        return self.stemmer.stem(word.lower().strip())

    def map_cluster(self, bertopic_keywords, defined_topics):
        # 1. kito stem BERTopic keywords (top 10 ignore the score)
        cluster_words = []
        for i, (word, _) in enumerate(bertopic_keywords[:10]):
            stemmed = self.stem(word)
            if stemmed:
            # fuzzy weight by rank: #1 = strongest evidence, floor 0.5
                weight = max(2.0 - 0.5 * i, 0.5)
                cluster_words.append((stemmed, weight))

        best_topic = None
        best_score = 0

        for topic in defined_topics:
            # 2. Stem the defined topic's keywords
            topic_words = {self.stem(k) for k in topic.keywords}

            # 3. count how many cluster words hit this topic keywords
            score = sum(weight for word, weight in cluster_words if word in topic_words)
            
            if score > best_score:
                best_score = score
                best_topic = topic

        # 4. only accept if weight evidence clears the alpha cut
        if best_score >= self.threshold:
            return best_topic, best_score

        return None, 0.0

    def map_message(self, text, defined_topics):
        
        tokens = [self.stem(t) for t in text.split() if self.stem(t)]
        best_topic = None
        best_score = 0
        for topic in defined_topics:
            topic_words = {self.stem(k) for k in topic.keywords}
            score = sum(max(2.0 - 0.5 * i, 0.5)
                        for i, t in enumerate(tokens) if t in topic_words)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_score >= self.threshold:
            return best_topic, best_score
        
        return None, 0.0


