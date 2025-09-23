# Test Suite for Multi-hop Research Agent

This directory contains comprehensive tests for the modular Multi-hop Research Agent system.

## Test Structure

### Core Test Files

- **`test_shared_models.py`** - Tests for shared data models (ChatMessage, Conversation, ResearchResult, etc.)
- **`test_shared_exceptions.py`** - Tests for custom exceptions
- **`test_shared_interfaces.py`** - Tests for interface definitions
- **`test_research_agent.py`** - Tests for research agent components (QueryPlanner, DocumentRetriever, AnswerSynthesizer, ResearchAgent)
- **`test_chat_agent.py`** - Tests for chat agent components (ConversationManager, ContextBuilder, ResponseGenerator, ChatAgent)
- **`test_integration.py`** - Integration tests for the full system
- **`test_auth.py`** - Tests for authentication system
- **`test_utils.py`** - Tests for utility functions and file processing
- **`test_simple.py`** - Simple tests for basic functionality verification

### Configuration Files

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`run_tests.py`** - Comprehensive test runner with options
- **`__init__.py`** - Package initialization

## Running Tests

### Quick Test (Recommended for basic verification)
```bash
python tests/test_simple.py
```

### Run All Tests with Pytest
```bash
# Activate virtual environment first
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_shared_models.py -v
```

### Run Tests by Category
```bash
python tests/run_tests.py --category shared
python tests/run_tests.py --category research
python tests/run_tests.py --category chat
python tests/run_tests.py --category integration
python tests/run_tests.py --category auth
python tests/run_tests.py --category utils
```

### Run Specific Test Module
```bash
python tests/run_tests.py --module test_shared_models
python tests/run_tests.py --module test_research_agent
```

### List Available Tests
```bash
python tests/run_tests.py --list
```

## Test Categories

### 1. Shared Components (`shared`)
- **Models**: ChatMessage, Conversation, ResearchResult, SubqueryResult, etc.
- **Exceptions**: AgentError, RetrievalError, LLMError, etc.
- **Interfaces**: IAgent, IRetriever, ILLMClient

### 2. Research Agent (`research`)
- **QueryPlanner**: Subquery generation and key term extraction
- **DocumentRetriever**: Document retrieval and collection statistics
- **AnswerSynthesizer**: Answer synthesis (rule-based and LLM)
- **ResearchAgent**: Main research processing logic

### 3. Chat Agent (`chat`)
- **ConversationManager**: Conversation creation, message management
- **ContextBuilder**: Context building and question enhancement
- **ResponseGenerator**: Response generation and formatting
- **ChatAgent**: Main chat processing logic

### 4. Integration (`integration`)
- **Full Workflow**: End-to-end testing of the complete system
- **Error Handling**: Cross-component error handling
- **Performance**: Basic performance characteristics
- **LLM Fallback**: Testing fallback when LLM is unavailable

### 5. Authentication (`auth`)
- **AuthService**: User creation, authentication, token management
- **API Endpoints**: Registration, login, protected routes
- **Token Verification**: JWT token validation

### 6. Utilities (`utils`)
- **File Processing**: Document processing and indexing
- **Embeddings**: Collection statistics and file indexing
- **Ollama Integration**: LLM client functionality
- **App Configuration**: Application setup and routes

## Test Fixtures

The test suite includes several useful fixtures defined in `conftest.py`:

- **`temp_dir`**: Temporary directory for test data
- **`mock_llm_client`**: Mock LLM client for testing
- **`mock_retriever`**: Mock document retriever
- **`sample_conversation`**: Pre-configured conversation for testing
- **`sample_research_result`**: Pre-configured research result

## Test Requirements

### Dependencies
- pytest
- fastapi
- sqlalchemy
- unittest.mock (built-in)

### Environment Variables
- `DATABASE_URL`: SQLite database for testing
- `SECRET_KEY`: Secret key for JWT tokens

### Test Database
Tests use a temporary SQLite database (`test_auth.db`) that is created and cleaned up automatically.

## Writing New Tests

### 1. Follow the naming convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### 2. Use fixtures when possible
```python
def test_my_function(mock_llm_client, temp_dir):
    # Your test code here
    pass
```

### 3. Test both success and failure cases
```python
def test_success_case():
    # Test normal operation
    pass

def test_error_case():
    # Test error handling
    with pytest.raises(ExpectedException):
        function_that_should_fail()
```

### 4. Use descriptive test names
```python
def test_create_conversation_with_valid_title():
    # Test creating conversation with valid title
    pass

def test_create_conversation_with_empty_title_fails():
    # Test that empty title fails
    pass
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running tests from the project root directory
2. **Database Errors**: Ensure the test database is properly cleaned up between tests
3. **Mock Issues**: Check that mocks are properly configured for the specific test case
4. **Environment Variables**: Ensure required environment variables are set

### Debug Mode
Run tests with verbose output to see detailed information:
```bash
python -m pytest tests/ -v -s
```

### Skip Tests
If certain tests fail due to missing dependencies, they will be automatically skipped with appropriate messages.

## Coverage

The test suite aims to provide comprehensive coverage of:
- ✅ All public methods and functions
- ✅ Error handling and edge cases
- ✅ Integration between components
- ✅ Authentication and authorization
- ✅ Data model validation
- ✅ API endpoint functionality

## Contributing

When adding new features:
1. Write tests for the new functionality
2. Ensure all tests pass
3. Update this README if needed
4. Follow the existing test patterns and conventions
