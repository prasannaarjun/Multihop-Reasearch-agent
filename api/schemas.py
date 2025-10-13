from typing import Any, Dict, List, Optional

from pydantic import BaseModel, field_validator


class QuestionRequest(BaseModel):
    question: str
    per_sub_k: int = 3

    @field_validator("per_sub_k")
    @classmethod
    def validate_per_sub_k(cls, v):
        if v < 1 or v > 20:
            raise ValueError("per_sub_k must be between 1 and 20")
        return v

    @field_validator("question")
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

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 10000:
            raise ValueError("Message is too long (maximum 10000 characters)")
        return v.strip()

    @field_validator("per_sub_k")
    @classmethod
    def validate_per_sub_k(cls, v):
        if v < 1 or v > 20:
            raise ValueError("per_sub_k must be between 1 and 20")
        return v

    @field_validator("selected_text")
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


class ModelChangeRequest(BaseModel):
    model_name: str



