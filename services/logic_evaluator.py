import os
from groq import Groq
from typing import List, Tuple, Dict
import asyncio
from services.rate_limiter import groq_call_with_retry

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

async def evaluate_logic(question: str, matched_clauses: List[Dict], document_type: str = "policy") -> Tuple[str, str]:
    """Simplified logic evaluation to reduce token usage"""
    
    # Take only top 3 clauses and shorten them
    top_clauses = []
    for mc in matched_clauses[:3]:
        clause = mc["clause"]
        if len(clause) > 200:
            clause = clause[:200] + "..."
        top_clauses.append(clause)
    
    context = "\n".join([f"- {clause}" for clause in top_clauses])
    
    # Much shorter prompt
    prompt = f"""Question: {question}
    
Context: {context}

Provide a direct answer based on the context above. Keep response under 100 words."""
    
    try:
        messages = [
            {"role": "system", "content": "You provide brief, direct answers."},
            {"role": "user", "content": prompt}
        ]
        
        response = await groq_call_with_retry(client, messages, max_retries=2)
        
        if "Error" in response:
            return f"Unable to process: Rate limit reached", "Please try again in a few minutes"
        
        # Limit response length
        answer = response[:200] if len(response) > 200 else response
        return answer, "Analysis completed"
        
    except Exception as e:
        return f"Unable to evaluate: {str(e)}", "Error in processing"