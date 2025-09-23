"""
Tests for shared interfaces.
"""

import pytest
from agents.shared.interfaces import IAgent, IRetriever, ILLMClient


class TestIAgent:
    """Test IAgent interface."""
    
    def test_agent_interface_implementation(self):
        """Test implementing IAgent interface."""
        class TestAgent(IAgent):
            def process(self, input_data):
                return f"Processed: {input_data}"
        
        agent = TestAgent()
        result = agent.process("test")
        assert result == "Processed: test"
    
    def test_agent_interface_abstract(self):
        """Test that IAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IAgent()


class TestIRetriever:
    """Test IRetriever interface."""
    
    def test_retriever_interface_implementation(self):
        """Test implementing IRetriever interface."""
        class TestRetriever(IRetriever):
            def retrieve(self, query, top_k=3):
                return [{"title": "Test Doc", "score": 0.9}]
        
        retriever = TestRetriever()
        results = retriever.retrieve("test query")
        assert len(results) == 1
        assert results[0]["title"] == "Test Doc"
    
    def test_retriever_interface_abstract(self):
        """Test that IRetriever cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IRetriever()


class TestILLMClient:
    """Test ILLMClient interface."""
    
    def test_llm_client_interface_implementation(self):
        """Test implementing ILLMClient interface."""
        class TestLLMClient(ILLMClient):
            def generate_text(self, prompt, system_prompt=None, max_tokens=1000):
                return "Generated text"
            
            def is_available(self):
                return True
        
        client = TestLLMClient()
        assert client.is_available() == True
        result = client.generate_text("test prompt")
        assert result == "Generated text"
    
    def test_llm_client_interface_abstract(self):
        """Test that ILLMClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ILLMClient()
    
    def test_llm_client_interface_methods(self):
        """Test that ILLMClient has required methods."""
        class TestLLMClient(ILLMClient):
            def generate_text(self, prompt, system_prompt=None, max_tokens=1000):
                return "Generated text"
            
            def is_available(self):
                return True
        
        client = TestLLMClient()
        
        # Test that methods exist and are callable
        assert hasattr(client, 'generate_text')
        assert hasattr(client, 'is_available')
        assert callable(client.generate_text)
        assert callable(client.is_available)
        
        # Test method signatures
        import inspect
        
        generate_text_sig = inspect.signature(client.generate_text)
        assert 'prompt' in generate_text_sig.parameters
        assert 'system_prompt' in generate_text_sig.parameters
        assert 'max_tokens' in generate_text_sig.parameters
        
        is_available_sig = inspect.signature(client.is_available)
        assert len(is_available_sig.parameters) == 0  # No parameters except self

