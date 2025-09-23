"""
Document Retriever for Multi-hop Research Agent
Handles document retrieval from Chroma database.
"""

from typing import List, Dict, Any
from ..shared.interfaces import IRetriever
from ..shared.exceptions import RetrievalError


class DocumentRetriever(IRetriever):
    """
    Document retriever that queries Chroma collection for relevant documents.
    """
    
    def __init__(self, collection, model):
        """
        Initialize retriever with Chroma collection and embedding model.
        
        Args:
            collection: Chroma collection instance
            model: Sentence transformer model
        """
        self.collection = collection
        self.model = model
        print(f"Document retriever initialized with collection containing {self.collection.count()} documents")
    
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
            query_embedding = self.model.encode([query], normalize_embeddings=True)
            
            # Query collection
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Convert distance to similarity score (1 - distance for cosine similarity)
                    score = 1 - distance
                    
                    # Create snippet (first 200 chars)
                    snippet = doc[:200] + "..." if len(doc) > 200 else doc
                    
                    formatted_results.append({
                        'doc_id': results['ids'][0][i],
                        'title': metadata.get('title', 'Unknown'),
                        'snippet': snippet,
                        'score': float(score),
                        'filename': metadata.get('filename', 'Unknown'),
                        'full_text': doc
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
            total_docs = self.collection.count()
            
            # Get sample of documents to analyze file types
            sample_results = self.collection.get(limit=min(100, total_docs), include=['metadatas'])
            file_types = {}
            filenames = set()
            
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    file_type = metadata.get('file_type', 'unknown')
                    file_types[file_type] = file_types.get(file_type, 0) + 1
                    filenames.add(metadata.get('filename', 'unknown'))
            
            return {
                "total_documents": total_docs,
                "unique_files": len(filenames),
                "file_types": file_types,
                "collection_name": "research_documents"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total_documents": 0,
                "unique_files": 0,
                "file_types": {},
                "collection_name": "research_documents"
            }


if __name__ == "__main__":
    # Test the document retriever
    from embeddings import load_index
    
    print("Loading index...")
    try:
        collection, model = load_index("chroma_db")
        retriever = DocumentRetriever(collection, model)
        
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
                
    except Exception as e:
        print(f"Error: {e}")
