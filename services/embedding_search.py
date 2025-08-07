import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TFIDFEngine:
    def __init__(self):
        self.vectorizer = None
        self.matrix = None
        self.texts = []

    def build_index(self, texts):
        self.texts = texts
        self.vectorizer = TfidfVectorizer().fit(texts)
        self.matrix = self.vectorizer.transform(texts)

    def search(self, query, top_k=3):
        if self.matrix is None or not self.texts:
            raise ValueError("TF-IDF index not built.")
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.matrix)[0]
        top_indices = np.argsort(sims)[::-1][:top_k]
        results = [self.texts[i] for i in top_indices]
        return results

# Singleton for API usage
tfidf_engine = TFIDFEngine()

def search_embeddings(structured_data, questions):
    clauses = structured_data.get('clauses', [])
    if not clauses:
        raise ValueError("No clauses found for embedding search.")
    tfidf_engine.build_index(clauses)
    matches = []
    for q in questions:
        try:
            matched = tfidf_engine.search(q)
            matches.append(matched)
        except Exception as e:
            matches.append([f"Error: {str(e)}"])
    return matches