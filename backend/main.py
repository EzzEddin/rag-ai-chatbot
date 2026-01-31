from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from rag_engine import RAGEngine

# Load environment variables
load_dotenv()

# Initialize RAG engine
rag_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global rag_engine
    # Startup
    try:
        rag_engine = RAGEngine()
        # Index documents if not already indexed
        await rag_engine.initialize()
        print("RAG Engine initialized successfully")
    except Exception as e:
        print(f"Error initializing RAG engine: {e}")
        raise
    
    yield
    
    # Shutdown (cleanup if needed)
    print("Shutting down RAG Engine...")

app = FastAPI(title="Acme Tech RAG Chatbot API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = []

@app.get("/")
async def root():
    return {"message": "Acme Tech RAG Chatbot API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "rag_engine": "initialized" if rag_engine else "not initialized"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return a RAG-enhanced response
    """
    if not rag_engine:
        raise HTTPException(status_code=503, detail="RAG engine not initialized")
    
    try:
        # Get response from RAG engine
        response, sources = await rag_engine.query(request.message)
        
        return ChatResponse(
            response=response,
            sources=sources
        )
    except Exception as e:
        print(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
