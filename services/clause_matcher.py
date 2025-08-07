import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def match_clauses(clauses_list, questions):
    """
    clauses_list: List[List[str]] - Each inner list contains clauses matched for a question
    questions: List[str]
    Returns: List[List[dict]] - Each inner list contains dicts with clause and similarity score
    """
    results = []
    for q, clauses in zip(questions, clauses_list):
        if not clauses:
            results.append([])
            continue
        # Fit TF-IDF on clauses
        vectorizer = TfidfVectorizer().fit(clauses + [q])
        clause_vecs = vectorizer.transform(clauses)
        q_vec = vectorizer.transform([q])
        sims = cosine_similarity(q_vec, clause_vecs)[0]
        matched = [
            {"clause": clause, "similarity": float(sim)}
            for clause, sim in zip(clauses, sims)
        ]
        matched.sort(key=lambda x: x["similarity"], reverse=True)
        results.append(matched)
    return results