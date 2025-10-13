import os
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api.schemas import (
    QuestionRequest,
    QuestionResponse,
    FileUploadResponse,
    CollectionStatsResponse,
)
from api.dependencies import get_research_agent_for_user

from auth import get_current_active_user, TokenData

from report import generate_markdown_report, save_report
from document_processing import SUPPORTED_EXTENSIONS, DocumentProcessingError
from document_ingestion import process_and_store_file_content


router = APIRouter()


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest, current_user: TokenData = Depends(get_current_active_user)
):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        user_research_agent = get_research_agent_for_user(current_user, db_session)

        result = user_research_agent.ask(
            question=request.question, per_sub_k=request.per_sub_k
        )

        return QuestionResponse(
            question=result["question"],
            answer=result["answer"],
            subqueries=result["subqueries"],
            citations=result["citations"],
            total_documents=result["total_documents"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.get("/export")
async def export_report(question: str, current_user: TokenData = Depends(get_current_active_user)):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        user_research_agent = get_research_agent_for_user(current_user, db_session)

        result = user_research_agent.ask(question, per_sub_k=3)
        report = generate_markdown_report(result)
        filepath = save_report(report)

        return FileResponse(
            path=filepath, filename=os.path.basename(filepath), media_type="text/markdown"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.get("/stats")
async def get_stats(current_user: TokenData = Depends(get_current_active_user)):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        stats = user_research_agent.get_collection_stats()
        return {
            "documents_in_database": stats.get("total_documents", 0),
            "agent_status": "active",
            "database_type": "Postgres + pgvector",
            **stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...), current_user: TokenData = Depends(get_current_active_user)
):
    from api.dependencies import embedding_model
    from auth.validators import validate_file_upload_size, sanitize_string

    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Embedding model not initialized")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    sanitized_filename = sanitize_string(file.filename, max_length=255)
    if not sanitized_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_extension = Path(sanitized_filename).suffix.lower()
    if file_extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    try:
        file_content = await file.read()
        try:
            validate_file_upload_size(len(file_content), max_size_mb=50)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

        from auth.database import SessionLocal

        db_session = None
        try:
            db_session = SessionLocal()
            result = process_and_store_file_content(
                db_session=db_session,
                user_id=current_user.user_id,
                file_content=file_content,
                filename=sanitized_filename,
                model=embedding_model,
            )

            if result["success"]:
                return FileUploadResponse(
                    success=True,
                    filename=sanitized_filename,
                    message=result["message"],
                    file_type=file_extension,
                    word_count=result.get("word_count", 0),
                    chunks_added=result["chunks_added"],
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
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(exc)}")


@router.get("/collection-stats", response_model=CollectionStatsResponse)
async def get_collection_stats_endpoint(
    current_user: TokenData = Depends(get_current_active_user),
):
    from auth.database import SessionLocal

    db_session = None
    try:
        db_session = SessionLocal()
        user_research_agent = get_research_agent_for_user(current_user, db_session)
        stats = user_research_agent.get_collection_stats()
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        return CollectionStatsResponse(
            total_documents=stats["total_documents"],
            unique_files=stats["unique_files"],
            file_types=stats["file_types"],
            collection_name=stats["collection_name"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection stats: {str(e)}")
    finally:
        if db_session:
            db_session.close()


@router.get("/supported-file-types")
async def get_supported_file_types(current_user: TokenData = Depends(get_current_active_user)):
    return {"supported_extensions": sorted(SUPPORTED_EXTENSIONS), "max_file_size_mb": 50}




