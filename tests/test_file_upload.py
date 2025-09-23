#!/usr/bin/env python3
"""
Test script for file upload and processing functionality.
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from file_processor import file_processor
from embeddings import add_file_to_index, get_collection_stats

def test_file_processor():
    """Test the file processor with sample files."""
    print("Testing File Processor")
    print("=" * 50)
    
    # Test with existing text files
    data_dir = Path("data")
    if data_dir.exists():
        txt_files = list(data_dir.glob("*.txt"))
        if txt_files:
            test_file = txt_files[0]
            print(f"Testing with file: {test_file}")
            
            try:
                result = file_processor.process_file(str(test_file))
                print(f"✅ Success!")
                print(f"  Filename: {result['filename']}")
                print(f"  Title: {result['title']}")
                print(f"  File type: {result['file_type']}")
                print(f"  Word count: {result['word_count']}")
                print(f"  Text preview: {result['text'][:200]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("No text files found in data directory")
    else:
        print("Data directory not found")
    
    print(f"\nSupported file types: {file_processor.supported_extensions}")

def test_collection_stats():
    """Test collection statistics."""
    print("\nTesting Collection Stats")
    print("=" * 50)
    
    try:
        stats = get_collection_stats()
        if "error" in stats:
            print(f"❌ Error: {stats['error']}")
        else:
            print("✅ Collection stats retrieved successfully:")
            print(f"  Total documents: {stats['total_documents']}")
            print(f"  Unique files: {stats['unique_files']}")
            print(f"  File types: {stats['file_types']}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests."""
    print("File Upload and Processing Test")
    print("=" * 60)
    
    test_file_processor()
    test_collection_stats()
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    main()
