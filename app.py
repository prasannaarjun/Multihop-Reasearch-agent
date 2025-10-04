"""
Multi-hop Research Agent API - Modular Version
Updated to use the new modular agent architecture.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import os
import warnings
import logging
import threading
from pathlib import Path

# Suppress bcrypt version warning
warnings.filterwarnings("ignore", message=".*bcrypt.*")
logging.getLogger("passlib").setLevel(logging.ERROR)

# Import modular components
from agents.research import ResearchAgent, DocumentRetriever
from agents.chat import ChatAgent, ConversationManager
from agents.shared.models import ResearchResult, ChatMessage, ConversationInfo
from agents.shared.exceptions import AgentError

# Import existing utilities
from report import generate_markdown_report, save_report
from document_processing import process_file, SUPPORTED_EXTENSIONS, DocumentProcessingError
from document_ingestion import process_and_store_file_content, get_user_document_stats
from ollama_client import OllamaClient
from sentence_transformers import SentenceTransformer

# Authentication imports
from auth import auth_router, get_current_active_user, get_current_admin_user, TokenData
from auth.database import create_tables

# Global variables for agents
research_agent = None
current_model = None
available_models = []
embedding_model = None

# Thread safety lock for model loading
_model_lock = threading.Lock()

def get_conversation_manager_for_user(current_user: TokenData, db_session=None):
    """Get a conversation manager scoped to the current user."""
    if db_session is None:
        from auth.database import SessionLocal
        db_session = SessionLocal()
    return ConversationManager(
        db_session=db_session,
        current_user_id=current_user.user_id,
        is_admin=current_user.is_admin
    )

def get_research_agent_for_user(current_user: TokenData, db_session=None):
    """Get a research agent scoped to the current user."""
    global embedding_model, current_model
    
    if embedding_model is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding model not initialized"
        )
    
    if db_session is None:
        from auth.database import SessionLocal
        db_session = SessionLocal()
    
    # Create user-scoped document retriever
    retriever = DocumentRetriever(db_session, embedding_model, current_user.user_id)
    
    # Initialize LLM client if enabled
    llm_client = None
    use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
    if use_ollama and current_model:
        llm_client = OllamaClient(model_name=current_model)
        if not llm_client.is_available():
            llm_client = None
    
    # Create research agent
    return ResearchAgent(retriever, llm_client, use_ollama, current_model)

def load_available_models():
    """Load available models from Ollama and store them in memory."""
    global available_models, current_model
    
    with _model_lock:
        try:
            # Check if Ollama is enabled
            use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
            if not use_ollama:
                available_models = []
                current_model = None
                return
        
            # Get Ollama base URL
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            
            # Make direct request to Ollama /api/tags endpoint
            import requests
            try:
                response = requests.get(f"{ollama_base_url}/api/tags", timeout=10)
                response.raise_for_status()
                ollama_data = response.json()
            except requests.exceptions.RequestException as e:
                logging.warning(f"Could not connect to Ollama at {ollama_base_url}: {e}")
                # For testing purposes, add some mock models
                logging.info("Adding mock models for testing...")
                available_models = [
                    {"name": "llama2:latest", "size": 0, "modified_at": "", "family": "", "format": "", "families": [], "parameter_size": "", "quantization_level": ""},
                    {"name": "mistral:latest", "size": 0, "modified_at": "", "family": "", "format": "", "families": [], "parameter_size": "", "quantization_level": ""},
                    {"name": "codellama:latest", "size": 0, "modified_at": "", "family": "", "format": "", "families": [], "parameter_size": "", "quantization_level": ""}
                ]
                current_model = available_models[0]['name'] if available_models else None
                logging.info(f"Mock models set: {available_models}")
                return
            
            # Parse models from Ollama response
            models = []
            for model in ollama_data.get('models', []):
                model_info = {
                    "name": model.get('name', ''),
                    "size": model.get('size', 0),
                    "modified_at": model.get('modified_at', ''),
                    "family": model.get('details', {}).get('family', ''),
                    "format": model.get('details', {}).get('format', ''),
                    "families": model.get('details', {}).get('families', []),
                    "parameter_size": model.get('details', {}).get('parameter_size', ''),
                    "quantization_level": model.get('details', {}).get('quantization_level', '')
                }
                models.append(model_info)
            
            available_models = models
            
            # Set current model to first available model if none is set
            if not current_model and models:
                current_model = models[0]['name']
                logging.info(f"Auto-selected model: {current_model}")
            
        except Exception as e:
            logging.error(f"Error loading models: {e}")
            available_models = []
            current_model = None

def set_current_model(model_name: str) -> bool:
    """Set the current model if it exists in available models."""
    global current_model
    
    with _model_lock:
        if not available_models:
            return False
        
        # Check if model exists
        model_exists = any(model['name'] == model_name for model in available_models)
        if model_exists:
            current_model = model_name
            return True
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global research_agent, current_model, available_models, embedding_model
    
    # Startup
    try:
        # Create database tables
        create_tables()
        logging.info("Database tables created successfully")
        
        # Load available models from Ollama
        load_available_models()
        
        # Get configuration from environment variables
        use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logging.info("Embedding model loaded successfully")
        
        # Note: Document retriever and research agent are now created per-request
        # with user-scoped database sessions for multi-tenant support
        
        logging.info("Research agent system initialized successfully")
        if current_model:
            logging.info(f"Using LLM model: {current_model}")
        logging.info("Starting Multi-hop Research Agent API (Postgres Version)...")
    except Exception as e:
        logging.error(f"Failed to initialize agents: {e}")
        research_agent = None
        embedding_model = None
    
    yield
    
    # Shutdown
    logging.info("Shutting down Multi-hop Research Agent API...")
    
    # Clear global variables
    available_models = []
    current_model = None
    research_agent = None
    embedding_model = None
    logging.info("Global variables cleared.")

# Initialize FastAPI app
app = FastAPI(
    title="Multi-hop Research Agent",
    description="A research agent that uses Postgres + pgvector for document retrieval and multi-hop reasoning",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication router
app.include_router(auth_router)

# Mount static files for React app
if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

# Request/Response models
class QuestionRequest(BaseModel):
    question: str
    per_sub_k: int = 3
    
    @field_validator('per_sub_k')
    @classmethod
    def validate_per_sub_k(cls, v):
        if v < 1 or v > 20:
            raise ValueError("per_sub_k must be between 1 and 20")
        return v
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        if len(v) > 5000:
            raise ValueError("Question is too long (maximum 5000 characters)")
        return v.strip()

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

class ChatMessageResponse(BaseModel):
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
    selected_text: Optional[str] = None
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 10000:
            raise ValueError("Message is too long (maximum 10000 characters)")
        return v.strip()
    
    @field_validator('per_sub_k')
    @classmethod
    def validate_per_sub_k(cls, v):
        if v < 1 or v > 20:
            raise ValueError("per_sub_k must be between 1 and 20")
        return v
    
    @field_validator('selected_text')
    @classmethod
    def validate_selected_text(cls, v):
        if v and len(v) > 5000:
            raise ValueError("Selected text is too long (maximum 5000 characters)")
        return v

class ChatResponseModel(BaseModel):
    conversation_id: str
    message_id: str
    answer: str
    conversation_title: str
    message_count: int
    context_used: bool
    timestamp: str
    research_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[ChatMessageResponse]
    title: str
    message_count: int

class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"

class UpdateTitleRequest(BaseModel):
    title: str


@app.get("/")
async def root():
    """Serve React app or API information."""
    if os.path.exists("frontend/build/index.html"):
        return FileResponse("frontend/build/index.html")
    # Minimal info to prevent information disclosure
    return {
        "message": "Multi-hop Research Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Minimal information to prevent information disclosure.
    """
    return {
        "status": "healthy"
    }

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Ask a research question and get a multi-hop reasoned answer.
    
    Args:
        request: Question request with question text and optional per_sub_k parameter
        
    Returns:
        Research results with answer, subqueries, and citations
    """
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        # Get user-scoped research agent
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        
        # Ask the research agent
        result = user_research_agent.ask(
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
        
    except AgentError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )
    finally:
        if db_session:
            db_session.close()

@app.get("/export")
async def export_report(question: str, current_user: TokenData = Depends(get_current_active_user)):
    """
    Export research results as a markdown report.
    
    Args:
        question: The research question
        
    Returns:
        Markdown report file
    """
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        # Get user-scoped research agent
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        
        # Get research results
        result = user_research_agent.ask(question, per_sub_k=3)
        
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
    finally:
        if db_session:
            db_session.close()

@app.get("/stats")
async def get_stats(current_user: TokenData = Depends(get_current_active_user)):
    """Get statistics about the research agent."""
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        # Get user-scoped research agent
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        
        # Get collection stats
        stats = user_research_agent.get_collection_stats()
        
        return {
            "documents_in_database": stats.get("total_documents", 0),
            "agent_status": "active",
            "database_type": "Postgres + pgvector",
            **stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting stats: {str(e)}"
        )
    finally:
        if db_session:
            db_session.close()

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Upload a file (PDF, DOCX, or text) and add it to the research database.
    
    Args:
        file: Uploaded file (PDF, DOCX, or text)
        
    Returns:
        Upload result with processing information
    """
    from auth.validators import validate_file_upload_size, sanitize_string
    
    global embedding_model
    
    if embedding_model is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding model not initialized"
        )
    
    # Validate and sanitize filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    sanitized_filename = sanitize_string(file.filename, max_length=255)
    if not sanitized_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_extension = Path(sanitized_filename).suffix.lower()
    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    try:
        file_content = await file.read()
        
        # Validate file size
        try:
            validate_file_upload_size(len(file_content), max_size_mb=50)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Process and store the file using the new ingestion system
        from auth.database import SessionLocal
        db_session = None
        
        try:
            db_session = SessionLocal()
            result = process_and_store_file_content(
                db_session=db_session,
                user_id=current_user.user_id,
                file_content=file_content,
                filename=sanitized_filename,
                model=embedding_model
            )
            
            if result["success"]:
                return FileUploadResponse(
                    success=True,
                    filename=sanitized_filename,
                    message=result["message"],
                    file_type=file_extension,
                    word_count=result.get("word_count", 0),
                    chunks_added=result["chunks_added"]
                )
            else:
                raise HTTPException(status_code=400, detail=result["message"])
                
        finally:
            if db_session:
                db_session.close()

    except DocumentProcessingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(exc)}"
        )

@app.get("/collection-stats", response_model=CollectionStatsResponse)
async def get_collection_stats_endpoint(current_user: TokenData = Depends(get_current_active_user)):
    """
    Get detailed statistics about the document collection.
    
    Returns:
        Collection statistics including file types and counts
    """
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        # Get user-scoped research agent
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        
        # Get collection stats
        stats = user_research_agent.get_collection_stats()
        
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
    finally:
        if db_session:
            db_session.close()

@app.get("/supported-file-types")
async def get_supported_file_types(
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Get list of supported file types for upload (authentication required).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of supported file extensions
        
    Requires:
        User authentication
    """
    return {
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "max_file_size_mb": 50
    }

@app.get("/models")
async def get_available_models(
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Get list of available models from Ollama (authentication required).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of available models with their details
        
    Requires:
        User authentication
    """
    try:
        # Check if Ollama is enabled
        use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        if not use_ollama:
            return {
                "models": [],
                "ollama_enabled": False,
                "message": "Ollama is not enabled. Set USE_OLLAMA=true to enable model listing."
            }
        
        # Use in-memory models
        global available_models, current_model
        
        # Reload models if none are available
        if not available_models:
            load_available_models()
        
        return {
            "models": available_models,
            "ollama_enabled": True,
            "ollama_available": len(available_models) > 0,
            "current_model": current_model,
            "total_models": len(available_models)
        }
        
    except Exception as e:
        return {
            "models": [],
            "ollama_enabled": True,
            "ollama_available": False,
            "error": f"Error listing models: {str(e)}"
        }

class ModelChangeRequest(BaseModel):
    model_name: str

@app.post("/models/change")
async def change_model(
    request: ModelChangeRequest,
    current_user: TokenData = Depends(get_current_admin_user)
):
    """
    Change the current model for the research agent (admin only).
    
    Args:
        request: Model change request with model_name
        current_user: Current authenticated admin user
        
    Returns:
        Success message and new model info
        
    Requires:
        Admin authentication
    """
    global current_model, research_agent
    
    try:
        # Check if Ollama is enabled
        use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        if not use_ollama:
            raise HTTPException(
                status_code=400,
                detail="Ollama is not enabled. Set USE_OLLAMA=true to enable model changes."
            )
        
        # Reload models if none are available
        if not available_models:
            load_available_models()
        
        # Verify the model exists
        model_exists = any(model['name'] == request.model_name for model in available_models)
        if not model_exists:
            available_model_names = [model['name'] for model in available_models]
            raise HTTPException(
                status_code=400,
                detail=f"Model '{request.model_name}' not found. Available models: {available_model_names}"
            )
        
        # Set the new current model
        old_model = current_model
        success = set_current_model(request.model_name)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to set the new model"
            )
        
        # Note: Research agents are now created per-request with user-scoped sessions
        # No need to reinitialize global research agent
        
        return {
            "message": f"Model successfully changed to '{request.model_name}'",
            "new_model": request.model_name,
            "old_model": old_model,
            "restart_required": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error changing model: {str(e)}"
        )

# Chat endpoints
@app.post("/chat", response_model=ChatResponseModel)
async def chat_with_agent(
    request: ChatRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Chat with the research agent in a conversational context (user-scoped conversations).
    
    Args:
        request: Chat request with message and optional conversation_id
        
    Returns:
        Chat response with answer and conversation info
    """
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        # Get user-scoped research agent
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        
        # Create user-scoped conversation manager and chat agent
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        user_chat_agent = ChatAgent(user_research_agent, conversation_manager)
        
        # If selected text is provided, store it as a highlight
        if request.selected_text and request.conversation_id:
            conversation_manager.add_highlight(request.conversation_id, request.selected_text)
        
        # Create enhanced message with highlight context if selected text is provided
        enhanced_message = request.message
        if request.selected_text:
            enhanced_message = f"""[Context from user highlight]:
"{request.selected_text}"

[User question]:
"{request.message}" """
        
        response = user_chat_agent.process(
            message=enhanced_message,
            conversation_id=request.conversation_id,
            per_sub_k=request.per_sub_k,
            include_context=request.include_context
        )
        
        return ChatResponseModel(
            conversation_id=response.conversation_id,
            message_id=response.message_id,
            answer=response.answer,
            conversation_title=response.conversation_title,
            message_count=response.message_count,
            context_used=response.context_used,
            timestamp=response.timestamp,
            research_result=response.research_result.to_dict() if response.research_result else None,
            error=response.error
        )
        
    except AgentError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )
    finally:
        if db_session:
            db_session.close()

@app.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations(
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    List all conversations for the current user (admin can see all).
    
    Returns:
        List of conversation information
    """
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        conversations = conversation_manager.list_conversations()
        return [ConversationInfo(**conv) for conv in conversations]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing conversations: {str(e)}"
        )
    finally:
        if db_session:
            db_session.close()

@app.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str, 
    max_messages: int = 50,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Get conversation history (user can only access their own conversations).
    
    Args:
        conversation_id: ID of the conversation
        max_messages: Maximum number of messages to return
        
    Returns:
        Conversation history with messages
    """
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        messages = conversation_manager.get_conversation_history(conversation_id, max_messages)
        
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=[ChatMessageResponse(**msg.to_dict()) for msg in messages],
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
    finally:
        if db_session:
            db_session.close()

@app.post("/conversations", response_model=Dict[str, str])
async def create_conversation(
    request: CreateConversationRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Create a new conversation for the current user.
    
    Args:
        request: Request body with title
        
    Returns:
        Conversation ID
    """
    from auth.validators import validate_conversation_title, sanitize_string
    from auth.database import SessionLocal
    
    # Validate and sanitize title
    try:
        sanitized_title = sanitize_string(request.title, max_length=255)
        validate_conversation_title(sanitized_title)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    db_session = None
    
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        conversation_id = conversation_manager.create_conversation(sanitized_title)
        return {"conversation_id": conversation_id, "title": sanitized_title}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating conversation: {str(e)}"
        )
    finally:
        if db_session:
            db_session.close()

@app.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str, 
    request: UpdateTitleRequest,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Update conversation title (user can only update their own conversations).
    
    Args:
        conversation_id: ID of the conversation
        request: Request body with new title
        
    Returns:
        Success message
    """
    from auth.validators import validate_conversation_title, sanitize_string
    from auth.database import SessionLocal
    
    # Validate and sanitize title
    try:
        sanitized_title = sanitize_string(request.title, max_length=255)
        validate_conversation_title(sanitized_title)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    db_session = None
    
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        success = conversation_manager.update_conversation_title(conversation_id, sanitized_title)
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
    finally:
        if db_session:
            db_session.close()

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Delete a conversation (user can only delete their own conversations).
    
    Args:
        conversation_id: ID of the conversation
        
    Returns:
        Success message
    """
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        success = conversation_manager.delete_conversation(conversation_id)
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
    finally:
        if db_session:
            db_session.close()

@app.get("/conversations/{conversation_id}/suggestions")
async def get_follow_up_suggestions(
    conversation_id: str,
    current_user: TokenData = Depends(get_current_active_user)
):
    """
    Get follow-up question suggestions for a conversation (user can only access their own conversations).
    
    Args:
        conversation_id: ID of the conversation
        
    Returns:
        List of suggested follow-up questions
    """
    from auth.database import SessionLocal
    db_session = None
    
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        # Verify conversation exists and user has access
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        
        # Note: Follow-up suggestions would need to be implemented with user-scoped chat agent
        # For now, return empty suggestions
        suggestions = []
        return {"suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting suggestions: {str(e)}"
        )
    finally:
        if db_session:
            db_session.close()

if __name__ == "__main__":
    import uvicorn
    
    logging.info("Starting Multi-hop Research Agent API (Postgres Version)...")
    logging.info("Make sure you have run the Alembic migration to create the embeddings table")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
