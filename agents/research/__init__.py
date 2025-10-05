"""
Research Agent Module
Contains core research functionality for multi-hop reasoning and document retrieval.
Now includes adaptive subquery generation with complexity analysis.
"""

from .research_agent import ResearchAgent
from .query_planner import QueryPlanner, QueryComplexity, ScoredSubquery
from .document_retriever import DocumentRetriever
from .answer_synthesizer import AnswerSynthesizer

__all__ = [
    'ResearchAgent',
    'QueryPlanner',
    'QueryComplexity',
    'ScoredSubquery',
    'DocumentRetriever',
    'AnswerSynthesizer'
]
