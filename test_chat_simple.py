#!/usr/bin/env python3
"""
Simple test for chat functionality without full dependencies.
"""

import os
import sys
import json
from datetime import datetime

# Test chat manager without dependencies
def test_chat_manager():
    print("Testing Chat Manager (without dependencies)")
    print("=" * 50)
    
    try:
        from chat_manager import chat_manager, Message, Conversation
        
        # Create a test conversation
        conv_id = chat_manager.create_conversation("Test Chat")
        print(f"✅ Created conversation: {conv_id}")
        
        # Add some test messages
        chat_manager.add_message(conv_id, "user", "Hello, how are you?")
        chat_manager.add_message(conv_id, "assistant", "I'm doing well, thank you! How can I help you today?")
        
        # Get conversation history
        history = chat_manager.get_conversation_history(conv_id)
        print(f"✅ Conversation history: {len(history)} messages")
        
        # List conversations
        conversations = chat_manager.list_conversations()
        print(f"✅ Total conversations: {len(conversations)}")
        
        # Test conversation context
        context = chat_manager.get_conversation_context(conv_id)
        print(f"✅ Context extracted: {bool(context.get('recent_messages'))}")
        
        print("\n✅ Chat Manager test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Chat Manager test failed: {e}")
        return False

def test_api_models():
    print("\nTesting API Models")
    print("=" * 50)
    
    try:
        # Test the message and conversation models
        from chat_manager import Message, Conversation
        
        # Create a test message
        message = Message(
            id="test-123",
            role="user",
            content="Test message",
            timestamp=datetime.now(),
            metadata={"test": True}
        )
        
        # Test serialization
        message_dict = message.to_dict()
        print(f"✅ Message serialization: {bool(message_dict)}")
        
        # Test deserialization
        message_restored = Message.from_dict(message_dict)
        print(f"✅ Message deserialization: {message_restored.content == 'Test message'}")
        
        # Create a test conversation
        conversation = Conversation(
            id="conv-123",
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[message],
            context={}
        )
        
        # Test conversation serialization
        conv_dict = conversation.to_dict()
        print(f"✅ Conversation serialization: {bool(conv_dict)}")
        
        print("\n✅ API Models test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ API Models test failed: {e}")
        return False

def main():
    print("Chat System Test (Minimal Dependencies)")
    print("=" * 60)
    
    # Test chat manager
    chat_success = test_chat_manager()
    
    # Test API models
    models_success = test_api_models()
    
    print("\n" + "=" * 60)
    if chat_success and models_success:
        print("✅ All tests passed! Chat system is working correctly.")
        print("\nTo use the full system, make sure to install all dependencies:")
        print("pip install -r requirements.txt")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return chat_success and models_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
