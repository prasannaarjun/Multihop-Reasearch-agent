import ollama
import logging
from typing import List, Dict, Any, Optional
import json
import re


class OllamaClient:
    """
    Client for interacting with local Ollama models.
    """
    
    def __init__(self, model_name: str = "mistral:latest", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama client.
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Base URL for Ollama API
        """
        self.model_name = model_name
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)
        
        # Test connection
        try:
            self._test_connection()
            logging.info(f"Ollama client initialized with model: {model_name}")
        except Exception as e:
            logging.warning(f"Could not connect to Ollama at {base_url}: {e}")
            logging.warning("Make sure Ollama is running and the model is available")
    
    def _test_connection(self):
        """Test connection to Ollama."""
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            if self.model_name not in available_models:
                logging.warning(f"Model '{self.model_name}' not found. Available models: {available_models}")
                if available_models:
                    self.model_name = available_models[0]
                    logging.info(f"Using model: {self.model_name}")
        except Exception as e:
            # Try a simple test generation instead
            try:
                response = self.client.chat(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Hello"}],
                    options={"num_predict": 10}
                )
                logging.info(f"Ollama connection successful with model: {self.model_name}")
            except Exception as e2:
                raise Exception(f"Failed to connect to Ollama: {e2}")
    
    def generate_text(self, prompt: str, system_prompt: str = None, max_tokens: int = 1000) -> str:
        """
        Generate text using Ollama model.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )
            
            return response['message']['content'].strip()
            
        except Exception as e:
            logging.error(f"Error generating text: {e}")
            return f"Error: Could not generate text - {e}"
    
    def generate_subqueries(self, question: str, target_count: int = 5) -> List[str]:
        """
        Generate subqueries for a research question using LLM.
        
        Args:
            question: Main research question
            target_count: Target number of subqueries to generate (default: 5)
            
        Returns:
            List of subqueries
        """
        system_prompt = f"""You are a research assistant that breaks down complex questions into focused subqueries. 
        Generate exactly {target_count} specific subqueries that would help answer the main question comprehensively.
        Each subquery should be a clear, focused question that can be answered by searching documents.
        The subqueries should cover different aspects of the main question and be complementary.
        Return only the subqueries, one per line, without numbering or bullet points."""
        
        prompt = f"Main question: {question}\n\nGenerate {target_count} focused subqueries:"
        
        response = self.generate_text(prompt, system_prompt, max_tokens=800)
        
        # Parse response into list
        subqueries = [line.strip() for line in response.split('\n') if line.strip()]
        
        # Clean up any numbering that might have been added
        cleaned_subqueries = []
        for sq in subqueries:
            # Remove leading numbers, bullets, dashes
            cleaned = re.sub(r'^[\d\.\)\-\*\•]+\s*', '', sq).strip()
            if cleaned and len(cleaned) > 5:  # Ensure it's a real question
                cleaned_subqueries.append(cleaned)
        
        # If LLM fails or returns too few, create fallback
        if len(cleaned_subqueries) < max(1, target_count // 2):
            logger.warning(f"LLM generated only {len(cleaned_subqueries)} subqueries, expected {target_count}. Using fallback.")
            # Simple fallback
            key_terms = ' '.join([word for word in question.split() if len(word) > 3])[:50]
            fallback = [
                question,
                f"What is {key_terms}?",
                f"How does {key_terms} work?",
                f"What are the applications of {key_terms}?",
                f"What are the benefits and challenges of {key_terms}?",
            ]
            cleaned_subqueries.extend(fallback[len(cleaned_subqueries):target_count])
        
        return cleaned_subqueries[:target_count]
    
    def summarize_documents(self, documents: List[Dict[str, Any]], subquery: str) -> str:
        """
        Summarize retrieved documents for a specific subquery using LLM.
        
        Args:
            documents: List of retrieved documents
            subquery: The subquery being addressed
            
        Returns:
            Summarized text
        """
        if not documents:
            return "No relevant information found for this aspect."
        
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
        
        return self.generate_text(prompt, system_prompt, max_tokens=800)
    
    def synthesize_answer(self, question: str, subquery_results: List[Dict[str, Any]]) -> str:
        """
        Synthesize final answer from subquery results using LLM.
        
        Args:
            question: Original research question
            subquery_results: Results from each subquery
            
        Returns:
            Final synthesized answer
        """
        # Prepare subquery summaries
        subquery_texts = []
        for i, result in enumerate(subquery_results, 1):
            if result.get('summary') and result['summary'] != "No relevant information found for this aspect.":
                subquery_texts.append(f"Research Area {i}: {result['subquery']}\n{result['summary']}")
        
        system_prompt = """You are a research assistant that synthesizes information from multiple sources.
        Create a comprehensive, well-structured answer that addresses the main question.
        Use information from all the research areas provided.
        Structure your answer clearly and provide a coherent narrative.
        Be thorough but concise."""
        
        prompt = f"""Main Question: {question}

Research Findings:
{chr(10).join(subquery_texts)}

Provide a comprehensive answer that synthesizes all the research findings:"""
        
        return self.generate_text(prompt, system_prompt, max_tokens=1500)
    
    def generate_report_intro(self, question: str) -> str:
        """
        Generate an introduction for the research report.
        
        Args:
            question: Research question
            
        Returns:
            Report introduction
        """
        system_prompt = """You are a research assistant writing a professional report introduction.
        Write a brief, engaging introduction that sets the context for the research question.
        Keep it concise and professional."""
        
        prompt = f"Write an introduction for a research report about: {question}"
        
        return self.generate_text(prompt, system_prompt, max_tokens=300)
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available and working.
        
        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            self._test_connection()
            return True
        except Exception:
            return False


