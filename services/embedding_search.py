import faiss
from sentence_transformers import SentenceTransformer
import numpy as np

# Load embedding model once
embedder = SentenceTransformer("all-MiniLM-L6-v2")  # Fast, small, free

class FAISSEngine:
    def __init__(self):
        self.index = None
        self.texts = []

    def build_index(self, texts):
        self.texts = texts
        embeddings = embedder.encode(texts, convert_to_numpy=True)
        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def search(self, query, top_k=3):
        if self.index is None or not self.texts:
            raise ValueError("FAISS index not built.")
        query_emb = embedder.encode([query], convert_to_numpy=True)
        D, I = self.index.search(query_emb, top_k)
        results = [self.texts[i] for i in I[0]]
        return results

# Singleton for API usage
faiss_engine = FAISSEngine()

def search_embeddings(structured_data, questions):
    # Assume structured_data['clauses'] is a list of clause texts
    clauses = structured_data.get('clauses', [])
    if not clauses:
        raise ValueError("No clauses found for embedding search.")
    faiss_engine.build_index(clauses)
    matches = []
    for q in questions:
        try:
            matched = faiss_engine.search(q)
            matches.append(matched)
        except Exception as e:
            matches.append([f"Error: {str(e)}"])
    return matches