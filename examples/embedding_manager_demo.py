#!/usr/bin/env python3
"""
Demonstration script for using the EmbeddingManager programmatically.

This script shows how to use the EmbeddingManager class directly in your code
without the interactive menu system.
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from embedding_manager import EmbeddingManager


def demo_embedding_manager():
    """Demonstrate the EmbeddingManager functionality."""
    print("Embedding Manager Demo")
    print("=" * 50)
    
    # Initialize the manager
    manager = EmbeddingManager()
    
    try:
        # 1. Get overall statistics
        print("\n1. Getting overall statistics...")
        stats = manager.get_embedding_statistics()
        print("Statistics:")
        for key, value in stats.items():
            if key != 'error':
                print(f"  {key}: {value}")
        
        # 2. List all users
        print("\n2. Listing all users...")
        users = manager.list_users_with_embeddings()
        print(f"Found {len(users)} users:")
        for user in users[:5]:  # Show first 5 users
            print(f"  User {user['id']}: {user['username']} ({user['embedding_count']} embeddings)")
        
        # 3. Get embeddings for the first user (if any)
        if users and users[0]['embedding_count'] > 0:
            user_id = users[0]['id']
            print(f"\n3. Getting embeddings for user {user_id}...")
            embeddings = manager.get_user_embeddings(user_id, limit=3)
            print(f"Found {len(embeddings)} embeddings:")
            for emb in embeddings:
                print(f"  Embedding {emb['id']}: {emb['message_content'][:50]}...")
        
        # 4. Show how to clear embeddings (commented out for safety)
        print("\n4. Embedding clearing functions available:")
        print("  - manager.clear_user_embeddings(user_id)")
        print("  - manager.clear_all_embeddings()")
        print("  (These are commented out for safety in this demo)")
        
        # Uncomment the following lines to actually clear embeddings (USE WITH CAUTION!)
        # if users and users[0]['embedding_count'] > 0:
        #     user_id = users[0]['id']
        #     print(f"\nClearing embeddings for user {user_id}...")
        #     count = manager.clear_user_embeddings(user_id)
        #     print(f"Cleared {count} embeddings")
        
    except Exception as e:
        print(f"Error during demo: {e}")
    
    finally:
        # The manager will automatically close the database connection
        print("\nDemo completed.")


def demo_specific_user(user_id: int):
    """Demonstrate functionality for a specific user."""
    print(f"Embedding Manager Demo - User {user_id}")
    print("=" * 50)
    
    manager = EmbeddingManager()
    
    try:
        # Get user embeddings
        print(f"Getting embeddings for user {user_id}...")
        embeddings = manager.get_user_embeddings(user_id, limit=10)
        
        if embeddings:
            print(f"Found {len(embeddings)} embeddings:")
            for i, emb in enumerate(embeddings, 1):
                print(f"\n{i}. Embedding ID: {emb['id']}")
                print(f"   Message ID: {emb['message_id']}")
                print(f"   Role: {emb['message_role']}")
                print(f"   Content: {emb['message_content']}")
                print(f"   Created: {emb['created_at']}")
                print(f"   Conversation: {emb['conversation_title']}")
        else:
            print("No embeddings found for this user.")
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Embedding Manager Demo")
    parser.add_argument("--user-id", type=int, help="Show details for specific user ID")
    
    args = parser.parse_args()
    
    if args.user_id:
        demo_specific_user(args.user_id)
    else:
        demo_embedding_manager()
