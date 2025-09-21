from typing import List, Dict, Any
from embeddings import load_index, query_index


class Retriever:
    """
    Retriever class for querying Chroma collection.
    """
    
    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize retriever by loading Chroma collection and model.
        
        Args:
            persist_directory: Directory containing Chroma database
        """
        self.collection, self.model = load_index(persist_directory)
        print(f"Retriever initialized with collection containing {self.collection.count()} documents")
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most relevant documents for a query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of dictionaries with doc_id, title, snippet, score
        """
        return query_index(self.collection, self.model, query, top_k)


if __name__ == "__main__":
    # Test the retriever
    print("Initializing retriever...")
    retriever = Retriever("chroma_db")
    
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
