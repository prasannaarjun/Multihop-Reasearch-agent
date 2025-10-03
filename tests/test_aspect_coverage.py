"""
Test suite for aspect-based coverage tracking in multihop subquery generation.
"""

import pytest
from agents.research.query_planner import (
    QueryPlanner,
    QueryAspect,
    AspectCoverage
)


class TestQueryAspect:
    """Test QueryAspect dataclass."""
    
    def test_query_aspect_creation(self):
        """Test creating a QueryAspect."""
        aspect = QueryAspect(
            aspect="Definition of self-attention",
            aspect_type="definition",
            importance=1.0,
            keywords=["self-attention", "definition"]
        )
        
        assert aspect.aspect == "Definition of self-attention"
        assert aspect.aspect_type == "definition"
        assert aspect.importance == 1.0
        assert len(aspect.keywords) == 2


class TestAspectCoverage:
    """Test AspectCoverage tracking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.aspects = [
            QueryAspect(
                aspect="Definition of self-attention",
                aspect_type="definition",
                importance=1.0,
                keywords=["self-attention", "definition"]
            ),
            QueryAspect(
                aspect="Definition of multi-head attention",
                aspect_type="definition",
                importance=1.0,
                keywords=["multi-head", "attention", "definition"]
            ),
            QueryAspect(
                aspect="Comparison between mechanisms",
                aspect_type="comparison",
                importance=1.0,
                keywords=["comparison", "difference", "self-attention", "multi-head"]
            )
        ]
    
    def test_aspect_coverage_initialization(self):
        """Test initializing AspectCoverage."""
        coverage = AspectCoverage(aspects=self.aspects)
        
        assert len(coverage.aspects) == 3
        assert len(coverage.coverage_scores) == 3
        assert all(score == 0.0 for score in coverage.coverage_scores.values())
    
    def test_is_aspect_covered(self):
        """Test checking if an aspect is covered."""
        coverage = AspectCoverage(aspects=self.aspects)
        
        # Initially not covered
        assert not coverage.is_aspect_covered("Definition of self-attention")
        
        # Set coverage and check
        coverage.coverage_scores["Definition of self-attention"] = 0.8
        assert coverage.is_aspect_covered("Definition of self-attention", threshold=0.5)
        assert not coverage.is_aspect_covered("Definition of self-attention", threshold=0.9)
    
    def test_get_uncovered_aspects(self):
        """Test getting uncovered aspects."""
        coverage = AspectCoverage(aspects=self.aspects)
        
        # All uncovered initially
        uncovered = coverage.get_uncovered_aspects(threshold=0.5)
        assert len(uncovered) == 3
        
        # Cover one aspect
        coverage.coverage_scores["Definition of self-attention"] = 0.7
        uncovered = coverage.get_uncovered_aspects(threshold=0.5)
        assert len(uncovered) == 2
        
        # Cover all aspects
        for aspect in self.aspects:
            coverage.coverage_scores[aspect.aspect] = 0.8
        uncovered = coverage.get_uncovered_aspects(threshold=0.5)
        assert len(uncovered) == 0
    
    def test_get_coverage_percentage(self):
        """Test calculating overall coverage percentage."""
        coverage = AspectCoverage(aspects=self.aspects)
        
        # 0% initially
        assert coverage.get_coverage_percentage() == 0.0
        
        # 33% after one aspect
        coverage.coverage_scores[self.aspects[0].aspect] = 1.0
        assert coverage.get_coverage_percentage() == pytest.approx(1/3, rel=0.01)
        
        # 100% when all covered
        for aspect in self.aspects:
            coverage.coverage_scores[aspect.aspect] = 1.0
        assert coverage.get_coverage_percentage() == 1.0
    
    def test_get_weighted_coverage(self):
        """Test calculating weighted coverage."""
        aspects_with_weights = [
            QueryAspect("Core aspect", "definition", 1.0, ["test"]),
            QueryAspect("Optional aspect", "application", 0.5, ["test"])
        ]
        coverage = AspectCoverage(aspects=aspects_with_weights)
        
        # 0% initially
        assert coverage.get_weighted_coverage() == 0.0
        
        # Cover core aspect only
        coverage.coverage_scores["Core aspect"] = 1.0
        weighted = coverage.get_weighted_coverage()
        assert weighted == pytest.approx(1.0 / 1.5, rel=0.01)  # 1.0 / (1.0 + 0.5)
        
        # Cover both
        coverage.coverage_scores["Optional aspect"] = 1.0
        assert coverage.get_weighted_coverage() == 1.0


class TestAspectExtraction:
    """Test aspect extraction from queries."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(min_hops=3, max_hops=10, enable_aspect_coverage=True)
    
    def test_extract_aspects_comparison_vs(self):
        """Test extracting aspects from comparison question with 'vs'."""
        question = "self-attention vs multi-head attention"
        aspects = self.planner._extract_aspects_heuristic(question)
        
        # Should identify 3 aspects: 2 definitions + 1 comparison
        assert len(aspects) >= 3
        
        aspect_types = [a.aspect_type for a in aspects]
        assert 'definition' in aspect_types
        assert 'comparison' in aspect_types
    
    def test_extract_aspects_comparison_versus(self):
        """Test extracting aspects from comparison question with 'versus'."""
        question = "Compare transformer architecture versus RNN architecture"
        aspects = self.planner._extract_aspects_heuristic(question)
        
        assert len(aspects) >= 3
        aspect_types = [a.aspect_type for a in aspects]
        assert 'definition' in aspect_types
        assert 'comparison' in aspect_types
    
    def test_extract_aspects_what_is(self):
        """Test extracting aspects from 'what is' question."""
        question = "What is machine learning?"
        aspects = self.planner._extract_aspects_heuristic(question)
        
        assert len(aspects) >= 1
        assert aspects[0].aspect_type == 'definition'
    
    def test_extract_aspects_how(self):
        """Test extracting aspects from 'how' question."""
        question = "How does gradient descent work?"
        aspects = self.planner._extract_aspects_heuristic(question)
        
        assert len(aspects) >= 1
        assert 'process' in [a.aspect_type for a in aspects]
    
    def test_extract_aspects_why(self):
        """Test extracting aspects from 'why' question."""
        question = "Why is regularization important in deep learning?"
        aspects = self.planner._extract_aspects_heuristic(question)
        
        assert len(aspects) >= 1
        assert 'causal' in [a.aspect_type for a in aspects]
    
    def test_extract_aspects_advantages_disadvantages(self):
        """Test extracting aspects from pros/cons question."""
        question = "What are the advantages and disadvantages of neural networks?"
        aspects = self.planner._extract_aspects_heuristic(question)
        
        aspect_types = [a.aspect_type for a in aspects]
        assert 'evaluation' in aspect_types


class TestCoverageUpdate:
    """Test updating coverage based on documents."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(enable_aspect_coverage=True)
        
        self.aspects = [
            QueryAspect(
                aspect="Definition of transformers",
                aspect_type="definition",
                importance=1.0,
                keywords=["transformer", "definition", "architecture"]
            ),
            QueryAspect(
                aspect="Applications of transformers",
                aspect_type="application",
                importance=0.7,
                keywords=["transformer", "application", "use"]
            )
        ]
        
        self.coverage = AspectCoverage(aspects=self.aspects)
    
    def test_update_coverage_relevant_document(self):
        """Test updating coverage with relevant document."""
        documents = [
            {
                'title': 'Transformer Architecture',
                'content': 'A transformer is a deep learning architecture that uses self-attention mechanisms. The definition includes encoder and decoder components.',
                'score': 0.9
            }
        ]
        
        self.planner.update_aspect_coverage(self.coverage, documents, current_hop=1)
        
        # Should have coverage for definition aspect
        definition_score = self.coverage.coverage_scores["Definition of transformers"]
        assert definition_score > 0.0
        
        # Should track hop number
        assert self.coverage.covered_by_hop.get("Definition of transformers") == 1
    
    def test_update_coverage_multiple_documents(self):
        """Test updating coverage with multiple documents."""
        documents = [
            {
                'title': 'What is a Transformer?',
                'content': 'Definition: A transformer is a neural network architecture.',
                'score': 0.8
            },
            {
                'title': 'Transformer Applications',
                'content': 'Transformers are used in NLP, translation, and image processing.',
                'score': 0.85
            }
        ]
        
        self.planner.update_aspect_coverage(self.coverage, documents, current_hop=2)
        
        # Both aspects should have some coverage
        assert self.coverage.coverage_scores["Definition of transformers"] > 0.0
        assert self.coverage.coverage_scores["Applications of transformers"] > 0.0
    
    def test_update_coverage_irrelevant_document(self):
        """Test updating coverage with irrelevant document."""
        documents = [
            {
                'title': 'Random Topic',
                'content': 'This is about something completely different.',
                'score': 0.5
            }
        ]
        
        self.planner.update_aspect_coverage(self.coverage, documents, current_hop=1)
        
        # Coverage should remain low or zero
        assert self.coverage.coverage_scores["Definition of transformers"] < 0.3


class TestCoverageBasedStopping:
    """Test stopping condition based on aspect coverage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(min_hops=2, max_hops=8, enable_aspect_coverage=True)
        
        self.aspects = [
            QueryAspect("Core aspect 1", "definition", 1.0, ["test"]),
            QueryAspect("Core aspect 2", "definition", 1.0, ["test"]),
            QueryAspect("Optional aspect", "application", 0.6, ["test"])
        ]
        
        self.coverage = AspectCoverage(aspects=self.aspects)
        
        self.mock_docs = [
            {'title': 'Doc 1', 'content': 'Test content', 'score': 0.8}
        ]
    
    def test_continue_when_aspects_uncovered(self):
        """Test that it continues when aspects are uncovered."""
        # No coverage yet
        should_continue, reason = self.planner.should_continue_retrieval(
            self.mock_docs,
            current_hop=3,
            aspect_coverage=self.coverage
        )
        
        assert should_continue
        assert "uncovered" in reason.lower() or "coverage" in reason.lower()
    
    def test_stop_when_all_core_aspects_covered(self):
        """Test that it stops when all core aspects are covered."""
        # Cover all core aspects
        self.coverage.coverage_scores["Core aspect 1"] = 0.9
        self.coverage.coverage_scores["Core aspect 2"] = 0.9
        self.coverage.coverage_scores["Optional aspect"] = 0.4  # Not covered but optional
        
        should_continue, reason = self.planner.should_continue_retrieval(
            self.mock_docs,
            current_hop=3,
            aspect_coverage=self.coverage
        )
        
        assert not should_continue
        assert "covered" in reason.lower()
    
    def test_continue_below_min_hops(self):
        """Test that it continues below min_hops even with good coverage."""
        # Good coverage but below min hops
        for aspect in self.aspects:
            self.coverage.coverage_scores[aspect.aspect] = 0.9
        
        should_continue, reason = self.planner.should_continue_retrieval(
            self.mock_docs,
            current_hop=1,  # Below min_hops=2
            aspect_coverage=self.coverage
        )
        
        assert should_continue
        assert "minimum" in reason.lower()
    
    def test_stop_at_max_hops(self):
        """Test that it stops at max_hops regardless of coverage."""
        # No coverage but at max hops
        should_continue, reason = self.planner.should_continue_retrieval(
            self.mock_docs,
            current_hop=8,  # At max_hops
            aspect_coverage=self.coverage
        )
        
        assert not should_continue
        assert "maximum" in reason.lower()
    
    def test_fallback_to_traditional_stopping(self):
        """Test fallback to traditional stopping when coverage disabled."""
        planner_no_coverage = QueryPlanner(enable_aspect_coverage=False)
        
        should_continue, reason = planner_no_coverage.should_continue_retrieval(
            self.mock_docs * 3,  # Sufficient docs
            current_hop=3
        )
        
        # Should use document-quality based stopping
        assert not should_continue
        assert "document" in reason.lower()


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(min_hops=3, max_hops=10, enable_aspect_coverage=True)
    
    def test_comparison_query_scenario(self):
        """Test end-to-end scenario with comparison query."""
        question = "self-attention vs multi-head attention"
        
        # Extract aspects
        coverage = self.planner.extract_aspects(question, llm_client=None)
        
        # Should identify multiple aspects
        assert len(coverage.aspects) >= 3
        
        # Simulate document retrieval hop 1 - covers self-attention
        docs_hop1 = [
            {
                'title': 'Self-Attention Mechanism',
                'content': 'Self-attention is a mechanism where each position attends to all positions.',
                'score': 0.85
            }
        ]
        self.planner.update_aspect_coverage(coverage, docs_hop1, current_hop=1)
        
        # Should continue - not all aspects covered
        should_continue, _ = self.planner.should_continue_retrieval(
            docs_hop1, current_hop=1, aspect_coverage=coverage
        )
        assert should_continue
        
        # Simulate hop 2 - covers multi-head attention
        docs_hop2 = docs_hop1 + [
            {
                'title': 'Multi-Head Attention',
                'content': 'Multi-head attention uses multiple attention mechanisms in parallel.',
                'score': 0.88
            }
        ]
        self.planner.update_aspect_coverage(coverage, docs_hop2, current_hop=2)
        
        # Should continue - comparison not covered yet
        should_continue, _ = self.planner.should_continue_retrieval(
            docs_hop2, current_hop=2, aspect_coverage=coverage
        )
        assert should_continue
        
        # Simulate hop 3 - covers comparison
        docs_hop3 = docs_hop2 + [
            {
                'title': 'Comparing Attention Mechanisms',
                'content': 'The main difference between self-attention and multi-head attention is that multi-head uses multiple parallel attention layers.',
                'score': 0.90
            }
        ]
        self.planner.update_aspect_coverage(coverage, docs_hop3, current_hop=3)
        
        # Should stop now - all aspects covered
        should_continue, reason = self.planner.should_continue_retrieval(
            docs_hop3, current_hop=3, aspect_coverage=coverage
        )
        assert not should_continue
        assert "covered" in reason.lower()
    
    def test_simple_query_scenario(self):
        """Test scenario with simple definition query."""
        question = "What is a neural network?"
        
        coverage = self.planner.extract_aspects(question, llm_client=None)
        
        # Should have at least a definition aspect
        assert len(coverage.aspects) >= 1
        
        # Good document covers the definition
        docs = [
            {
                'title': 'Neural Networks Explained',
                'content': 'A neural network is a computational model inspired by biological neurons. It consists of interconnected nodes that process information.',
                'score': 0.92
            }
        ]
        
        self.planner.update_aspect_coverage(coverage, docs, current_hop=1)
        
        # Might stop early if single aspect is well covered
        should_continue, _ = self.planner.should_continue_retrieval(
            docs, current_hop=3, aspect_coverage=coverage
        )
        
        # With good coverage, should be able to stop
        coverage_pct = coverage.get_coverage_percentage()
        assert coverage_pct > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

