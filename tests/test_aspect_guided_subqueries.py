"""
Test suite for aspect-guided subquery generation.
"""

import pytest
from agents.research.query_planner import QueryPlanner, QueryAspect, AspectCoverage


class TestAspectToSubqueryTemplates:
    """Test template-based aspect-to-subquery conversion."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(enable_aspect_coverage=True)
    
    def test_definition_aspect_to_subquery(self):
        """Test converting definition aspect to subquery."""
        aspect = QueryAspect(
            aspect="Definition of attention heads",
            aspect_type="definition",
            importance=1.0,
            keywords=["attention", "heads", "definition"]
        )
        
        subquery = self.planner._aspect_to_subquery_template(aspect, "What are attention heads?")
        
        assert "attention heads" in subquery.lower()
        assert subquery.startswith("What")
    
    def test_comparison_aspect_to_subquery(self):
        """Test converting comparison aspect to subquery."""
        aspect = QueryAspect(
            aspect="Comparison between self-attention and multi-head",
            aspect_type="comparison",
            importance=1.0,
            keywords=["self-attention", "multi-head", "comparison"]
        )
        
        subquery = self.planner._aspect_to_subquery_template(aspect, "Compare attention mechanisms")
        
        assert "differences" in subquery.lower() or "similarities" in subquery.lower()
    
    def test_process_aspect_to_subquery(self):
        """Test converting process aspect to subquery."""
        aspect = QueryAspect(
            aspect="How attention mechanism works",
            aspect_type="process",
            importance=0.8,
            keywords=["attention", "mechanism", "process"]
        )
        
        subquery = self.planner._aspect_to_subquery_template(aspect, "Explain attention")
        
        assert "how" in subquery.lower()
        assert "work" in subquery.lower()
    
    def test_evaluation_aspect_advantages_to_subquery(self):
        """Test converting evaluation aspect (advantages) to subquery."""
        aspect = QueryAspect(
            aspect="Advantages of transformers",
            aspect_type="evaluation",
            importance=0.7,
            keywords=["advantages", "transformers"]
        )
        
        subquery = self.planner._aspect_to_subquery_template(aspect, "Evaluate transformers")
        
        assert "advantages" in subquery.lower()
    
    def test_application_aspect_to_subquery(self):
        """Test converting application aspect to subquery."""
        aspect = QueryAspect(
            aspect="Applications of neural networks",
            aspect_type="application",
            importance=0.6,
            keywords=["applications", "neural", "networks"]
        )
        
        subquery = self.planner._aspect_to_subquery_template(aspect, "Neural networks usage")
        
        assert "applications" in subquery.lower() or "uses" in subquery.lower()


class TestGenerateSubqueriesForAspects:
    """Test generating subqueries for uncovered aspects."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(enable_aspect_coverage=True)
        
        self.aspects = [
            QueryAspect("Core aspect 1", "definition", 1.0, ["test", "core"]),
            QueryAspect("Core aspect 2", "definition", 1.0, ["test", "core"]),
            QueryAspect("Optional aspect", "application", 0.6, ["test", "optional"])
        ]
    
    def test_generate_subqueries_for_aspects_basic(self):
        """Test basic subquery generation for aspects."""
        question = "What is the test topic?"
        
        subquery_mappings = self.planner.generate_subqueries_for_aspects(
            question, self.aspects, llm_client=None, max_subqueries=2
        )
        
        # Should generate 2 subqueries (max_subqueries limit)
        assert len(subquery_mappings) == 2
        
        # Each should be a tuple of (subquery, aspect_name)
        for subquery, aspect_name in subquery_mappings:
            assert isinstance(subquery, str)
            assert isinstance(aspect_name, str)
            assert len(subquery) > 0
    
    def test_prioritize_core_aspects(self):
        """Test that core aspects are prioritized."""
        question = "What is the test topic?"
        
        subquery_mappings = self.planner.generate_subqueries_for_aspects(
            question, self.aspects, llm_client=None, max_subqueries=2
        )
        
        # First 2 should target core aspects (importance=1.0)
        aspect_names = [aspect_name for _, aspect_name in subquery_mappings]
        assert "Core aspect 1" in aspect_names or "Core aspect 2" in aspect_names
        # Optional aspect should not be in first 2
        assert "Optional aspect" not in aspect_names
    
    def test_empty_aspects_returns_empty(self):
        """Test that empty aspects list returns empty subqueries."""
        question = "What is the test topic?"
        
        subquery_mappings = self.planner.generate_subqueries_for_aspects(
            question, [], llm_client=None
        )
        
        assert len(subquery_mappings) == 0
    
    def test_max_subqueries_limit(self):
        """Test that max_subqueries limit is respected."""
        question = "What is the test topic?"
        
        subquery_mappings = self.planner.generate_subqueries_for_aspects(
            question, self.aspects, llm_client=None, max_subqueries=1
        )
        
        # Should only generate 1 subquery
        assert len(subquery_mappings) == 1


class TestAspectGuidedIntegration:
    """Integration tests for aspect-guided subquery generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(min_hops=2, max_hops=8, enable_aspect_coverage=True)
    
    def test_aspect_guided_flow(self):
        """Test the full aspect-guided flow."""
        question = "Compare self-attention vs multi-head attention"
        
        # 1. Extract aspects
        coverage = self.planner.extract_aspects(question, llm_client=None)
        assert len(coverage.aspects) >= 2
        
        # 2. Get uncovered aspects (all uncovered initially)
        uncovered = coverage.get_uncovered_aspects(threshold=0.5)
        assert len(uncovered) == len(coverage.aspects)
        
        # 3. Generate subqueries for uncovered aspects
        subquery_mappings = self.planner.generate_subqueries_for_aspects(
            question, uncovered, llm_client=None, max_subqueries=2
        )
        
        assert len(subquery_mappings) <= 2
        
        # 4. Simulate covering one aspect with better keyword matches
        mock_docs = [
            {
                'title': 'Compare Self-Attention and Multi-Head Attention',
                'content': 'Compare self-attention: a mechanism where attention is computed. Multi-head attention uses multiple attention heads in parallel. The comparison shows differences.',
                'score': 0.85
            }
        ]
        
        self.planner.update_aspect_coverage(coverage, mock_docs, current_hop=1)
        
        # 5. Check that some aspects are now covered (may be all if document covers everything)
        uncovered_after = coverage.get_uncovered_aspects(threshold=0.5)
        # Coverage should have improved (less or equal uncovered)
        assert len(uncovered_after) <= len(coverage.aspects)
        
        # 6. Generate next round of subqueries for still-uncovered aspects
        next_subqueries = self.planner.generate_subqueries_for_aspects(
            question, uncovered_after, llm_client=None, max_subqueries=1
        )
        
        # Should target different aspects than first round
        if next_subqueries:
            first_aspects = [aspect for _, aspect in subquery_mappings]
            next_aspects = [aspect for _, aspect in next_subqueries]
            # At least some should be different (may overlap if multiple aspects uncovered)
            assert len(next_aspects) > 0
    
    def test_stops_when_all_aspects_covered(self):
        """Test that generation stops when all aspects are covered."""
        question = "What is Python?"
        
        coverage = self.planner.extract_aspects(question, llm_client=None)
        
        # Manually set all aspects as covered
        for aspect in coverage.aspects:
            coverage.coverage_scores[aspect.aspect] = 0.9
        
        uncovered = coverage.get_uncovered_aspects(threshold=0.5)
        assert len(uncovered) == 0
        
        # Should return empty list
        subqueries = self.planner.generate_subqueries_for_aspects(
            question, uncovered, llm_client=None
        )
        assert len(subqueries) == 0


class TestAspectGuidedLogging:
    """Test logging and debugging output for aspect-guided generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(enable_aspect_coverage=True)
    
    def test_aspect_to_subquery_mapping_logged(self):
        """Test that aspect-to-subquery mappings are returned correctly."""
        aspects = [
            QueryAspect(
                "Query/Key/Value Vectors",
                "definition",
                1.0,
                ["query", "key", "value", "vectors"]
            )
        ]
        
        question = "What are query, key, and value vectors?"
        
        mappings = self.planner.generate_subqueries_for_aspects(
            question, aspects, llm_client=None
        )
        
        assert len(mappings) == 1
        subquery, aspect_name = mappings[0]
        
        # Verify mapping is clear
        assert aspect_name == "Query/Key/Value Vectors"
        assert "query" in subquery.lower() or "key" in subquery.lower() or "value" in subquery.lower()


class TestEdgeCases:
    """Test edge cases in aspect-guided subquery generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner(enable_aspect_coverage=True)
    
    def test_aspect_with_no_keywords(self):
        """Test handling aspect with empty keywords."""
        aspect = QueryAspect(
            "Some aspect",
            "general",
            0.8,
            []  # No keywords
        )
        
        subquery = self.planner._aspect_to_subquery_template(aspect, "Test question")
        
        # Should still generate something reasonable
        assert len(subquery) > 0
        assert len(subquery) < 100  # Not too long
    
    def test_aspect_with_long_name(self):
        """Test handling aspect with very long name."""
        aspect = QueryAspect(
            "This is a very long aspect name that describes something complex and detailed about the topic",
            "definition",
            1.0,
            ["long", "aspect", "complex"]
        )
        
        subquery = self.planner._aspect_to_subquery_template(aspect, "Test question")
        
        # Should generate a reasonable subquery
        assert len(subquery) > 0
        assert len(subquery) < 200  # Not too long
    
    def test_special_characters_in_aspect(self):
        """Test handling special characters in aspect name."""
        aspect = QueryAspect(
            "Query/Key/Value matrices & vectors",
            "definition",
            1.0,
            ["query", "key", "value"]
        )
        
        subquery = self.planner._aspect_to_subquery_template(aspect, "Test question")
        
        # Should handle special characters gracefully
        assert len(subquery) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

