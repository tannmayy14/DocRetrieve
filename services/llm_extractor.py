# SOLUTION 2: Updated llm_extractor.py with rate limiting
import os
from groq import Groq
import json
import re
from typing import Dict, List
from dotenv import load_dotenv
import asyncio
from services.rate_limiter import groq_call_with_retry

load_dotenv() 
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

async def extract_structured_data(document_text: str) -> Dict:
    """Extract structured data with rate limiting"""
    
    # Much more aggressive chunking to reduce token usage
    max_chunk_size = 1500  # Reduced from 3000
    if len(document_text) > max_chunk_size:
        chunks = [document_text[i:i+max_chunk_size] 
                 for i in range(0, len(document_text), max_chunk_size-100)]
        # Limit to first 3 chunks to avoid rate limits
        chunks = chunks[:3]
    else:
        chunks = [document_text]
    
    all_clauses = []
    
    for i, chunk in enumerate(chunks):
        # Simplified prompt to use fewer tokens
        prompt = f"""Extract key clauses from this text. Return only JSON:
        
        {chunk[:1000]}...
        
        JSON format:
        {{"clauses": ["clause1", "clause2"]}}"""
        
        try:
            messages = [
                {"role": "system", "content": "Extract clauses. Return only JSON."},
                {"role": "user", "content": prompt}
            ]
            
            result_text = await groq_call_with_retry(client, messages, max_retries=2)
            
            if "Error" in result_text:
                # Fallback extraction
                sentences = re.split(r'[.!?]+', chunk)
                clauses = [s.strip() for s in sentences if len(s.strip()) > 30][:10]
                all_clauses.extend(clauses)
                continue
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                all_clauses.extend(data.get("clauses", [])[:10])  # Limit clauses
            
            # Add delay between chunks
            if i < len(chunks) - 1:
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"Error extracting from chunk {i}: {e}")
            # Fallback
            sentences = re.split(r'[.!?]+', chunk)
            clauses = [s.strip() for s in sentences if len(s.strip()) > 30][:5]
            all_clauses.extend(clauses)
    
    return {
        "clauses": list(set(all_clauses))[:20],  # Limit total clauses
        "entities": [],
        "sections": []
    }