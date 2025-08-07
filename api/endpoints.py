from fastapi import APIRouter, HTTPException,Depends
from models.schemas import QueryRequest, QueryResponse, DetailedAnswer
from services.document_loader import load_document
from services.llm_extractor import extract_structured_data
from services.embedding_search import search_embeddings
from services.clause_matcher import match_clauses
from services.logic_evaluator import evaluate_logic
from utils.auth import verify_token
import asyncio
import logging

router = APIRouter()

@router.post("/hackrx/run", response_model=QueryResponse)
async def run_query(request: QueryRequest, auth=Depends(verify_token)):
    try:
        # Step 1: Load and process document
        doc_text = await load_document(request.documents)
        if not doc_text or len(doc_text.strip()) < 50:
            raise ValueError("Document appears to be empty or too short")
        
        # Step 2: Extract structured data
        try:
            structured_data = await extract_structured_data(doc_text)
            #checking if clauses were extracted
            if not structured_data.get("clauses"):
                print("No clauses extracted, using fallback extraction")
                #fallback:splitting document into sentences
                sentences = doc_text.split('.')
                clauses = [s.strip() for s in sentences if len(s.strip()) > 20][:10]
                structured_data = {"clauses": clauses, "entities": [], "sections": []}

        except Exception as e:
            print(f"LLM extraction failed: {e}, using simple fallback")
            #emergency fallback
            sentences= doc_text.split('.')
            clauses=[s.strip() for s in sentences if len(s.strip()) > 20][:10]
            structured_data = {"clauses": clauses, "entities": [],"sections": []}
        
        if not structured_data.get("clauses"):
            raise ValueError("No valid clauses extracted from the document")
        
        # Step 3: Search embeddings
        matches = search_embeddings(structured_data, request.questions)
        
        # Step 4: Match clauses with similarity scores
        matched_clauses = match_clauses(matches, request.questions)
        
        # Step 5: Evaluate logic with delays to avoid rate limits
        answers = []
        for i, (question, clauses) in enumerate(zip(request.questions, matched_clauses)):
            try:
                answer, rationale = await evaluate_logic(question, clauses)
                answers.append(answer)
                
                # Add delay between questions to avoid rate limits
                if i < len(request.questions) - 1:
                    await asyncio.sleep(3)
                    
            except Exception as e:
                logging.error(f"Error evaluating question '{question}': {e}")
                answers.append(f"Unable to process: {str(e)}")
        
        return QueryResponse(answers=answers)
        
    except Exception as e:
        logging.error(f"Error in run_query: {e}")
        error_answers = [f"Error: {str(e)}" for _ in request.questions]
        return QueryResponse(answers=error_answers)


@router.get("/health")
async def health_check():
    return {"status": "healthy", "message": "DocRetrieve API is running"}