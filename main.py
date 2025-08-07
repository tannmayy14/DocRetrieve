from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.endpoints import router
from utils.auth import verify_token
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="DocRetrieve API",
    description="LLM-Powered Document Intelligence System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router,
    prefix="/api/v1",
    dependencies=[Depends(verify_token)]
)

@app.get("/")
async def root():
    return {"message": "DocRetrieve API is running", "version": "1.0.0"}

# Add this at the end:
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)