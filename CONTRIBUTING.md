# Contributing to Vietnamese Business Registration RAG Chatbot

Chúng tôi rất hoan nghênh các đóng góp cho dự án! Đây là hướng dẫn để bạn có thể contribute hiệu quả.

## 🚀 Quick Start

### Development Setup

1. **Clone repository**
```bash
git clone <repository-url>
cd rag_chatbot
```

2. **Setup environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

3. **Start development server**
```bash
# New clean architecture (recommended)
python start_new_system.py --mode new --reload

# Or legacy architecture
python start_all.py --mode api --reload
```

## 🏗️ Architecture Guidelines

### Clean Architecture Principles

Dự án follow **Clean Architecture** pattern:

```
├── core/                    # Domain layer - Business logic
│   ├── entities/           # Domain entities (no dependencies)
│   ├── interfaces/         # Ports (abstract interfaces)
│   └── use_cases/          # Application business logic
├── infrastructure/         # Infrastructure layer - External concerns
│   ├── repositories/      # Repository implementations
│   ├── services/          # Service implementations
│   └── logging/           # Logging infrastructure
├── application/           # Application layer - Orchestration
│   ├── config.py         # Configuration
│   └── dependencies.py   # Dependency injection
└── api/                   # Presentation layer - External interfaces
```

### Development Rules

1. **Domain Independence**: Core domain không depend vào external frameworks
2. **Dependency Inversion**: High-level modules không depend vào low-level modules
3. **Interface Segregation**: Use small, focused interfaces
4. **Single Responsibility**: Mỗi class/function có một responsibility duy nhất

## 📝 Coding Standards

### Python Code Style

- **PEP 8**: Follow Python PEP 8 style guide
- **Type Hints**: Use type hints cho tất cả functions
- **Docstrings**: Document tất cả public methods
- **Import Order**: Standard library → Third party → Local imports

### Example Code Style

```python
from typing import List, Optional
from datetime import datetime

from src.core.entities.conversation import Message
from src.core.interfaces.services import LLMService
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class ChatService:
    """Service for processing chat messages."""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    async def process_message(
        self, 
        message: str, 
        context: Optional[str] = None
    ) -> str:
        """
        Process a chat message and return response.
        
        Args:
            message: User message to process
            context: Optional conversation context
            
        Returns:
            Generated response text
            
        Raises:
            ValueError: If message is empty
        """
        if not message.strip():
            raise ValueError("Message cannot be empty")
        
        logger.info(
            "Processing message",
            extra={
                "message_length": len(message),
                "has_context": bool(context)
            }
        )
        
        try:
            response = await self.llm_service.generate_response(
                message, context
            )
            
            logger.info(
                "Message processed successfully",
                extra={"response_length": len(response)}
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Failed to process message",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/                   # Unit tests
│   ├── core/              # Core domain tests
│   ├── infrastructure/    # Infrastructure tests
│   └── application/       # Application tests
├── integration/           # Integration tests
├── fixtures/              # Test fixtures
└── conftest.py            # Pytest configuration
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock

from src.core.use_cases.chat_use_case import ChatUseCase
from src.core.entities.conversation import Conversation


class TestChatUseCase:
    """Test suite for ChatUseCase."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies."""
        return {
            'conversation_repo': Mock(),
            'llm_service': AsyncMock(),
            'intent_service': AsyncMock(),
            'metrics_service': AsyncMock()
        }
    
    @pytest.fixture
    def chat_use_case(self, mock_dependencies):
        """Create ChatUseCase instance with mocks."""
        return ChatUseCase(**mock_dependencies)
    
    @pytest.mark.asyncio
    async def test_process_message_success(self, chat_use_case, mock_dependencies):
        """Test successful message processing."""
        # Arrange
        conversation_id = "test-conversation"
        user_message = "Test message"
        
        mock_conversation = Conversation(id=conversation_id)
        mock_dependencies['conversation_repo'].get_conversation.return_value = mock_conversation
        mock_dependencies['intent_service'].classify_intent.return_value = {
            "intent": "general",
            "confidence": 0.9
        }
        mock_dependencies['llm_service'].generate_response.return_value = "Test response"
        
        # Act
        response = await chat_use_case.process_message(conversation_id, user_message)
        
        # Assert
        assert response.message == "Test response"
        assert response.intent.value == "general"
        mock_dependencies['conversation_repo'].save_conversation.assert_called_once()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/core/test_chat_use_case.py

# Run with verbose output
pytest -v
```

## 📊 Logging Guidelines

### Structured Logging

Sử dụng structured logging với correlation IDs:

```python
from src.infrastructure.logging.context import get_logger, LoggingContext

logger = get_logger(__name__)

# In request handlers
with LoggingContext(session_id="session_123"):
    logger.info(
        "Processing user request",
        extra={
            "user_id": "user_456",
            "request_type": "chat_message",
            "request_size": len(request_data)
        }
    )
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General application flow
- **WARNING**: Something unexpected but not error
- **ERROR**: Serious problem occurred
- **CRITICAL**: System failure

## 🔄 Git Workflow

### Branch Naming

- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `refactor/description` - Code refactoring
- `docs/description` - Documentation updates

### Commit Messages

Follow **Conventional Commits** format:

```
type(scope): description

body (optional)

footer (optional)
```

Examples:
```
feat(chat): add intent classification
fix(api): handle empty message error
docs(readme): update installation guide
refactor(core): extract message processing logic
```

### Pull Request Process

1. **Create feature branch**
```bash
git checkout -b feature/new-feature
```

2. **Make changes and commit**
```bash
git add .
git commit -m "feat(scope): description"
```

3. **Push and create PR**
```bash
git push origin feature/new-feature
```

4. **PR Requirements**
   - [ ] Code follows style guidelines
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   - [ ] All checks passing

### Code Review Checklist

**For Reviewers:**
- [ ] Code follows architecture principles
- [ ] Business logic is in correct layer
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] Performance considerations addressed

## 🚀 Deployment Guidelines

### Environment Setup

```bash
# Development
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG

# Staging
ENVIRONMENT=staging
DEBUG=False
LOG_LEVEL=INFO

# Production
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING
```

### Docker Deployment

```bash
# Build image
docker build -t rag-chatbot:latest .

# Run with docker-compose
docker-compose -f docker-compose.api.yml up -d
```

## 🐛 Issue Reporting

### Bug Reports

Include:
- **Environment**: OS, Python version, dependencies
- **Steps to reproduce**: Detailed steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Relevant log entries
- **Screenshots**: If applicable

### Feature Requests

Include:
- **Use case**: Why is this needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered
- **Additional context**: Any other relevant info

## 📚 Documentation

### Code Documentation

- **Docstrings**: All public methods
- **Type hints**: All function parameters and returns
- **Comments**: Complex logic explanation
- **README updates**: For new features

### API Documentation

- **OpenAPI**: Auto-generated from FastAPI
- **Examples**: Include request/response examples
- **Error codes**: Document all possible errors

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain professional communication

### Getting Help

- **Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Documentation**: Check existing docs first
- **Code**: Follow examples in codebase

---

## 📞 Contact

- **Issues**: GitHub Issues
- **Email**: [maintainer-email]
- **Documentation**: See README.md

Thank you for contributing! 🙏