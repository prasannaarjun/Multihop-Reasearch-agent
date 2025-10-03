#!/usr/bin/env python3
"""
Embedding Management Script

This script provides functionality to view and manage user embeddings in the database.
It allows you to:
- List all users and their embedding counts
- View detailed embedding information for specific users
- Clear embeddings for specific users or all users
- View overall embedding statistics

Usage:
    python embedding_manager.py
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth.database import SessionLocal, User
from agents.shared.models import EmbeddingDB, ChatMessageDB, ConversationDB
from embedding_storage import get_embedding_stats, delete_embeddings_by_user, delete_embeddings_by_message
from sqlalchemy import text, func
from sqlalchemy.orm import joinedload

# Load environment variables
load_dotenv()


class EmbeddingManager:
    """Main class for managing embeddings."""
    
    def __init__(self):
        """Initialize the embedding manager."""
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database connection when object is destroyed."""
        if hasattr(self, 'db'):
            self.db.close()
    
    def list_users_with_embeddings(self) -> List[Dict[str, Any]]:
        """
        List all users with their embedding counts and statistics.
        
        Returns:
            List of dictionaries containing user information and embedding stats
        """
        try:
            # Query to get users with their embedding counts
            query = text("""
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.full_name,
                    u.created_at,
                    u.last_login,
                    COUNT(e.id) as embedding_count,
                    COUNT(DISTINCT e.message_id) as unique_messages,
                    MIN(e.created_at) as first_embedding,
                    MAX(e.created_at) as last_embedding
                FROM users u
                LEFT JOIN embeddings e ON u.id = e.user_id
                GROUP BY u.id, u.username, u.email, u.full_name, u.created_at, u.last_login
                ORDER BY embedding_count DESC, u.username
            """)
            
            result = self.db.execute(query)
            users = []
            
            for row in result:
                users.append({
                    'id': row.id,
                    'username': row.username,
                    'email': row.email,
                    'full_name': row.full_name or 'N/A',
                    'created_at': row.created_at,
                    'last_login': row.last_login,
                    'embedding_count': row.embedding_count or 0,
                    'unique_messages': row.unique_messages or 0,
                    'first_embedding': row.first_embedding,
                    'last_embedding': row.last_embedding
                })
            
            return users
            
        except Exception as e:
            print(f"Error listing users: {e}")
            return []
    
    def get_user_embeddings(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get detailed embedding information for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of embeddings to return
            
        Returns:
            List of dictionaries containing embedding details
        """
        try:
            # Query to get embeddings with related message and conversation info
            query = text("""
                SELECT 
                    e.id,
                    e.message_id,
                    e.created_at,
                    e.embedding_metadata,
                    cm.role,
                    cm.content,
                    cm.created_at as message_created_at,
                    c.title as conversation_title,
                    c.id as conversation_id
                FROM embeddings e
                JOIN chat_messages cm ON e.message_id = cm.id
                JOIN conversations c ON cm.conversation_id = c.id
                WHERE e.user_id = :user_id
                ORDER BY e.created_at DESC
                LIMIT :limit
            """)
            
            result = self.db.execute(query, {"user_id": user_id, "limit": limit})
            embeddings = []
            
            for row in result:
                # Truncate content for display
                content_preview = row.content[:100] + "..." if len(row.content) > 100 else row.content
                
                embeddings.append({
                    'id': row.id,
                    'message_id': row.message_id,
                    'created_at': row.created_at,
                    'metadata': row.embedding_metadata or {},
                    'message_role': row.role,
                    'message_content': content_preview,
                    'message_created_at': row.message_created_at,
                    'conversation_title': row.conversation_title,
                    'conversation_id': row.conversation_id
                })
            
            return embeddings
            
        except Exception as e:
            print(f"Error getting user embeddings: {e}")
            return []
    
    def get_embedding_statistics(self) -> Dict[str, Any]:
        """
        Get overall embedding statistics.
        
        Returns:
            Dictionary containing embedding statistics
        """
        try:
            stats = get_embedding_stats(self.db)
            
            # Get additional statistics
            query = text("""
                SELECT 
                    COUNT(DISTINCT user_id) as total_users,
                    AVG(embedding_count) as avg_embeddings_per_user,
                    MAX(embedding_count) as max_embeddings_per_user
                FROM (
                    SELECT user_id, COUNT(*) as embedding_count
                    FROM embeddings
                    GROUP BY user_id
                ) user_counts
            """)
            
            result = self.db.execute(query)
            row = result.fetchone()
            
            if row:
                stats.update({
                    'total_users_with_embeddings': row.total_users or 0,
                    'avg_embeddings_per_user': float(row.avg_embeddings_per_user or 0),
                    'max_embeddings_per_user': row.max_embeddings_per_user or 0
                })
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def clear_user_embeddings(self, user_id: int) -> int:
        """
        Clear all embeddings for a specific user.
        
        Args:
            user_id: ID of the user whose embeddings to clear
            
        Returns:
            Number of embeddings deleted
        """
        try:
            count = delete_embeddings_by_user(self.db, user_id)
            print(f"Deleted {count} embeddings for user {user_id}")
            return count
        except Exception as e:
            print(f"Error clearing user embeddings: {e}")
            return 0
    
    def clear_all_embeddings(self) -> int:
        """
        Clear all embeddings from the database.
        
        Returns:
            Number of embeddings deleted
        """
        try:
            # Get count before deletion
            count_query = text("SELECT COUNT(*) FROM embeddings")
            result = self.db.execute(count_query)
            count_before = result.scalar()
            
            # Delete all embeddings
            delete_query = text("DELETE FROM embeddings")
            self.db.execute(delete_query)
            self.db.commit()
            
            print(f"Deleted {count_before} embeddings from the database")
            return count_before
            
        except Exception as e:
            self.db.rollback()
            print(f"Error clearing all embeddings: {e}")
            return 0
    
    def format_datetime(self, dt) -> str:
        """Format datetime for display."""
        if dt is None:
            return "N/A"
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def display_users(self, users: List[Dict[str, Any]]):
        """Display users in a formatted table."""
        if not users:
            print("No users found.")
            return
        
        print("\n" + "="*120)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Full Name':<20} {'Embeddings':<10} {'Messages':<10} {'Last Login':<20}")
        print("="*120)
        
        for user in users:
            print(f"{user['id']:<5} {user['username']:<20} {user['email']:<30} {user['full_name']:<20} "
                  f"{user['embedding_count']:<10} {user['unique_messages']:<10} {self.format_datetime(user['last_login']):<20}")
        
        print("="*120)
    
    def display_embeddings(self, embeddings: List[Dict[str, Any]], user_info: Dict[str, Any]):
        """Display embeddings in a formatted table."""
        if not embeddings:
            print(f"No embeddings found for user {user_info['username']}.")
            return
        
        print(f"\nEmbeddings for user: {user_info['username']} (ID: {user_info['id']})")
        print("="*150)
        print(f"{'Embedding ID':<15} {'Message ID':<15} {'Role':<10} {'Content Preview':<50} {'Created':<20} {'Conversation':<30}")
        print("="*150)
        
        for emb in embeddings:
            print(f"{emb['id']:<15} {emb['message_id']:<15} {emb['message_role']:<10} "
                  f"{emb['message_content']:<50} {self.format_datetime(emb['created_at']):<20} "
                  f"{emb['conversation_title']:<30}")
        
        print("="*150)
    
    def display_statistics(self, stats: Dict[str, Any]):
        """Display embedding statistics."""
        print("\n" + "="*60)
        print("EMBEDDING STATISTICS")
        print("="*60)
        
        for key, value in stats.items():
            if key == 'error':
                print(f"Error: {value}")
            else:
                # Format the key for display
                display_key = key.replace('_', ' ').title()
                if isinstance(value, float):
                    print(f"{display_key}: {value:.2f}")
                else:
                    print(f"{display_key}: {value}")
        
        print("="*60)


def main():
    """Main function to run the embedding manager."""
    manager = EmbeddingManager()
    
    while True:
        print("\n" + "="*60)
        print("EMBEDDING MANAGEMENT SYSTEM")
        print("="*60)
        print("1. List all users with embedding counts")
        print("2. View embeddings for a specific user")
        print("3. View overall statistics")
        print("4. Clear embeddings for a specific user")
        print("5. Clear all embeddings")
        print("6. Exit")
        print("="*60)
        
        try:
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == '1':
                print("\nLoading users...")
                users = manager.list_users_with_embeddings()
                manager.display_users(users)
                
            elif choice == '2':
                user_id = input("Enter user ID: ").strip()
                if not user_id.isdigit():
                    print("Invalid user ID. Please enter a number.")
                    continue
                
                user_id = int(user_id)
                
                # Get user info first
                users = manager.list_users_with_embeddings()
                user_info = next((u for u in users if u['id'] == user_id), None)
                
                if not user_info:
                    print(f"User with ID {user_id} not found.")
                    continue
                
                limit = input("Enter limit for embeddings to display (default 50): ").strip()
                limit = int(limit) if limit.isdigit() else 50
                
                print(f"\nLoading embeddings for user {user_info['username']}...")
                embeddings = manager.get_user_embeddings(user_id, limit)
                manager.display_embeddings(embeddings, user_info)
                
            elif choice == '3':
                print("\nLoading statistics...")
                stats = manager.get_embedding_statistics()
                manager.display_statistics(stats)
                
            elif choice == '4':
                user_id = input("Enter user ID to clear embeddings: ").strip()
                if not user_id.isdigit():
                    print("Invalid user ID. Please enter a number.")
                    continue
                
                user_id = int(user_id)
                
                # Confirm deletion
                confirm = input(f"Are you sure you want to clear all embeddings for user {user_id}? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    count = manager.clear_user_embeddings(user_id)
                    print(f"Successfully cleared {count} embeddings for user {user_id}")
                else:
                    print("Operation cancelled.")
                
            elif choice == '5':
                # Confirm deletion
                confirm = input("Are you sure you want to clear ALL embeddings? This cannot be undone! (yes/no): ").strip().lower()
                if confirm in ['yes', 'y']:
                    count = manager.clear_all_embeddings()
                    print(f"Successfully cleared {count} embeddings from the database")
                else:
                    print("Operation cancelled.")
                
            elif choice == '6':
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter a number between 1 and 6.")
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()
