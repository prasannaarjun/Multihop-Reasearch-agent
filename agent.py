from typing import List, Dict, Any
from retriever import Retriever
from planner import generate_subqueries
from ollama_client import OllamaClient
import re


class ResearchAgent:
    """
    Multi-hop research agent using Chroma for document retrieval.
    """
    
    def __init__(self, persist_directory: str = "chroma_db", use_ollama: bool = True, ollama_model: str = "mistral:latest"):
        """
        Initialize research agent.
        
        Args:
            persist_directory: Directory containing Chroma database
            use_ollama: Whether to use Ollama for text generation
            ollama_model: Ollama model to use
        """
        self.retriever = Retriever(persist_directory)
        self.use_ollama = use_ollama
        
        if use_ollama:
            self.ollama_client = OllamaClient(model_name=ollama_model)
            if not self.ollama_client.is_available():
                print("Warning: Ollama not available, falling back to rule-based processing")
                self.use_ollama = False
        else:
            self.ollama_client = None
            
        print(f"Research agent initialized (Ollama: {'enabled' if self.use_ollama else 'disabled'})")
    
    def ask(self, question: str, per_sub_k: int = 3) -> Dict[str, Any]:
        """
        Answer a research question using multi-hop reasoning.
        
        Args:
            question: Research question
            per_sub_k: Number of documents to retrieve per subquery
            
        Returns:
            Dictionary containing answer, subqueries, and citations
        """
        print(f"\nResearching: {question}")
        
        # Generate subqueries
        if self.use_ollama:
            subqueries = self.ollama_client.generate_subqueries(question)
        else:
            subqueries = generate_subqueries(question)
        print(f"Generated {len(subqueries)} subqueries")
        
        # Process each subquery
        subquery_results = []
        all_citations = []
        
        for i, subquery in enumerate(subqueries, 1):
            print(f"\nSubquery {i}: {subquery}")
            
            # Retrieve documents for this subquery
            results = self.retriever.retrieve(subquery, top_k=per_sub_k)
            
            if results:
                # Summarize results for this subquery
                if self.use_ollama:
                    summary = self.ollama_client.summarize_documents(results, subquery)
                else:
                    summary = self._summarize_results(results, subquery)
                
                subquery_results.append({
                    'subquery': subquery,
                    'summary': summary,
                    'documents': results
                })
                
                # Collect citations
                for doc in results:
                    if doc not in all_citations:
                        all_citations.append(doc)
                
                print(f"  Found {len(results)} relevant documents")
            else:
                print(f"  No relevant documents found")
                subquery_results.append({
                    'subquery': subquery,
                    'summary': "No relevant information found for this aspect.",
                    'documents': []
                })
        
        # Generate final synthesis
        if self.use_ollama:
            final_answer = self.ollama_client.synthesize_answer(question, subquery_results)
        else:
            final_answer = self._synthesize_answer(question, subquery_results)
        
        return {
            'question': question,
            'answer': final_answer,
            'subqueries': subquery_results,
            'citations': all_citations,
            'total_documents': len(all_citations)
        }
    
    def _summarize_results(self, results: List[Dict], subquery: str) -> str:
        """
        Create an extractive summary from retrieved documents.
        
        Args:
            results: List of retrieved documents
            subquery: The subquery being addressed
            
        Returns:
            Summary text
        """
        if not results:
            return "No relevant information found."
        
        # Extract key sentences from each document
        key_sentences = []
        
        for result in results:
            text = result.get('full_text', '')
            if text:
                # Split into sentences and pick the most relevant ones
                sentences = self._split_into_sentences(text)
                relevant_sentences = self._select_relevant_sentences(sentences, subquery)
                key_sentences.extend(relevant_sentences[:2])  # Top 2 sentences per doc
        
        # Remove duplicates and join
        unique_sentences = list(dict.fromkeys(key_sentences))
        summary = " ".join(unique_sentences[:3])  # Top 3 sentences total
        
        return summary if summary else "Relevant information found but could not be summarized."
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with more sophisticated NLP)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        return sentences
    
    def _select_relevant_sentences(self, sentences: List[str], query: str) -> List[str]:
        """
        Select the most relevant sentences for a query.
        
        Args:
            sentences: List of sentences
            query: Query text
            
        Returns:
            List of relevant sentences
        """
        if not sentences:
            return []
        
        query_words = set(query.lower().split())
        scored_sentences = []
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            # Simple scoring based on word overlap
            overlap = len(query_words.intersection(sentence_words))
            if overlap > 0:
                scored_sentences.append((overlap, sentence))
        
        # Sort by relevance score and return top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        return [sentence for _, sentence in scored_sentences[:2]]
    
    def _synthesize_answer(self, question: str, subquery_results: List[Dict]) -> str:
        """
        Synthesize final answer from subquery results.
        
        Args:
            question: Original question
            subquery_results: Results from each subquery
            
        Returns:
            Final synthesized answer
        """
        if not subquery_results:
            return "I couldn't find enough information to answer your question."
        
        # Collect all summaries
        summaries = [result['summary'] for result in subquery_results if result['summary']]
        
        if not summaries:
            return "I found some relevant documents but couldn't extract meaningful information."
        
        # Create synthesis
        synthesis_parts = [
            f"Based on my research, here's what I found about '{question}':\n\n"
        ]
        
        for i, result in enumerate(subquery_results, 1):
            if result['summary'] and result['summary'] != "No relevant information found for this aspect.":
                synthesis_parts.append(f"{i}. {result['summary']}\n")
        
        synthesis_parts.append("\nThis information is synthesized from multiple sources to provide a comprehensive answer.")
        
        return "".join(synthesis_parts)


if __name__ == "__main__":
    # Test the research agent
    print("Initializing research agent...")
    agent = ResearchAgent("chroma_db")
    
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
        
        result = agent.ask(question, per_sub_k=2)
        
        print(f"\nANSWER:")
        print(result['answer'])
        
        print(f"\nCITATIONS ({len(result['citations'])} documents):")
        for i, citation in enumerate(result['citations'][:5], 1):  # Show top 5
            print(f"{i}. {citation['title']} (Score: {citation['score']:.3f})")
        
        print("\n" + "-"*80)
