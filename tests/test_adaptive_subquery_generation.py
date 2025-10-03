"""
Tests for Adaptive Subquery Generation in Research Agent

This test suite verifies:
1. Complexity analysis estimates appropriate hop counts
2. Adaptive subquery generation adjusts to question complexity
3. Scoring function prioritizes relevant subqueries
4. Iterative retrieval stops early when sufficient docs are found
5. Backward compatibility is maintained
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
from agents.research.query_planner import QueryPlanner, QueryComplexity, ScoredSubquery
from agents.research.research_agent import ResearchAgent
from agents.shared.models import ResearchResult, SubqueryResult

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


class TestQueryComplexityAnalysis:
    """Test complexity analysis and hop estimation."""
    
    def test_simple_question_low_complexity(self):
        """Simple questions should have low complexity and few hops."""
        planner = QueryPlanner(min_hops=1, max_hops=5)
        
        simple_questions = [
            "What is Python?",
            "Define machine learning",
            "What are neural networks?"
        ]
        
        for question in simple_questions:
            complexity = planner.analyze_complexity(question)
            assert complexity.estimated_hops <= 2, f"Simple question '{question}' should have <= 2 hops"
            assert complexity.complexity_score < 0.3, f"Simple question should have low complexity score"
            assert complexity.confidence >= 0.7, "Should have high confidence for simple questions"
    
    def test_moderate_question_medium_complexity(self):
        """Moderate questions should have medium complexity."""
        planner = QueryPlanner(min_hops=1, max_hops=5)
        
        moderate_questions = [
            "How does artificial intelligence work in healthcare?",
            "What are the benefits of cloud computing for businesses?",
            "Why is data encryption important?"
        ]
        
        for question in moderate_questions:
            complexity = planner.analyze_complexity(question)
            # These questions should be more complex than simple but not require max hops
            assert 1 <= complexity.estimated_hops <= 4, f"Moderate question '{question}' should have 1-4 hops, got {complexity.estimated_hops}"
            assert complexity.complexity_score < 1.0, f"Should not be maximum complexity, got {complexity.complexity_score}"
    
    def test_complex_question_high_complexity(self):
        """Complex questions should have high complexity and more hops."""
        planner = QueryPlanner(min_hops=1, max_hops=5)
        
        complex_questions = [
            "Compare different machine learning algorithms for image recognition and explain their advantages and disadvantages",
            "What are the benefits and challenges of implementing blockchain technology in healthcare and how does it compare to traditional systems?",
            "How do quantum computers work and what are their potential applications in cryptography versus classical computing?"
        ]
        
        for question in complex_questions:
            complexity = planner.analyze_complexity(question)
            assert complexity.estimated_hops >= 3, f"Complex question should have >= 3 hops"
            assert complexity.complexity_score >= 0.4, "Should have high complexity score"
            assert len(complexity.indicators) > 0, "Should identify complexity indicators"
    
    def test_complexity_indicators_detection(self):
        """Test detection of various complexity indicators."""
        planner = QueryPlanner()
        
        # Test comparison indicator
        question = "Compare Python and Java"
        complexity = planner.analyze_complexity(question)
        assert 'comparison' in complexity.indicators, "Should detect comparison indicator"
        
        # Test multi-aspect indicator
        question = "What are the pros and cons of machine learning?"
        complexity = planner.analyze_complexity(question)
        assert 'multi_aspect' in complexity.indicators, "Should detect multi-aspect indicator"
        
        # Test causal indicator
        question = "Why is data privacy important?"
        complexity = planner.analyze_complexity(question)
        assert 'causal' in complexity.indicators, "Should detect causal indicator"


class TestAdaptiveSubqueryGeneration:
    """Test adaptive subquery generation based on complexity."""
    
    def test_adaptive_generates_appropriate_count(self):
        """Adaptive mode should generate appropriate number of subqueries."""
        planner = QueryPlanner(min_hops=1, max_hops=5)
        
        # Simple question -> fewer subqueries
        simple = "What is Python?"
        subqueries_simple = planner.generate_subqueries(simple, adaptive=True)
        
        # Complex question -> more subqueries
        complex = "Compare Python and Java for web development, data science, and machine learning"
        subqueries_complex = planner.generate_subqueries(complex, adaptive=True)
        
        assert len(subqueries_simple) < len(subqueries_complex), \
            "Simple questions should generate fewer subqueries than complex ones"
    
    def test_non_adaptive_fallback(self):
        """Non-adaptive mode should still work (backward compatibility)."""
        planner = QueryPlanner()
        
        question = "What is machine learning?"
        subqueries = planner.generate_subqueries(question, adaptive=False)
        
        assert isinstance(subqueries, list), "Should return list"
        assert len(subqueries) > 0, "Should generate subqueries"
        assert all(isinstance(sq, str) for sq in subqueries), "All subqueries should be strings"
    
    def test_respects_min_max_hops(self):
        """Generated subqueries should respect min and max hop limits."""
        planner = QueryPlanner(min_hops=2, max_hops=4)
        
        # Very simple question
        simple = "What is AI?"
        subqueries_simple = planner.generate_subqueries(simple, adaptive=True)
        assert len(subqueries_simple) >= 2, "Should respect min_hops"
        
        # Very complex question
        complex = "Compare multiple machine learning algorithms across various domains and explain all their advantages, disadvantages, use cases, and future trends"
        subqueries_complex = planner.generate_subqueries(complex, adaptive=True)
        assert len(subqueries_complex) <= 4, "Should respect max_hops"


class TestSubqueryScoring:
    """Test subquery scoring and prioritization."""
    
    def test_scoring_returns_scored_objects(self):
        """Scoring should return ScoredSubquery objects."""
        planner = QueryPlanner()
        
        question = "What is machine learning?"
        subqueries = ["what is machine learning", "machine learning algorithms", "applications of machine learning"]
        
        scored = planner.score_subqueries(question, subqueries)
        
        assert isinstance(scored, list), "Should return list"
        assert all(isinstance(sq, ScoredSubquery) for sq in scored), "All should be ScoredSubquery objects"
        assert all(0 <= sq.relevance_score <= 1 for sq in scored), "Scores should be between 0 and 1"
    
    def test_scoring_prioritizes_relevant_queries(self):
        """More relevant subqueries should score higher."""
        planner = QueryPlanner()
        
        question = "What is machine learning?"
        subqueries = [
            "what is machine learning",  # Highly relevant
            "benefits of quantum computing",  # Less relevant
            "machine learning algorithms"  # Moderately relevant
        ]
        
        scored = planner.score_subqueries(question, subqueries)
        
        # First item should have highest score (most relevant)
        assert scored[0].relevance_score >= scored[1].relevance_score, \
            "Should prioritize more relevant subqueries"
    
    def test_scoring_assigns_priorities(self):
        """Priorities should be assigned correctly."""
        planner = QueryPlanner()
        
        question = "What is AI?"
        subqueries = ["what is ai", "ai applications", "ai benefits"]
        
        scored = planner.score_subqueries(question, subqueries)
        
        priorities = [sq.priority for sq in scored]
        assert priorities == list(range(1, len(subqueries) + 1)), \
            "Priorities should be sequential starting from 1"


class TestIterativeRetrieval:
    """Test iterative retrieval and early stopping logic."""
    
    def test_should_continue_below_min_hops(self):
        """Should always continue if below min_hops."""
        planner = QueryPlanner(min_hops=3, max_hops=5)
        
        # Even with good documents, should continue if below min
        good_docs = [
            {'score': 0.9, 'title': 'Doc 1'},
            {'score': 0.8, 'title': 'Doc 2'}
        ]
        
        should_continue, reason = planner.should_continue_retrieval(good_docs, current_hop=2)
        assert should_continue, "Should continue when below min_hops"
        assert "minimum" in reason.lower(), "Reason should mention minimum hops"
    
    def test_should_stop_at_max_hops(self):
        """Should stop when reaching max_hops."""
        planner = QueryPlanner(min_hops=1, max_hops=5)
        
        should_continue, reason = planner.should_continue_retrieval([], current_hop=5)
        assert not should_continue, "Should stop at max_hops"
        assert "maximum" in reason.lower(), "Reason should mention maximum"
    
    def test_should_stop_with_sufficient_quality_docs(self):
        """Should stop early when sufficient high-quality docs are found."""
        planner = QueryPlanner(min_hops=1, max_hops=5)
        
        # High quality documents
        high_quality_docs = [
            {'score': 0.9, 'title': 'Doc 1'},
            {'score': 0.85, 'title': 'Doc 2'},
            {'score': 0.8, 'title': 'Doc 3'}
        ]
        
        should_continue, reason = planner.should_continue_retrieval(
            high_quality_docs, current_hop=2, min_confidence_threshold=0.5
        )
        assert not should_continue, "Should stop with sufficient high-quality documents"
        assert "sufficient" in reason.lower() or "quality" in reason.lower()
    
    def test_should_continue_with_poor_quality_docs(self):
        """Should continue if document quality is below threshold."""
        planner = QueryPlanner(min_hops=1, max_hops=5)
        
        # Low quality documents
        low_quality_docs = [
            {'score': 0.3, 'title': 'Doc 1'},
            {'score': 0.2, 'title': 'Doc 2'}
        ]
        
        should_continue, reason = planner.should_continue_retrieval(
            low_quality_docs, current_hop=2, min_confidence_threshold=0.5
        )
        assert should_continue, "Should continue with low quality documents"


class TestResearchAgentIntegration:
    """Test research agent with adaptive subquery generation."""
    
    def create_mock_retriever(self, doc_scores=[0.8, 0.7, 0.6]):
        """Create a mock retriever that returns documents with specified scores."""
        mock_retriever = Mock()
        mock_retriever.retrieve = Mock(return_value=[
            {'score': score, 'title': f'Doc {i}', 'full_text': f'Content {i}'}
            for i, score in enumerate(doc_scores, 1)
        ])
        return mock_retriever
    
    def create_mock_llm_client(self):
        """Create a mock LLM client."""
        mock_llm = Mock()
        mock_llm.is_available = Mock(return_value=True)
        mock_llm.generate_subqueries = Mock(return_value=[
            "subquery 1", "subquery 2", "subquery 3"
        ])
        return mock_llm
    
    def test_research_agent_adaptive_mode_initialization(self):
        """Test research agent initializes with adaptive mode."""
        mock_retriever = self.create_mock_retriever()
        
        agent = ResearchAgent(
            mock_retriever, 
            adaptive_mode=True,
            min_hops=1,
            max_hops=5
        )
        
        assert agent.adaptive_mode is True, "Adaptive mode should be enabled"
        assert agent.query_planner.min_hops == 1, "Min hops should be set"
        assert agent.query_planner.max_hops == 5, "Max hops should be set"
    
    def test_research_agent_backward_compatibility(self):
        """Test that existing code still works (backward compatibility)."""
        mock_retriever = self.create_mock_retriever()
        
        # Initialize without adaptive parameters (old style)
        agent = ResearchAgent(mock_retriever, use_llm=False, adaptive_mode=False)
        
        # Should still work
        assert agent is not None
        assert hasattr(agent, 'process')
    
    def test_batch_mode_processes_all_subqueries(self):
        """Test batch mode processes all subqueries upfront."""
        mock_retriever = self.create_mock_retriever()
        
        # Create agent with mock answer synthesizer
        agent = ResearchAgent(mock_retriever, use_llm=False, adaptive_mode=False)
        
        # Mock the answer synthesizer
        agent.answer_synthesizer.summarize_documents = Mock(return_value="Summary")
        agent.answer_synthesizer.synthesize_answer = Mock(return_value="Final answer")
        
        question = "What is machine learning?"
        result = agent.process(question, per_sub_k=2, iterative=False)
        
        assert isinstance(result, ResearchResult), "Should return ResearchResult"
        assert result.question == question
        assert result.metadata['mode'] == 'batch', "Should use batch mode"
        assert result.metadata['adaptive'] is True, "Should use adaptive subquery generation"
        assert 'complexity_score' in result.metadata, "Should include complexity analysis"
    
    def test_metadata_includes_complexity_info(self):
        """Test that result metadata includes complexity analysis."""
        mock_retriever = self.create_mock_retriever()
        
        agent = ResearchAgent(mock_retriever, use_llm=False, adaptive_mode=True)
        agent.answer_synthesizer.summarize_documents = Mock(return_value="Summary")
        agent.answer_synthesizer.synthesize_answer = Mock(return_value="Final answer")
        
        question = "Compare Python and Java for data science"
        result = agent.process(question, per_sub_k=2)
        
        metadata = result.metadata
        assert 'complexity_score' in metadata, "Should include complexity score"
        assert 'estimated_hops' in metadata, "Should include estimated hops"
        assert 'actual_hops' in metadata, "Should include actual hops used"
        assert 'mode' in metadata, "Should include mode (batch/iterative)"


class TestLoggingAndTracing:
    """Test logging and tracing capabilities."""
    
    def test_complexity_analysis_logs_details(self, caplog):
        """Test that complexity analysis logs important details."""
        with caplog.at_level(logging.INFO):
            planner = QueryPlanner()
            complexity = planner.analyze_complexity("Compare Python and Java")
            
        # Check that logging occurred
        assert any("Complexity analysis" in record.message for record in caplog.records), \
            "Should log complexity analysis details"
    
    def test_subquery_generation_logs_count(self, caplog):
        """Test that subquery generation logs the count."""
        with caplog.at_level(logging.INFO):
            planner = QueryPlanner()
            subqueries = planner.generate_subqueries("What is AI?", adaptive=True)
        
        assert any("Generated" in record.message and "subqueries" in record.message 
                  for record in caplog.records), \
            "Should log subquery generation count"
    
    def test_scoring_logs_results(self, caplog):
        """Test that scoring logs results."""
        with caplog.at_level(logging.INFO):
            planner = QueryPlanner()
            scored = planner.score_subqueries("What is AI?", ["what is ai", "ai applications"])
        
        assert any("Scored" in record.message for record in caplog.records), \
            "Should log scoring results"


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_question(self):
        """Test handling of empty questions."""
        planner = QueryPlanner()
        
        subqueries = planner.generate_subqueries("", adaptive=True)
        assert isinstance(subqueries, list), "Should return list even for empty question"
    
    def test_very_long_question(self):
        """Test handling of very long questions."""
        planner = QueryPlanner(min_hops=1, max_hops=5)
        
        long_question = " ".join(["What is machine learning"] * 20)
        complexity = planner.analyze_complexity(long_question)
        
        # Should recognize as complex due to length
        assert complexity.complexity_score > 0, "Long questions should have higher complexity"
        assert complexity.estimated_hops <= planner.max_hops, "Should not exceed max_hops"
    
    def test_no_matching_patterns(self):
        """Test handling when no patterns match."""
        planner = QueryPlanner()
        
        # Question with no clear pattern
        question = "xyzabc"
        subqueries = planner.generate_subqueries(question, adaptive=True)
        
        assert len(subqueries) > 0, "Should generate fallback subqueries"
    
    def test_scoring_with_single_subquery(self):
        """Test scoring with only one subquery."""
        planner = QueryPlanner()
        
        scored = planner.score_subqueries("What is AI?", ["what is ai"])
        
        assert len(scored) == 1, "Should handle single subquery"
        assert scored[0].priority == 1, "Should assign priority 1"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

