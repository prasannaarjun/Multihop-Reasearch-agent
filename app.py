from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
from agent import ResearchAgent
from report import generate_markdown_report, save_report
from embeddings import add_file_to_index, get_collection_stats
from file_processor import file_processor

# Initialize FastAPI app
app = FastAPI(
    title="Multi-hop Research Agent",
    description="A research agent that uses Chroma for document retrieval and multi-hop reasoning",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for React app
if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Initialize research agent
research_agent = None

# Request/Response models
class QuestionRequest(BaseModel):
    question: str
    per_sub_k: int = 3

class QuestionResponse(BaseModel):
    question: str
    answer: str
    subqueries: list
    citations: list
    total_documents: int

class ExportResponse(BaseModel):
    message: str
    filepath: str

class FileUploadResponse(BaseModel):
    success: bool
    filename: str
    message: str
    file_type: Optional[str] = None
    word_count: Optional[int] = None
    chunks_added: Optional[int] = None
    error: Optional[str] = None

class CollectionStatsResponse(BaseModel):
    total_documents: int
    unique_files: int
    file_types: Dict[str, int]
    collection_name: str
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the research agent on startup."""
    global research_agent
    try:
        # Get configuration from environment variables
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        ollama_model = os.getenv("OLLAMA_MODEL", "mistral:latest")
        
        research_agent = ResearchAgent(
            persist_directory="chroma_db",
            use_ollama=use_ollama,
            ollama_model=ollama_model
        )
        print("Research agent initialized successfully")
    except Exception as e:
        print(f"Failed to initialize research agent: {e}")
        research_agent = None

@app.get("/")
async def root():
    """Serve React app or API information."""
    if os.path.exists("frontend/build/index.html"):
        return FileResponse("frontend/build/index.html")
    return {
        "message": "Multi-hop Research Agent API",
        "version": "1.0.0",
        "status": "running",
        "agent_initialized": research_agent is not None
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_initialized": research_agent is not None
    }

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a research question and get a multi-hop reasoned answer.
    
    Args:
        request: Question request with question text and optional per_sub_k parameter
        
    Returns:
        Research results with answer, subqueries, and citations
    """
    if research_agent is None:
        raise HTTPException(
            status_code=503, 
            detail="Research agent not initialized. Please check if Chroma database exists."
        )
    
    try:
        # Ask the research agent
        result = research_agent.ask(
            question=request.question,
            per_sub_k=request.per_sub_k
        )
        
        return QuestionResponse(
            question=result['question'],
            answer=result['answer'],
            subqueries=result['subqueries'],
            citations=result['citations'],
            total_documents=result['total_documents']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

@app.get("/export")
async def export_report(question: str):
    """
    Export research results as a markdown report.
    
    Args:
        question: The research question
        
    Returns:
        Markdown report file
    """
    if research_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Research agent not initialized"
        )
    
    try:
        # Get research results
        result = research_agent.ask(question, per_sub_k=3)
        
        # Generate markdown report
        report = generate_markdown_report(result)
        
        # Save report
        filepath = save_report(report)
        
        return FileResponse(
            path=filepath,
            filename=os.path.basename(filepath),
            media_type='text/markdown'
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )

@app.get("/stats")
async def get_stats():
    """Get statistics about the research agent."""
    if research_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Research agent not initialized"
        )
    
    try:
        # Get collection stats
        collection = research_agent.retriever.collection
        doc_count = collection.count()
        
        return {
            "documents_in_database": doc_count,
            "agent_status": "active",
            "database_type": "Chroma"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file (PDF, LaTeX, or text) and add it to the research database.
    
    Args:
        file: Uploaded file
        
    Returns:
        Upload result with processing information
    """
    if research_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Research agent not initialized"
        )
    
    # Check if file type is supported
    if not file_processor.is_supported(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {list(file_processor.supported_extensions)}"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file uploaded"
            )
        
        # Check file size (limit to 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 50MB."
            )
        
        # Add file to index
        result = add_file_to_index(file_content, file.filename)
        
        if result["success"]:
            return FileUploadResponse(
                success=True,
                filename=result["filename"],
                message=result["message"],
                file_type=result["file_type"],
                word_count=result["word_count"],
                chunks_added=result["chunks_added"]
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@app.get("/collection-stats", response_model=CollectionStatsResponse)
async def get_collection_stats_endpoint():
    """
    Get detailed statistics about the document collection.
    
    Returns:
        Collection statistics including file types and counts
    """
    try:
        stats = get_collection_stats()
        
        if "error" in stats:
            raise HTTPException(
                status_code=500,
                detail=stats["error"]
            )
        
        return CollectionStatsResponse(
            total_documents=stats["total_documents"],
            unique_files=stats["unique_files"],
            file_types=stats["file_types"],
            collection_name=stats["collection_name"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting collection stats: {str(e)}"
        )

@app.get("/supported-file-types")
async def get_supported_file_types():
    """
    Get list of supported file types for upload.
    
    Returns:
        List of supported file extensions
    """
    return {
        "supported_extensions": list(file_processor.supported_extensions),
        "max_file_size_mb": 50
    }

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Multi-hop Research Agent API...")
    print("Make sure you have built the Chroma index first using embeddings.py")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
