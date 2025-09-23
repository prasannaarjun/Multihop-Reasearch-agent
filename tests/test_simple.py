#!/usr/bin/env python3
"""
Simple test script for basic functionality verification.
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test shared modules
        from agents.shared.models import ChatMessage, Conversation, ResearchResult
        from agents.shared.exceptions import AgentError
        from agents.shared.interfaces import IAgent
        print("✅ Shared modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import shared modules: {e}")
        return False
    
    try:
        # Test research modules
        from agents.research import ResearchAgent, QueryPlanner, DocumentRetriever, AnswerSynthesizer
        print("✅ Research modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import research modules: {e}")
        return False
    
    try:
        # Test chat modules
        from agents.chat import ChatAgent, ConversationManager, ContextBuilder, ResponseGenerator
        print("✅ Chat modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import chat modules: {e}")
        return False
    
    return True

def test_basic_models():
    """Test basic model creation."""
    print("\nTesting basic models...")
    
    try:
        from agents.shared.models import ChatMessage, Conversation, ResearchResult, SubqueryResult
        
        # Test ChatMessage
        message = ChatMessage(
            id="test-1",
            role="user",
            content="Hello world",
            timestamp=datetime.now()
        )
        assert message.content == "Hello world"
        print("✅ ChatMessage creation works")
        
        # Test Conversation
        conversation = Conversation(
            id="conv-1",
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
            context={}
        )
        assert conversation.title == "Test Conversation"
        print("✅ Conversation creation works")
        
        # Test SubqueryResult
        subquery = SubqueryResult(
            subquery="What is AI?",
            summary="AI is artificial intelligence",
            documents=[],
            success=True
        )
        assert subquery.subquery == "What is AI?"
        print("✅ SubqueryResult creation works")
        
        # Test ResearchResult
        research_result = ResearchResult(
            question="What is AI?",
            answer="AI is artificial intelligence",
            subqueries=[subquery],
            citations=[],
            total_documents=0
        )
        assert research_result.question == "What is AI?"
        print("✅ ResearchResult creation works")
        
        return True
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False

def test_basic_components():
    """Test basic component initialization."""
    print("\nTesting basic components...")
    
    try:
        from agents.research import QueryPlanner, AnswerSynthesizer
        from agents.chat import ContextBuilder, ResponseGenerator
        
        # Test QueryPlanner
        planner = QueryPlanner()
        subqueries = planner.generate_subqueries("What is machine learning?")
        assert isinstance(subqueries, list)
        assert len(subqueries) > 0
        print("✅ QueryPlanner works")
        
        # Test AnswerSynthesizer
        synthesizer = AnswerSynthesizer()
        assert synthesizer is not None
        print("✅ AnswerSynthesizer works")
        
        # Test ContextBuilder
        builder = ContextBuilder()
        assert builder is not None
        print("✅ ContextBuilder works")
        
        # Test ResponseGenerator
        generator = ResponseGenerator()
        assert generator is not None
        print("✅ ResponseGenerator works")
        
        return True
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        return False

def test_conversation_manager():
    """Test conversation manager functionality."""
    print("\nTesting ConversationManager...")
    
    try:
        from agents.chat import ConversationManager
        import tempfile
        import shutil
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            manager = ConversationManager(persist_directory=temp_dir)
            
            # Test conversation creation
            conv_id = manager.create_conversation("Test Conversation")
            assert conv_id is not None
            print("✅ Conversation creation works")
            
            # Test adding messages
            message = manager.add_message(conv_id, "user", "Hello")
            assert message.content == "Hello"
            print("✅ Message addition works")
            
            # Test conversation history
            history = manager.get_conversation_history(conv_id)
            assert len(history) == 1
            print("✅ Conversation history works")
            
            # Test conversation listing
            conversations = manager.list_conversations()
            assert len(conversations) == 1
            print("✅ Conversation listing works")
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        print(f"❌ ConversationManager test failed: {e}")
        return False

def main():
    """Run all simple tests."""
    print("🧪 Multi-hop Research Agent - Simple Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_basic_models,
        test_basic_components,
        test_conversation_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All simple tests passed!")
        print("\nTo run the full test suite, use:")
        print("  python -m pytest tests/")
        print("  or")
        print("  python tests/run_tests.py")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

