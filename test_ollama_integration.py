#!/usr/bin/env python3
"""
Test script to demonstrate the Ollama integration.
This script shows how the research agent works with and without Ollama.
"""

from agent import ResearchAgent
import os


def test_without_ollama():
    """Test the research agent without Ollama (rule-based)."""
    print("=" * 60)
    print("TESTING WITHOUT OLLAMA (Rule-based processing)")
    print("=" * 60)
    
    # Initialize agent without Ollama
    agent = ResearchAgent(persist_directory="chroma_db", use_ollama=False)
    
    # Test question
    question = "What are the advantages of different programming languages for data science?"
    
    print(f"Question: {question}")
    print("\nProcessing...")
    
    result = agent.ask(question, per_sub_k=2)
    
    print(f"\nAnswer:")
    print("-" * 40)
    print(result['answer'])
    
    print(f"\nSubqueries generated: {len(result['subqueries'])}")
    for i, sq in enumerate(result['subqueries'], 1):
        print(f"{i}. {sq['subquery']}")
    
    print(f"\nTotal documents consulted: {result['total_documents']}")
    print("=" * 60)


def test_with_ollama():
    """Test the research agent with Ollama (if available)."""
    print("=" * 60)
    print("TESTING WITH OLLAMA (LLM-powered processing)")
    print("=" * 60)
    
    # Initialize agent with Ollama
    agent = ResearchAgent(persist_directory="chroma_db", use_ollama=True, ollama_model="mistral:latest")
    
    if not agent.use_ollama:
        print("Ollama not available, skipping LLM test")
        return
    
    # Test question
    question = "What are the advantages of different programming languages for data science?"
    
    print(f"Question: {question}")
    print("\nProcessing with Ollama...")
    
    result = agent.ask(question, per_sub_k=2)
    
    print(f"\nAnswer:")
    print("-" * 40)
    print(result['answer'])
    
    print(f"\nSubqueries generated: {len(result['subqueries'])}")
    for i, sq in enumerate(result['subqueries'], 1):
        print(f"{i}. {sq['subquery']}")
    
    print(f"\nTotal documents consulted: {result['total_documents']}")
    print("=" * 60)


def main():
    """Main test function."""
    print("🧪 Testing Multi-hop Research Agent with Ollama Integration")
    print("This test demonstrates the difference between rule-based and LLM-powered processing")
    
    # Test without Ollama first
    test_without_ollama()
    
    # Test with Ollama (if available)
    test_with_ollama()
    
    print("\n📋 Summary:")
    print("- Without Ollama: Uses rule-based subquery generation and simple text extraction")
    print("- With Ollama: Uses LLM for intelligent subquery generation and text synthesis")
    print("- Both approaches use Chroma DB for semantic document retrieval")
    
    print("\n🚀 To use Ollama:")
    print("1. Install Ollama from https://ollama.ai/download")
    print("2. Start Ollama service: ollama serve")
    print("3. Pull a model: ollama pull llama3.2")
    print("4. Restart the research agent")


if __name__ == "__main__":
    main()
