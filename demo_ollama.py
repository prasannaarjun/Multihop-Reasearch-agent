#!/usr/bin/env python3
"""
Demo script showing the Ollama integration capabilities.
This script demonstrates the enhanced text generation features.
"""

from agent import ResearchAgent
import json


def demo_ollama_features():
    """Demonstrate the enhanced features with Ollama integration."""
    print("🎯 Multi-hop Research Agent - Ollama Integration Demo")
    print("=" * 60)
    
    # Initialize agent with Ollama
    print("Initializing research agent with Ollama support...")
    agent = ResearchAgent(
        persist_directory="chroma_db",
        use_ollama=True,
        ollama_model="llama3.2"
    )
    
    if not agent.use_ollama:
        print("⚠️  Ollama not available - using rule-based fallback")
        print("To use Ollama features:")
        print("1. Install Ollama: https://ollama.ai/download")
        print("2. Start service: ollama serve")
        print("3. Pull model: ollama pull llama3.2")
        print()
    
    # Test questions
    test_questions = [
        "What are the best machine learning algorithms for image recognition?",
        "How does artificial intelligence work in healthcare applications?",
        "Compare different programming languages for data science projects"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"QUESTION {i}: {question}")
        print('='*60)
        
        # Ask the question
        result = agent.ask(question, per_sub_k=2)
        
        # Display results
        print(f"\n📝 ANSWER:")
        print("-" * 40)
        print(result['answer'])
        
        print(f"\n🔍 SUBQUERIES GENERATED ({len(result['subqueries'])}):")
        for j, sq in enumerate(result['subqueries'], 1):
            print(f"{j}. {sq['subquery']}")
        
        print(f"\n📚 SOURCES CONSULTED: {result['total_documents']} documents")
        
        # Show first few citations
        if result['citations']:
            print(f"\n📖 TOP SOURCES:")
            for j, citation in enumerate(result['citations'][:3], 1):
                print(f"{j}. {citation['title']} (Score: {citation['score']:.3f})")
        
        print(f"\n{'='*60}")
        
        # Ask user if they want to continue
        if i < len(test_questions):
            input("Press Enter to continue to next question...")
    
    print(f"\n🎉 Demo completed!")
    print(f"\n💡 Key Features Demonstrated:")
    print(f"   • Intelligent subquery generation")
    print(f"   • Semantic document retrieval with Chroma DB")
    print(f"   • Advanced text synthesis and summarization")
    print(f"   • Comprehensive citation tracking")
    print(f"   • Professional report generation")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Start the web interface: Open frontend/index.html")
    print(f"   2. Start the API server: python app.py")
    print(f"   3. Try your own research questions!")


if __name__ == "__main__":
    demo_ollama_features()
