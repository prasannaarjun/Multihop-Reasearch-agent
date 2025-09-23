"""
Answer Synthesizer for Multi-hop Research Agent
Handles answer synthesis from subquery results.
"""

from typing import List, Dict, Any
import re
from ..shared.interfaces import IAnswerSynthesizer, ILLMClient
from ..shared.models import SubqueryResult


class AnswerSynthesizer(IAnswerSynthesizer):
    """
    Answer synthesizer that combines subquery results into a final answer.
    """
    
    def __init__(self, llm_client: ILLMClient = None):
        """
        Initialize answer synthesizer.
        
        Args:
            llm_client: Optional LLM client for advanced synthesis
        """
        self.llm_client = llm_client
        self.use_llm = llm_client is not None and llm_client.is_available()
    
    def synthesize_answer(self, question: str, subquery_results: List[Dict[str, Any]]) -> str:
        """
        Synthesize final answer from subquery results.
        
        Args:
            question: Original research question
            subquery_results: Results from each subquery
            
        Returns:
            Final synthesized answer
        """
        if self.use_llm:
            return self._synthesize_with_llm(question, subquery_results)
        else:
            return self._synthesize_rule_based(question, subquery_results)
    
    def _synthesize_with_llm(self, question: str, subquery_results: List[Dict[str, Any]]) -> str:
        """Synthesize answer using LLM."""
        # Prepare subquery summaries
        subquery_texts = []
        for i, result in enumerate(subquery_results, 1):
            if hasattr(result, 'summary') and result.summary and result.summary != "No relevant information found for this aspect.":
                subquery_texts.append(f"Research Area {i}: {result.subquery}\n{result.summary}")
        
        # Check if we have any successful research findings
        if not subquery_texts:
            return "I apologize, but I encountered errors while researching your question and couldn't retrieve relevant information. Please try rephrasing your question or check if the knowledge base is accessible."
        
        system_prompt = """You are a research assistant that synthesizes information from multiple sources.
        Create a comprehensive, well-structured answer that addresses the main question.
        Use information from all the research areas provided.
        Structure your answer clearly and provide a coherent narrative.
        Be thorough but concise."""
        
        prompt = f"""Main Question: {question}

Research Findings:
{chr(10).join(subquery_texts)}

Provide a comprehensive answer that synthesizes all the research findings:"""
        
        return self.llm_client.generate_text(prompt, system_prompt, max_tokens=1500)
    
    def _synthesize_rule_based(self, question: str, subquery_results: List[Dict[str, Any]]) -> str:
        """Synthesize answer using rule-based approach."""
        if not subquery_results:
            return "I couldn't find enough information to answer your question."
        
        # Collect all summaries
        summaries = [result.summary for result in subquery_results if hasattr(result, 'summary') and result.summary]
        
        if not summaries:
            return "I found some relevant documents but couldn't extract meaningful information."
        
        # Create synthesis
        synthesis_parts = [
            f"Based on my research, here's what I found about '{question}':\n\n"
        ]
        
        for i, result in enumerate(subquery_results, 1):
            if hasattr(result, 'summary') and result.summary and result.summary != "No relevant information found for this aspect.":
                synthesis_parts.append(f"{i}. {result.summary}\n")
        
        synthesis_parts.append("\nThis information is synthesized from multiple sources to provide a comprehensive answer.")
        
        return "".join(synthesis_parts)
    
    def summarize_documents(self, documents: List[Dict[str, Any]], subquery: str) -> str:
        """
        Summarize retrieved documents for a specific subquery.
        
        Args:
            documents: List of retrieved documents
            subquery: The subquery being addressed
            
        Returns:
            Summarized text
        """
        if not documents:
            return "No relevant information found for this aspect."
        
        if self.use_llm:
            return self._summarize_with_llm(documents, subquery)
        else:
            return self._summarize_rule_based(documents, subquery)
    
    def _summarize_with_llm(self, documents: List[Dict[str, Any]], subquery: str) -> str:
        """Summarize documents using LLM."""
        # Prepare document content
        doc_texts = []
        for i, doc in enumerate(documents, 1):
            doc_texts.append(f"Document {i}: {doc.get('title', 'Unknown')}\n{doc.get('full_text', '')[:1000]}...")
        
        system_prompt = """You are a research assistant that summarizes documents to answer specific questions.
        Focus on information that directly relates to the question being asked.
        Synthesize information from multiple documents into a coherent summary.
        Be concise but comprehensive. Use information from the documents provided."""
        
        prompt = f"""Question: {subquery}

Documents to summarize:
{chr(10).join(doc_texts)}

Provide a focused summary that answers the question:"""
        
        return self.llm_client.generate_text(prompt, system_prompt, max_tokens=800)
    
    def _summarize_rule_based(self, documents: List[Dict[str, Any]], subquery: str) -> str:
        """Summarize documents using rule-based approach."""
        # Extract key sentences from each document
        key_sentences = []
        
        for doc in documents:
            text = doc.get('full_text', '')
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
        """Split text into sentences."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        return sentences
    
    def _select_relevant_sentences(self, sentences: List[str], query: str) -> List[str]:
        """Select the most relevant sentences for a query."""
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


if __name__ == "__main__":
    # Test the answer synthesizer
    synthesizer = AnswerSynthesizer()
    
    # Test with sample data
    subquery_results = [
        {
            'subquery': 'What is machine learning?',
            'summary': 'Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.',
            'documents': []
        },
        {
            'subquery': 'How does machine learning work?',
            'summary': 'Machine learning works by using algorithms to identify patterns in data and make predictions or decisions based on those patterns.',
            'documents': []
        }
    ]
    
    question = "What is machine learning and how does it work?"
    answer = synthesizer.synthesize_answer(question, subquery_results)
    
    print(f"Question: {question}")
    print(f"Answer: {answer}")
