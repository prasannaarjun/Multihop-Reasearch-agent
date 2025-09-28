# Multi-hop Research Agent

A sophisticated research platform that combines multi-hop reasoning with document retrieval capabilities, featuring both research and conversational chat modes. The system uses ChromaDB for semantic search, optional Ollama integration for LLM capabilities, and includes a modern React frontend with comprehensive authentication.

## 🚀 Features

- **Multi-hop Research**: Advanced query decomposition and reasoning across multiple documents
- **Conversational Chat**: Interactive chat interface with conversation history
- **Document Processing**: Support for PDF, text, and LaTeX document ingestion
- **Semantic Search**: ChromaDB-powered vector search with sentence transformers
- **User Authentication**: JWT-based authentication with user management
- **Modern Frontend**: React-based web interface with responsive design
- **Modular Architecture**: Clean separation of concerns with well-defined interfaces

## 📁 Project Structure

```
.
├── agents/                     # Core agent modules
│   ├── chat/                  # Chat functionality
│   ├── research/              # Research capabilities
│   └── shared/                # Shared interfaces and models
├── auth/                      # Authentication system
├── frontend/                  # React web application
├── tests/                     # Test suite
├── chroma_db/                 # ChromaDB vector database
├── alembic/                   # Database migrations
└── examples/                  # Setup examples and utilities
```

## 🧩 Core Modules

### Agents Module (`agents/`)

The heart of the system, implementing a modular agent architecture:

#### Research Agent (`agents/research/`)
- **ResearchAgent**: Main orchestrator for research operations
- **QueryPlanner**: Decomposes complex questions into sub-queries
- **DocumentRetriever**: Handles semantic search and document retrieval
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
- **FastAPI**: High-performance web framework
- **SQLAlchemy**: Database ORM with PostgreSQL support
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: Text embedding generation
- **Ollama**: Optional local LLM integration
- **JWT**: Secure token-based authentication
- **Alembic**: Database migration management

### Frontend
- **React 18**: Modern React with hooks
- **CSS3**: Custom styling with responsive design
- **Context API**: State management
- **Fetch API**: HTTP client for backend communication

### Development & Testing
- **pytest**: Python testing framework
- **Jest**: JavaScript testing framework
- **Testing Library**: React component testing
- **PowerShell**: Windows development environment

## 🚦 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database
- (Optional) Ollama for local LLM support

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Multihop Reasearch agent"
   ```

2. **Backend Setup**
   ```powershell
   # Create and activate virtual environment
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Setup environment variables
   copy env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**
   ```powershell
   # Initialize database
   python -m auth.init_db
   
   # Run migrations
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
   # Start backend server
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   
   # In another terminal, start frontend (development)
   cd frontend
   npm start
   ```

### Document Ingestion

Add documents to the knowledge base:

```python
# Example: Add documents to ChromaDB
from embeddings import add_file_to_index

# Add a PDF file
add_file_to_index("path/to/document.pdf", "collection_name")
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

```python
# Research API
POST /research/ask
{
    "question": "What are the main causes of climate change?",
    "per_sub_k": 3
}

# Chat API
POST /chat/send
{
    "message": "Tell me about renewable energy",
    "conversation_id": "optional-conversation-id",
    "include_context": true
}
```

## 🔧 Configuration

Key environment variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/research_agent_auth

# Authentication
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Integration
USE_OLLAMA=true
OLLAMA_MODEL=mistral:latest
```

## 🧪 Testing

Run the comprehensive test suite:

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run all tests
cd tests
python -m pytest -v

# Run specific test categories
python -m pytest test_auth.py -v
python -m pytest test_research_agent.py -v
python -m pytest test_chat_agent.py -v
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
- Vector database optimization
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

## 🔮 Future Enhancements

- Multi-language support
- Advanced visualization of research chains
- Plugin system for custom document processors
- Real-time collaboration features
- Enhanced LLM integration options
- Mobile application support
