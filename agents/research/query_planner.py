"""
Query Planner for Multi-hop Research Agent
Handles subquery generation and query planning with adaptive complexity analysis.
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import logging
from dataclasses import dataclass
from ..shared.interfaces import IQueryPlanner

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class QueryComplexity:
    """Represents the estimated complexity of a query."""
    estimated_hops: int
    confidence: float  # 0.0 to 1.0
    complexity_score: float  # 0.0 to 1.0 (simple to complex)
    reasoning: str
    indicators: Dict[str, Any]


@dataclass
class ScoredSubquery:
    """Represents a subquery with relevance and priority scores."""
    subquery: str
    relevance_score: float  # 0.0 to 1.0
    priority: int  # 1 (highest) to N (lowest)
    reasoning: str


class QueryPlanner(IQueryPlanner):
    """
    Adaptive query planner that breaks down complex research questions into focused subqueries.
    Uses complexity analysis to determine the optimal number of hops dynamically.
    """
    
    def __init__(self, min_hops: int = 3, max_hops: int = 10):
        """
        Initialize the query planner with adaptive parameters.
        
        Args:
            min_hops: Minimum number of subqueries to generate (default: 3)
            max_hops: Maximum number of subqueries to prevent infinite loops (default: 10)
        """
        self.min_hops = min_hops
        self.max_hops = max_hops
        
        # Complexity indicators
        self.complexity_indicators = {
            'multi_aspect': [r'\band\b', r'\bor\b', r','],  # Multiple aspects
            'comparison': [r'compare|vs|versus|difference|similarities'],
            'causal': [r'why|because|reason|cause|effect|impact'],
            'process': [r'how|process|steps|mechanism|procedure'],
            'evaluation': [r'best|worst|better|worse|advantage|disadvantage|pros|cons'],
            'temporal': [r'future|past|history|evolution|trend|development'],
            'complex_connectives': [r'however|although|despite|while|whereas']
        }
        
        logger.info(f"QueryPlanner initialized with adaptive parameters: min_hops={min_hops}, max_hops={max_hops}")
    
    def analyze_complexity(self, question: str) -> QueryComplexity:
        """
        Analyze the complexity of a question to estimate required hops.
        
        Args:
            question: The research question to analyze
            
        Returns:
            QueryComplexity object with estimated hops and reasoning
        """
        question_lower = question.lower()
        indicators_found = {}
        complexity_score = 0.0
        
        # Check for complexity indicators
        for indicator_type, patterns in self.complexity_indicators.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    matches.append(pattern)
            
            if matches:
                indicators_found[indicator_type] = matches
                # Weight different indicators
                if indicator_type == 'multi_aspect':
                    complexity_score += 0.3 * len(matches)
                elif indicator_type == 'comparison':
                    complexity_score += 0.4
                elif indicator_type == 'causal':
                    complexity_score += 0.2
                elif indicator_type == 'process':
                    complexity_score += 0.2
                elif indicator_type == 'evaluation':
                    complexity_score += 0.3
                elif indicator_type == 'temporal':
                    complexity_score += 0.15
                elif indicator_type == 'complex_connectives':
                    complexity_score += 0.25
        
        # Question length as a complexity factor
        word_count = len(question.split())
        if word_count > 15:
            complexity_score += 0.2
        elif word_count > 10:
            complexity_score += 0.1
        
        # Normalize complexity score
        complexity_score = min(complexity_score, 1.0)
        
        # Estimate hops based on complexity (dev settings: simple=3, medium=7, hard=10)
        if complexity_score < 0.2:
            estimated_hops = 3  # Simple questions
            reasoning = "Simple, focused question requiring minimal decomposition"
            confidence = 0.9
        elif complexity_score < 0.4:
            estimated_hops = 5
            reasoning = "Moderately simple question with 1-2 aspects"
            confidence = 0.8
        elif complexity_score < 0.6:
            estimated_hops = 7  # Medium complexity
            reasoning = "Complex question with multiple aspects or comparisons"
            confidence = 0.7
        elif complexity_score < 0.8:
            estimated_hops = 9
            reasoning = "Highly complex question requiring multiple perspectives"
            confidence = 0.6
        else:
            estimated_hops = 10  # Hard/very complex questions
            reasoning = "Very complex question with many interconnected aspects"
            confidence = 0.5
        
        # Ensure within bounds
        estimated_hops = max(self.min_hops, min(estimated_hops, self.max_hops))
        
        logger.info(f"Complexity analysis: score={complexity_score:.2f}, estimated_hops={estimated_hops}, indicators={list(indicators_found.keys())}")
        
        return QueryComplexity(
            estimated_hops=estimated_hops,
            confidence=confidence,
            complexity_score=complexity_score,
            reasoning=reasoning,
            indicators=indicators_found
        )
    
    def generate_subqueries(self, question: str, llm_client=None, adaptive: bool = True) -> List[str]:
        """
        Generate subqueries using LLM-based generation (no regex patterns).
        This is a placeholder that should be called via the research agent with an LLM client.
        
        Args:
            question: The main research question
            llm_client: LLM client for generating subqueries (required)
            adaptive: If True, use adaptive logic based on complexity (default: True)
            
        Returns:
            List of subqueries to investigate
        """
        # Clean the question
        question_clean = question.strip()
        
        # Analyze complexity if adaptive mode is enabled
        if adaptive:
            complexity = self.analyze_complexity(question_clean)
            target_count = complexity.estimated_hops
            logger.info(f"Target subquery count: {target_count} ({complexity.reasoning})")
        else:
            target_count = 5  # Default fallback
        
        # Check if LLM client is available
        if llm_client is None:
            logger.warning("No LLM client provided. Using simple fallback subquery generation.")
            # Simple fallback: create basic variations of the question
            key_terms = self._extract_key_terms(question_clean.lower())
            base_terms = " ".join(key_terms)
            
            subqueries = [
                question_clean,  # Original question
                f"what is {base_terms}",
                f"how does {base_terms} work",
                f"examples of {base_terms}",
                f"applications of {base_terms}",
                f"benefits of {base_terms}",
                f"challenges of {base_terms}",
                f"future of {base_terms}"
            ]
            
            # Remove duplicates and limit to target count
            subqueries = list(dict.fromkeys(subqueries))[:target_count]
            
            logger.info(f"Generated {len(subqueries)} fallback subqueries")
            return subqueries
        
        # Use LLM to generate subqueries
        logger.info(f"Using LLM to generate {target_count} subqueries")
        
        # The LLM client will handle generation in the research agent
        # This method is kept for compatibility but defers to LLM
        return []  # Empty list signals to use LLM generation
    
    def score_subqueries(self, main_question: str, subqueries: List[str]) -> List[ScoredSubquery]:
        """
        Score and prioritize subqueries based on relevance to main question.
        
        Args:
            main_question: The original research question
            subqueries: List of candidate subqueries
            
        Returns:
            List of ScoredSubquery objects sorted by priority
        """
        main_terms = set(self._extract_key_terms(main_question.lower()))
        scored_subqueries = []
        
        for subquery in subqueries:
            subquery_terms = set(self._extract_key_terms(subquery.lower()))
            
            # Calculate term overlap
            if len(main_terms) > 0:
                overlap = len(main_terms & subquery_terms) / len(main_terms)
            else:
                overlap = 0.0
            
            # Calculate diversity (prefer queries that add new terms)
            new_terms = len(subquery_terms - main_terms)
            diversity_score = min(new_terms / 5.0, 1.0)  # Normalize
            
            # Combined relevance score (70% overlap, 30% diversity)
            relevance_score = (0.7 * overlap) + (0.3 * diversity_score)
            
            # Determine reasoning
            if relevance_score > 0.7:
                reasoning = "High relevance with good term overlap"
            elif relevance_score > 0.5:
                reasoning = "Moderate relevance with some new perspective"
            elif relevance_score > 0.3:
                reasoning = "Lower relevance but adds diversity"
            else:
                reasoning = "Low relevance, may be too divergent"
            
            scored_subqueries.append(ScoredSubquery(
                subquery=subquery,
                relevance_score=relevance_score,
                priority=0,  # Will be set after sorting
                reasoning=reasoning
            ))
        
        # Sort by relevance score (descending)
        scored_subqueries.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Assign priorities
        for i, scored in enumerate(scored_subqueries, 1):
            scored.priority = i
        
        logger.info(f"Scored {len(scored_subqueries)} subqueries, top score: {scored_subqueries[0].relevance_score:.2f}")
        
        return scored_subqueries
    
    def should_continue_retrieval(self, retrieved_docs: List[Dict[str, Any]], 
                                  current_hop: int, 
                                  min_confidence_threshold: float = 0.5) -> Tuple[bool, str]:
        """
        Determine if more subqueries should be generated based on retrieved results.
        Used for iterative retrieval in the research agent.
        
        Args:
            retrieved_docs: Documents retrieved so far
            current_hop: Current hop number (1-indexed)
            min_confidence_threshold: Minimum average confidence score to stop early
            
        Returns:
            Tuple of (should_continue, reasoning)
        """
        # Stop if we've reached max hops
        if current_hop >= self.max_hops:
            return False, f"Reached maximum hop limit ({self.max_hops})"
        
        # Continue if we have no documents yet
        if not retrieved_docs or len(retrieved_docs) == 0:
            if current_hop < self.max_hops:
                return True, "No documents found yet, continuing search"
            else:
                return False, "No documents found and at max hops"
        
        # Check document quality/relevance
        if len(retrieved_docs) > 0:
            avg_score = sum(doc.get('score', 0.0) for doc in retrieved_docs) / len(retrieved_docs)
            
            if avg_score >= min_confidence_threshold and len(retrieved_docs) >= 3:
                return False, f"Sufficient high-quality documents found (avg score: {avg_score:.2f})"
            elif current_hop < self.min_hops:
                return True, f"Below minimum hops ({self.min_hops}), continuing"
            elif avg_score < min_confidence_threshold:
                return True, f"Document quality below threshold ({avg_score:.2f} < {min_confidence_threshold}), continuing"
        
        # Default: continue if below max hops
        if current_hop < self.max_hops:
            return True, "Continuing to gather more information"
        else:
            return False, "Stopping at current hop"
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from a question, removing common stop words.
        
        Args:
            text: Input text
            
        Returns:
            List of key terms
        """
        # Common stop words to remove
        stop_words = {
            'what', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'how', 'why', 'when', 'where', 'who', 'which', 'that', 'this', 'these', 'those', 'do', 'does', 'did',
            'can', 'could', 'should', 'would', 'will', 'may', 'might', 'must', 'have', 'has', 'had', 'be', 'been',
            'being', 'was', 'were', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
        }
        
        # Clean and split text
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stop words and short words
        key_terms = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return key_terms


if __name__ == "__main__":
    # Test the adaptive query planner
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    planner = QueryPlanner(min_hops=1, max_hops=5)
    
    test_questions = [
        "What is Python?",  # Simple question
        "How does artificial intelligence work in healthcare?",  # Moderate
        "Compare different machine learning algorithms for image recognition and explain their advantages and disadvantages",  # Complex
        "What are the future trends in quantum computing?",  # Moderate
        "Why is cybersecurity important for businesses and what are the best practices?"  # Moderately complex
    ]
    
    for question in test_questions:
        print(f"\n{'='*80}")
        print(f"Question: {question}")
        print('='*80)
        
        # Analyze complexity
        complexity = planner.analyze_complexity(question)
        print(f"\nComplexity Analysis:")
        print(f"  - Estimated hops: {complexity.estimated_hops}")
        print(f"  - Complexity score: {complexity.complexity_score:.2f}")
        print(f"  - Confidence: {complexity.confidence:.2f}")
        print(f"  - Reasoning: {complexity.reasoning}")
        print(f"  - Indicators: {list(complexity.indicators.keys())}")
        
        # Generate subqueries
        subqueries = planner.generate_subqueries(question, adaptive=True)
        print(f"\nGenerated {len(subqueries)} subqueries:")
        for i, subquery in enumerate(subqueries, 1):
            print(f"  {i}. {subquery}")
        
        # Score subqueries
        if len(subqueries) > 1:
            scored = planner.score_subqueries(question, subqueries)
            print(f"\nTop 3 Scored Subqueries:")
            for sq in scored[:3]:
                print(f"  - [{sq.relevance_score:.2f}] {sq.subquery}")
                print(f"    Reasoning: {sq.reasoning}")
