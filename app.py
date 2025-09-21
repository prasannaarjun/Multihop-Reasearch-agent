from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
from agent import ResearchAgent
from chat_agent import ChatResearchAgent
from report import generate_markdown_report, save_report
from embeddings import add_file_to_index, get_collection_stats
from file_processor import file_processor
from chat_manager import chat_manager

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
chat_research_agent = None

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

class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    per_sub_k: int = 3
    include_context: bool = True

class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    conversation_title: str
    message_count: int
    context_used: bool
    timestamp: str
    research_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ConversationInfo(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    is_active: bool

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    title: str
    message_count: int

class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"

class UpdateTitleRequest(BaseModel):
    title: str

@app.on_event("startup")
async def startup_event():
    """Initialize the research agent on startup."""
    global research_agent, chat_research_agent
    try:
        # Get configuration from environment variables
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        ollama_model = os.getenv("OLLAMA_MODEL", "mistral:latest")
        
        research_agent = ResearchAgent(
            persist_directory="chroma_db",
            use_ollama=use_ollama,
            ollama_model=ollama_model
        )
        
        # Initialize chat research agent
        chat_research_agent = ChatResearchAgent(
            persist_directory="chroma_db",
            use_ollama=use_ollama,
            ollama_model=ollama_model
        )
        
        print("Research agent and chat agent initialized successfully")
    except Exception as e:
        print(f"Failed to initialize research agent: {e}")
        research_agent = None
        chat_research_agent = None

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

# Chat endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Chat with the research agent in a conversational context.
    
    Args:
        request: Chat request with message and optional conversation_id
        
    Returns:
        Chat response with answer and conversation info
    """
    if chat_research_agent is None:
        raise HTTPException(
            status_code=503,
            detail="Chat research agent not initialized"
        )
    
    try:
        result = chat_research_agent.chat_ask(
            question=request.message,
            conversation_id=request.conversation_id,
            per_sub_k=request.per_sub_k,
            include_context=request.include_context
        )
        
        return ChatResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            answer=result["answer"],
            conversation_title=result["conversation_title"],
            message_count=result["message_count"],
            context_used=result["context_used"],
            timestamp=result["timestamp"],
            research_result=result.get("research_result"),
            error=result.get("error")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )

@app.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations():
    """
    List all conversations.
    
    Returns:
        List of conversation information
    """
    try:
        conversations = chat_manager.list_conversations()
        return [ConversationInfo(**conv) for conv in conversations]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing conversations: {str(e)}"
        )

@app.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(conversation_id: str, max_messages: int = 50):
    """
    Get conversation history.
    
    Args:
        conversation_id: ID of the conversation
        max_messages: Maximum number of messages to return
        
    Returns:
        Conversation history with messages
    """
    try:
        conversation = chat_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        messages = chat_manager.get_conversation_history(conversation_id, max_messages)
        
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=[ChatMessage(**msg.to_dict()) for msg in messages],
            title=conversation.title,
            message_count=len(conversation.messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting conversation history: {str(e)}"
        )

@app.post("/conversations", response_model=Dict[str, str])
async def create_conversation(request: CreateConversationRequest):
    """
    Create a new conversation.
    
    Args:
        request: Request body with title
        
    Returns:
        Conversation ID
    """
    try:
        conversation_id = chat_manager.create_conversation(request.title)
        return {"conversation_id": conversation_id, "title": request.title}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating conversation: {str(e)}"
        )

@app.put("/conversations/{conversation_id}/title")
async def update_conversation_title(conversation_id: str, request: UpdateTitleRequest):
    """
    Update conversation title.
    
    Args:
        conversation_id: ID of the conversation
        request: Request body with new title
        
    Returns:
        Success message
    """
    try:
        success = chat_manager.update_conversation_title(conversation_id, request.title)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        return {"message": "Title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating conversation title: {str(e)}"
        )

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation.
    
    Args:
        conversation_id: ID of the conversation
        
    Returns:
        Success message
    """
    try:
        success = chat_manager.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting conversation: {str(e)}"
        )

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
