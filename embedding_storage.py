"""
Embedding storage utilities for Postgres + pgvector.
Replaces Chroma-based embedding storage with Postgres vector operations.
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_
from agents.shared.models import EmbeddingDB
from agents.shared.exceptions import AgentError


# Get embedding dimension from environment variable
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))


def store_embedding(
    db_session: Session,
    user_id: int,
    message_id: str,
    vector: List[float],
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Store an embedding in the Postgres database.
    
    Args:
        db_session: Database session
        user_id: ID of the user who owns the embedding
        message_id: ID of the chat message this embedding belongs to
        vector: Embedding vector as list of floats
        metadata: Optional metadata dictionary
        
    Returns:
        ID of the created embedding record
        
    Raises:
        AgentError: If validation fails or storage fails
    """
    try:
        # Validate vector length
        if len(vector) != EMBEDDING_DIM:
            raise AgentError(
                f"Vector dimension mismatch: expected {EMBEDDING_DIM}, got {len(vector)}"
            )
        
        # Validate vector contains only numeric values
        if not all(isinstance(x, (int, float)) for x in vector):
            raise AgentError("Vector must contain only numeric values")
        
        # Convert to numpy array for validation
        vector_array = np.array(vector, dtype=np.float32)
        
        # Check for NaN or infinite values
        if np.any(np.isnan(vector_array)) or np.any(np.isinf(vector_array)):
            raise AgentError("Vector contains NaN or infinite values")
        
        # Create embedding record
        embedding = EmbeddingDB(
            message_id=message_id,
            user_id=user_id,
            vector=vector_array.tolist(),  # Convert back to list for storage
            embedding_metadata=metadata or {}
        )
        
        # Add to session and commit
        db_session.add(embedding)
        db_session.commit()
        
        return embedding.id
        
    except Exception as e:
        db_session.rollback()
        if isinstance(e, AgentError):
            raise
        raise AgentError(f"Failed to store embedding: {str(e)}")


def retrieve_similar_embeddings(
    db_session: Session,
    user_id: int,
    query_vector: List[float],
    k: int = 3,
    similarity_threshold: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Retrieve similar embeddings using cosine similarity.
    
    Args:
        db_session: Database session
        user_id: ID of the user to search within
        query_vector: Query vector for similarity search
        k: Number of results to return
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        List of dictionaries with embedding data and similarity scores
        
    Raises:
        AgentError: If query fails
    """
    try:
        # Validate query vector
        if len(query_vector) != EMBEDDING_DIM:
            raise AgentError(
                f"Query vector dimension mismatch: expected {EMBEDDING_DIM}, got {len(query_vector)}"
            )
        
        # Convert to numpy array
        query_array = np.array(query_vector, dtype=np.float32)
        
        # Check for zero vector to avoid division by zero
        vector_norm = np.linalg.norm(query_array)
        if vector_norm == 0:
            raise AgentError("Query vector cannot be all zeros")
        
        # Normalize query vector for cosine similarity
        query_norm = query_array / vector_norm
        
        # Convert query vector to PostgreSQL array format for vector operations
        query_vector_array = f"[{','.join(map(str, query_vector))}]"
        
        # Use SQLAlchemy ORM with func for vector operations
        # Note: We use the original query_vector (not normalized) for the database query
        # as the database will handle the vector operations
        query = db_session.query(
            EmbeddingDB.id,
            EmbeddingDB.message_id,
            EmbeddingDB.user_id,
            EmbeddingDB.embedding_metadata,
            EmbeddingDB.created_at,
            (1 - func.cosine_distance(EmbeddingDB.vector, query_vector_array)).label('similarity_score')
        ).filter(
            and_(
                EmbeddingDB.user_id == user_id,
                func.cosine_distance(EmbeddingDB.vector, query_vector_array) <= (1 - similarity_threshold)
            )
        ).order_by(
            func.cosine_distance(EmbeddingDB.vector, query_vector_array)
        ).limit(k)
        
        # Execute query
        result = query.all()
        
        # Format results
        embeddings = []
        for row in result:
            # The similarity threshold is already applied in the query filter
            # but we double-check here for safety
            if row.similarity_score >= similarity_threshold:
                embeddings.append({
                    "id": row.id,
                    "message_id": row.message_id,
                    "user_id": row.user_id,
                    "metadata": row.embedding_metadata or {},
                    "created_at": row.created_at,
                    "similarity_score": float(row.similarity_score)
                })
        
        return embeddings
        
    except Exception as e:
        if isinstance(e, AgentError):
            raise
        raise AgentError(f"Failed to retrieve similar embeddings: {str(e)}")


def get_embedding_stats(db_session: Session, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get statistics about embeddings in the database.
    
    Args:
        db_session: Database session
        user_id: Optional user ID to filter by (None for all users)
        
    Returns:
        Dictionary with embedding statistics
    """
    try:
        if user_id:
            # Get stats for specific user using ORM
            total_embeddings = db_session.query(EmbeddingDB).filter(EmbeddingDB.user_id == user_id).count()
            
            # Get unique messages count using ORM
            unique_messages = db_session.query(EmbeddingDB.message_id).filter(
                EmbeddingDB.user_id == user_id
            ).distinct().count()
            
        else:
            # Get stats for all users using ORM
            total_embeddings = db_session.query(EmbeddingDB).count()
            
            # Get unique messages count using ORM
            unique_messages = db_session.query(EmbeddingDB.message_id).distinct().count()
            
            # Get unique users count using ORM
            unique_users = db_session.query(EmbeddingDB.user_id).distinct().count()
        
        stats = {
            "total_embeddings": total_embeddings,
            "unique_messages": unique_messages,
            "embedding_dimension": EMBEDDING_DIM
        }
        
        if not user_id:
            stats["unique_users"] = unique_users
        
        return stats
        
    except Exception as e:
        return {
            "error": str(e),
            "total_embeddings": 0,
            "unique_messages": 0,
            "embedding_dimension": EMBEDDING_DIM
        }


def delete_embeddings_by_message(db_session: Session, message_id: str) -> int:
    """
    Delete all embeddings for a specific message.
    
    Args:
        db_session: Database session
        message_id: ID of the message whose embeddings to delete
        
    Returns:
        Number of embeddings deleted
    """
    try:
        # Count embeddings before deletion using ORM
        count_before = db_session.query(EmbeddingDB).filter(EmbeddingDB.message_id == message_id).count()
        
        # Delete embeddings using ORM
        deleted_count = db_session.query(EmbeddingDB).filter(EmbeddingDB.message_id == message_id).delete()
        db_session.commit()
        
        return deleted_count
        
    except Exception as e:
        db_session.rollback()
        raise AgentError(f"Failed to delete embeddings: {str(e)}")


def delete_embeddings_by_user(db_session: Session, user_id: int) -> int:
    """
    Delete all embeddings for a specific user.
    
    Args:
        db_session: Database session
        user_id: ID of the user whose embeddings to delete
        
    Returns:
        Number of embeddings deleted
    """
    try:
        # Count embeddings before deletion using ORM
        count_before = db_session.query(EmbeddingDB).filter(EmbeddingDB.user_id == user_id).count()
        
        # Delete embeddings using ORM
        deleted_count = db_session.query(EmbeddingDB).filter(EmbeddingDB.user_id == user_id).delete()
        db_session.commit()
        
        return deleted_count
        
    except Exception as e:
        db_session.rollback()
        raise AgentError(f"Failed to delete user embeddings: {str(e)}")



