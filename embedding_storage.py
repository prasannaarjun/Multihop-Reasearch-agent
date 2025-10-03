"""
Embedding storage utilities for Postgres + pgvector.
Replaces Chroma-based embedding storage with Postgres vector operations.
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
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
        
        # Normalize query vector for cosine similarity
        query_norm = query_array / np.linalg.norm(query_array)
        
        # SQL query for vector similarity search
        # Convert query vector to string format for PostgreSQL
        query_vector_str = '[' + ','.join(map(str, query_vector)) + ']'
        
        sql_query = text(f"""
            SELECT 
                e.id,
                e.message_id,
                e.user_id,
                e.embedding_metadata,
                e.created_at,
                1 - (e.vector <=> '{query_vector_str}'::vector) as similarity_score
            FROM embeddings e
            WHERE e.user_id = :user_id
            ORDER BY e.vector <=> '{query_vector_str}'::vector
            LIMIT :k
        """)
        
        # Execute query
        result = db_session.execute(
            sql_query,
            {
                "query_vector": query_norm.tolist(),
                "user_id": user_id,
                "k": k
            }
        )
        
        # Format results
        embeddings = []
        for row in result:
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
            # Get stats for specific user
            count_query = text("SELECT COUNT(*) as count FROM embeddings WHERE user_id = :user_id")
            result = db_session.execute(count_query, {"user_id": user_id})
            total_embeddings = result.scalar()
            
            # Get unique messages count
            messages_query = text("""
                SELECT COUNT(DISTINCT message_id) as count 
                FROM embeddings 
                WHERE user_id = :user_id
            """)
            result = db_session.execute(messages_query, {"user_id": user_id})
            unique_messages = result.scalar()
            
        else:
            # Get stats for all users
            count_query = text("SELECT COUNT(*) as count FROM embeddings")
            result = db_session.execute(count_query)
            total_embeddings = result.scalar()
            
            # Get unique messages count
            messages_query = text("SELECT COUNT(DISTINCT message_id) as count FROM embeddings")
            result = db_session.execute(messages_query)
            unique_messages = result.scalar()
            
            # Get unique users count
            users_query = text("SELECT COUNT(DISTINCT user_id) as count FROM embeddings")
            result = db_session.execute(users_query)
            unique_users = result.scalar()
        
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
        # Count embeddings before deletion
        count_query = text("SELECT COUNT(*) FROM embeddings WHERE message_id = :message_id")
        result = db_session.execute(count_query, {"message_id": message_id})
        count_before = result.scalar()
        
        # Delete embeddings
        delete_query = text("DELETE FROM embeddings WHERE message_id = :message_id")
        db_session.execute(delete_query, {"message_id": message_id})
        db_session.commit()
        
        return count_before
        
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
        # Count embeddings before deletion
        count_query = text("SELECT COUNT(*) FROM embeddings WHERE user_id = :user_id")
        result = db_session.execute(count_query, {"user_id": user_id})
        count_before = result.scalar()
        
        # Delete embeddings
        delete_query = text("DELETE FROM embeddings WHERE user_id = :user_id")
        db_session.execute(delete_query, {"user_id": user_id})
        db_session.commit()
        
        return count_before
        
    except Exception as e:
        db_session.rollback()
        raise AgentError(f"Failed to delete user embeddings: {str(e)}")



