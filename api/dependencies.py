import os
import threading
import warnings
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import HTTPException, FastAPI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress bcrypt version warning similar to original
warnings.filterwarnings("ignore", message=".*bcrypt.*")

# External imports used across dependencies
from sentence_transformers import SentenceTransformer

from agents.research import ResearchAgent, DocumentRetriever
from agents.chat import ConversationManager
from agents.shared.exceptions import AgentError
from agents.shared.models import ConversationInfo
from ollama_client import OllamaClient


# Shared state
research_agent = None  # kept for compatibility (not used directly per-request)
current_model: Optional[str] = None
available_models = []
embedding_model: Optional[SentenceTransformer] = None

_model_lock = threading.Lock()


def get_conversation_manager_for_user(current_user, db_session=None) -> ConversationManager:
    """Get a conversation manager scoped to the current user."""
    if db_session is None:
        from auth.database import SessionLocal
        db_session = SessionLocal()
    return ConversationManager(
        db_session=db_session,
        current_user_id=current_user.user_id,
        is_admin=current_user.is_admin,
    )


def get_research_agent_for_user(current_user, db_session=None) -> ResearchAgent:
    """Get a research agent scoped to the current user."""
    global embedding_model, current_model

    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Embedding model not initialized")

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
            use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
            if not use_ollama:
                available_models = []
                current_model = None
                return

            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

            import requests

            try:
                response = requests.get(f"{ollama_base_url}/api/tags", timeout=10)
                response.raise_for_status()
                ollama_data = response.json()
            except requests.exceptions.RequestException:
                available_models = []
                current_model = None
                return

            models = []
            for model in ollama_data.get("models", []):
                model_info = {
                    "name": model.get("name", ""),
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", ""),
                    "family": model.get("details", {}).get("family", ""),
                    "format": model.get("details", {}).get("format", ""),
                    "families": model.get("details", {}).get("families", []),
                    "parameter_size": model.get("details", {}).get("parameter_size", ""),
                    "quantization_level": model.get("details", {}).get("quantization_level", ""),
                }
                models.append(model_info)

            available_models = models

            if not current_model and models:
                current_model = models[0]["name"]

        except Exception:
            available_models = []
            current_model = None


def set_current_model(model_name: str) -> bool:
    """Set the current model if it exists in available models."""
    global current_model

    with _model_lock:
        if not available_models:
            return False

        model_exists = any(model["name"] == model_name for model in available_models)
        if model_exists:
            current_model = model_name
            return True
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events (startup/shutdown)."""
    global research_agent, current_model, available_models, embedding_model

    try:
        # Create database tables
        from auth.database import create_tables

        create_tables()

        # Load available models from Ollama
        load_available_models()

        # Initialize embedding model
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    except Exception:
        research_agent = None
        embedding_model = None

    yield

    # Shutdown cleanup
    available_models = []
    current_model = None
    research_agent = None
    embedding_model = None



