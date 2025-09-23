"""
Query Planner for Multi-hop Research Agent
Handles subquery generation and query planning.
"""

from typing import List
import re
from ..shared.interfaces import IQueryPlanner


class QueryPlanner(IQueryPlanner):
    """
    Query planner that breaks down complex research questions into focused subqueries.
    """
    
    def __init__(self):
        """Initialize the query planner."""
        self.patterns = {
            r'what is|what are|define|definition': [
                "definition of {question}",
                "what is {question}",
                "explain {question}",
                "overview of {question}"
            ],
            r'how does|how do|how to|how can': [
                "how {question}",
                "mechanism of {question}",
                "process of {question}",
                "steps for {question}"
            ],
            r'why|reasons|benefits|advantages|disadvantages': [
                "why {question}",
                "benefits of {question}",
                "advantages of {question}",
                "reasons for {question}"
            ],
            r'compare|comparison|vs|versus|difference': [
                "comparison of {question}",
                "differences between {question}",
                "{question} comparison",
                "pros and cons of {question}"
            ],
            r'best|top|recommend|suggest|choose': [
                "best {question}",
                "top {question}",
                "recommended {question}",
                "popular {question}"
            ],
            r'example|examples|case study|use case': [
                "examples of {question}",
                "case studies of {question}",
                "use cases for {question}",
                "real world {question}"
            ],
            r'future|trends|development|evolution': [
                "future of {question}",
                "trends in {question}",
                "development of {question}",
                "evolution of {question}"
            ]
        }
    
    def generate_subqueries(self, question: str) -> List[str]:
        """
        Generate subqueries from a complex research question.
        
        Args:
            question: The main research question
            
        Returns:
            List of subqueries to investigate
        """
        # Clean the question
        question = question.strip().lower()
        
        # Find matching patterns
        subqueries = []
        
        for pattern, templates in self.patterns.items():
            if re.search(pattern, question):
                # Extract key terms from the question
                key_terms = self._extract_key_terms(question)
                
                for template in templates:
                    # Replace placeholder with actual terms
                    subquery = template.replace("{question}", " ".join(key_terms))
                    subqueries.append(subquery)
        
        # If no patterns match, create generic subqueries
        if not subqueries:
            key_terms = self._extract_key_terms(question)
            base_terms = " ".join(key_terms)
            
            subqueries = [
                f"what is {base_terms}",
                f"how does {base_terms} work",
                f"benefits of {base_terms}",
                f"examples of {base_terms}",
                f"applications of {base_terms}"
            ]
        
        # Remove duplicates and limit to reasonable number
        subqueries = list(dict.fromkeys(subqueries))[:5]
        
        return subqueries
    
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
    # Test the query planner
    planner = QueryPlanner()
    
    test_questions = [
        "What are the best machine learning algorithms for image recognition?",
        "How does artificial intelligence work in healthcare?",
        "Compare different programming languages for data science",
        "What are the future trends in quantum computing?",
        "Why is cybersecurity important for businesses?"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        print("-" * 50)
        subqueries = planner.generate_subqueries(question)
        for i, subquery in enumerate(subqueries, 1):
            print(f"{i}. {subquery}")
