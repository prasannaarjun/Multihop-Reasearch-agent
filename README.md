# Multi-hop Research Agent

A sophisticated research platform that combines multi-hop reasoning with document retrieval capabilities, featuring both research and conversational chat modes. The system uses Postgres + pgvector for semantic search, optional Ollama integration for LLM capabilities, and includes a modern React frontend with comprehensive authentication.

## 🚀 Features

- **Multi-hop Research**: Advanced query decomposition and reasoning across multiple documents
- **Aspect-Guided Subqueries**: Intelligent aspect extraction and coverage tracking to ensure comprehensive answers
- **Adaptive Query Planning**: Dynamic subquery generation based on uncovered aspects
- **Conversational Chat**: Interactive chat interface with conversation history and context awareness
- **Document Processing**: Support for PDF, text, and LaTeX document ingestion with Docling
- **Semantic Search**: Postgres + pgvector-powered vector search with sentence transformers
- **User Authentication**: JWT-based authentication with secure session management
- **Modern Frontend**: React-based web interface with responsive design and real-time updates
- **Modular Architecture**: Clean separation of concerns with well-defined interfaces
- **Comprehensive Testing**: Full test suite with unit, integration, and API testing

## 📁 Project Structure

```
.
├── agents/                     # Core agent modules
│   ├── chat/                  # Chat functionality
│   │   ├── chat_agent.py      # Main chat orchestrator
│   │   ├── conversation_manager.py  # Conversation persistence
│   │   ├── context_builder.py # Context management
│   │   └── response_generator.py    # Response generation
│   ├── research/              # Research capabilities
│   │   ├── research_agent.py  # Main research orchestrator
│   │   ├── query_planner.py   # Aspect-guided query planning
│   │   ├── document_retriever.py    # Postgres + pgvector retrieval
│   │   └── answer_synthesizer.py    # Answer synthesis
│   └── shared/                # Shared interfaces and models
│       ├── interfaces.py      # Abstract base classes
│       ├── models.py          # Data models
│       ├── exceptions.py      # Custom exceptions
│       └── streaming_controller.py  # Streaming utilities
├── api/                       # FastAPI application
│   ├── routes/                # API route modules
│   │   ├── core.py           # Core endpoints
│   │   ├── research.py       # Research API
│   │   ├── chat.py           # Chat API
│   │   ├── conversations.py  # Conversation management
│   │   └── models.py         # Model management
│   ├── dependencies.py       # Dependency injection
│   └── schemas.py            # Pydantic schemas
├── auth/                      # Authentication system
│   ├── auth_service.py       # Core auth logic
│   ├── auth_middleware.py    # FastAPI middleware
│   ├── auth_routes.py        # Auth endpoints
│   ├── auth_models.py        # User/session models
│   ├── database.py           # Database connection
│   ├── init_db.py            # Database initialization
│   └── validators.py         # Input validation
├── frontend/                  # React web application
│   ├── src/                  # Source code
│   │   ├── components/       # React components
│   │   ├── contexts/         # React contexts
│   │   └── services/         # API services
│   ├── public/               # Static assets
│   └── build/                # Production build
├── tests/                     # Comprehensive test suite
│   ├── test_auth.py          # Authentication tests
│   ├── test_research_agent.py # Research agent tests
│   ├── test_chat_agent.py    # Chat agent tests
│   ├── test_embedding_storage.py # Vector storage tests
│   ├── test_document_ingestion.py # Document processing tests
│   └── test_integration.py   # End-to-end tests
├── docs/                      # Documentation
│   ├── ASPECT_GUIDED_IMPLEMENTATION_SUMMARY.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── [additional docs]     # Feature documentation
├── alembic/                   # Database migrations
│   └── versions/             # Migration files
├── examples/                  # Setup examples and demos
├── embedding_manager.py       # Embedding management utilities
├── embedding_storage.py       # Postgres + pgvector utilities
├── document_ingestion.py      # Document processing pipeline
├── document_processing.py    # Document parsing utilities
├── ollama_client.py          # Ollama LLM integration
├── app.py                    # FastAPI application entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🧩 Core Modules

### Agents Module (`agents/`)

The heart of the system, implementing a modular agent architecture:

#### Research Agent (`agents/research/`)
- **ResearchAgent**: Main orchestrator for research operations with multi-hop reasoning
- **QueryPlanner**: Advanced aspect-guided query decomposition and coverage tracking
  - **Aspect Extraction**: LLM-based intelligent identification of query facets
  - **Coverage Tracking**: Ensures all aspects are addressed before stopping
  - **Adaptive Subqueries**: Dynamic generation based on uncovered aspects
  - **Importance Weighting**: Core vs optional aspect prioritization
- **DocumentRetriever**: Handles Postgres + pgvector semantic search and document retrieval
- **AnswerSynthesizer**: Combines multiple sources into comprehensive answers

#### Chat Agent (`agents/chat/`)
- **ChatAgent**: Manages conversational interactions with research capabilities
- **ConversationManager**: Handles conversation persistence and retrieval
- **ContextBuilder**: Builds context from conversation history
- **ResponseGenerator**: Generates contextual responses

#### Shared Components (`agents/shared/`)
- **Interfaces**: Abstract base classes (IAgent, IRetriever, ILLMClient)
- **Models**: Data models for research results, chat messages, conversations
- **Exceptions**: Custom exception hierarchy for error handling

### Authentication System (`auth/`)

Comprehensive user management and security:

- **AuthService**: Core authentication logic with JWT token handling
- **AuthMiddleware**: FastAPI middleware for request authentication
- **AuthRoutes**: API endpoints for user registration, login, logout
- **Database Models**: User and session management with SQLAlchemy
- **Password Security**: bcrypt hashing with secure token generation

### Frontend Application (`frontend/`)

Modern React-based web interface:

#### Core Components
- **App.js**: Main application with routing and state management
- **AuthContext**: React context for authentication state
- **ProtectedRoute**: Route protection for authenticated users

#### UI Components
- **ChatInterface**: Real-time chat with research integration
- **QuestionForm**: Research query input and submission
- **Results**: Research results display with source attribution
- **ConversationList**: Chat history management
- **FileUpload**: Document ingestion interface
- **UserProfile**: User account management

#### Services
- **apiService**: Centralized API communication with error handling

### Testing Suite (`tests/`)

Comprehensive test coverage:

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Database Tests**: Authentication and conversation persistence
- **API Tests**: Endpoint validation and error handling

## 🛠️ Technology Stack

### Backend
- **FastAPI** (≥0.104.0): High-performance web framework with automatic API documentation
- **SQLAlchemy** (≥2.0.23): Modern Python ORM with PostgreSQL support
- **Postgres + pgvector** (≥0.2.4): Vector database for semantic search with IVFFlat indexing
- **Sentence Transformers** (≥2.2.2): Text embedding generation with all-MiniLM-L6-v2 model
- **Docling** (≥1.0.0): Advanced document processing for PDF, text, and LaTeX
- **Ollama** (≥0.1.7): Optional local LLM integration for privacy-focused deployments
- **JWT + python-jose**: Secure token-based authentication with cryptography
- **Alembic** (≥1.13.0): Database migration management
- **Pydantic** (≥2.5.0): Data validation and serialization
- **Uvicorn**: ASGI server for production deployment

### Frontend
- **React** (18.2.0): Modern React with hooks and functional components
- **DOMPurify** (3.2.7): XSS protection for user-generated content
- **CSS3**: Custom styling with responsive design and modern UI patterns
- **Context API**: Built-in state management for authentication and app state
- **Fetch API**: Native HTTP client with error handling and interceptors

### Development & Testing
- **pytest**: Comprehensive Python testing framework with fixtures
- **Jest + Testing Library**: React component testing with user interaction simulation
- **PowerShell**: Windows-native development environment with virtual environment support
- **Cross-env**: Cross-platform environment variable management
- **TypeScript**: Optional type safety for React components

## 🚦 Getting Started

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **PostgreSQL 12+** with pgvector extension
- **PowerShell 5.1+** (Windows 10/11)
- **(Optional) Ollama** for local LLM support

### Installation

1. **Clone the repository**
   ```powershell
   git clone <repository-url>
   cd "Multihop Reasearch agent"
   ```

2. **Backend Setup**
   ```powershell
   # Create and activate virtual environment
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Setup environment variables (create .env file)
   # Copy and modify the example configuration
   ```

3. **Database Setup**
   ```powershell
   # Install pgvector extension in PostgreSQL
   # Connect to your PostgreSQL database and run:
   # CREATE EXTENSION IF NOT EXISTS vector;
   
   # Initialize database tables
   python -m auth.init_db
   
   # Run database migrations (includes embeddings table with pgvector)
   alembic upgrade head
   ```

4. **Frontend Setup**
   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

5. **Start the Application**
   ```powershell
   # Activate virtual environment (if not already active)
   .venv\Scripts\Activate.ps1
   
   # Start backend server
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   
   # In another PowerShell window, start frontend (development)
   cd frontend
   npm start
   ```

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/research_agent_db

# Authentication
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Embedding Configuration
EMBEDDING_DIM=384  # Dimension for sentence transformer embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# LLM Integration (Optional)
USE_OLLAMA=true
OLLAMA_MODEL=mistral:latest
OLLAMA_BASE_URL=http://localhost:11434

# Frontend Configuration
FRONTEND_ORIGIN=http://localhost:3000

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
```

### Document Ingestion

Add documents to the knowledge base:

```python
# Example: Add documents to Postgres + pgvector
from document_ingestion import process_and_store_document
from sentence_transformers import SentenceTransformer
from auth.database import SessionLocal

# Initialize components
db_session = SessionLocal()
model = SentenceTransformer('all-MiniLM-L6-v2')

# Add a document
result = process_and_store_document(
    db_session=db_session,
    user_id=1,  # Your user ID
    file_path="path/to/document.pdf",
    filename="document.pdf",
    model=model
)

print(f"Added {result['chunks_added']} chunks to the database")
```

## 📖 Usage

### Research Mode
1. Upload documents through the web interface
2. Ask complex questions that require multi-hop reasoning
3. View decomposed sub-queries and synthesized answers
4. Access source attributions and relevance scores

### Chat Mode
1. Switch to chat interface
2. Engage in conversational research
3. Reference previous conversation context
4. Save and retrieve conversation history

### API Usage

The system provides a comprehensive REST API with the following main endpoints:

#### Authentication Endpoints
```http
POST /auth/register
Content-Type: application/json
{
    "username": "user@example.com",
    "password": "secure_password",
    "full_name": "John Doe"
}

POST /auth/login
Content-Type: application/json
{
    "username": "user@example.com",
    "password": "secure_password"
}

POST /auth/logout
Authorization: Bearer <access_token>
```

#### Research Endpoints
```http
POST /research/ask
Authorization: Bearer <access_token>
Content-Type: application/json
{
    "question": "What are the main differences between self-attention and multi-head attention mechanisms?",
    "per_sub_k": 3,
    "max_hops": 5,
    "include_aspects": true
}

# Response includes:
# - Decomposed aspects (e.g., "Definition of Attention", "Self-Attention Mechanism", "Multi-Head Architecture")
# - Coverage tracking for each aspect
# - Synthesized answer with source attribution
# - Relevance scores and document references
```

#### Chat Endpoints
```http
POST /chat/send
Authorization: Bearer <access_token>
Content-Type: application/json
{
    "message": "Can you explain how transformers work?",
    "conversation_id": "optional-conversation-id",
    "include_context": true,
    "research_mode": false
}

GET /conversations/
Authorization: Bearer <access_token>

GET /conversations/{conversation_id}/messages
Authorization: Bearer <access_token>
```

#### Document Management
```http
POST /documents/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
file: <document_file>
filename: "research_paper.pdf"

GET /documents/
Authorization: Bearer <access_token>

DELETE /documents/{document_id}
Authorization: Bearer <access_token>
```

#### Model Management
```http
GET /models/available
Authorization: Bearer <access_token>

POST /models/set-embedding-model
Authorization: Bearer <access_token>
Content-Type: application/json
{
    "model_name": "all-MiniLM-L6-v2"
}
```

#### Python Client Example
```python
import requests
import json

# Authentication
auth_response = requests.post("http://localhost:8000/auth/login", json={
    "username": "user@example.com",
    "password": "secure_password"
})
token = auth_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Research Query with Aspect Coverage
research_response = requests.post("http://localhost:8000/research/ask", 
    headers=headers,
    json={
        "question": "How does gradient descent work in neural networks?",
        "per_sub_k": 3,
        "max_hops": 4,
        "include_aspects": True
    }
)

result = research_response.json()
print(f"Answer: {result['answer']}")
print(f"Aspects covered: {len(result['aspects'])}")
for aspect in result['aspects']:
    print(f"- {aspect['name']}: {aspect['coverage_score']:.2f}")

# Chat with Context
chat_response = requests.post("http://localhost:8000/chat/send",
    headers=headers,
    json={
        "message": "Can you elaborate on the learning rate?",
        "conversation_id": result.get('conversation_id'),
        "include_context": True
    }
)

print(f"Chat response: {chat_response.json()['response']}")
```

## 🎯 Advanced Features

### Aspect-Guided Query Planning

The system now features intelligent aspect extraction and coverage tracking:

#### Aspect Extraction
- **LLM-based**: Uses language models to identify query facets intelligently
- **Heuristic Fallback**: Regex patterns for comparison, definition, process, causal, evaluation aspects
- **Importance Weighting**: Core aspects (1.0) vs optional aspects (0.5-0.7)
- **Keyword Association**: Each aspect includes relevant keywords for document matching

#### Coverage Tracking
- **Real-time Monitoring**: Tracks which aspects are covered during multi-hop research
- **Coverage Scoring**: Calculates coverage percentage for each aspect
- **Adaptive Stopping**: Only stops when all core aspects are covered or max hops reached
- **Visual Feedback**: Shows coverage progress in the frontend interface

#### Example Aspect Decomposition
```
Query: "self-attention vs multi-head attention"

Extracted Aspects:
1. "Definition of Attention" (core: 1.0)
2. "Self-Attention Mechanism" (core: 1.0) 
3. "Multi-Head Architecture" (core: 1.0)
4. "Performance Comparison" (optional: 0.7)
5. "Use Cases" (optional: 0.5)
```

### Adaptive Subquery Generation

- **Dynamic Planning**: Generates subqueries based on uncovered aspects
- **Context-Aware**: Each subquery builds on previous findings
- **Efficiency Optimization**: Stops early when sufficient coverage is achieved
- **Quality Assurance**: Ensures comprehensive answers across all query facets

## 🔧 Configuration

### Environment Variables

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/research_agent_db

# Authentication
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Embedding Configuration
EMBEDDING_DIM=384  # Dimension for sentence transformer embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# LLM Integration (Optional)
USE_OLLAMA=true
OLLAMA_MODEL=mistral:latest
OLLAMA_BASE_URL=http://localhost:11434

# Research Configuration
MAX_HOPS=5  # Maximum number of research hops
PER_SUB_K=3  # Documents retrieved per subquery
MIN_COVERAGE_THRESHOLD=0.8  # Minimum aspect coverage before stopping

# Frontend Configuration
FRONTEND_ORIGIN=http://localhost:3000

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
```

### Database Configuration

The system uses PostgreSQL with pgvector extension for vector operations:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table with vector support
CREATE TABLE embeddings (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(384),  -- Adjust dimension based on model
    metadata JSONB,
    document_id INTEGER,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create vector index for efficient similarity search
CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);
```

## 🧪 Testing

The project includes a comprehensive test suite covering all major components:

### Test Structure

```
tests/
├── test_auth.py                    # Authentication and user management
├── test_research_agent.py          # Research agent functionality
├── test_chat_agent.py              # Chat agent and conversation management
├── test_embedding_storage.py       # Postgres + pgvector operations
├── test_document_ingestion.py      # Document processing pipeline
├── test_document_retriever_postgres.py # Vector search and retrieval
├── test_aspect_coverage.py         # Aspect-guided query planning
├── test_aspect_guided_subqueries.py # Subquery generation
├── test_adaptive_subquery_generation.py # Adaptive query planning
├── test_conversation_manager_db.py # Database conversation persistence
├── test_conversation_api_isolation.py # API conversation isolation
├── test_ask_model_streaming.py     # Streaming response handling
├── test_integration.py             # End-to-end integration tests
├── test_shared_*.py                # Shared component tests
└── conftest.py                     # Test configuration and fixtures
```

### Running Tests

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run all tests with verbose output
cd tests
python -m pytest -v

# Run specific test categories
python -m pytest test_auth.py -v                    # Authentication tests
python -m pytest test_research_agent.py -v          # Research functionality
python -m pytest test_chat_agent.py -v              # Chat functionality
python -m pytest test_embedding_storage.py -v       # Vector storage
python -m pytest test_document_ingestion.py -v      # Document processing
python -m pytest test_aspect_coverage.py -v         # Aspect coverage
python -m pytest test_integration.py -v             # Integration tests

# Run tests with coverage reporting
python -m pytest --cov=agents --cov=auth --cov=api --cov-report=html

# Run specific test methods
python -m pytest test_research_agent.py::test_multi_hop_research -v

# Run tests in parallel (if pytest-xdist is installed)
python -m pytest -n auto
```

### Test Categories

#### Unit Tests
- **Agent Components**: Individual agent functionality testing
- **Authentication**: User registration, login, token validation
- **Database Operations**: CRUD operations and data persistence
- **Document Processing**: File parsing and embedding generation
- **Vector Search**: Semantic search and retrieval accuracy

#### Integration Tests
- **End-to-End Workflows**: Complete research and chat flows
- **API Endpoints**: HTTP request/response validation
- **Database Integration**: Multi-table operations and transactions
- **Authentication Flow**: Complete user session management

#### Feature Tests
- **Aspect Coverage**: Query decomposition and coverage tracking
- **Multi-hop Reasoning**: Complex query resolution across documents
- **Conversation Management**: Chat history and context building
- **Streaming Responses**: Real-time response generation

### Test Configuration

The test suite uses pytest with the following configuration:

```python
# conftest.py - Test fixtures and configuration
@pytest.fixture
def db_session():
    """Database session for testing"""
    
@pytest.fixture
def test_user():
    """Test user for authentication tests"""
    
@pytest.fixture
def sample_documents():
    """Sample documents for retrieval tests"""
```

### Frontend Testing

```powershell
cd frontend

# Run React component tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode
npm test -- --watch
```

## 🏗️ Architecture Highlights

### Modular Design
- Clean separation between research, chat, and shared components
- Interface-based design for easy extensibility
- Dependency injection for testability

### Security
- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- Session management and tracking
- Protected API endpoints

### Scalability
- Stateless API design
- Database connection pooling
- Postgres + pgvector optimization with IVFFlat indexing
- Multi-tenant user isolation
- Modular frontend components

### Error Handling
- Custom exception hierarchy
- Graceful error recovery
- Comprehensive logging
- User-friendly error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔄 Migration from ChromaDB

If you're upgrading from a previous version that used ChromaDB:

1. **Install pgvector extension** in your PostgreSQL database:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Run the migration** to create the embeddings table:
   ```powershell
   alembic upgrade head
   ```

3. **Re-upload your documents** through the web interface or API, as the embedding storage format has changed.

4. **Remove old ChromaDB files** (the `chroma_db/` directory is no longer needed).

## 🔮 Future Enhancements

### Planned Features
- **Multi-language Support**: Support for non-English documents and queries
- **Advanced Visualization**: Interactive research chain visualization
- **Plugin System**: Custom document processors and LLM integrations
- **Real-time Collaboration**: Multi-user research sessions
- **Mobile Application**: Native mobile app for research on-the-go
- **Advanced Analytics**: Research pattern analysis and insights
- **Custom Models**: Support for fine-tuned embedding models
- **API Rate Limiting**: Advanced API management and usage tracking

### Performance Optimizations
- **Caching Layer**: Redis-based caching for frequent queries
- **Batch Processing**: Efficient bulk document ingestion
- **Query Optimization**: Advanced query planning algorithms
- **Distributed Search**: Multi-node vector search capabilities

## 📚 Documentation

### Additional Resources
- **[Aspect-Guided Implementation](docs/ASPECT_GUIDED_IMPLEMENTATION_SUMMARY.md)**: Detailed guide to aspect-guided subquery generation
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)**: Overview of coverage tracking features
- **[Security Fixes](docs/SECURITY_FIXES_COMPLETE.md)**: Security improvements and best practices
- **[Quick Start Guide](docs/QUICK_START_ADAPTIVE_SUBQUERY.md)**: Getting started with adaptive subqueries

### Examples and Demos
- **[Adaptive Subquery Demo](examples/adaptive_subquery_demo.py)**: Interactive demonstration of aspect-guided research
- **[Aspect Coverage Demo](examples/aspect_coverage_demo.py)**: Coverage tracking visualization
- **[Embedding Manager Demo](examples/embedding_manager_demo.py)**: Document processing pipeline
- **[Setup Examples](examples/)**: Authentication and Ollama setup guides

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Add comprehensive tests** for new functionality
3. **Ensure all tests pass** before submitting
4. **Update documentation** for new features
5. **Follow code style** guidelines (PEP 8 for Python)
6. **Submit a pull request** with a clear description

### Development Setup
```powershell
# Clone your fork
git clone https://github.com/yourusername/multihop-research-agent.git
cd multihop-research-agent

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install development dependencies
pip install -r requirements.txt
pip install pytest-cov black flake8

# Run pre-commit checks
black --check .
flake8 .
pytest --cov=agents --cov=auth --cov=api
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Sentence Transformers**: For providing excellent embedding models
- **PostgreSQL + pgvector**: For robust vector database capabilities
- **FastAPI**: For the high-performance web framework
- **React**: For the modern frontend framework
- **Docling**: For advanced document processing capabilities
