"""
Document Retriever for Multi-hop Research Agent
Handles document retrieval from Postgres + pgvector database.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, text
from sentence_transformers import SentenceTransformer
from ..shared.interfaces import IRetriever
from ..shared.exceptions import RetrievalError
from embedding_storage import retrieve_similar_embeddings
from agents.shared.models import EmbeddingDB


class DocumentRetriever(IRetriever):
    """
    Document retriever that queries Postgres + pgvector for relevant documents.
    """
    
    def __init__(self, db_session: Session, model: SentenceTransformer, user_id: int):
        """
        Initialize retriever with database session and embedding model.
        
        Args:
            db_session: Database session for Postgres queries
            model: Sentence transformer model for generating embeddings
            user_id: User ID for multi-tenant isolation
        """
        self.db_session = db_session
        self.model = model
        self.user_id = user_id
        print(f"Document retriever initialized for user {user_id}")
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of dictionaries with doc_id, title, snippet, score
            
        Raises:
            RetrievalError: If retrieval fails
        """
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], normalize_embeddings=True)[0]
            
            # Query Postgres for similar embeddings
            embedding_results = retrieve_similar_embeddings(
                db_session=self.db_session,
                user_id=self.user_id,
                query_vector=query_embedding.tolist(),
                k=top_k
            )
            
            # Format results
            formatted_results = []
            for result in embedding_results:
                metadata = result.get('metadata', {})
                
                # Extract text content from metadata
                text_content = metadata.get('text', '')
                if not text_content:
                    continue
                
                # Create snippet (first 200 chars)
                snippet = text_content[:200] + "..." if len(text_content) > 200 else text_content
                
                formatted_results.append({
                    'doc_id': result['id'],
                    'title': metadata.get('title', 'Unknown'),
                    'snippet': snippet,
                    'score': result['similarity_score'],
                    'filename': metadata.get('filename', 'Unknown'),
                    'full_text': text_content,
                    'message_id': result['message_id'],
                    'chunk_index': metadata.get('chunk_index', 0)
                })
            
            return formatted_results
            
        except Exception as e:
            raise RetrievalError(f"Failed to retrieve documents: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            from embedding_storage import get_embedding_stats
            
            # Get embedding statistics
            stats = get_embedding_stats(self.db_session, self.user_id)
            
            if "error" in stats:
                return {
                    "error": stats["error"],
                    "total_documents": 0,
                    "unique_files": 0,
                    "file_types": {},
                    "collection_name": "postgres_embeddings"
                }
            
            # Get file type distribution from metadata using JSONB operators
            # Use raw SQL with text() for JSONB ->> operator
            file_types_query = text("""
                SELECT 
                    embedding_metadata->>'file_type' as file_type,
                    COUNT(*) as count
                FROM embeddings 
                WHERE user_id = :user_id 
                AND embedding_metadata->>'file_type' IS NOT NULL
                GROUP BY embedding_metadata->>'file_type'
            """)
            file_types_result = self.db_session.execute(file_types_query, {"user_id": self.user_id})
            file_types = {row.file_type: row.count for row in file_types_result if row.file_type}
            
            # Get unique filenames using JSONB operators
            filenames_query = text("""
                SELECT DISTINCT embedding_metadata->>'filename' as filename
                FROM embeddings 
                WHERE user_id = :user_id 
                AND embedding_metadata->>'filename' IS NOT NULL
            """)
            filenames_result = self.db_session.execute(filenames_query, {"user_id": self.user_id})
            unique_files = len([row.filename for row in filenames_result if row.filename])
            
            return {
                "total_documents": stats["total_embeddings"],
                "unique_files": unique_files,
                "file_types": file_types,
                "collection_name": "postgres_embeddings",
                "embedding_dimension": stats["embedding_dimension"]
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total_documents": 0,
                "unique_files": 0,
                "file_types": {},
                "collection_name": "postgres_embeddings"
            }


if __name__ == "__main__":
    # Test the document retriever
    from sentence_transformers import SentenceTransformer
    from auth.database import SessionLocal
    
    print("Testing Postgres Document Retriever...")
    try:
        # Initialize database session
        db_session = SessionLocal()
        
        # Load embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create retriever (using user_id=1 for testing)
        retriever = DocumentRetriever(db_session, model, user_id=1)
        
        # Test queries
        test_queries = [
            "artificial intelligence applications",
            "machine learning algorithms",
            "data science techniques"
        ]
        
        for query in test_queries:
            print(f"\n{'='*50}")
            print(f"Query: {query}")
            print('='*50)
            
            results = retriever.retrieve(query, top_k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. {result['title']} (Score: {result['score']:.3f})")
                    print(f"   File: {result['filename']}")
                    print(f"   Snippet: {result['snippet']}")
            else:
                print("No results found")
        
        # Test collection stats
        print(f"\n{'='*50}")
        print("Collection Stats:")
        print('='*50)
        stats = retriever.get_collection_stats()
        print(f"Total documents: {stats.get('total_documents', 0)}")
        print(f"Unique files: {stats.get('unique_files', 0)}")
        print(f"File types: {stats.get('file_types', {})}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'db_session' in locals():
            db_session.close()
