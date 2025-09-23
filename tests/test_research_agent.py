"""
Tests for research agent components.
"""

import pytest
from unittest.mock import Mock, patch
from agents.research import ResearchAgent, QueryPlanner, DocumentRetriever, AnswerSynthesizer
from agents.shared.models import ResearchResult, SubqueryResult
from agents.shared.exceptions import AgentError, RetrievalError


class TestQueryPlanner:
    """Test QueryPlanner functionality."""
    
    def test_init(self):
        """Test QueryPlanner initialization."""
        planner = QueryPlanner()
        assert planner is not None
    
    def test_generate_subqueries_what_question(self):
        """Test subquery generation for 'what' questions."""
        planner = QueryPlanner()
        question = "What are the best machine learning algorithms?"
        subqueries = planner.generate_subqueries(question)
        
        assert isinstance(subqueries, list)
        assert len(subqueries) > 0
        assert len(subqueries) <= 5
        
        # Check that subqueries contain relevant terms
        subquery_text = ' '.join(subqueries).lower()
        assert 'machine' in subquery_text
        assert 'learning' in subquery_text
    
    def test_generate_subqueries_how_question(self):
        """Test subquery generation for 'how' questions."""
        planner = QueryPlanner()
        question = "How does artificial intelligence work?"
        subqueries = planner.generate_subqueries(question)
        
        assert isinstance(subqueries, list)
        assert len(subqueries) > 0
        
        # Check for 'how' related subqueries
        subquery_text = ' '.join(subqueries).lower()
        assert any('how' in sq for sq in subqueries)
    
    def test_generate_subqueries_comparison_question(self):
        """Test subquery generation for comparison questions."""
        planner = QueryPlanner()
        question = "Compare Python and Java for data science"
        subqueries = planner.generate_subqueries(question)
        
        assert isinstance(subqueries, list)
        assert len(subqueries) > 0
        
        # Check for comparison-related terms
        subquery_text = ' '.join(subqueries).lower()
        assert any('comparison' in sq or 'difference' in sq for sq in subqueries)
    
    def test_extract_key_terms(self):
        """Test key term extraction."""
        planner = QueryPlanner()
        text = "What are the best machine learning algorithms for image recognition?"
        terms = planner._extract_key_terms(text)
        
        assert isinstance(terms, list)
        assert 'machine' in terms
        assert 'learning' in terms
        assert 'algorithms' in terms
        assert 'image' in terms
        assert 'recognition' in terms
        
        # Check that stop words are removed
        assert 'what' not in terms
        assert 'are' not in terms
        assert 'the' not in terms
        assert 'for' not in terms


class TestDocumentRetriever:
    """Test DocumentRetriever functionality."""
    
    def test_init(self):
        """Test DocumentRetriever initialization."""
        mock_collection = Mock()
        mock_model = Mock()
        retriever = DocumentRetriever(mock_collection, mock_model)
        
        assert retriever.collection == mock_collection
        assert retriever.model == mock_model
    
    def test_retrieve_success(self, mock_retriever):
        """Test successful document retrieval."""
        # Mock collection query response
        mock_results = {
            'documents': [['Document 1 content', 'Document 2 content']],
            'metadatas': [[
                {'title': 'Test Doc 1', 'filename': 'test1.txt'},
                {'title': 'Test Doc 2', 'filename': 'test2.txt'}
            ]],
            'distances': [[0.1, 0.2]],
            'ids': [['doc1', 'doc2']]
        }
        
        mock_retriever.collection.query.return_value = mock_results
        mock_retriever.model.encode.return_value = [[0.1, 0.2, 0.3]]
        
        results = mock_retriever.retrieve("test query", top_k=2)
        
        assert isinstance(results, list)
        assert len(results) == 2
        
        # Check result structure
        for result in results:
            assert 'doc_id' in result
            assert 'title' in result
            assert 'snippet' in result
            assert 'score' in result
            assert 'filename' in result
            assert 'full_text' in result
    
    def test_retrieve_no_results(self, mock_retriever):
        """Test retrieval when no results are found."""
        mock_results = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]],
            'ids': [[]]
        }
        
        mock_retriever.collection.query.return_value = mock_results
        mock_retriever.model.encode.return_value = [[0.1, 0.2, 0.3]]
        
        results = mock_retriever.retrieve("test query", top_k=2)
        
        assert isinstance(results, list)
        assert len(results) == 0
    
    def test_retrieve_error(self, mock_retriever):
        """Test retrieval error handling."""
        mock_retriever.collection.query.side_effect = Exception("Database error")
        mock_retriever.model.encode.return_value = [[0.1, 0.2, 0.3]]
        
        with pytest.raises(RetrievalError):
            mock_retriever.retrieve("test query", top_k=2)
    
    def test_get_collection_stats(self, mock_retriever):
        """Test collection statistics retrieval."""
        # Mock collection count
        mock_retriever.collection.count.return_value = 100
        
        # Mock sample results
        mock_sample = {
            'metadatas': [
                {'file_type': 'txt', 'filename': 'test1.txt'},
                {'file_type': 'pdf', 'filename': 'test2.pdf'},
                {'file_type': 'txt', 'filename': 'test3.txt'}
            ]
        }
        mock_retriever.collection.get.return_value = mock_sample
        
        stats = mock_retriever.get_collection_stats()
        
        assert 'total_documents' in stats
        assert 'unique_files' in stats
        assert 'file_types' in stats
        assert 'collection_name' in stats
        
        assert stats['total_documents'] == 100
        assert stats['unique_files'] == 3
        assert stats['file_types']['txt'] == 2
        assert stats['file_types']['pdf'] == 1


class TestAnswerSynthesizer:
    """Test AnswerSynthesizer functionality."""
    
    def test_init_without_llm(self):
        """Test initialization without LLM client."""
        synthesizer = AnswerSynthesizer()
        assert synthesizer.llm_client is None
        assert synthesizer.use_llm == False
    
    def test_init_with_llm(self, mock_llm_client):
        """Test initialization with LLM client."""
        synthesizer = AnswerSynthesizer(mock_llm_client)
        assert synthesizer.llm_client == mock_llm_client
        assert synthesizer.use_llm == True
    
    def test_synthesize_answer_rule_based(self):
        """Test rule-based answer synthesis."""
        synthesizer = AnswerSynthesizer()
        
        subquery_results = [
            SubqueryResult(
                subquery='What is machine learning?',
                summary='Machine learning is a subset of AI that enables computers to learn from data.',
                documents=[],
                success=True
            ),
            SubqueryResult(
                subquery='How does machine learning work?',
                summary='ML works by using algorithms to identify patterns in data.',
                documents=[],
                success=True
            )
        ]
        
        question = "What is machine learning and how does it work?"
        answer = synthesizer.synthesize_answer(question, subquery_results)
        
        assert isinstance(answer, str)
        assert 'machine learning' in answer.lower()
        assert 'subset of ai' in answer.lower()
        assert 'algorithms' in answer.lower()
    
    def test_synthesize_answer_with_llm(self, mock_llm_client):
        """Test answer synthesis with LLM."""
        synthesizer = AnswerSynthesizer(mock_llm_client)
        
        subquery_results = [
            SubqueryResult(
                subquery='What is machine learning?',
                summary='ML is a subset of AI.',
                documents=[],
                success=True
            )
        ]
        
        question = "What is machine learning?"
        answer = synthesizer.synthesize_answer(question, subquery_results)
        
        assert isinstance(answer, str)
        assert answer == "Test response from LLM"
        mock_llm_client.generate_text.assert_called_once()
    
    def test_synthesize_answer_no_results(self):
        """Test answer synthesis with no results."""
        synthesizer = AnswerSynthesizer()
        subquery_results = []
        question = "Test question"
        
        answer = synthesizer.synthesize_answer(question, subquery_results)
        
        assert "couldn't find enough information" in answer.lower()
    
    def test_summarize_documents_rule_based(self):
        """Test rule-based document summarization."""
        synthesizer = AnswerSynthesizer()
        
        documents = [
            {
                'title': 'ML Basics',
                'full_text': 'Machine learning is a subset of artificial intelligence. It enables computers to learn from data without being explicitly programmed. The algorithms identify patterns and make predictions.'
            },
            {
                'title': 'ML Applications',
                'full_text': 'Machine learning is used in many applications. These include image recognition, natural language processing, and recommendation systems. The technology is transforming various industries.'
            }
        ]
        
        subquery = "What is machine learning?"
        summary = synthesizer.summarize_documents(documents, subquery)
        
        assert isinstance(summary, str)
        assert 'machine learning' in summary.lower()
        assert 'artificial intelligence' in summary.lower()
    
    def test_summarize_documents_no_documents(self):
        """Test document summarization with no documents."""
        synthesizer = AnswerSynthesizer()
        documents = []
        subquery = "Test query"
        
        summary = synthesizer.summarize_documents(documents, subquery)
        
        assert summary == "No relevant information found for this aspect."
    
    def test_split_into_sentences(self):
        """Test sentence splitting functionality."""
        synthesizer = AnswerSynthesizer()
        text = "This is sentence one. This is sentence two! This is sentence three?"
        sentences = synthesizer._split_into_sentences(text)
        
        assert isinstance(sentences, list)
        assert len(sentences) > 0
        assert 'This is sentence one' in sentences
        assert 'This is sentence two' in sentences
        assert 'This is sentence three' in sentences
    
    def test_select_relevant_sentences(self):
        """Test relevant sentence selection."""
        synthesizer = AnswerSynthesizer()
        sentences = [
            "Machine learning is a subset of artificial intelligence.",
            "The weather is nice today.",
            "Deep learning uses neural networks for pattern recognition.",
            "I like to eat pizza."
        ]
        query = "machine learning neural networks"
        
        relevant = synthesizer._select_relevant_sentences(sentences, query)
        
        assert isinstance(relevant, list)
        assert "Machine learning is a subset of artificial intelligence." in relevant
        assert "Deep learning uses neural networks for pattern recognition." in relevant


class TestResearchAgent:
    """Test ResearchAgent functionality."""
    
    def test_init_without_llm(self, mock_retriever):
        """Test initialization without LLM client."""
        agent = ResearchAgent(mock_retriever, use_llm=False)
        assert agent.retriever == mock_retriever
        assert agent.llm_client is None
        assert agent.use_llm == False
    
    def test_init_with_llm(self, mock_retriever, mock_llm_client):
        """Test initialization with LLM client."""
        agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        assert agent.retriever == mock_retriever
        assert agent.llm_client == mock_llm_client
        assert agent.use_llm == True
    
    @patch('agents.research.research_agent.time.time')
    def test_process_success(self, mock_time, mock_retriever):
        """Test successful research processing."""
        # Mock time for processing time calculation
        mock_time.side_effect = [0, 1.5]
        
        # Mock retriever responses
        mock_docs = [
            {'title': 'Test Doc', 'full_text': 'Test content', 'score': 0.9}
        ]
        mock_retriever.retrieve.return_value = mock_docs
        
        agent = ResearchAgent(mock_retriever, use_llm=False)
        
        result = agent.process("What is test?", per_sub_k=1)
        
        assert isinstance(result, ResearchResult)
        assert result.question == "What is test?"
        assert isinstance(result.answer, str)
        assert len(result.subqueries) > 0
        assert result.processing_time > 0
    
    def test_process_with_llm(self, mock_retriever, mock_llm_client):
        """Test processing with LLM client."""
        agent = ResearchAgent(mock_retriever, mock_llm_client, use_llm=True)
        
        # Mock retriever
        mock_retriever.retrieve.return_value = [
            {'title': 'Test Doc', 'full_text': 'Test content', 'score': 0.9}
        ]
        
        result = agent.process("What is test?", per_sub_k=1)
        
        assert isinstance(result, ResearchResult)
        mock_llm_client.generate_text.assert_called()
    
    def test_ask_legacy_method(self, mock_retriever):
        """Test legacy ask method."""
        agent = ResearchAgent(mock_retriever, use_llm=False)
        
        # Mock the process method
        mock_result = ResearchResult(
            question="Test question",
            answer="Test answer",
            subqueries=[],
            citations=[],
            total_documents=0
        )
        
        with patch.object(agent, 'process', return_value=mock_result):
            result = agent.ask("Test question", per_sub_k=1)
        
        assert isinstance(result, dict)
        assert 'question' in result
        assert 'answer' in result
        assert 'subqueries' in result
        assert 'citations' in result
        assert 'total_documents' in result
    
    def test_get_collection_stats(self, mock_retriever):
        """Test collection statistics retrieval."""
        mock_stats = {'total_documents': 100, 'file_types': {'txt': 50}}
        mock_retriever.get_collection_stats.return_value = mock_stats
        
        agent = ResearchAgent(mock_retriever, use_llm=False)
        stats = agent.get_collection_stats()
        
        assert stats == mock_stats
        mock_retriever.get_collection_stats.assert_called_once()
    
    def test_process_error_handling(self, mock_retriever):
        """Test error handling in process method."""
        mock_retriever.retrieve.side_effect = Exception("Retrieval error")
        
        agent = ResearchAgent(mock_retriever, use_llm=False)
        
        with pytest.raises(AgentError):
            agent.process("Test question")
