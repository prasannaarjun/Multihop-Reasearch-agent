#!/usr/bin/env python3
"""
Script to clear all vectors from ChromaDB.
This will delete all documents from the 'research_documents' collection.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path so we can import from embeddings
sys.path.append(str(Path(__file__).parent))

from embeddings import clear_index, delete_collection


def main():
    """Main function to clear ChromaDB vectors."""
    print("ChromaDB Vector Deletion Script")
    print("=" * 40)
    
    # Check if chroma_db directory exists
    chroma_dir = "chroma_db"
    if not os.path.exists(chroma_dir):
        print(f"ChromaDB directory '{chroma_dir}' not found.")
        print("No vectors to delete.")
        return
    
    print(f"ChromaDB directory found: {chroma_dir}")
    
    # Ask user what they want to do
    print("\nChoose an option:")
    print("1. Clear all vectors (keep collection)")
    print("2. Delete entire collection")
    print("3. Cancel")
    
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\nClearing all vectors from the collection...")
            clear_index(chroma_dir)
            break
        elif choice == "2":
            print("\nDeleting entire collection...")
            delete_collection(chroma_dir)
            break
        elif choice == "3":
            print("Operation cancelled.")
            return
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    print("\nOperation completed!")


if __name__ == "__main__":
    main()
