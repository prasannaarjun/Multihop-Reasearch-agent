# 🔍 Multi-hop Research Agent

A sophisticated research agent that uses Chroma DB for document retrieval and multi-hop reasoning to answer complex research questions. The system supports PDF, LaTeX, and text file uploads with a modern React frontend and FastAPI backend, featuring both traditional research mode and conversational chat interface.

## ✨ Features

- **Multi-hop Reasoning**: Breaks down complex questions into subqueries for comprehensive answers
- **Dual Interface Modes**: 
  - **Research Mode**: Traditional question-answer interface with detailed results
  - **Chat Mode**: Conversational interface with context-aware responses
- **Document Upload**: Support for PDF, LaTeX (.tex), and text files with real-time processing
- **Conversation Management**: Create, manage, and switch between multiple chat conversations
- **Context-Aware Chat**: AI remembers previous conversation context for better responses
- **File Upload in Chat**: Upload documents directly within chat conversations
- **Modern UI**: React-based frontend with flexible, responsive design
- **Export Functionality**: Generate markdown reports of research results
- **Collection Analytics**: Track document statistics and file types
- **Ollama Integration**: Optional local LLM support for offline processing

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   FastAPI Backend│    │   Chroma DB     │
│                 │    │                 │    │                 │
│ • Dual Modes    │◄──►│ • File Processing│◄──►│ • Vector Store  │
│ • Chat Interface│    │ • Chat Agent    │    │ • Similarity    │
│ • File Upload   │    │ • Multi-hop     │    │   Search        │
│ • Conversations │    │   Reasoning     │    │                 │
│ • Collection Stats│   │ • Context Mgmt  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Ollama LLM    │
                       │   (Optional)    │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Ollama (optional, for local LLM)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd multihop-research-agent
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Initialize the Database

```bash
# Build the initial index from data directory
python embeddings.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Start the Application

#### Development Mode

```bash
# Terminal 1 - Start Backend
python app.py

# Terminal 2 - Start Frontend
cd frontend
npm install  # Install dependencies including cross-env
npm start    # This will suppress deprecation warnings
```

**Alternative for Windows users:**
```bash
# Use the batch file to suppress warnings
cd frontend
start.bat
```

**Alternative for macOS/Linux users:**
```bash
# Use the shell script to suppress warnings
cd frontend
chmod +x start.sh
./start.sh
```

#### Production Mode

```bash
# Build React app
cd frontend
npm run build

# Start backend (serves built React app)
python app.py
```

## 📋 Detailed Setup Instructions

### Backend Configuration

#### Environment Variables

Create a `.env` file in the root directory:

```env
# Ollama Configuration (Optional)
USE_OLLAMA=true
OLLAMA_MODEL=mistral:latest

# Database Configuration
CHROMA_PERSIST_DIRECTORY=chroma_db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

#### File Processing Dependencies

The system supports multiple file types with specific dependencies:

- **PDF Processing**: `PyPDF2`, `pypdf`
- **LaTeX Processing**: `python-latex`
- **Text Processing**: Built-in

Install additional dependencies if needed:

```bash
pip install PyPDF2 pypdf python-latex
```

#### Database Initialization

1. **Prepare Data Directory**: Place your documents in the `data/` directory
2. **Supported Formats**: `.txt`, `.pdf`, `.tex`, `.latex`
3. **Build Index**: Run `python embeddings.py` to create the initial database

### Frontend Configuration

#### Environment Variables

Create `frontend/.env.local`:

```env
REACT_APP_API_URL=http://localhost:8000
```

#### Development Server

The React development server runs on `http://localhost:3000` with automatic API proxying.

### Ollama Setup (Optional)

For local LLM processing:

1. **Install Ollama**: Follow instructions at [ollama.ai](https://ollama.ai)
2. **Pull Model**: `ollama pull mistral:latest`
3. **Start Ollama**: `ollama serve`
4. **Configure**: Set `USE_OLLAMA=true` in your `.env` file

## 🎯 Usage

### 1. Interface Modes

#### Research Mode
- **Traditional Interface**: Question-answer format with detailed results
- **Subquery Control**: Adjust "Documents per subquery" (default: 3)
- **Export Reports**: Download comprehensive markdown reports
- **Collection Stats**: View real-time document statistics

#### Chat Mode
- **Conversational Interface**: Natural chat with context awareness
- **Multiple Conversations**: Create and manage multiple chat sessions
- **Context Memory**: AI remembers previous conversation context
- **File Upload in Chat**: Upload documents directly within conversations

### 2. Upload Documents

- **Drag & Drop**: Drag files onto the upload area
- **Click to Upload**: Click the upload area to select files
- **Chat Upload**: Use the 📁 button in chat mode for quick uploads
- **Supported Formats**: PDF, LaTeX (.tex), text files
- **File Size Limit**: 50MB per file
- **Real-time Processing**: Immediate embedding generation and indexing

### 3. Ask Questions

#### Research Mode
- Enter your research question in the text area
- Click "Ask Question" or press Ctrl+Enter
- View comprehensive results with citations and subqueries

#### Chat Mode
- Type your message in the flexible chat input
- Press Enter or click Send
- AI responds with context from previous messages
- Upload files mid-conversation using the 📁 button

### 4. Manage Conversations

- **Create New**: Start a new conversation anytime
- **Switch Between**: Click on conversation titles to switch
- **Rename**: Double-click conversation titles to rename
- **Delete**: Remove conversations you no longer need
- **Context**: Each conversation maintains its own context

### 5. Export and Monitor

- **Export Reports**: Download markdown reports of research results
- **Collection Stats**: Monitor document statistics and file types
- **Real-time Updates**: Stats update automatically after uploads

## 🔧 API Endpoints

### Core Endpoints

- `GET /` - Serve React app or API info
- `GET /health` - Health check
- `POST /ask` - Ask research question (Research Mode)
- `GET /export` - Export research report

### File Management

- `POST /upload` - Upload and process files
- `GET /collection-stats` - Get collection statistics
- `GET /supported-file-types` - List supported file types

### Chat Endpoints

- `POST /chat` - Send chat message with context
- `GET /conversations` - List all conversations
- `GET /conversations/{id}` - Get conversation history
- `POST /conversations` - Create new conversation
- `PUT /conversations/{id}/title` - Update conversation title
- `DELETE /conversations/{id}` - Delete conversation

### Example API Usage

```bash
# Research Mode - Ask a question
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the best machine learning algorithms?", "per_sub_k": 3}'

# Chat Mode - Send a message
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Can you explain machine learning?", "conversation_id": "optional-id"}'

# Upload a file
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"

# Get collection stats
curl "http://localhost:8000/collection-stats"

# Create a new conversation
curl -X POST "http://localhost:8000/conversations" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Research Chat"}'

# Get conversation history
curl "http://localhost:8000/conversations/your-conversation-id"
```

## 📁 Project Structure

```
multihop-research-agent/
├── frontend/                 # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── ChatInterface.js    # Chat mode interface
│   │   │   ├── ConversationList.js # Conversation management
│   │   │   ├── ChatMessage.js      # Individual chat messages
│   │   │   ├── FileUpload.js       # File upload component
│   │   │   └── ...                 # Other components
│   │   ├── services/        # API services
│   │   └── App.js          # Main app component
│   ├── package.json
│   ├── start.bat           # Windows startup script
│   ├── start.sh            # Unix startup script
│   └── README.md
├── data/                    # Document storage
├── reports/                 # Generated reports
├── conversations/           # Chat conversation storage
├── chroma_db/              # Chroma database
├── agent.py                # Main research agent
├── chat_agent.py           # Chat-enhanced research agent
├── chat_manager.py         # Conversation management
├── app.py                  # FastAPI backend
├── embeddings.py           # Embedding management
├── file_processor.py       # File processing
├── retriever.py            # Document retrieval
├── planner.py              # Query planning
├── report.py               # Report generation
├── requirements.txt        # Python dependencies
├── dev_setup.py           # Development setup script
└── README.md              # This file
```

## 🎨 UI Features

### Responsive Design

- **Flexible Chat Input**: Auto-resizing textarea with smooth animations
- **Centered Layout**: Buttons and input are perfectly centered for better UX
- **Mobile-First**: Optimized for all screen sizes from mobile to desktop
- **Smooth Transitions**: Elegant animations for all interactions

### Chat Interface

- **Dual Mode Toggle**: Switch between Research and Chat modes seamlessly
- **Conversation Sidebar**: Manage multiple chat conversations
- **Context Awareness**: AI remembers conversation history
- **File Upload Integration**: Upload documents directly in chat
- **Real-time Updates**: Instant message delivery and status updates

### Modern Components

- **Drag & Drop**: Intuitive file upload with visual feedback
- **Loading States**: Clear progress indicators for all operations
- **Error Handling**: User-friendly error messages and recovery
- **Success Feedback**: Confirmation messages for successful operations

## 🛠️ Development

### Running Tests

```bash
# Test file processing
python test_file_upload.py

# Test API endpoints
python -m pytest tests/

# Test chat functionality
python test_chat_simple.py
```

### Code Quality

```bash
# Format code
black *.py
prettier --write frontend/src/**/*.{js,css}

# Lint code
flake8 *.py
eslint frontend/src/
```

### Database Management

```bash
# Rebuild entire index
python embeddings.py

# Add single file to existing index
python -c "from embeddings import add_file_to_index; add_file_to_index(open('file.pdf', 'rb').read(), 'file.pdf')"

# Get collection statistics
python -c "from embeddings import get_collection_stats; print(get_collection_stats())"

# Chat data is stored in conversations/ directory
# Each conversation is saved as a JSON file
ls conversations/
```

### Chat Data Management

```bash
# View conversation data
cat conversations/*.json

# Clear all conversations (if needed)
rm -rf conversations/*

# The chat_manager.py handles all conversation operations
python -c "from chat_manager import chat_manager; print(chat_manager.list_conversations())"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. PDF Processing Errors

```bash
# Install PDF dependencies
pip install PyPDF2 pypdf

# Check file permissions
ls -la data/*.pdf
```

#### 2. Chroma Database Issues

```bash
# Clear and rebuild database
rm -rf chroma_db/
python embeddings.py
```

#### 3. Frontend Build Errors

```bash
# Clear node modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### 4. Ollama Connection Issues

```bash
# Check Ollama status
ollama list
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

#### 5. Node.js Deprecation Warnings

If you see `util._extend` deprecation warnings:

```bash
# Install cross-env for cross-platform compatibility
cd frontend
npm install cross-env

# Or use the provided scripts
# Windows
start.bat

# macOS/Linux
chmod +x start.sh
./start.sh
```

#### 6. Chat Mode Issues

If chat mode isn't working properly:

```bash
# Check if conversations directory exists
ls -la conversations/

# Check chat agent initialization
python -c "from chat_agent import ChatResearchAgent; print('Chat agent loaded successfully')"

# Test chat API endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "conversation_id": null}'
```

#### 7. File Upload in Chat Issues

If file upload in chat mode fails:

```bash
# Check file processor
python -c "from file_processor import file_processor; print('File processor loaded')"

# Test upload endpoint
curl -X POST "http://localhost:8000/upload" \
  -F "file=@test.txt"

# Check collection stats
curl "http://localhost:8000/collection-stats"
```

### Logs and Debugging

- **Backend Logs**: Check console output when running `python app.py`
- **Frontend Logs**: Check browser console and network tab
- **File Processing**: Check console output during file uploads

## 🔒 Security Considerations

- **File Upload Limits**: 50MB maximum file size
- **CORS Configuration**: Configured for development (adjust for production)
- **Environment Variables**: Store sensitive data in `.env` files
- **File Validation**: All uploaded files are validated before processing

## 🚀 Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN cd frontend && npm install && npm run build

EXPOSE 8000
CMD ["python", "app.py"]
```

### Production Considerations

1. **Environment Variables**: Set production environment variables
2. **CORS Settings**: Configure CORS for your domain
3. **File Storage**: Consider cloud storage for large document collections
4. **Database Backup**: Regular backups of Chroma database
5. **Monitoring**: Add logging and monitoring for production use

## 📊 Performance

### Optimization Tips

- **Chunk Size**: Adjust `max_chunk_size` in `embeddings.py` for your use case
- **Batch Processing**: Process multiple files in batches for better performance
- **Memory Usage**: Monitor memory usage with large document collections
- **Caching**: Consider implementing caching for frequent queries

### Scaling

- **Horizontal Scaling**: Use multiple backend instances with shared Chroma database
- **Database Optimization**: Consider Chroma's clustering for large datasets
- **CDN**: Use CDN for static frontend assets

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -m 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Chroma DB**: Vector database for similarity search
- **Sentence Transformers**: Embedding generation
- **FastAPI**: Modern Python web framework
- **React**: Frontend framework with modern hooks and components
- **Ollama**: Local LLM support
- **PyPDF2 & pypdf**: PDF document processing
- **python-latex**: LaTeX document processing
- **Cross-env**: Cross-platform environment variable management

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed information
4. Include logs and error messages

---

**Happy Researching! 🔍📚**
