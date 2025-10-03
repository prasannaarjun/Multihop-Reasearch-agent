"""
Research Agent for Multi-hop Research
Main research agent that orchestrates the research process with adaptive subquery generation.
"""

from typing import List, Dict, Any, Optional
import time
import logging
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
        
        print(f"Research agent initialized (LLM: {'enabled' if self.use_llm else 'disabled'}, Adaptive: {adaptive_mode})")
    
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
            print(f"\nResearching: {question}")
            print(f"Mode: {'Adaptive Iterative' if iterative else 'Standard Batch'}")
            
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
        print(f"Complexity: {complexity.complexity_score:.2f} - {complexity.reasoning}")
        print(f"Target subqueries: {complexity.estimated_hops}")
        
        # Generate subqueries using LLM (always required now)
        if not self.use_llm or self.llm_client is None:
            raise AgentError("LLM client is required for subquery generation. Please provide a valid LLM client.")
        
        subqueries = self.llm_client.generate_subqueries(question, target_count=complexity.estimated_hops)
        print(f"Generated {len(subqueries)} subqueries")
        
        # Process each subquery
        subquery_results = []
        all_citations = []
        
        for i, subquery in enumerate(subqueries, 1):
            print(f"\nSubquery {i}/{len(subqueries)}: {subquery}")
            
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
                    
                    print(f"  Found {len(documents)} relevant documents")
                else:
                    print(f"  No relevant documents found")
                    subquery_result = SubqueryResult(
                        subquery=subquery,
                        summary="No relevant information found for this aspect.",
                        documents=[],
                        success=False,
                        error="No documents found"
                    )
                
                subquery_results.append(subquery_result)
                
            except Exception as e:
                print(f"  Error processing subquery: {e}")
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
    
    def _process_iterative(self, question: str, per_sub_k: int, start_time: float) -> ResearchResult:
        """
        New iterative processing: generate subqueries one at a time based on results.
        Stops early when sufficient information is gathered.
        """
        # Analyze complexity
        complexity = self.query_planner.analyze_complexity(question)
        print(f"Complexity: {complexity.complexity_score:.2f} - {complexity.reasoning}")
        print(f"Estimated hops needed: {complexity.estimated_hops}")
        
        subquery_results = []
        all_citations = []
        current_hop = 0
        max_hops = self.query_planner.max_hops
        
        # Generate initial set of candidate subqueries using LLM
        if not self.use_llm or self.llm_client is None:
            raise AgentError("LLM client is required for subquery generation. Please provide a valid LLM client.")
        
        candidate_subqueries = self.llm_client.generate_subqueries(question, target_count=complexity.estimated_hops)
        
        # Score and prioritize subqueries
        scored_subqueries = self.query_planner.score_subqueries(question, candidate_subqueries)
        print(f"Generated {len(scored_subqueries)} candidate subqueries (prioritized)")
        
        # Process subqueries iteratively
        for scored in scored_subqueries:
            current_hop += 1
            subquery = scored.subquery
            
            print(f"\n[Hop {current_hop}/{max_hops}] Subquery: {subquery}")
            print(f"  Relevance: {scored.relevance_score:.2f} - {scored.reasoning}")
            
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
                    
                    print(f"  Found {len(documents)} relevant documents (total: {len(all_citations)})")
                else:
                    print(f"  No relevant documents found")
                    subquery_result = SubqueryResult(
                        subquery=subquery,
                        summary="No relevant information found for this aspect.",
                        documents=[],
                        success=False,
                        error="No documents found"
                    )
                
                subquery_results.append(subquery_result)
                
                # Check if we should continue
                should_continue, reasoning = self.query_planner.should_continue_retrieval(
                    all_citations, current_hop
                )
                
                print(f"  Decision: {'Continue' if should_continue else 'Stop'} - {reasoning}")
                
                if not should_continue:
                    print(f"\n✓ Stopping early after {current_hop} hops: {reasoning}")
                    break
                
            except Exception as e:
                print(f"  Error processing subquery: {e}")
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
                'mode': 'iterative',
                'adaptive': True,
                'complexity_score': complexity.complexity_score,
                'estimated_hops': complexity.estimated_hops,
                'actual_hops': current_hop,
                'candidate_count': len(candidate_subqueries),
                'subquery_count': len(subquery_results),
                'successful_subqueries': len([r for r in subquery_results if r.success]),
                'early_stop': current_hop < len(scored_subqueries)
            }
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
