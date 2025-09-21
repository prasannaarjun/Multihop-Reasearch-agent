import os
import glob
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import numpy as np
from file_processor import file_processor


def build_index(data_dir: str, persist_directory: str = "chroma_db") -> None:
    """
    Build Chroma index from files in data_dir.
    
    Args:
        data_dir: Directory containing supported files (.txt, .pdf, .tex)
        persist_directory: Directory to persist Chroma database
    """
    # Initialize Chroma client
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Create or get collection
    collection = client.get_or_create_collection(
        name="research_documents",
        metadata={"description": "Research documents for multi-hop retrieval"}
    )
    
    # Load sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Get all supported files
    supported_files = []
    for ext in file_processor.supported_extensions:
        pattern = os.path.join(data_dir, f"*{ext}")
        supported_files.extend(glob.glob(pattern))
    
    if not supported_files:
        print(f"No supported files found in {data_dir}")
        print(f"Supported extensions: {file_processor.supported_extensions}")
        return
    
    print(f"Found {len(supported_files)} supported files")
    
    # Process each file
    documents = []
    metadatas = []
    ids = []
    
    for i, file_path in enumerate(supported_files):
        try:
            # Use file processor to extract text
            file_data = file_processor.process_file(file_path)
            content = file_data['text']
            filename = file_data['filename']
            title = file_data['title']
            file_type = file_data['file_type']
            
            if not content:
                continue
            
            # Split content into chunks if too long (Chroma has limits)
            max_chunk_size = 10000  # Adjust as needed
            if len(content) > max_chunk_size:
                chunks = [content[i:i+max_chunk_size] for i in range(0, len(content), max_chunk_size)]
                for j, chunk in enumerate(chunks):
                    chunk_id = f"{filename}_{j}"
                    documents.append(chunk)
                    metadatas.append({
                        "filename": filename,
                        "title": f"{title} (Part {j+1})",
                        "text": chunk,
                        "chunk_index": j,
                        "file_type": file_type,
                        "word_count": len(chunk.split())
                    })
                    ids.append(chunk_id)
            else:
                documents.append(content)
                metadatas.append({
                    "filename": filename,
                    "title": title,
                    "text": content,
                    "chunk_index": 0,
                    "file_type": file_type,
                    "word_count": len(content.split())
                })
                ids.append(filename)
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    if documents:
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = model.encode(documents, normalize_embeddings=True)
        
        # Add to collection
        print(f"Adding {len(documents)} documents to Chroma collection...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings.tolist()
        )
        
        print(f"Successfully built index with {len(documents)} documents")
    else:
        print("No valid documents found to index")


def load_index(persist_directory: str = "chroma_db") -> tuple:
    """
    Load Chroma collection and embedding model.
    
    Args:
        persist_directory: Directory containing Chroma database
        
    Returns:
        Tuple of (collection, model)
    """
    # Initialize Chroma client
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Get collection
    try:
        collection = client.get_collection("research_documents")
    except Exception as e:
        raise Exception(f"Collection not found. Please build index first: {e}")
    
    # Load model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    return collection, model


def query_index(collection, model, text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Query Chroma collection for similar documents.
    
    Args:
        collection: Chroma collection
        model: Sentence transformer model
        text: Query text
        top_k: Number of results to return
        
    Returns:
        List of dictionaries with doc_id, title, snippet, score
    """
    # Generate query embedding
    query_embedding = model.encode([text], normalize_embeddings=True)
    
    # Query collection
    results = collection.query(
        query_embeddings=query_embedding.tolist(),
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


def add_file_to_index(file_content: bytes, filename: str, persist_directory: str = "chroma_db") -> Dict[str, Any]:
    """
    Add a single uploaded file to the existing Chroma index.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        persist_directory: Directory containing Chroma database
        
    Returns:
        Dictionary with processing results
    """
    # Initialize Chroma client
    client = chromadb.PersistentClient(path=persist_directory)
    
    # Get existing collection
    try:
        collection = client.get_collection("research_documents")
    except Exception as e:
        raise Exception(f"Collection not found. Please build index first: {e}")
    
    # Load model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Process the uploaded file
    try:
        file_data = file_processor.process_uploaded_file(file_content, filename)
        content = file_data['text']
        title = file_data['title']
        file_type = file_data['file_type']
        word_count = file_data['word_count']
        
        # Split content into chunks if too long
        max_chunk_size = 10000
        if len(content) > max_chunk_size:
            chunks = [content[i:i+max_chunk_size] for i in range(0, len(content), max_chunk_size)]
            documents = []
            metadatas = []
            ids = []
            
            for j, chunk in enumerate(chunks):
                chunk_id = f"{filename}_{j}"
                documents.append(chunk)
                metadatas.append({
                    "filename": filename,
                    "title": f"{title} (Part {j+1})",
                    "text": chunk,
                    "chunk_index": j,
                    "file_type": file_type,
                    "word_count": len(chunk.split())
                })
                ids.append(chunk_id)
        else:
            documents = [content]
            metadatas = [{
                "filename": filename,
                "title": title,
                "text": content,
                "chunk_index": 0,
                "file_type": file_type,
                "word_count": word_count
            }]
            ids = [filename]
        
        # Generate embeddings
        embeddings = model.encode(documents, normalize_embeddings=True)
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings.tolist()
        )
        
        return {
            "success": True,
            "filename": filename,
            "title": title,
            "file_type": file_type,
            "word_count": word_count,
            "chunks_added": len(documents),
            "message": f"Successfully added {filename} to the index"
        }
        
    except Exception as e:
        return {
            "success": False,
            "filename": filename,
            "error": str(e),
            "message": f"Failed to process {filename}: {str(e)}"
        }


def get_collection_stats(persist_directory: str = "chroma_db") -> Dict[str, Any]:
    """
    Get statistics about the Chroma collection.
    
    Args:
        persist_directory: Directory containing Chroma database
        
    Returns:
        Dictionary with collection statistics
    """
    try:
        client = chromadb.PersistentClient(path=persist_directory)
        collection = client.get_collection("research_documents")
        
        # Get basic stats
        total_docs = collection.count()
        
        # Get sample of documents to analyze file types
        sample_results = collection.get(limit=min(100, total_docs), include=['metadatas'])
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
    # Example usage
    data_dir = "data"  # Directory containing .txt files
    persist_dir = "chroma_db"
    
    # Build index
    print("Building index...")
    build_index(data_dir, persist_dir)
    
    # Load and test
    print("Loading index...")
    collection, model = load_index(persist_dir)
    
    # Test query
    test_query = "machine learning applications"
    print(f"\nTesting query: '{test_query}'")
    results = query_index(collection, model, test_query, top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']} (Score: {result['score']:.3f})")
        print(f"   {result['snippet']}")
