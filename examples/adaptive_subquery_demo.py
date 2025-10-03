"""
Demo: Adaptive Subquery Generation in Research Agent

This demo showcases the new adaptive subquery generation features:
1. Complexity analysis that estimates required hops
2. Adaptive subquery generation based on question complexity
3. Subquery scoring and prioritization
4. Iterative retrieval with early stopping
5. Comprehensive logging and tracing

Dev Settings:
- Simple questions: 3 hops
- Medium questions: 7 hops
- Hard questions: 10 hops

Run this demo to see how the system adapts to different question complexities.
"""

import logging
import sys
from agents.research.query_planner import QueryPlanner, QueryComplexity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s [%(name)s]: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def demo_complexity_analysis():
    """Demonstrate complexity analysis on various questions."""
    print("\n" + "="*80)
    print("DEMO 1: COMPLEXITY ANALYSIS")
    print("="*80)
    
    planner = QueryPlanner(min_hops=3, max_hops=10)
    
    test_questions = [
        ("Simple", "What is Python?"),
        ("Moderate", "How does artificial intelligence work in healthcare?"),
        ("Complex", "Compare different machine learning algorithms for image recognition and explain their advantages and disadvantages"),
        ("Very Complex", "What are the benefits and challenges of implementing blockchain technology in healthcare and how does it compare to traditional database systems in terms of security, scalability, and cost-effectiveness?")
    ]
    
    for category, question in test_questions:
        print(f"\n{category} Question:")
        print(f"  '{question}'")
        print("-" * 80)
        
        complexity = planner.analyze_complexity(question)
        
        print(f"  Complexity Score: {complexity.complexity_score:.2f}")
        print(f"  Estimated Hops: {complexity.estimated_hops}")
        print(f"  Confidence: {complexity.confidence:.2f}")
        print(f"  Reasoning: {complexity.reasoning}")
        if complexity.indicators:
            print(f"  Indicators Found: {', '.join(complexity.indicators.keys())}")


def demo_adaptive_subquery_generation():
    """Demonstrate adaptive subquery generation."""
    print("\n" + "="*80)
    print("DEMO 2: ADAPTIVE SUBQUERY GENERATION")
    print("="*80)
    
    planner = QueryPlanner(min_hops=3, max_hops=10)
    
    test_cases = [
        ("Simple Question", "What is machine learning?"),
        ("Complex Question", "Compare Python, Java, and JavaScript for web development, data science, and mobile app development")
    ]
    
    for case_name, question in test_cases:
        print(f"\n{case_name}:")
        print(f"  '{question}'")
        print("-" * 80)
        
        # Analyze complexity
        complexity = planner.analyze_complexity(question)
        print(f"  Expected hops: {complexity.estimated_hops}")
        
        # Generate subqueries adaptively
        subqueries = planner.generate_subqueries(question, adaptive=True)
        print(f"  Generated {len(subqueries)} subqueries:")
        for i, sq in enumerate(subqueries, 1):
            print(f"    {i}. {sq}")


def demo_subquery_scoring():
    """Demonstrate subquery scoring and prioritization."""
    print("\n" + "="*80)
    print("DEMO 3: SUBQUERY SCORING AND PRIORITIZATION")
    print("="*80)
    
    planner = QueryPlanner()
    
    question = "What is deep learning and how is it used?"
    print(f"\nMain Question: '{question}'")
    print("-" * 80)
    
    # Generate candidate subqueries
    subqueries = planner.generate_subqueries(question, adaptive=True)
    print(f"\nCandidate Subqueries ({len(subqueries)}):")
    for i, sq in enumerate(subqueries, 1):
        print(f"  {i}. {sq}")
    
    # Score and prioritize
    scored = planner.score_subqueries(question, subqueries)
    print(f"\nScored and Prioritized:")
    for sq in scored:
        print(f"  Priority {sq.priority}: [{sq.relevance_score:.3f}] {sq.subquery}")
        print(f"    → {sq.reasoning}")


def demo_iterative_decision_logic():
    """Demonstrate iterative retrieval decision logic."""
    print("\n" + "="*80)
    print("DEMO 4: ITERATIVE RETRIEVAL DECISION LOGIC")
    print("="*80)
    
    planner = QueryPlanner(min_hops=3, max_hops=10)
    
    scenarios = [
        ("Scenario 1: High quality docs early", [
            {'score': 0.95, 'title': 'Excellent Doc 1'},
            {'score': 0.90, 'title': 'Excellent Doc 2'},
            {'score': 0.85, 'title': 'Good Doc 3'}
        ], 2),
        ("Scenario 2: Low quality docs", [
            {'score': 0.3, 'title': 'Poor Doc 1'},
            {'score': 0.25, 'title': 'Poor Doc 2'}
        ], 2),
        ("Scenario 3: At max hops", [
            {'score': 0.7, 'title': 'Doc 1'}
        ], 10),
        ("Scenario 4: Below min hops", [
            {'score': 0.9, 'title': 'Great Doc'}
        ], 2)
    ]
    
    for scenario_name, docs, current_hop in scenarios:
        print(f"\n{scenario_name}:")
        print(f"  Current Hop: {current_hop}/{planner.max_hops}")
        print(f"  Documents: {len(docs)}")
        if docs:
            avg_score = sum(d['score'] for d in docs) / len(docs)
            print(f"  Average Score: {avg_score:.2f}")
        print("-" * 80)
        
        should_continue, reasoning = planner.should_continue_retrieval(
            docs, current_hop, min_confidence_threshold=0.5
        )
        
        decision = "✓ CONTINUE" if should_continue else "✗ STOP"
        print(f"  Decision: {decision}")
        print(f"  Reasoning: {reasoning}")


def demo_comparison_adaptive_vs_fixed():
    """Compare adaptive vs fixed subquery generation."""
    print("\n" + "="*80)
    print("DEMO 5: ADAPTIVE VS FIXED COMPARISON")
    print("="*80)
    
    planner = QueryPlanner(min_hops=3, max_hops=10)
    
    questions = [
        "What is Python?",  # Simple
        "How does machine learning work?",  # Moderate
        "Compare supervised, unsupervised, and reinforcement learning algorithms and explain their use cases"  # Complex
    ]
    
    for question in questions:
        print(f"\nQuestion: '{question}'")
        print("-" * 80)
        
        # Adaptive mode
        adaptive_subqueries = planner.generate_subqueries(question, adaptive=True)
        complexity = planner.analyze_complexity(question)
        
        # Non-adaptive (fixed at 3)
        non_adaptive_subqueries = planner.generate_subqueries(question, adaptive=False)
        
        print(f"  Complexity: {complexity.complexity_score:.2f}")
        print(f"  Adaptive Mode: {len(adaptive_subqueries)} subqueries")
        print(f"  Fixed Mode: {len(non_adaptive_subqueries)} subqueries")
        print(f"  Difference: {abs(len(adaptive_subqueries) - len(non_adaptive_subqueries))} subqueries")
        
        if len(adaptive_subqueries) < len(non_adaptive_subqueries):
            savings = ((len(non_adaptive_subqueries) - len(adaptive_subqueries)) / len(non_adaptive_subqueries)) * 100
            print(f"  → Savings: {savings:.1f}% fewer queries (more efficient)")
        elif len(adaptive_subqueries) > len(non_adaptive_subqueries):
            improvement = ((len(adaptive_subqueries) - len(non_adaptive_subqueries)) / len(non_adaptive_subqueries)) * 100
            print(f"  → Improvement: {improvement:.1f}% more queries (better coverage)")


def demo_logging_and_tracing():
    """Demonstrate comprehensive logging and tracing."""
    print("\n" + "="*80)
    print("DEMO 6: LOGGING AND TRACING")
    print("="*80)
    print("\nNote: All demos above include comprehensive logging.")
    print("Check the console output to see detailed traces including:")
    print("  - Complexity analysis details")
    print("  - Subquery generation progress")
    print("  - Scoring calculations")
    print("  - Decision-making reasoning")
    print("\nThis helps with:")
    print("  - Debugging issues")
    print("  - Understanding system behavior")
    print("  - Performance optimization")
    print("  - Auditing decisions")


def main():
    """Run all demos."""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + " "*20 + "ADAPTIVE SUBQUERY GENERATION DEMO" + " "*25 + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    try:
        demo_complexity_analysis()
        demo_adaptive_subquery_generation()
        demo_subquery_scoring()
        demo_iterative_decision_logic()
        demo_comparison_adaptive_vs_fixed()
        demo_logging_and_tracing()
        
        print("\n" + "="*80)
        print("DEMO COMPLETE!")
        print("="*80)
        print("\nKey Takeaways:")
        print("  ✓ Complexity analysis automatically estimates required hops")
        print("  ✓ Adaptive generation creates optimal number of subqueries")
        print("  ✓ Scoring prioritizes most relevant subqueries")
        print("  ✓ Iterative retrieval stops early when sufficient info is found")
        print("  ✓ Comprehensive logging aids debugging and monitoring")
        print("\nBenefits:")
        print("  • Reduced computational cost for simple questions")
        print("  • Better coverage for complex questions")
        print("  • More efficient resource utilization")
        print("  • Transparent decision-making")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

