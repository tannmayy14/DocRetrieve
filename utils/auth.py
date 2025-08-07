# utils/auth.py
from fastapi import Header, HTTPException
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.environ.get("API_KEY")  # Replace with your actual key or load from env

async def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    token = authorization.split(" ")[1]
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")