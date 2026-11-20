from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.github_loader import fetch_repo_files
from app.rag_engine import index_repository, ask_repository

app = FastAPI(title="AI GitHub Repository Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend static files (CSS/JS) 
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

class IngestRequest(BaseModel):
    repo_url: str

class AskRequest(BaseModel):
    repo_url: str
    question: str

@app.post("/ingest")
def ingest_repo(request: IngestRequest):
    try:
        files = fetch_repo_files(request.repo_url)
        chunks_count = index_repository(request.repo_url, files)
        return {
            "status": "success",
            "repo_url": request.repo_url,
            "files_processed": len(files),
            "chunks_indexed": chunks_count,
            "files": [f["path"] for f in files]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask_question(request: AskRequest):
    try:
        result = ask_repository(request.repo_url, request.question)
        return {
            "repo_url": request.repo_url,
            "question": request.question,
            "answer": result["answer"],
            "sources": result["sources"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))