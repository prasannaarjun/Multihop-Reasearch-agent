from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from api.schemas import (
    ConversationHistoryResponse,
    ChatMessageResponse,
    CreateConversationRequest,
    UpdateTitleRequest,
)
from api.dependencies import get_conversation_manager_for_user
from auth import get_current_active_user, TokenData
from agents.shared.models import ConversationInfo


router = APIRouter()


@router.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations(current_user: TokenData = Depends(get_current_active_user)):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        conversations = conversation_manager.list_conversations()
        return [ConversationInfo(**conv) for conv in conversations]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    max_messages: int = 50,
    current_user: TokenData = Depends(get_current_active_user),
):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = conversation_manager.get_conversation_history(conversation_id, max_messages)
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=[ChatMessageResponse(**msg.to_dict()) for msg in messages],
            title=conversation.title,
            message_count=len(conversation.messages),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.post("/conversations", response_model=Dict[str, str])
async def create_conversation(
    request: CreateConversationRequest, current_user: TokenData = Depends(get_current_active_user)
):
    from auth.validators import validate_conversation_title, sanitize_string
    from auth.database import SessionLocal

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
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    request: UpdateTitleRequest,
    current_user: TokenData = Depends(get_current_active_user),
):
    from auth.validators import validate_conversation_title, sanitize_string
    from auth.database import SessionLocal

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
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating conversation title: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str, current_user: TokenData = Depends(get_current_active_user)
):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        success = conversation_manager.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.get("/conversations/{conversation_id}/suggestions")
async def get_follow_up_suggestions(
    conversation_id: str, current_user: TokenData = Depends(get_current_active_user)
):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        suggestions = []
        return {"suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")
    finally:
        if db_session:
            db_session.close()





