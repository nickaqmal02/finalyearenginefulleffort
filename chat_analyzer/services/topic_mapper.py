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
        cluster_words = [self.stem(word) for word, _ in bertopic_keywords[:10]]
        cluster_words = [w for w in cluster_words if w]

        best_topic = None
        best_score = 0

        for topic in defined_topics:
            # 2. Stem the defined topic's keywords
            topic_words = {self.stem(k) for k in topic.keywords}

            # 3. count how many cluster words hit this topic keywords
            matches = sum(1 for w in cluster_words if w in topic_words)

            if matches > best_score:
                best_score = matches
                best_topic = topic

        # 4. only accept if we have enough evidence
        if best_score >= self.threshold:
            return best_topic, best_score

        return None, 0
