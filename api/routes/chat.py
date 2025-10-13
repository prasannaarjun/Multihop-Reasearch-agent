import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.schemas import ChatRequest, ChatResponseModel
from api.dependencies import get_conversation_manager_for_user, get_research_agent_for_user
from auth import get_current_active_user, TokenData
from agents.chat import ChatAgent


router = APIRouter()


@router.post("/chat", response_model=ChatResponseModel)
async def chat_with_agent(
    request: ChatRequest, current_user: TokenData = Depends(get_current_active_user)
):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        user_chat_agent = ChatAgent(user_research_agent, conversation_manager)

        if request.selected_text and request.conversation_id:
            conversation_manager.add_highlight(request.conversation_id, request.selected_text)

        enhanced_message = request.message
        if request.selected_text:
            enhanced_message = (
                f"""[Context from user highlight]:\n"{request.selected_text}"\n\n[User question]:\n"{request.message}" """
            )

        response = user_chat_agent.process(
            message=enhanced_message,
            conversation_id=request.conversation_id,
            per_sub_k=request.per_sub_k,
            include_context=request.include_context,
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
            error=response.error,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.post("/chat/stream")
async def chat_with_agent_streaming(
    request: ChatRequest, current_user: TokenData = Depends(get_current_active_user)
):
    from auth.database import SessionLocal
    from agents.shared.streaming_controller import streaming_manager

    db_session = None
    try:
        db_session = SessionLocal()
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        conversation_manager = get_conversation_manager_for_user(current_user, db_session)
        user_chat_agent = ChatAgent(user_research_agent, conversation_manager)

        request_id = str(uuid.uuid4())
        controller = streaming_manager.create_controller(request_id)
        # Bind ownership for authorization: only the requesting user can stop this stream
        controller.owner_user_id = current_user.user_id

        if request.selected_text and request.conversation_id:
            conversation_manager.add_highlight(request.conversation_id, request.selected_text)

        enhanced_message = request.message
        if request.selected_text:
            enhanced_message = (
                f"""[Context from user highlight]:\n"{request.selected_text}"\n\n[User question]:\n"{request.message}" """
            )

        def generate_streaming_response():
            try:
                for chunk in user_chat_agent.process_streaming(
                    message=enhanced_message,
                    conversation_id=request.conversation_id,
                    per_sub_k=request.per_sub_k,
                    include_context=request.include_context,
                    stop_flag=controller.stop_flag,
                ):
                    if controller.is_stopped():
                        break

                    try:
                        chunk_data = {"chunk": chunk, "request_id": request_id, "type": "content"}
                        json_data = json.dumps(chunk_data, ensure_ascii=False)
                        yield f"data: {json_data}\n\n"
                    except (TypeError, ValueError):
                        escaped_chunk = (
                            chunk.replace("\\", "\\\\")
                            .replace('"', '\\"')
                            .replace("\n", "\\n")
                            .replace("\r", "\\r")
                        )
                        yield (
                            f"data: {{\"chunk\": \"{escaped_chunk}\", \"request_id\": \"{request_id}\", \"type\": \"content\"}}\n\n"
                        )

                final_conversation = conversation_manager.get_conversation(request.conversation_id)
                research_metadata = {}
                if final_conversation and final_conversation.messages:
                    last_message = final_conversation.messages[-1]
                    if last_message.role == "assistant" and last_message.metadata:
                        research_metadata = {
                            "research_result": last_message.metadata.get("research_result", {}),
                            "subqueries": last_message.metadata.get("subqueries", []),
                            "citations_count": last_message.metadata.get("citations_count", 0),
                            "total_documents": last_message.metadata.get("total_documents", 0),
                        }

                completion_data = {
                    "request_id": request_id,
                    "type": "complete",
                    "conversation_id": request.conversation_id,
                    "message_count": len(final_conversation.messages) if final_conversation else 1,
                    **research_metadata,
                }
                try:
                    json_data = json.dumps(completion_data, ensure_ascii=False)
                    yield f"data: {json_data}\n\n"
                except (TypeError, ValueError):
                    yield (
                        f"data: {{\"request_id\": \"{request_id}\", \"type\": \"complete\", \"conversation_id\": \"{request.conversation_id}\"}}\n\n"
                    )
            except Exception as e:
                error_data = {"type": "error", "error": str(e), "request_id": request_id}
                try:
                    json_data = json.dumps(error_data, ensure_ascii=False)
                    yield f"data: {json_data}\n\n"
                except (TypeError, ValueError):
                    escaped_error = (
                        str(e)
                        .replace("\\", "\\\\")
                        .replace('"', '\\"')
                        .replace("\n", "\\n")
                        .replace("\r", "\\r")
                    )
                    yield (
                        f"data: {{\"type\": \"error\", \"error\": \"{escaped_error}\", \"request_id\": \"{request_id}\"}}\n\n"
                    )
            finally:
                streaming_manager.remove_controller(request_id)
                if db_session:
                    db_session.close()

        return StreamingResponse(
            generate_streaming_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8",
                "X-Request-ID": request_id,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing streaming chat: {str(e)}")


@router.post("/chat/stream/stop")
async def stop_streaming(request_id: str, current_user: TokenData = Depends(get_current_active_user)):
    from agents.shared.streaming_controller import streaming_manager
    # Enforce ownership: only the owner of the request_id can stop it
    controller = streaming_manager.get_controller(request_id)
    if not controller:
        return {"status": "not_found", "request_id": request_id}
    if controller.owner_user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to stop this stream")
    success = streaming_manager.stop_controller(request_id)
    if success:
        return {"status": "stopped", "request_id": request_id}
    return {"status": "not_found", "request_id": request_id}




