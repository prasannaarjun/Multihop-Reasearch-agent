"""
Research Agent for Multi-hop Research
Main research agent that orchestrates the research process with adaptive subquery generation.
"""

from typing import List, Dict, Any, Optional
import time
import logging
import threading
from ..shared.interfaces import IAgent, IRetriever, ILLMClient
from ..shared.models import ResearchResult, SubqueryResult
from ..shared.exceptions import AgentError
from .query_planner import QueryPlanner
from .document_retriever import DocumentRetriever
from .answer_synthesizer import AnswerSynthesizer

# Configure logging
logger = logging.getLogger(__name__)


class ResearchAgent(IAgent):
    """
    Multi-hop research agent using Postgres + pgvector for document retrieval.
    Now supports adaptive, iterative subquery generation based on question complexity.
    """
    
    def __init__(self, retriever: IRetriever, llm_client: ILLMClient = None, 
                 use_llm: bool = True, ollama_model: str = "mistral:latest",
                 adaptive_mode: bool = True, min_hops: int = 3, max_hops: int = 10):
        """
        Initialize research agent with adaptive capabilities.
        
        Args:
            retriever: Document retriever instance
            llm_client: Optional LLM client for advanced processing
            use_llm: Whether to use LLM for processing
            ollama_model: Ollama model to use (if using Ollama)
            adaptive_mode: Enable adaptive subquery generation (default: True)
            min_hops: Minimum number of subqueries (default: 3 for dev)
            max_hops: Maximum number of subqueries to prevent loops (default: 10 for dev)
        """
        self.retriever = retriever
        self.llm_client = llm_client
        self.use_llm = use_llm and llm_client is not None and llm_client.is_available()
        self.adaptive_mode = adaptive_mode
        
        # Initialize components with adaptive parameters
        self.query_planner = QueryPlanner(min_hops=min_hops, max_hops=max_hops)
        self.answer_synthesizer = AnswerSynthesizer(llm_client)
        
        logger.debug(
            "ResearchAgent initialized (llm_enabled=%s, adaptive_mode=%s)",
            self.use_llm,
            adaptive_mode,
        )
    
    def process(self, question: str, per_sub_k: int = 3, iterative: bool = None) -> ResearchResult:
        """
        Process a research question using adaptive multi-hop reasoning.
        
        Args:
            question: Research question
            per_sub_k: Number of documents to retrieve per subquery
            iterative: Use iterative retrieval (None = use adaptive_mode setting)
            
        Returns:
            ResearchResult with answer, subqueries, and citations
        """
        start_time = time.time()
        
        # Use instance setting if not specified
        if iterative is None:
            iterative = self.adaptive_mode
        
        try:
            logger.info("Starting research", extra={"question": question, "mode": "adaptive_iterative" if iterative else "standard_batch"})
            
            if iterative:
                # Use new iterative adaptive approach
                result = self._process_iterative(question, per_sub_k, start_time)
            else:
                # Use traditional batch approach for backward compatibility
                result = self._process_batch(question, per_sub_k, start_time)
            
            return result
            
        except Exception as e:
            raise AgentError(f"Failed to process research question: {str(e)}")
    
    def _process_batch(self, question: str, per_sub_k: int, start_time: float) -> ResearchResult:
        """
        Traditional batch processing: generate all subqueries upfront, then retrieve.
        Maintains backward compatibility with existing code.
        """
        # Analyze complexity first (for metadata)
        complexity = self.query_planner.analyze_complexity(question)
        logger.info(
            "Batch mode complexity analysis",
            extra={
                "complexity_score": complexity.complexity_score,
                "reasoning": complexity.reasoning,
                "estimated_hops": complexity.estimated_hops,
            },
        )

        subqueries: List[str]
        if self.use_llm and self.llm_client is not None:
            subqueries = self.llm_client.generate_subqueries(
                question, target_count=complexity.estimated_hops
            )
        else:
            logger.info(
                "Batch mode using planner fallback subquery generation", extra={"target_count": complexity.estimated_hops}
            )
            subqueries = self.query_planner.generate_subqueries(
                question, llm_client=None, adaptive=True
            )

        logger.info("Generated subqueries", extra={"subquery_count": len(subqueries)})
        
        # Process each subquery
        subquery_results = []
        all_citations = []
        
        for i, subquery in enumerate(subqueries, 1):
            logger.debug("Processing subquery", extra={"index": i, "total": len(subqueries), "subquery": subquery})
            
            # Retrieve documents for this subquery
            try:
                documents = self.retriever.retrieve(subquery, top_k=per_sub_k)
                
                if documents:
                    # Summarize results for this subquery
                    summary = self.answer_synthesizer.summarize_documents(documents, subquery)
                    
                    subquery_result = SubqueryResult(
                        subquery=subquery,
                        summary=summary,
                        documents=documents,
                        success=True
                    )
                    
                    # Collect citations
                    for doc in documents:
                        if doc not in all_citations:
                            all_citations.append(doc)
                    
                    logger.debug("Subquery retrieval succeeded", extra={"documents": len(documents)})
                else:
                    logger.debug("Subquery retrieval returned no documents")
                    subquery_result = SubqueryResult(
                        subquery=subquery,
                        summary="No relevant information found for this aspect.",
                        documents=[],
                        success=False,
                        error="No documents found"
                    )
                
                subquery_results.append(subquery_result)
                
            except Exception as e:
                logger.exception("Error processing subquery", extra={"subquery": subquery})
                subquery_result = SubqueryResult(
                    subquery=subquery,
                    summary="Error processing this aspect.",
                    documents=[],
                    success=False,
                    error=str(e)
                )
                subquery_results.append(subquery_result)
        
        # Generate final synthesis
        final_answer = self.answer_synthesizer.synthesize_answer(question, subquery_results)
        
        processing_time = time.time() - start_time
        
        return ResearchResult(
            question=question,
            answer=final_answer,
            subqueries=subquery_results,
            citations=all_citations,
            total_documents=len(all_citations),
            processing_time=processing_time,
            metadata={
                'use_llm': self.use_llm,
                'mode': 'batch',
                'adaptive': True,
                'complexity_score': complexity.complexity_score,
                'estimated_hops': complexity.estimated_hops,
                'actual_hops': len(subqueries),
                'subquery_count': len(subqueries),
                'successful_subqueries': len([r for r in subquery_results if r.success])
            }
        )
    
    def process_streaming(self, question: str, per_sub_k: int = 3, stop_flag: threading.Event = None) -> ResearchResult:
        """
        Process a research question with streaming support for the final answer.
        
        Args:
            question: Research question
            per_sub_k: Number of documents to retrieve per subquery
            stop_flag: Threading event to signal stop
            
        Returns:
            ResearchResult with streaming generator for the final answer
        """
        start_time = time.time()
        
        try:
            logger.info("Starting streaming research", extra={"question": question, "mode": "streaming"})
            
            # Use iterative processing (same as before)
            result = self._process_iterative(question, per_sub_k, start_time)
            
            # Create streaming generator for the final answer
            if stop_flag is None:
                stop_flag = threading.Event()
            
            # Generate streaming answer
            answer_generator = self.answer_synthesizer.synthesize_answer_streaming(
                question, result.subqueries, stop_flag
            )
            
            # Set streaming generator in result
            result.set_streaming_generator(answer_generator, stop_flag)
            
            return result
            
        except Exception as e:
            raise AgentError(f"Failed to process streaming research question: {str(e)}")
    
    def _process_iterative(self, question: str, per_sub_k: int, start_time: float) -> ResearchResult:
        """
        New iterative processing: generate subqueries one at a time based on results.
        Stops early when sufficient information is gathered or all aspects are covered.
        """
        # Analyze complexity
        complexity = self.query_planner.analyze_complexity(question)
        logger.info(
            "Iterative mode complexity analysis",
            extra={
                "complexity_score": complexity.complexity_score,
                "reasoning": complexity.reasoning,
                "estimated_hops": complexity.estimated_hops,
            },
        )
        
        # Extract aspects for coverage tracking
        aspect_coverage = None
        if self.query_planner.enable_aspect_coverage:
            aspect_coverage = self.query_planner.extract_aspects(question, self.llm_client)
            logger.info(
                "Identified aspects",
                extra={
                    "aspect_count": len(aspect_coverage.aspects),
                    "aspects": [
                        {
                            "aspect": aspect.aspect,
                            "type": aspect.aspect_type,
                            "importance": aspect.importance,
                        }
                        for aspect in aspect_coverage.aspects
                    ],
                },
            )
        
        subquery_results = []
        all_citations = []
        current_hop = 0
        max_hops = self.query_planner.max_hops
        past_subqueries: List[str] = []
        coverage_history: Dict[str, float] = {}
        
        # Aspect-guided iterative loop
        while current_hop < max_hops:
            current_hop += 1
            
            # Determine which aspects need coverage
            if aspect_coverage is not None:
                uncovered = aspect_coverage.get_uncovered_aspects(threshold=0.5)
                
                if uncovered:
                    # Generate subqueries targeting uncovered aspects
                    logger.debug(
                        "Targeting uncovered aspects",
                        extra={
                            "hop": current_hop,
                            "max_hops": max_hops,
                            "uncovered_count": len(uncovered),
                        },
                    )
                    
                    subquery_mappings = self.query_planner.generate_subqueries_for_aspects(
                        question,
                        uncovered,
                        self.llm_client if self.use_llm else None,
                        max_subqueries=1,
                        past_subqueries=past_subqueries,
                        coverage_scores=coverage_history,
                        retrieved_docs=all_citations[-5:],
                        uncovered_aspect_names=[aspect.aspect for aspect in uncovered],
                    )
                    
                    if not subquery_mappings:
                        logger.debug("No subqueries generated for uncovered aspects; stopping")
                        break

                    subquery, target_aspect = subquery_mappings[0]
                    past_subqueries.append(subquery)
                    logger.debug(
                        "Generated aspect-focused subquery",
                        extra={"target_aspect": target_aspect, "subquery": subquery},
                    )
                else:
                    # All aspects covered, optionally do one more exploratory query
                    logger.debug(
                        "All aspects covered; stopping iterative retrieval",
                        extra={"hop": current_hop, "max_hops": max_hops},
                    )
                    break
            else:
                # No aspect coverage tracking, generate generic subquery
                if self.use_llm and self.llm_client is not None:
                    candidate_subqueries = self.llm_client.generate_subqueries(question, target_count=1)
                else:
                    candidate_subqueries = self.query_planner.generate_subqueries(
                        question, llm_client=None, adaptive=True
                    )
                if not candidate_subqueries:
                    break
                subquery = candidate_subqueries[0]
                past_subqueries.append(subquery)
                target_aspect = "General"
                logger.debug(
                    "Generated generic subquery",
                    extra={"hop": current_hop, "max_hops": max_hops, "subquery": subquery},
                )
            
            # Retrieve documents for this subquery
            try:
                documents = self.retriever.retrieve(subquery, top_k=per_sub_k)
                
                if documents:
                    # Summarize results for this subquery
                    summary = self.answer_synthesizer.summarize_documents(documents, subquery)
                    
                    subquery_result = SubqueryResult(
                        subquery=subquery,
                        summary=summary,
                        documents=documents,
                        success=True
                    )
                    
                    # Collect citations
                    for doc in documents:
                        if doc not in all_citations:
                            all_citations.append(doc)
                    
                    logger.debug(
                        "Subquery retrieval succeeded",
                        extra={
                            "documents": len(documents),
                            "total_citations": len(all_citations),
                        },
                    )
                else:
                    logger.debug("Subquery retrieval returned no documents")
                    subquery_result = SubqueryResult(
                        subquery=subquery,
                        summary="No relevant information found for this aspect.",
                        documents=[],
                        success=False,
                        error="No documents found"
                    )
                
                subquery_results.append(subquery_result)
                
                # Update aspect coverage if enabled
                if aspect_coverage is not None:
                    self.query_planner.update_aspect_coverage(
                        aspect_coverage,
                        all_citations,
                        current_hop,
                        embedder=getattr(self.retriever, 'model', None),
                    )

                    coverage_history = dict(aspect_coverage.coverage_scores)
                    uncovered = aspect_coverage.get_uncovered_aspects()
                    coverage_pct = aspect_coverage.get_coverage_percentage()
                    logger.debug(
                        "Aspect coverage progress",
                        extra={
                            "coverage": coverage_pct,
                            "uncovered_count": len(uncovered),
                            "sample_uncovered": [a.aspect for a in uncovered[:2]],
                        },
                    )
                
                # Check if we should continue
                should_continue, reasoning = self.query_planner.should_continue_retrieval(
                    all_citations, current_hop, aspect_coverage=aspect_coverage
                )

                logger.debug(
                    "Continuation decision",
                    extra={
                        "should_continue": should_continue,
                        "reasoning": reasoning,
                        "current_hop": current_hop,
                    },
                )

                if not should_continue:
                    logger.debug(
                        "Stopping iterative retrieval early", extra={"hop": current_hop, "reason": reasoning}
                    )
                    break
                
            except Exception as e:
                logger.exception("Error processing subquery", extra={"subquery": subquery})
                subquery_result = SubqueryResult(
                    subquery=subquery,
                    summary="Error processing this aspect.",
                    documents=[],
                    success=False,
                    error=str(e)
                )
                subquery_results.append(subquery_result)
        
        # Generate final synthesis
        final_answer = self.answer_synthesizer.synthesize_answer(question, subquery_results)
        
        processing_time = time.time() - start_time
        
        # Build metadata
        metadata = {
            'use_llm': self.use_llm,
            'mode': 'iterative_aspect_guided',
            'adaptive': True,
            'complexity_score': complexity.complexity_score,
            'estimated_hops': complexity.estimated_hops,
            'actual_hops': current_hop,
            'subquery_count': len(subquery_results),
            'successful_subqueries': len([r for r in subquery_results if r.success]),
            'early_stop': current_hop < max_hops
        }
        
        # Add aspect coverage metadata if enabled
        if aspect_coverage is not None:
            metadata['aspect_coverage'] = {
                'enabled': True,
                'total_aspects': len(aspect_coverage.aspects),
                'coverage_percentage': aspect_coverage.get_coverage_percentage(),
                'weighted_coverage': aspect_coverage.get_weighted_coverage(),
                'uncovered_count': len(aspect_coverage.get_uncovered_aspects()),
                'aspects': [
                    {
                        'aspect': a.aspect,
                        'type': a.aspect_type,
                        'importance': a.importance,
                        'coverage_score': aspect_coverage.coverage_scores.get(a.aspect, 0.0),
                        'covered_at_hop': aspect_coverage.covered_by_hop.get(a.aspect)
                    }
                    for a in aspect_coverage.aspects
                ]
            }
        else:
            metadata['aspect_coverage'] = {'enabled': False}
        
        return ResearchResult(
            question=question,
            answer=final_answer,
            subqueries=subquery_results,
            citations=all_citations,
            total_documents=len(all_citations),
            processing_time=processing_time,
            metadata=metadata
        )
    
    def ask(self, question: str, per_sub_k: int = 3) -> Dict[str, Any]:
        """
        Ask a research question and get a multi-hop reasoned answer.
        Legacy method for backward compatibility.
        
        Args:
            question: Research question
            per_sub_k: Number of documents to retrieve per subquery
            
        Returns:
            Dictionary containing answer, subqueries, and citations
        """
        result = self.process(question, per_sub_k)
        
        # Convert to legacy format
        return {
            'question': result.question,
            'answer': result.answer,
            'subqueries': [
                {
                    'subquery': sq.subquery,
                    'summary': sq.summary,
                    'documents': sq.documents
                }
                for sq in result.subqueries
            ],
            'citations': result.citations,
            'total_documents': result.total_documents
        }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection."""
        if hasattr(self.retriever, 'get_collection_stats'):
            return self.retriever.get_collection_stats()
        else:
            return {"error": "Collection stats not available"}


if __name__ == "__main__":
    # Test the research agent
    from sentence_transformers import SentenceTransformer
    from auth.database import SessionLocal
    from ollama_client import OllamaClient
    
    print("Initializing research agent...")
    
    try:
        # Initialize database session
        db_session = SessionLocal()
        
        # Load embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create retriever (using user_id=1 for testing)
        retriever = DocumentRetriever(db_session, model, user_id=1)
        
        # Initialize LLM client (optional)
        llm_client = OllamaClient()
        
        # Create research agent
        agent = ResearchAgent(retriever, llm_client)
        
        # Test questions
        test_questions = [
            "What are the best machine learning algorithms for image recognition?",
            "How does artificial intelligence work in healthcare?",
            "What are the advantages and disadvantages of different programming languages?"
        ]
        
        for question in test_questions:
            print(f"\n{'='*80}")
            print(f"QUESTION: {question}")
            print('='*80)
            
            result = agent.process(question, per_sub_k=2)
            
            print(f"\nANSWER:")
            print(result.answer)
            
            print(f"\nCITATIONS ({len(result.citations)} documents):")
            for i, citation in enumerate(result.citations[:5], 1):  # Show top 5
                print(f"{i}. {citation['title']} (Score: {citation['score']:.3f})")
            
            print(f"\nProcessing time: {result.processing_time:.2f} seconds")
            print("\n" + "-"*80)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'db_session' in locals():
            db_session.close()
