from sentence_transformers import util

def match_clauses(clauses_list, questions):
    """
    clauses_list: List[List[str]] - Each inner list contains clauses matched for a question
    questions: List[str]
    Returns: List[List[dict]] - Each inner list contains dicts with clause and similarity score
    """
    results = []
    for q, clauses in zip(questions, clauses_list):
        q_emb = util.cos_sim  # For clarity
        # Get embedding for question
        from services.embedding_search import embedder
        q_vec = embedder.encode([q], convert_to_tensor=True)
        clause_vecs = embedder.encode(clauses, convert_to_tensor=True)
        # Compute similarity
        sims = util.cos_sim(q_vec, clause_vecs)[0]
        matched = [
            {"clause": clause, "similarity": float(sim)}
            for clause, sim in zip(clauses, sims)
        ]
        # Sort by similarity descending
        matched.sort(key=lambda x: x["similarity"], reverse=True)
        results.append(matched)
    return results