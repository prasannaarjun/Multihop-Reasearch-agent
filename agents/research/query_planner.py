"""
Query Planner for Multi-hop Research Agent
Handles subquery generation and query planning with adaptive complexity analysis.
"""

from typing import List, Dict, Any, Optional, Tuple, Set, Iterable
import re
import logging
import random
import textwrap
from dataclasses import dataclass, field
from itertools import cycle
from difflib import SequenceMatcher

import numpy as np
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


@dataclass
class QueryAspect:
    """Represents a facet or aspect of a query."""
    aspect: str
    aspect_type: str  # e.g., 'definition', 'comparison', 'application'
    importance: float  # 0.0 to 1.0 (optional vs. core)
    keywords: List[str]  # Keywords associated with this aspect


@dataclass
class AspectCoverage:
    """Tracks coverage of query aspects across retrieved documents."""
    aspects: List[QueryAspect]
    coverage_scores: Dict[str, float] = field(default_factory=dict)  # aspect -> coverage score
    covered_by_hop: Dict[str, int] = field(default_factory=dict)  # aspect -> hop number when covered
    
    def __post_init__(self):
        """Initialize coverage scores to 0.0 for all aspects."""
        for aspect in self.aspects:
            if aspect.aspect not in self.coverage_scores:
                self.coverage_scores[aspect.aspect] = 0.0
    
    def is_aspect_covered(self, aspect: str, threshold: float = 0.5) -> bool:
        """Check if an aspect is covered above the threshold."""
        return self.coverage_scores.get(aspect, 0.0) >= threshold
    
    def get_uncovered_aspects(self, threshold: float = 0.5) -> List[QueryAspect]:
        """Get list of aspects that are not yet adequately covered."""
        return [
            aspect for aspect in self.aspects
            if not self.is_aspect_covered(aspect.aspect, threshold)
        ]
    
    def get_coverage_percentage(self) -> float:
        """Get overall coverage percentage (0.0 to 1.0)."""
        if not self.aspects:
            return 1.0  # No aspects = fully covered
        total_score = sum(self.coverage_scores.values())
        max_score = len(self.aspects)
        return total_score / max_score if max_score > 0 else 0.0
    
    def get_weighted_coverage(self) -> float:
        """Get weighted coverage based on aspect importance."""
        if not self.aspects:
            return 1.0
        total_weighted = sum(
            self.coverage_scores.get(aspect.aspect, 0.0) * aspect.importance
            for aspect in self.aspects
        )
        total_importance = sum(aspect.importance for aspect in self.aspects)
        return total_weighted / total_importance if total_importance > 0 else 0.0


class QueryPlanner(IQueryPlanner):
    """
    Adaptive query planner that breaks down complex research questions into focused subqueries.
    Uses complexity analysis to determine the optimal number of hops dynamically.
    """
    
    def __init__(
        self,
        min_hops: int = 3,
        max_hops: int = 10,
        enable_aspect_coverage: bool = True,
        coverage_goal: float = 0.8,
    ):
        """
        Initialize the query planner with adaptive parameters.
        
        Args:
            min_hops: Minimum number of subqueries to generate (default: 3)
            max_hops: Maximum number of subqueries to prevent infinite loops (default: 10)
            enable_aspect_coverage: Enable aspect-based coverage tracking (default: True)
        """
        self.min_hops = min_hops
        self.max_hops = max_hops
        self.enable_aspect_coverage = enable_aspect_coverage
        self.coverage_goal = coverage_goal
        self.duplicate_similarity_threshold = 0.8
        self.coverage_similarity_threshold = 0.7
        self._phrasing_cycle = cycle(
            [
                "definition focused angle",
                "functional role angle",
                "mechanism/process angle",
                "context/use-case angle",
                "example/comparison angle",
            ]
        )
        
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
        
        logger.info(
            "QueryPlanner initialized with adaptive parameters: min_hops=%s, max_hops=%s, aspect_coverage=%s, coverage_goal=%.2f",
            min_hops,
            max_hops,
            enable_aspect_coverage,
            coverage_goal,
        )
    
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
        
        # Estimate hops based on complexity (dev settings: simple=2, medium=6, hard=10)
        if complexity_score < 0.2:
            base_hops = 2
            reasoning = "Simple, focused question requiring minimal decomposition"
            confidence = 0.9
        elif complexity_score < 0.4:
            base_hops = 4
            reasoning = "Moderately simple question with 1-2 aspects"
            confidence = 0.8
        elif complexity_score < 0.6:
            base_hops = 6  # Medium complexity
            reasoning = "Complex question with multiple aspects or comparisons"
            confidence = 0.7
        elif complexity_score < 0.8:
            base_hops = 8
            reasoning = "Highly complex question requiring multiple perspectives"
            confidence = 0.6
        else:
            base_hops = 10  # Hard/very complex questions
            reasoning = "Very complex question with many interconnected aspects"
            confidence = 0.5

        # Ensure within bounds while respecting configured hop limits
        estimated_hops = max(self.min_hops, min(base_hops, self.max_hops))
        
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
                                  min_confidence_threshold: float = 0.5,
                                  aspect_coverage: Optional[AspectCoverage] = None,
                                  coverage_threshold: float = 0.5) -> Tuple[bool, str]:
        """
        Determine if more subqueries should be generated based on retrieved results.
        Used for iterative retrieval in the research agent.
        
        Args:
            retrieved_docs: Documents retrieved so far
            current_hop: Current hop number (1-indexed)
            min_confidence_threshold: Minimum average confidence score to stop early
            aspect_coverage: Optional AspectCoverage for aspect-based stopping
            coverage_threshold: Threshold for considering an aspect covered (default: 0.5)
            
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
        
        # Check aspect coverage if enabled and available
        if self.enable_aspect_coverage and aspect_coverage is not None:
            uncovered = aspect_coverage.get_uncovered_aspects(threshold=coverage_threshold)
            coverage_pct = aspect_coverage.get_coverage_percentage()
            weighted_coverage = aspect_coverage.get_weighted_coverage()

            logger.info("Coverage status at hop %s:", current_hop)
            logger.info("  Overall coverage: %.1f%%", coverage_pct * 100)
            logger.info("  Weighted coverage: %.1f%%", weighted_coverage * 100)
            logger.info(
                "  Uncovered aspects: %s/%s",
                len(uncovered),
                len(aspect_coverage.aspects),
            )

            uncovered_core = [a for a in uncovered if a.importance >= 0.8]

            if current_hop < self.min_hops:
                return True, (
                    f"Below minimum hops ({self.min_hops}), continuing to cover {len(uncovered)}"
                    " aspects"
                )

            if coverage_pct >= self.coverage_goal and not uncovered_core:
                return False, (
                    f"Coverage goal reached ({coverage_pct:.1%} >= {self.coverage_goal:.0%})"
                )

            if not uncovered_core and weighted_coverage >= self.coverage_goal:
                return False, (
                    f"All core aspects covered (weighted coverage: {weighted_coverage:.1%})"
                )

            if uncovered_core:
                uncovered_names = [a.aspect for a in uncovered_core[:2]]
                return True, f"Core aspects still uncovered: {uncovered_names}"

            if weighted_coverage < self.coverage_goal:
                return True, (
                    f"Weighted coverage below goal ({weighted_coverage:.1%} < "
                    f"{self.coverage_goal:.0%}), continuing"
                )

            return False, (
                f"Sufficient aspect coverage achieved ({weighted_coverage:.1%})"
            )
        
        # Fallback to traditional document-quality based stopping
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
    
    def extract_aspects(self, question: str, llm_client=None) -> AspectCoverage:
        """
        Extract aspects/facets from a research question.
        
        Uses LLM if available, falls back to heuristics.
        
        Args:
            question: The research question
            llm_client: Optional LLM client for aspect extraction
            
        Returns:
            AspectCoverage object with identified aspects
        """
        if llm_client is not None and hasattr(llm_client, 'generate_text'):
            try:
                aspects = self._extract_aspects_llm(question, llm_client)
                if aspects:
                    logger.info(f"Extracted {len(aspects)} aspects using LLM")
                    return AspectCoverage(aspects=aspects)
            except Exception as e:
                logger.warning(f"LLM aspect extraction failed: {e}, falling back to heuristics")
        
        # Fallback to heuristic extraction
        aspects = self._extract_aspects_heuristic(question)
        logger.info(f"Extracted {len(aspects)} aspects using heuristics")
        return AspectCoverage(aspects=aspects)
    
    def _extract_aspects_llm(self, question: str, llm_client) -> List[QueryAspect]:
        """
        Extract aspects using LLM.
        
        Args:
            question: The research question
            llm_client: LLM client for generation
            
        Returns:
            List of QueryAspect objects
        """
        system_prompt = """You are a research assistant that breaks down complex questions into their key aspects or facets.
        Identify distinct aspects that need to be addressed to fully answer the question.
        For each aspect, provide:
        1. The aspect name (brief description)
        2. The type (definition, comparison, process, application, evaluation, example, etc.)
        3. Importance (core or optional)
        4. Keywords related to this aspect
        
        Return your response in this format (one aspect per line):
        ASPECT: <name> | TYPE: <type> | IMPORTANCE: <core/optional> | KEYWORDS: <keyword1, keyword2, ...>
        """
        
        prompt = f"Question: {question}\n\nIdentify the key aspects that need to be covered:"
        
        response = llm_client.generate_text(prompt, system_prompt, max_tokens=600)
        
        # Parse the response
        aspects = []
        for line in response.strip().split('\n'):
            if not line.strip() or 'ASPECT:' not in line:
                continue
            
            try:
                # Parse the structured response
                parts = line.split('|')
                aspect_name = ''
                aspect_type = 'general'
                importance = 0.8
                keywords = []
                
                for part in parts:
                    part = part.strip()
                    if part.startswith('ASPECT:'):
                        aspect_name = part.replace('ASPECT:', '').strip()
                    elif part.startswith('TYPE:'):
                        aspect_type = part.replace('TYPE:', '').strip().lower()
                    elif part.startswith('IMPORTANCE:'):
                        imp_str = part.replace('IMPORTANCE:', '').strip().lower()
                        importance = 1.0 if 'core' in imp_str else 0.6
                    elif part.startswith('KEYWORDS:'):
                        kw_str = part.replace('KEYWORDS:', '').strip()
                        keywords = [k.strip() for k in kw_str.split(',') if k.strip()]
                
                if aspect_name:
                    aspects.append(QueryAspect(
                        aspect=aspect_name,
                        aspect_type=aspect_type,
                        importance=importance,
                        keywords=keywords
                    ))
            except Exception as e:
                logger.debug(f"Failed to parse aspect line: {line} - {e}")
                continue
        
        return aspects
    
    def _extract_aspects_heuristic(self, question: str) -> List[QueryAspect]:
        """
        Extract aspects using heuristic rules.
        
        Args:
            question: The research question
            
        Returns:
            List of QueryAspect objects
        """
        question_lower = question.lower()
        aspects = []
        
        # Check for comparison pattern
        comparison_patterns = [
            (r'([\w\s-]+)\s+(?:vs\.?|versus|compared to|vs|difference between|compare)\s+([\w\s-]+)', 'comparison'),
            (r'compare\s+([\w\s-]+)\s+and\s+([\w\s-]+)', 'comparison'),
            (r'difference\s+between\s+([\w\s-]+)\s+and\s+([\w\s-]+)', 'comparison'),
        ]
        
        for pattern, aspect_type in comparison_patterns:
            match = re.search(pattern, question_lower)
            if match:
                # Extract the two entities being compared
                entity1 = match.group(1).strip()
                entity2 = match.group(2).strip()
                
                aspects.append(QueryAspect(
                    aspect=f"Definition/explanation of {entity1}",
                    aspect_type='definition',
                    importance=1.0,
                    keywords=[entity1]
                ))
                
                aspects.append(QueryAspect(
                    aspect=f"Definition/explanation of {entity2}",
                    aspect_type='definition',
                    importance=1.0,
                    keywords=[entity2]
                ))
                
                aspects.append(QueryAspect(
                    aspect=f"Comparison between {entity1} and {entity2}",
                    aspect_type='comparison',
                    importance=1.0,
                    keywords=[entity1, entity2, 'difference', 'comparison']
                ))
                
                logger.debug(f"Detected comparison: {entity1} vs {entity2}")
        
        # If aspects already identified from comparison, return them
        if aspects:
            return aspects
        
        # Otherwise, extract aspects based on question type
        key_terms = self._extract_key_terms(question_lower)
        main_topic = ' '.join(key_terms[:3]) if len(key_terms) >= 3 else ' '.join(key_terms)
        
        # Check what type of question this is and create relevant aspects
        if re.search(r'\bwhat\s+is\b|\bwhat\s+are\b|\bdefine\b', question_lower):
            aspects.append(QueryAspect(
                aspect=f"Definition of {main_topic}",
                aspect_type='definition',
                importance=1.0,
                keywords=key_terms
            ))
        
        if re.search(r'\bhow\b', question_lower):
            aspects.append(QueryAspect(
                aspect=f"Process/mechanism of {main_topic}",
                aspect_type='process',
                importance=1.0,
                keywords=key_terms + ['process', 'mechanism', 'how']
            ))
        
        if re.search(r'\bwhy\b', question_lower):
            aspects.append(QueryAspect(
                aspect=f"Reasons/causes related to {main_topic}",
                aspect_type='causal',
                importance=1.0,
                keywords=key_terms + ['reason', 'cause', 'why']
            ))
        
        if re.search(r'\badvantage|benefit|pro\b', question_lower):
            aspects.append(QueryAspect(
                aspect=f"Advantages of {main_topic}",
                aspect_type='evaluation',
                importance=0.8,
                keywords=key_terms + ['advantage', 'benefit', 'pro']
            ))
        
        if re.search(r'\bdisadvantage|drawback|con\b', question_lower):
            aspects.append(QueryAspect(
                aspect=f"Disadvantages of {main_topic}",
                aspect_type='evaluation',
                importance=0.8,
                keywords=key_terms + ['disadvantage', 'drawback', 'con']
            ))
        
        if re.search(r'\bapplication|use|example\b', question_lower):
            aspects.append(QueryAspect(
                aspect=f"Applications/examples of {main_topic}",
                aspect_type='application',
                importance=0.7,
                keywords=key_terms + ['application', 'use', 'example']
            ))
        
        # If no specific aspects identified, create a general one
        if not aspects:
            aspects.append(QueryAspect(
                aspect=f"General information about {main_topic}",
                aspect_type='general',
                importance=1.0,
                keywords=key_terms
            ))
        
        return aspects
    
    def update_aspect_coverage(
        self,
        aspect_coverage: AspectCoverage,
        documents: List[Dict[str, Any]],
        current_hop: int,
        embedder: Optional[Any] = None,
    ) -> None:
        """
        Update aspect coverage based on retrieved documents.
        
        Args:
            aspect_coverage: AspectCoverage object to update
            documents: Retrieved documents
            current_hop: Current hop number
        """
        for aspect in aspect_coverage.aspects:
            keyword_score = self._calculate_keyword_overlap_score(aspect, documents)

            similarity_score = 0.0
            if embedder is not None:
                similarity_score = self._calculate_embedding_similarity(
                    aspect, documents, embedder
                )

            combined_score = max(keyword_score, similarity_score)

            current_score = aspect_coverage.coverage_scores.get(aspect.aspect, 0.0)
            new_score = max(current_score, combined_score)
            aspect_coverage.coverage_scores[aspect.aspect] = new_score

            if (
                new_score >= self.coverage_similarity_threshold
                and aspect.aspect not in aspect_coverage.covered_by_hop
            ):
                aspect_coverage.covered_by_hop[aspect.aspect] = current_hop
                logger.info(
                    "Aspect '%s' covered at hop %s (score: %.2f)",
                    aspect.aspect,
                    current_hop,
                    new_score,
                )

    def generate_subqueries_for_aspects(
        self,
        main_question: str,
        uncovered_aspects: List[QueryAspect],
        llm_client=None,
        max_subqueries: int = 3,
        past_subqueries: Optional[List[str]] = None,
        coverage_scores: Optional[Dict[str, float]] = None,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None,
        uncovered_aspect_names: Optional[List[str]] = None,
    ) -> List[Tuple[str, str]]:
        """
        Generate targeted subqueries for uncovered aspects.
        
        Args:
            main_question: The original research question
            uncovered_aspects: List of aspects that need coverage
            llm_client: Optional LLM client for natural subquery generation
            max_subqueries: Maximum number of subqueries to generate
            
        Returns:
            List of tuples (subquery, aspect_name) mapping subqueries to aspects
        """
        if not uncovered_aspects:
            return []
        
        # Sort by importance (core aspects first)
        sorted_aspects = sorted(uncovered_aspects, key=lambda a: a.importance, reverse=True)
        
        # Limit to max_subqueries
        aspects_to_target = sorted_aspects[:max_subqueries]
        
        subquery_mapping = []

        if coverage_scores is None:
            coverage_scores = {}

        if past_subqueries is None:
            past_subqueries = []

        if retrieved_docs is None:
            retrieved_docs = []

        if uncovered_aspect_names is None:
            uncovered_aspect_names = [aspect.aspect for aspect in aspects_to_target]

        if llm_client is not None and hasattr(llm_client, 'generate_text'):
            try:
                llm_subqueries = self._generate_aspect_subqueries_llm(
                    main_question,
                    aspects_to_target,
                    llm_client,
                    past_subqueries=past_subqueries,
                    coverage_scores=coverage_scores,
                    retrieved_docs=retrieved_docs,
                    uncovered_aspect_names=uncovered_aspect_names,
                )
                if llm_subqueries:
                    logger.info(
                        "Generated %d aspect-guided subqueries using LLM",
                        len(llm_subqueries),
                    )
                    unique_llm_subqueries = self._filter_duplicate_subqueries(
                        [sq for sq, _ in llm_subqueries], past_subqueries
                    )
                    filtered_results = [
                        (subquery, aspect)
                        for subquery, aspect in llm_subqueries
                        if subquery in unique_llm_subqueries
                    ]

                    if filtered_results:
                        return filtered_results
            except Exception as exc:
                logger.warning(
                    "LLM subquery generation failed: %s, falling back to templates",
                    exc,
                )

        # Fallback to template-based generation with phrasing variations
        for aspect in aspects_to_target:
            template_subquery = self._aspect_to_subquery_template(aspect, main_question)
            varied_subquery = self._apply_phrasing_variation(template_subquery)
            subquery_mapping.append((varied_subquery, aspect.aspect))

        logger.info(
            "Generated %d aspect-guided subqueries using templates",
            len(subquery_mapping),
        )
        filtered_templates = self._filter_duplicate_subqueries(
            [sq for sq, _ in subquery_mapping], past_subqueries
        )
        return [pair for pair in subquery_mapping if pair[0] in filtered_templates]

    def _generate_aspect_subqueries_llm(
        self,
        main_question: str,
        aspects: List[QueryAspect],
        llm_client,
        past_subqueries: Optional[List[str]] = None,
        coverage_scores: Optional[Dict[str, float]] = None,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None,
        uncovered_aspect_names: Optional[List[str]] = None,
    ) -> List[Tuple[str, str]]:
        """
        Use LLM to generate natural subqueries for uncovered aspects.
        
        Args:
            main_question: Original question
            aspects: Aspects to target
            llm_client: LLM client
            
        Returns:
            List of (subquery, aspect_name) tuples
        """
        if past_subqueries is None:
            past_subqueries = []

        if coverage_scores is None:
            coverage_scores = {}

        if retrieved_docs is None:
            retrieved_docs = []

        if uncovered_aspect_names is None:
            uncovered_aspect_names = [aspect.aspect for aspect in aspects]

        coverage_recap = ", ".join(
            f"{name}: {coverage_scores.get(name, 0.0):.2f}" for name in uncovered_aspect_names
        ) or "N/A"

        retrieved_titles = [
            f"- {doc.get('title', 'Unknown')}" for doc in retrieved_docs[:5]
        ]
        retrieved_summary = "\n".join(retrieved_titles) if retrieved_titles else "(no documents yet)"

        phrasing_guidance = next(self._phrasing_cycle)

        system_prompt = textwrap.dedent(
            """
            You are an expert research planner coordinating iterative, aspect-guided discovery.
            Generate new subqueries that explore uncovered aspects using varied phrasing and angle.
            Avoid repeating concepts that were already explored.
            """
        ).strip()

        aspect_table = "\n".join(
            [
                f"- Aspect: {aspect.aspect} | Type: {aspect.aspect_type} | Importance: {'CORE' if aspect.importance >= 0.8 else 'optional'}"
                for aspect in aspects
            ]
        )

        prompt = textwrap.dedent(
            f"""
            Given the uncovered aspects: {', '.join(uncovered_aspect_names)}, and these past subqueries: {self._inline_join(past_subqueries)}, generate 1–3 new subqueries that cover different conceptual angles or missing perspectives.
            Avoid repeating phrasing or concepts already seen.
            Each subquery should target a distinct aspect of the topic.

            Context:
            Main question: {main_question}
            Aspect focus:
            {aspect_table}

            Past attempts:
            {self._format_for_prompt(past_subqueries)}

            Recently retrieved documents:
            {retrieved_summary}

            Coverage snapshot: {coverage_recap}

            Guidance: produce 1-3 fresh subqueries, each targeting a distinct uncovered aspect and using a {phrasing_guidance}.
            Respond with lines in the format:
            SUBQUERY: <subquery text> | ASPECT: <matching aspect name>
            """
        ).strip()

        response = llm_client.generate_text(prompt, system_prompt, max_tokens=500)

        subquery_mapping = []
        for line in response.strip().split('\n'):
            if 'SUBQUERY:' not in line:
                continue

            try:
                parts = line.split('|')
                subquery = parts[0].replace('SUBQUERY:', '').strip()
                aspect_name = parts[1].replace('ASPECT:', '').strip() if len(parts) > 1 else ''

                if subquery:
                    matched_aspect = self._match_aspect_name(aspect_name, aspects)
                    subquery_mapping.append((subquery, matched_aspect))
            except Exception as exc:
                logger.debug("Failed to parse subquery line: %s - %s", line, exc)

        return self._enforce_semantic_diversity(subquery_mapping)

    def _format_for_prompt(self, items: Iterable[str], limit: int = 6) -> str:
        if not items:
            return "(none)"
        trimmed = [str(item).strip() for item in items if str(item).strip()]
        if not trimmed:
            return "(none)"
        if len(trimmed) > limit:
            trimmed = trimmed[-limit:]
        return "\n".join(f"- {entry}" for entry in trimmed)

    def _inline_join(self, items: Iterable[str], limit: int = 6) -> str:
        if not items:
            return "(none)"
        trimmed = [str(item).strip() for item in items if str(item).strip()]
        if not trimmed:
            return "(none)"
        if len(trimmed) > limit:
            trimmed = trimmed[-limit:]
        return '; '.join(trimmed)

    def _filter_duplicate_subqueries(
        self, candidates: List[str], past_subqueries: List[str]
    ) -> List[str]:
        history = [self._normalize_subquery_text(sq) for sq in past_subqueries if isinstance(sq, str)]
        filtered: List[str] = []
        for candidate in candidates:
            if not candidate:
                continue
            normalized = self._normalize_subquery_text(candidate)
            if self._is_duplicate(normalized, history):
                continue
            filtered.append(candidate)
            history.append(normalized)
        return filtered

    def _is_duplicate(self, candidate_norm: str, history: List[str]) -> bool:
        candidate_words = self._tokenize(candidate_norm)
        for past in history:
            if not past:
                continue
            if candidate_norm == past:
                return True
            if candidate_norm.startswith(past) or past.startswith(candidate_norm):
                return True
            ratio = SequenceMatcher(None, candidate_norm, past).ratio()
            if ratio >= self.duplicate_similarity_threshold:
                return True
            past_words = self._tokenize(past)
            if past_words:
                overlap = len(candidate_words & past_words)
                union = len(candidate_words | past_words)
                if union > 0 and (overlap / union) >= 0.75:
                    return True
        return False

    def _match_aspect_name(self, aspect_candidate: str, aspects: List[QueryAspect]) -> str:
        if not aspects:
            return aspect_candidate or "General"
        if not aspect_candidate:
            return aspects[0].aspect
        best_match = aspects[0].aspect
        best_score = 0.0
        target = aspect_candidate.lower()
        for aspect in aspects:
            score = SequenceMatcher(None, target, aspect.aspect.lower()).ratio()
            if score > best_score:
                best_score = score
                best_match = aspect.aspect
        return best_match

    def _enforce_semantic_diversity(
        self, subquery_mapping: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        if not subquery_mapping:
            return []
        unique_pairs: List[Tuple[str, str]] = []
        seen: List[str] = []
        for subquery, aspect in subquery_mapping:
            if not subquery:
                continue
            normalized = self._normalize_subquery_text(subquery)
            if self._is_duplicate(normalized, seen):
                continue
            unique_pairs.append((subquery, aspect))
            seen.append(normalized)
        return unique_pairs

    def _apply_phrasing_variation(self, subquery: str) -> str:
        if not subquery:
            return subquery
        question = subquery.strip()
        if question.endswith('?'):
            question_root = question[:-1]
        else:
            question_root = question
        suffix_options = [
            " specifically",
            " in practical transformer deployments",
            " within modern architectures",
            " for real-world scenarios",
            " from a conceptual standpoint",
        ]
        suffix = random.choice(suffix_options)
        if suffix.strip() in question_root.lower():
            suffix = ''
        return f"{question_root}{suffix}?".strip()

    def _calculate_keyword_overlap_score(
        self, aspect: QueryAspect, documents: List[Dict[str, Any]]
    ) -> float:
        if not documents or not aspect.keywords:
            return 0.0
        best_score = 0.0
        keywords = [kw.lower() for kw in aspect.keywords]
        for doc in documents:
            text = self._extract_text_from_doc(doc)
            if not text:
                continue
            matches = sum(1 for kw in keywords if kw in text)
            if matches == 0:
                continue
            coverage_fraction = matches / max(len(keywords), 1)
            doc_score = float(doc.get('score', 0.5))
            best_score = max(best_score, min(coverage_fraction * doc_score, 1.0))
        return best_score

    def _extract_text_from_doc(self, doc: Dict[str, Any]) -> str:
        fields = [
            doc.get('summary', ''),
            doc.get('snippet', ''),
            doc.get('content', ''),
            doc.get('full_text', ''),
        ]
        combined = ' '.join(field for field in fields if field)
        return combined.lower()

    def _calculate_embedding_similarity(
        self, aspect: QueryAspect, documents: List[Dict[str, Any]], embedder: Any
    ) -> float:
        if not documents:
            return 0.0
        try:
            aspect_text = f"{aspect.aspect}. Keywords: {' '.join(aspect.keywords)}"
            aspect_vector = self._encode_text(embedder, aspect_text)
        except Exception as exc:
            logger.debug("Failed to encode aspect for similarity: %s", exc)
            return 0.0

        best_similarity = 0.0
        for doc in documents:
            doc_text = self._extract_text_from_doc(doc)
            if not doc_text:
                continue
            try:
                doc_vector = self._encode_text(embedder, doc_text)
            except Exception as exc:
                logger.debug("Failed to encode document for similarity: %s", exc)
                continue
            similarity = self._cosine_similarity(aspect_vector, doc_vector)
            best_similarity = max(best_similarity, similarity)
        return best_similarity

    def _encode_text(self, embedder: Any, text: str) -> np.ndarray:
        if not hasattr(embedder, 'encode'):
            raise ValueError("Embedder does not implement encode method")
        try:
            vector = embedder.encode(text, convert_to_numpy=True)
        except TypeError:
            vector = embedder.encode([text])[0]
        if isinstance(vector, list):
            vector = np.array(vector, dtype=float)
        vector = np.asarray(vector, dtype=float)
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def _cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        if vec_a.size == 0 or vec_b.size == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b))

    def _normalize_subquery_text(self, text: str) -> str:
        stripped = re.sub(r'[^a-z0-9\s]', ' ', text.lower())
        stripped = re.sub(r'\s+', ' ', stripped).strip()
        return stripped

    def _tokenize(self, text: str) -> Set[str]:
        if not text:
            return set()
        return set(word for word in text.split() if word)
    
    def _aspect_to_subquery_template(self, aspect: QueryAspect, main_question: str) -> str:
        """
        Convert an aspect to a subquery using templates.
        
        Args:
            aspect: The aspect to convert
            main_question: Original question for context
            
        Returns:
            Subquery string
        """
        aspect_text = aspect.aspect.lower()
        aspect_type = aspect.aspect_type
        
        # Extract main topic from aspect
        main_terms = [kw for kw in aspect.keywords if len(kw) > 3][:3]
        topic = " ".join(main_terms) if main_terms else aspect_text
        
        # Generate based on aspect type
        if aspect_type == 'definition':
            if 'definition' in aspect_text:
                # Extract what needs defining
                subject = aspect_text.replace('definition of', '').replace('definition', '').strip()
                return f"What is {subject}?"
            return f"What is the definition of {topic}?"
        
        elif aspect_type == 'comparison':
            return f"What are the differences and similarities in {topic}?"
        
        elif aspect_type == 'process':
            return f"How does {topic} work?"
        
        elif aspect_type == 'causal':
            return f"Why is {topic} important?"
        
        elif aspect_type == 'evaluation':
            if 'advantage' in aspect_text:
                return f"What are the advantages of {topic}?"
            elif 'disadvantage' in aspect_text:
                return f"What are the disadvantages of {topic}?"
            return f"What are the pros and cons of {topic}?"
        
        elif aspect_type == 'application':
            return f"What are the applications and uses of {topic}?"
        
        else:
            # Generic fallback
            return f"Tell me about {topic}"


