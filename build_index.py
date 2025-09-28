#!/usr/bin/env python3
"""
Script to build ChromaDB index from documents.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path so we can import from embeddings
sys.path.append(str(Path(__file__).parent))

from embeddings import build_index


def main():
    """Main function to build ChromaDB index."""
    print("ChromaDB Index Builder")
    print("=" * 30)
    
    # Check if data directory exists
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"Data directory '{data_dir}' not found.")
        print("Creating sample data directory...")
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Create a sample text file
        sample_file = os.path.join(data_dir, "sample.txt")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("""
This is a sample document for testing the multi-hop research agent.

Key topics covered:
- Machine Learning
- Natural Language Processing
- Vector Databases
- Document Processing

This document contains information about various AI technologies and their applications in research and development.
            """.strip())
        
        print(f"Created sample file: {sample_file}")
    
    print(f"Building index from directory: {data_dir}")
    print("Supported file types: .pdf, .docx, .tex, .latex, .txt")
    
    try:
        # Build the index
        build_index(data_dir)
        print("\nIndex building completed successfully!")
        
    except Exception as e:
        print(f"\nError building index: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
