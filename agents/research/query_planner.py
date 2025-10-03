"""
Query Planner for Multi-hop Research Agent
Handles subquery generation and query planning with adaptive complexity analysis.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
import re
import logging
from dataclasses import dataclass, field
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
    
    def __init__(self, min_hops: int = 3, max_hops: int = 10, enable_aspect_coverage: bool = True):
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
        
        logger.info(f"QueryPlanner initialized with adaptive parameters: min_hops={min_hops}, max_hops={max_hops}, aspect_coverage={enable_aspect_coverage}")
    
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
            
            # Log current coverage status
            logger.info(f"Coverage status at hop {current_hop}:")
            logger.info(f"  Overall coverage: {coverage_pct:.1%}")
            logger.info(f"  Weighted coverage: {weighted_coverage:.1%}")
            logger.info(f"  Uncovered aspects: {len(uncovered)}/{len(aspect_coverage.aspects)}")
            
            # Check if all core aspects are covered
            uncovered_core = [a for a in uncovered if a.importance >= 0.8]
            
            # Always continue if below minimum hops (even with good coverage)
            if current_hop < self.min_hops:
                return True, f"Below minimum hops ({self.min_hops}), continuing to cover {len(uncovered)} aspects"
            
            # After min_hops, check coverage quality
            if not uncovered_core and weighted_coverage >= 0.7:
                # All core aspects covered
                return False, f"All core aspects covered (weighted coverage: {weighted_coverage:.1%})"
            elif uncovered_core:
                # Still have uncovered core aspects
                uncovered_names = [a.aspect for a in uncovered_core[:2]]  # Show first 2
                return True, f"Core aspects still uncovered: {uncovered_names}"
            elif weighted_coverage < 0.7:
                # Coverage not sufficient
                return True, f"Weighted coverage below threshold ({weighted_coverage:.1%} < 70%), continuing"
            else:
                # Good coverage, can stop
                return False, f"Sufficient aspect coverage achieved ({weighted_coverage:.1%})"
        
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
    
    def update_aspect_coverage(self, aspect_coverage: AspectCoverage, 
                              documents: List[Dict[str, Any]], 
                              current_hop: int) -> None:
        """
        Update aspect coverage based on retrieved documents.
        
        Args:
            aspect_coverage: AspectCoverage object to update
            documents: Retrieved documents
            current_hop: Current hop number
        """
        for aspect in aspect_coverage.aspects:
            # Calculate coverage for this aspect based on documents
            aspect_score = 0.0
            
            for doc in documents:
                doc_text = doc.get('content', '').lower()
                doc_title = doc.get('title', '').lower()
                combined_text = doc_text + ' ' + doc_title
                
                # Count keyword matches
                keyword_matches = sum(1 for kw in aspect.keywords if kw.lower() in combined_text)
                
                # Calculate relevance score for this document to this aspect
                if aspect.keywords:
                    doc_relevance = keyword_matches / len(aspect.keywords)
                    # Weight by document score if available
                    doc_score = doc.get('score', 0.5)
                    aspect_score = max(aspect_score, doc_relevance * doc_score)
            
            # Update coverage score (take max of current and new score)
            current_score = aspect_coverage.coverage_scores.get(aspect.aspect, 0.0)
            new_score = max(current_score, aspect_score)
            aspect_coverage.coverage_scores[aspect.aspect] = new_score
            
            # Track when aspect was first covered
            if new_score >= 0.5 and aspect.aspect not in aspect_coverage.covered_by_hop:
                aspect_coverage.covered_by_hop[aspect.aspect] = current_hop
                logger.info(f"Aspect '{aspect.aspect}' covered at hop {current_hop} (score: {new_score:.2f})")
    
    def generate_subqueries_for_aspects(self, main_question: str, 
                                       uncovered_aspects: List[QueryAspect],
                                       llm_client=None,
                                       max_subqueries: int = 3) -> List[Tuple[str, str]]:
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
        
        if llm_client is not None and hasattr(llm_client, 'generate_text'):
            # Use LLM to generate natural subqueries
            try:
                llm_subqueries = self._generate_aspect_subqueries_llm(
                    main_question, aspects_to_target, llm_client
                )
                if llm_subqueries:
                    logger.info(f"Generated {len(llm_subqueries)} aspect-guided subqueries using LLM")
                    return llm_subqueries
            except Exception as e:
                logger.warning(f"LLM subquery generation failed: {e}, falling back to templates")
        
        # Fallback to template-based generation
        for aspect in aspects_to_target:
            subquery = self._aspect_to_subquery_template(aspect, main_question)
            subquery_mapping.append((subquery, aspect.aspect))
        
        logger.info(f"Generated {len(subquery_mapping)} aspect-guided subqueries using templates")
        return subquery_mapping
    
    def _generate_aspect_subqueries_llm(self, main_question: str,
                                       aspects: List[QueryAspect],
                                       llm_client) -> List[Tuple[str, str]]:
        """
        Use LLM to generate natural subqueries for uncovered aspects.
        
        Args:
            main_question: Original question
            aspects: Aspects to target
            llm_client: LLM client
            
        Returns:
            List of (subquery, aspect_name) tuples
        """
        system_prompt = """You are a research assistant that generates focused subqueries.
        Given a main question and specific aspects that need to be covered, generate natural,
        well-formed subqueries that will help retrieve information about those aspects.
        
        Each subquery should be a complete, standalone question that targets the specific aspect.
        Return one subquery per line in this format:
        SUBQUERY: <subquery text> | ASPECT: <aspect name>"""
        
        aspect_list = "\n".join([
            f"- {aspect.aspect} (type: {aspect.aspect_type}, importance: {'CORE' if aspect.importance >= 0.8 else 'optional'})"
            for aspect in aspects
        ])
        
        prompt = f"""Main Question: {main_question}

Uncovered Aspects:
{aspect_list}

Generate focused subqueries to cover these aspects. Each subquery should target one specific aspect."""
        
        response = llm_client.generate_text(prompt, system_prompt, max_tokens=500)
        
        # Parse response
        subquery_mapping = []
        for line in response.strip().split('\n'):
            if 'SUBQUERY:' not in line:
                continue
            
            try:
                parts = line.split('|')
                subquery = parts[0].replace('SUBQUERY:', '').strip()
                aspect_name = parts[1].replace('ASPECT:', '').strip() if len(parts) > 1 else ""
                
                if subquery:
                    # Match to actual aspect
                    matched_aspect = next((a.aspect for a in aspects if aspect_name in a.aspect or a.aspect in aspect_name), aspects[0].aspect)
                    subquery_mapping.append((subquery, matched_aspect))
            except Exception as e:
                logger.debug(f"Failed to parse subquery line: {line} - {e}")
        
        return subquery_mapping
    
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
