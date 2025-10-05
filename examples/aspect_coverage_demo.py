"""
Demonstration of the new aspect-based coverage tracking feature.

This example shows how the multihop subquery generation now tracks coverage
of different aspects of a query to ensure complete answers.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.research.query_planner import QueryPlanner, AspectCoverage, QueryAspect


def demo_aspect_extraction():
    """Demonstrate aspect extraction from different query types."""
    print("=" * 80)
    print("ASPECT EXTRACTION DEMO")
    print("=" * 80)
    
    planner = QueryPlanner(min_hops=3, max_hops=10, enable_aspect_coverage=True)
    
    test_queries = [
        "self-attention vs multi-head attention",
        "What is transformer architecture?",
        "How does backpropagation work?",
        "Why is regularization important in deep learning?",
        "Compare RNN and LSTM architectures",
        "What are the advantages and disadvantages of neural networks?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 80)
        
        # Extract aspects (without LLM - using heuristics)
        coverage = planner.extract_aspects(query, llm_client=None)
        
        print(f"Identified {len(coverage.aspects)} aspects:")
        for i, aspect in enumerate(coverage.aspects, 1):
            importance = "CORE" if aspect.importance >= 0.8 else "optional"
            print(f"  {i}. [{importance}] {aspect.aspect}")
            print(f"     Type: {aspect.aspect_type}")
            print(f"     Keywords: {', '.join(aspect.keywords[:5])}")
        
        print()


def demo_coverage_tracking():
    """Demonstrate coverage tracking during document retrieval."""
    print("\n" + "=" * 80)
    print("COVERAGE TRACKING DEMO")
    print("=" * 80)
    
    planner = QueryPlanner(min_hops=3, max_hops=8, enable_aspect_coverage=True)
    
    # Example query
    query = "self-attention vs multi-head attention"
    print(f"\n📝 Query: {query}")
    
    # Extract aspects
    coverage = planner.extract_aspects(query, llm_client=None)
    
    print(f"\nIdentified {len(coverage.aspects)} aspects:")
    for i, aspect in enumerate(coverage.aspects, 1):
        print(f"  {i}. {aspect.aspect}")
    
    print("\n" + "=" * 80)
    print("SIMULATING DOCUMENT RETRIEVAL")
    print("=" * 80)
    
    # Simulate hop 1: Documents about self-attention
    print("\n[Hop 1] Retrieving documents for 'self-attention'...")
    docs_hop1 = [
        {
            'title': 'Self-Attention Mechanism Explained',
            'content': 'Self-attention is a mechanism in neural networks where each element in a sequence attends to all other elements. It computes attention scores to determine relevance.',
            'score': 0.88
        },
        {
            'title': 'Introduction to Attention',
            'content': 'Attention mechanisms allow neural networks to focus on relevant parts of input. Self-attention is a type where the query, key, and value all come from the same sequence.',
            'score': 0.82
        }
    ]
    
    planner.update_aspect_coverage(coverage, docs_hop1, current_hop=1)
    print_coverage_status(coverage, current_hop=1)
    
    # Check if should continue
    should_continue, reason = planner.should_continue_retrieval(
        docs_hop1, current_hop=1, aspect_coverage=coverage
    )
    print(f"\n{'✅ Continue' if should_continue else '🛑 Stop'}: {reason}")
    
    # Simulate hop 2: Documents about multi-head attention
    print("\n[Hop 2] Retrieving documents for 'multi-head attention'...")
    docs_hop2 = docs_hop1 + [
        {
            'title': 'Multi-Head Attention Architecture',
            'content': 'Multi-head attention runs multiple attention mechanisms in parallel. Each head learns different aspects of the relationships between elements in the sequence.',
            'score': 0.90
        },
        {
            'title': 'Understanding Multi-Head Attention',
            'content': 'In multi-head attention, we use multiple attention heads. Each head has its own set of query, key, and value weight matrices.',
            'score': 0.85
        }
    ]
    
    planner.update_aspect_coverage(coverage, docs_hop2, current_hop=2)
    print_coverage_status(coverage, current_hop=2)
    
    should_continue, reason = planner.should_continue_retrieval(
        docs_hop2, current_hop=2, aspect_coverage=coverage
    )
    print(f"\n{'✅ Continue' if should_continue else '🛑 Stop'}: {reason}")
    
    # Simulate hop 3: Documents comparing the two
    print("\n[Hop 3] Retrieving documents for 'comparison'...")
    docs_hop3 = docs_hop2 + [
        {
            'title': 'Comparing Attention Mechanisms',
            'content': 'The key difference between self-attention and multi-head attention: self-attention uses a single attention mechanism, while multi-head attention uses multiple parallel attention mechanisms. Multi-head attention captures different types of relationships.',
            'score': 0.92
        }
    ]
    
    planner.update_aspect_coverage(coverage, docs_hop3, current_hop=3)
    print_coverage_status(coverage, current_hop=3)
    
    should_continue, reason = planner.should_continue_retrieval(
        docs_hop3, current_hop=3, aspect_coverage=coverage
    )
    print(f"\n{'✅ Continue' if should_continue else '🛑 Stop'}: {reason}")
    
    print("\n" + "=" * 80)
    print("FINAL COVERAGE SUMMARY")
    print("=" * 80)
    print(f"Overall Coverage: {coverage.get_coverage_percentage():.1%}")
    print(f"Weighted Coverage: {coverage.get_weighted_coverage():.1%}")
    print(f"\nAspects covered:")
    for aspect in coverage.aspects:
        score = coverage.coverage_scores.get(aspect.aspect, 0.0)
        hop = coverage.covered_by_hop.get(aspect.aspect, "N/A")
        status = "✅" if score >= 0.5 else "❌"
        print(f"  {status} {aspect.aspect}: {score:.1%} (covered at hop {hop})")


def demo_stopping_conditions():
    """Demonstrate different stopping conditions."""
    print("\n" + "=" * 80)
    print("STOPPING CONDITIONS DEMO")
    print("=" * 80)
    
    planner = QueryPlanner(min_hops=3, max_hops=8, enable_aspect_coverage=True)
    
    # Create mock aspects
    aspects = [
        QueryAspect("Core aspect 1", "definition", 1.0, ["test"]),
        QueryAspect("Core aspect 2", "definition", 1.0, ["test"]),
        QueryAspect("Optional aspect", "application", 0.6, ["test"])
    ]
    
    coverage = AspectCoverage(aspects=aspects)
    mock_docs = [{'title': 'Test', 'content': 'Test', 'score': 0.8}]
    
    # Scenario 1: Below min_hops
    print("\n📌 Scenario 1: Below minimum hops (even with good coverage)")
    coverage.coverage_scores = {a.aspect: 0.9 for a in aspects}
    should_continue, reason = planner.should_continue_retrieval(
        mock_docs, current_hop=2, aspect_coverage=coverage
    )
    print(f"   Current hop: 2, Min hops: {planner.min_hops}")
    print(f"   Result: {'Continue' if should_continue else 'Stop'}")
    print(f"   Reason: {reason}")
    
    # Scenario 2: Core aspects uncovered
    print("\n📌 Scenario 2: Core aspects still uncovered")
    coverage.coverage_scores = {
        "Core aspect 1": 0.3,
        "Core aspect 2": 0.2,
        "Optional aspect": 0.8
    }
    should_continue, reason = planner.should_continue_retrieval(
        mock_docs, current_hop=4, aspect_coverage=coverage
    )
    print(f"   Current hop: 4")
    print(f"   Result: {'Continue' if should_continue else 'Stop'}")
    print(f"   Reason: {reason}")
    
    # Scenario 3: All core aspects covered
    print("\n📌 Scenario 3: All core aspects covered")
    coverage.coverage_scores = {
        "Core aspect 1": 0.9,
        "Core aspect 2": 0.85,
        "Optional aspect": 0.3
    }
    should_continue, reason = planner.should_continue_retrieval(
        mock_docs, current_hop=4, aspect_coverage=coverage
    )
    print(f"   Current hop: 4")
    print(f"   Result: {'Continue' if should_continue else 'Stop'}")
    print(f"   Reason: {reason}")
    
    # Scenario 4: At max hops
    print("\n📌 Scenario 4: Reached maximum hops")
    coverage.coverage_scores = {a.aspect: 0.3 for a in aspects}  # Poor coverage
    should_continue, reason = planner.should_continue_retrieval(
        mock_docs, current_hop=8, aspect_coverage=coverage
    )
    print(f"   Current hop: 8, Max hops: {planner.max_hops}")
    print(f"   Result: {'Continue' if should_continue else 'Stop'}")
    print(f"   Reason: {reason}")


def print_coverage_status(coverage: AspectCoverage, current_hop: int):
    """Helper to print coverage status."""
    print(f"\nCoverage after Hop {current_hop}:")
    for aspect in coverage.aspects:
        score = coverage.coverage_scores.get(aspect.aspect, 0.0)
        status = "✅" if score >= 0.5 else "⏳"
        print(f"  {status} {aspect.aspect}: {score:.1%}")
    
    uncovered = coverage.get_uncovered_aspects()
    print(f"\nOverall: {coverage.get_coverage_percentage():.1%} ({len(uncovered)} aspects uncovered)")


if __name__ == "__main__":
    print("\n")
    print("🎯 ASPECT-BASED COVERAGE TRACKING DEMONSTRATION")
    print("=" * 80)
    print("This demo shows how the multihop research agent now tracks coverage")
    print("of different aspects to ensure complete answers.\n")
    
    # Run demonstrations
    demo_aspect_extraction()
    demo_coverage_tracking()
    demo_stopping_conditions()
    
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Features Demonstrated:")
    print("  1. Automatic aspect extraction from queries")
    print("  2. Coverage tracking across document retrieval hops")
    print("  3. Intelligent stopping based on aspect coverage")
    print("  4. Core vs. optional aspect prioritization")
    print("  5. Minimum hop enforcement for quality assurance")
    print("\n")

