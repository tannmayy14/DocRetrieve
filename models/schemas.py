from pydantic import BaseModel
from typing import List

class QueryRequest(BaseModel):
    documents: str  # URL to document
    questions: List[str]

class QueryResponse(BaseModel):
    answers: List[str]  # Simple string answers as required

# Internal use only
class DetailedAnswer(BaseModel):
    answer: str
    rationale: str
    confidence: float
    relevant_clauses: List[str]