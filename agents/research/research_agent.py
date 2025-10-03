"""
Research Agent for Multi-hop Research
Main research agent that orchestrates the research process.
"""

from typing import List, Dict, Any, Optional
import time
from ..shared.interfaces import IAgent, IRetriever, ILLMClient
from ..shared.models import ResearchResult, SubqueryResult
from ..shared.exceptions import AgentError
from .query_planner import QueryPlanner
from .document_retriever import DocumentRetriever
from .answer_synthesizer import AnswerSynthesizer


class ResearchAgent(IAgent):
    """
    Multi-hop research agent using Postgres + pgvector for document retrieval.
    """
    
    def __init__(self, retriever: IRetriever, llm_client: ILLMClient = None, 
                 use_llm: bool = True, ollama_model: str = "mistral:latest"):
        """
        Initialize research agent.
        
        Args:
            retriever: Document retriever instance
            llm_client: Optional LLM client for advanced processing
            use_llm: Whether to use LLM for processing
            ollama_model: Ollama model to use (if using Ollama)
        """
        self.retriever = retriever
        self.llm_client = llm_client
        self.use_llm = use_llm and llm_client is not None and llm_client.is_available()
        
        # Initialize components
        self.query_planner = QueryPlanner()
        self.answer_synthesizer = AnswerSynthesizer(llm_client)
        
        print(f"Research agent initialized (LLM: {'enabled' if self.use_llm else 'disabled'})")
    
    def process(self, question: str, per_sub_k: int = 3) -> ResearchResult:
        """
        Process a research question using multi-hop reasoning.
        
        Args:
            question: Research question
            per_sub_k: Number of documents to retrieve per subquery
            
        Returns:
            ResearchResult with answer, subqueries, and citations
        """
        start_time = time.time()
        
        try:
            print(f"\nResearching: {question}")
            
            # Generate subqueries
            if self.use_llm:
                subqueries = self.llm_client.generate_subqueries(question)
            else:
                subqueries = self.query_planner.generate_subqueries(question)
            
            print(f"Generated {len(subqueries)} subqueries")
            
            # Process each subquery
            subquery_results = []
            all_citations = []
            
            for i, subquery in enumerate(subqueries, 1):
                print(f"\nSubquery {i}: {subquery}")
                
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
                    'subquery_count': len(subqueries),
                    'successful_subqueries': len([r for r in subquery_results if r.success])
                }
            )
            
        except Exception as e:
            raise AgentError(f"Failed to process research question: {str(e)}")
    
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
