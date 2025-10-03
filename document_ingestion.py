"""
Document ingestion utilities for Postgres + pgvector.
Replaces Chroma-based document processing with Postgres embedding storage.
"""

import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from document_processing import process_file, SUPPORTED_EXTENSIONS, DocumentProcessingError
from embedding_storage import store_embedding
from agents.shared.models import ChatMessageDB


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 100 characters
            search_start = max(start + chunk_size - 100, start)
            for i in range(end - 1, search_start - 1, -1):
                if text[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def _get_or_create_document_system_conversation(db_session: Session, user_id: int) -> tuple[str, str]:
    """
    Get or create a single system conversation for document uploads per user.
    This prevents creating multiple conversations for each document upload.
    
    Args:
        db_session: Database session
        user_id: ID of the user
        
    Returns:
        Tuple of (conversation_id, message_id)
    """
    from agents.shared.models import ConversationDB, ChatMessageDB
    from sqlalchemy import and_
    
    # Look for existing system conversation for document uploads
    system_conversation = db_session.query(ConversationDB).filter(
        and_(
            ConversationDB.user_id == user_id,
            ConversationDB.conversation_metadata.like('%"source": "document_upload"%')
        )
    ).first()
    
    if system_conversation:
        # Use existing system conversation and create a new message for this document
        message_id = str(uuid.uuid4())
        system_message = ChatMessageDB(
            id=message_id,
            conversation_id=system_conversation.id,
            role="system",
            content="Document upload",
            message_metadata='{"source": "document_upload"}'
        )
        db_session.add(system_message)
        db_session.commit()
        return system_conversation.id, message_id
    else:
        # Create new system conversation and message
        conversation_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        system_conversation = ConversationDB(
            id=conversation_id,
            user_id=user_id,
            title="Document Uploads",
            conversation_metadata='{"source": "document_upload", "hidden": true}'
        )
        
        system_message = ChatMessageDB(
            id=message_id,
            conversation_id=conversation_id,
            role="system",
            content="Document upload system",
            message_metadata='{"source": "document_upload"}'
        )
        
        db_session.add(system_conversation)
        db_session.add(system_message)
        db_session.commit()
        return conversation_id, message_id


def process_and_store_document(
    db_session: Session,
    user_id: int,
    file_path: str,
    filename: str,
    model: SentenceTransformer,
    chunk_size: int = 1000,
    overlap: int = 200
) -> Dict[str, Any]:
    """
    Process a document and store its embeddings in Postgres.
    
    Args:
        db_session: Database session
        user_id: ID of the user who owns the document
        file_path: Path to the document file
        filename: Original filename
        model: Sentence transformer model for embeddings
        chunk_size: Size of text chunks
        overlap: Overlap between chunks
        
    Returns:
        Dictionary with processing results
    """
    try:
        # Process the file to extract text
        extracted_text = process_file(file_path)
        
        if not extracted_text.strip():
            return {
                "success": False,
                "message": "No text content extracted from file",
                "chunks_added": 0
            }
        
        # Get or create a single system conversation for document uploads per user
        conversation_id, message_id = _get_or_create_document_system_conversation(db_session, user_id)
        
        # Chunk the text
        chunks = chunk_text(extracted_text, chunk_size, overlap)
        
        # Generate embeddings for each chunk
        embeddings_added = 0
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding
                embedding = model.encode([chunk], normalize_embeddings=True)[0]
                
                # Prepare metadata
                metadata = {
                    "text": chunk,
                    "chunk_index": i,
                    "filename": filename,
                    "file_type": Path(filename).suffix.lower(),
                    "title": Path(filename).stem,
                    "total_chunks": len(chunks),
                    "source": "document_upload"
                }
                
                # Store embedding
                store_embedding(
                    db_session=db_session,
                    user_id=user_id,
                    message_id=message_id,
                    vector=embedding.tolist(),
                    metadata=metadata
                )
                
                embeddings_added += 1
                
            except Exception as e:
                logging.error(f"Error processing chunk {i}: {e}")
                continue
        
        return {
            "success": True,
            "message": f"Successfully processed {filename}",
            "chunks_added": embeddings_added,
            "total_chunks": len(chunks),
            "word_count": len(extracted_text.split()),
            "message_id": message_id
        }
        
    except DocumentProcessingError as e:
        return {
            "success": False,
            "message": f"Document processing error: {str(e)}",
            "chunks_added": 0
        }
    except Exception as e:
        db_session.rollback()
        return {
            "success": False,
            "message": f"Error processing document: {str(e)}",
            "chunks_added": 0
        }


def process_and_store_file_content(
    db_session: Session,
    user_id: int,
    file_content: bytes,
    filename: str,
    model: SentenceTransformer,
    chunk_size: int = 1000,
    overlap: int = 200
) -> Dict[str, Any]:
    """
    Process file content from bytes and store embeddings in Postgres.
    
    Args:
        db_session: Database session
        user_id: ID of the user who owns the document
        file_content: File content as bytes
        filename: Original filename
        model: Sentence transformer model for embeddings
        chunk_size: Size of text chunks
        overlap: Overlap between chunks
        
    Returns:
        Dictionary with processing results
    """
    from tempfile import TemporaryDirectory
    
    try:
        # Check file extension
        file_extension = Path(filename).suffix.lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            return {
                "success": False,
                "message": f"Unsupported file type: {file_extension}",
                "chunks_added": 0
            }
        
        # Write content to temporary file and process
        with TemporaryDirectory() as tmp_dir:
            temp_file = Path(tmp_dir) / filename
            temp_file.write_bytes(file_content)
            
            return process_and_store_document(
                db_session=db_session,
                user_id=user_id,
                file_path=str(temp_file),
                filename=filename,
                model=model,
                chunk_size=chunk_size,
                overlap=overlap
            )
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing file content: {str(e)}",
            "chunks_added": 0
        }


def batch_process_directory(
    db_session: Session,
    user_id: int,
    data_dir: str,
    model: SentenceTransformer,
    chunk_size: int = 1000,
    overlap: int = 200
) -> Dict[str, Any]:
    """
    Process all supported files in a directory and store embeddings.
    
    Args:
        db_session: Database session
        user_id: ID of the user who owns the documents
        data_dir: Directory containing files to process
        model: Sentence transformer model for embeddings
        chunk_size: Size of text chunks
        overlap: Overlap between chunks
        
    Returns:
        Dictionary with batch processing results
    """
    import glob
    
    try:
        # Get all supported files
        supported_files = []
        for ext in SUPPORTED_EXTENSIONS:
            pattern = os.path.join(data_dir, f"*{ext}")
            supported_files.extend(glob.glob(pattern))
        
        if not supported_files:
            return {
                "success": False,
                "message": f"No supported files found in {data_dir}",
                "files_processed": 0,
                "total_chunks": 0
            }
        
        # Process each file
        files_processed = 0
        total_chunks = 0
        errors = []
        
        for file_path in supported_files:
            try:
                filename = Path(file_path).name
                result = process_and_store_document(
                    db_session=db_session,
                    user_id=user_id,
                    file_path=file_path,
                    filename=filename,
                    model=model,
                    chunk_size=chunk_size,
                    overlap=overlap
                )
                
                if result["success"]:
                    files_processed += 1
                    total_chunks += result["chunks_added"]
                else:
                    errors.append(f"{filename}: {result['message']}")
                    
            except Exception as e:
                errors.append(f"{Path(file_path).name}: {str(e)}")
                continue
        
        return {
            "success": files_processed > 0,
            "message": f"Processed {files_processed} files with {total_chunks} total chunks",
            "files_processed": files_processed,
            "total_chunks": total_chunks,
            "errors": errors
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error processing directory: {str(e)}",
            "files_processed": 0,
            "total_chunks": 0
        }


def get_user_document_stats(db_session: Session, user_id: int) -> Dict[str, Any]:
    """
    Get statistics about a user's documents.
    
    Args:
        db_session: Database session
        user_id: ID of the user
        
    Returns:
        Dictionary with document statistics
    """
    try:
        from sqlalchemy import text
        
        # Get total embeddings count
        count_query = text("SELECT COUNT(*) FROM embeddings WHERE user_id = :user_id")
        result = db_session.execute(count_query, {"user_id": user_id})
        total_embeddings = result.scalar()
        
        # Get unique files count
        files_query = text("""
            SELECT COUNT(DISTINCT embedding_metadata->>'filename') 
            FROM embeddings 
            WHERE user_id = :user_id 
            AND embedding_metadata->>'filename' IS NOT NULL
        """)
        result = db_session.execute(files_query, {"user_id": user_id})
        unique_files = result.scalar()
        
        # Get file type distribution
        types_query = text("""
            SELECT 
                embedding_metadata->>'file_type' as file_type,
                COUNT(*) as count
            FROM embeddings 
            WHERE user_id = :user_id 
            AND embedding_metadata->>'file_type' IS NOT NULL
            GROUP BY embedding_metadata->>'file_type'
        """)
        result = db_session.execute(types_query, {"user_id": user_id})
        file_types = {row.file_type: row.count for row in result}
        
        return {
            "total_embeddings": total_embeddings,
            "unique_files": unique_files,
            "file_types": file_types,
            "user_id": user_id
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "total_embeddings": 0,
            "unique_files": 0,
            "file_types": {},
            "user_id": user_id
        }


