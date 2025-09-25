# Multi-hop Research Agent - Modular Architecture

A sophisticated research agent system that uses multi-hop reasoning to answer complex questions by breaking them down into focused subqueries and synthesizing comprehensive answers from multiple sources.

## 🏗️ Architecture Overview

The system has been refactored into a modular architecture that separates concerns and improves maintainability:

```
agents/
├── research/           # Research agent components
│   ├── research_agent.py      # Main research orchestrator
│   ├── query_planner.py       # Subquery generation
│   ├── document_retriever.py  # Document retrieval
│   └── answer_synthesizer.py  # Answer synthesis
├── chat/              # Chat agent components
│   ├── chat_agent.py          # Main chat orchestrator
│   ├── conversation_manager.py # Conversation management
│   ├── context_builder.py     # Context building
│   └── response_generator.py  # Response generation
└── shared/            # Shared utilities
    ├── interfaces.py          # Abstract interfaces
    ├── models.py             # Data models
    └── exceptions.py         # Custom exceptions
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Chroma database
- Ollama (optional, for advanced LLM features)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd multihop-research-agent
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment:**
```bash
cp env.example .env
# Edit .env with your configuration
```

4. **Build the document index:**
```bash
python embeddings.py
```

5. **Run the modular API:**
```bash
python app.py
```

## 📚 Component Documentation

### Research Agent Components

#### ResearchAgent
Main orchestrator for the research process.

```python
from agents.research import ResearchAgent, DocumentRetriever
from embeddings import load_index

# Load Chroma index
collection, model = load_index("chroma_db")
retriever = DocumentRetriever(collection, model)

# Create research agent
agent = ResearchAgent(retriever, use_ollama=True)

# Process research question
result = agent.process("What is machine learning?")
print(result.answer)
```

#### QueryPlanner
Generates focused subqueries from complex questions.

```python
from agents.research import QueryPlanner

planner = QueryPlanner()
subqueries = planner.generate_subqueries("What are the best ML algorithms?")
# Returns: ['what are best ml algorithms', 'how do ml algorithms work', ...]
```

#### DocumentRetriever
Handles document retrieval from Chroma database.

```python
from agents.research import DocumentRetriever

retriever = DocumentRetriever(collection, model)
documents = retriever.retrieve("machine learning", top_k=5)
```

#### AnswerSynthesizer
Combines subquery results into comprehensive answers.

```python
from agents.research import AnswerSynthesizer

synthesizer = AnswerSynthesizer()
answer = synthesizer.synthesize_answer(question, subquery_results)
```

### Chat Agent Components

#### ChatAgent
Main orchestrator for chat functionality.

```python
from agents.chat import ChatAgent, ConversationManager
from agents.research import ResearchAgent, DocumentRetriever

# Create components
retriever = DocumentRetriever(collection, model)
research_agent = ResearchAgent(retriever)
conversation_manager = ConversationManager()
chat_agent = ChatAgent(research_agent, conversation_manager)

# Process chat message
response = chat_agent.process("What is machine learning?")
print(response.answer)
```

#### ConversationManager
Manages conversation state and persistence.

```python
from agents.chat import ConversationManager

manager = ConversationManager()

# Create conversation
conv_id = manager.create_conversation("My Research Session")

# Add messages
manager.add_message(conv_id, "user", "What is AI?")
manager.add_message(conv_id, "assistant", "AI is...")

# Get history
history = manager.get_conversation_history(conv_id)
```

#### ContextBuilder
Builds context from conversation history.

```python
from agents.chat import ContextBuilder

builder = ContextBuilder()
context = builder.build_research_context(conversation)
enhanced_question = builder.enhance_question_with_context(question, context)
```

#### ResponseGenerator
Generates conversational responses.

```python
from agents.chat import ResponseGenerator

generator = ResponseGenerator()
response = generator.generate_chat_response(research_result, context)
```

### Shared Components

#### Models
Data models for the system.

```python
from agents.shared.models import ResearchResult, ChatMessage, Conversation

# Research result
result = ResearchResult(
    question="What is ML?",
    answer="ML is a subset of AI...",
    subqueries=[],
    citations=[],
    total_documents=5
)

# Chat message
message = ChatMessage(
    id="msg-1",
    role="user",
    content="Hello",
    timestamp=datetime.now()
)
```

#### Interfaces
Abstract interfaces for components.

```python
from agents.shared.interfaces import IAgent, IRetriever, ILLMClient

class MyAgent(IAgent):
    def process(self, input_data):
        return input_data
```

#### Exceptions
Custom exception classes.

```python
from agents.shared.exceptions import AgentError, RetrievalError, LLMError

try:
    result = agent.process(question)
except RetrievalError as e:
    print(f"Retrieval failed: {e}")
```

## 🧪 Testing

The modular architecture includes comprehensive tests for all components.

### Running Tests

```bash
# Run all modular tests
python tests/run_modular_tests.py

# Run specific test module
python tests/run_modular_tests.py --module test_research_agent_modular

# Run with verbose output
python tests/run_modular_tests.py --verbose
```

### Test Structure

```
tests/
├── test_research_agent_modular.py    # Research agent tests
├── test_chat_agent_modular.py        # Chat agent tests
├── test_shared_components.py         # Shared component tests
├── test_modular_integration.py       # Integration tests
└── run_modular_tests.py              # Test runner
```

## 🔧 Configuration

### Environment Variables

```bash
# .env file
USE_OLLAMA=true
OLLAMA_MODEL=mistral:latest
CHROMA_PERSIST_DIRECTORY=chroma_db
CHAT_DATA_DIRECTORY=chat_data
```

### Component Configuration

```python
# Research agent configuration
agent = ResearchAgent(
    retriever=retriever,
    llm_client=llm_client,
    use_ollama=True,
    ollama_model="mistral:latest"
)

# Chat agent configuration
chat_agent = ChatAgent(
    research_agent=research_agent,
    conversation_manager=ConversationManager(
        persist_directory="chat_data"
    )
)
```

## 📊 API Endpoints

The modular API provides the same endpoints as the original system:

### Research Endpoints
- `POST /ask` - Ask a research question
- `GET /export` - Export research results
- `GET /stats` - Get system statistics
- `POST /upload` - Upload documents

### Chat Endpoints
- `POST /chat` - Chat with the agent
- `GET /conversations` - List conversations
- `GET /conversations/{id}` - Get conversation history
- `POST /conversations` - Create conversation
- `PUT /conversations/{id}/title` - Update title
- `DELETE /conversations/{id}` - Delete conversation

## 🔄 Migration from Monolithic Structure

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed migration instructions.

## 🏗️ Architecture Benefits

### 1. Separation of Concerns
- **Research Logic**: Isolated in research components
- **Chat Logic**: Isolated in chat components
- **Shared Utilities**: Common functionality centralized

### 2. Improved Testability
- Each component can be tested independently
- Easy to mock dependencies
- Better test coverage and reliability

### 3. Enhanced Maintainability
- Clear module boundaries
- Easier to modify individual components
- Reduced coupling between components

### 4. Better Extensibility
- Easy to add new agent types
- Simple to extend existing functionality
- Plugin-like architecture

### 5. Performance Optimization
- Components can be optimized independently
- Better resource management
- Easier to implement caching strategies

## 🚀 Future Enhancements

The modular architecture enables several future enhancements:

1. **Plugin System**: Easy to add new agent types
2. **Distributed Processing**: Components can be distributed across services
3. **Advanced Caching**: Component-specific caching strategies
4. **Monitoring**: Component-level monitoring and metrics
5. **Configuration**: Component-specific configuration management
6. **Microservices**: Convert components to microservices
7. **API Gateway**: Centralized API management
8. **Load Balancing**: Distribute load across components

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
2. Review the test files for usage examples
3. Open an issue on GitHub
4. Check the component documentation

## 📈 Performance

The modular architecture provides several performance benefits:

- **Faster Testing**: Individual components can be tested quickly
- **Better Caching**: Component-specific caching strategies
- **Resource Optimization**: Better memory and CPU usage
- **Scalability**: Components can be scaled independently
- **Debugging**: Easier to identify performance bottlenecks

## 🔒 Security

The modular architecture improves security:

- **Isolation**: Components are isolated from each other
- **Access Control**: Fine-grained access control per component
- **Audit Trail**: Component-level logging and monitoring
- **Vulnerability Management**: Easier to patch individual components
