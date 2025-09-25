# Migration Guide: Modular Agent Architecture

This guide explains how to migrate from the monolithic agent structure to the new modular architecture.

## Overview

The codebase has been refactored into a modular structure that separates concerns and makes the system more maintainable and testable.

## New Structure

```
agents/
├── __init__.py
├── research/           # Research agent components
│   ├── __init__.py
│   ├── research_agent.py
│   ├── query_planner.py
│   ├── document_retriever.py
│   └── answer_synthesizer.py
├── chat/              # Chat agent components
│   ├── __init__.py
│   ├── chat_agent.py
│   ├── conversation_manager.py
│   ├── context_builder.py
│   └── response_generator.py
└── shared/            # Shared utilities
    ├── __init__.py
    ├── interfaces.py
    ├── models.py
    └── exceptions.py
```

## Key Changes

### 1. Research Agent Modularization

**Before:**
```python
from agent import ResearchAgent
agent = ResearchAgent(persist_directory="chroma_db")
```

**After:**
```python
from agents.research import ResearchAgent, DocumentRetriever
from embeddings import load_index

# Load Chroma index
collection, model = load_index("chroma_db")
retriever = DocumentRetriever(collection, model)

# Create research agent
agent = ResearchAgent(retriever, use_ollama=True)
```

### 2. Chat Agent Modularization

**Before:**
```python
from chat_agent import ChatResearchAgent
chat_agent = ChatResearchAgent(persist_directory="chroma_db")
```

**After:**
```python
from agents.chat import ChatAgent, ConversationManager
from agents.research import ResearchAgent, DocumentRetriever

# Create components
retriever = DocumentRetriever(collection, model)
research_agent = ResearchAgent(retriever)
conversation_manager = ConversationManager()
chat_agent = ChatAgent(research_agent, conversation_manager)
```

### 3. API Updates

**Before:**
```python
# app.py
from agent import ResearchAgent
from chat_agent import ChatResearchAgent

research_agent = ResearchAgent(persist_directory="chroma_db")
chat_research_agent = ChatResearchAgent(persist_directory="chroma_db")
```

**After:**
```python
# app.py (updated to use modular architecture)
from agents.research import ResearchAgent, DocumentRetriever
from agents.chat import ChatAgent, ConversationManager

# Initialize components
collection, model = load_index("chroma_db")
retriever = DocumentRetriever(collection, model)
research_agent = ResearchAgent(retriever)
conversation_manager = ConversationManager()
chat_agent = ChatAgent(research_agent, conversation_manager)
```

## Migration Steps

### Step 1: Update Imports

Replace old imports with new modular imports:

```python
# Old imports
from agent import ResearchAgent
from chat_agent import ChatResearchAgent
from chat_manager import chat_manager

# New imports
from agents.research import ResearchAgent, DocumentRetriever
from agents.chat import ChatAgent, ConversationManager
from agents.shared.models import ResearchResult, ChatMessage
```

### Step 2: Update Agent Initialization

**Research Agent:**
```python
# Old way
agent = ResearchAgent(persist_directory="chroma_db", use_ollama=True)

# New way
from embeddings import load_index
collection, model = load_index("chroma_db")
retriever = DocumentRetriever(collection, model)
agent = ResearchAgent(retriever, use_ollama=True)
```

**Chat Agent:**
```python
# Old way
chat_agent = ChatResearchAgent(persist_directory="chroma_db")

# New way
conversation_manager = ConversationManager()
chat_agent = ChatAgent(research_agent, conversation_manager)
```

### Step 3: Update API Endpoints

The current `app.py` has been updated to use the modular architecture:

```bash
# Run the modular version
python app.py
```

### Step 4: Update Tests

**Old test structure:**
```python
from agent import ResearchAgent
from chat_agent import ChatResearchAgent
```

**New test structure:**
```python
from agents.research import ResearchAgent, DocumentRetriever
from agents.chat import ChatAgent, ConversationManager
from agents.shared.models import ResearchResult, ChatMessage
```

## Benefits of Modular Architecture

### 1. Separation of Concerns
- **Research Agent**: Handles document retrieval and research logic
- **Chat Agent**: Manages conversations and user interactions
- **Shared Components**: Common utilities and data models

### 2. Improved Testability
- Each component can be tested independently
- Mock dependencies easily
- Better test coverage

### 3. Better Maintainability
- Clear module boundaries
- Easier to modify individual components
- Reduced coupling between components

### 4. Enhanced Extensibility
- Easy to add new agent types
- Simple to extend existing functionality
- Plugin-like architecture

## Component Responsibilities

### Research Agent Components

- **ResearchAgent**: Main orchestrator for research process
- **QueryPlanner**: Generates subqueries from main questions
- **DocumentRetriever**: Handles document retrieval from Chroma
- **AnswerSynthesizer**: Combines results into final answers

### Chat Agent Components

- **ChatAgent**: Main orchestrator for chat functionality
- **ConversationManager**: Manages conversation state and persistence
- **ContextBuilder**: Builds context from conversation history
- **ResponseGenerator**: Generates conversational responses

### Shared Components

- **Interfaces**: Abstract base classes for components
- **Models**: Data models and structures
- **Exceptions**: Custom exception classes

## Testing

Run the new modular tests:

```bash
# Run all modular tests
python tests/run_modular_tests.py

# Run specific test module
python tests/run_modular_tests.py --module test_research_agent_modular

# Run with verbose output
python tests/run_modular_tests.py --verbose
```

## Backward Compatibility

The old `agent.py` and `chat_agent.py` files are still available for backward compatibility, but they now use the new modular components internally. However, it's recommended to migrate to the new structure for better maintainability.

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to update all import statements
2. **Initialization Errors**: Check that all required components are properly initialized
3. **Test Failures**: Ensure test dependencies are properly mocked

### Getting Help

If you encounter issues during migration:

1. Check the test files for usage examples
2. Review the component documentation
3. Run the integration tests to verify setup

## Future Enhancements

The modular architecture enables several future enhancements:

1. **Plugin System**: Easy to add new agent types
2. **Distributed Processing**: Components can be distributed across services
3. **Advanced Caching**: Better caching strategies per component
4. **Monitoring**: Component-level monitoring and metrics
5. **Configuration**: Component-specific configuration management
