# 🏗️ Vietnamese Business Registration RAG Chatbot - New Architecture

## 📋 Architecture Overview

Hệ thống đã được tái cấu trúc theo **Clean Architecture** với comprehensive logging và monitoring.

### 🔧 Kiến trúc mới:

```
src/
├── core/                          # Domain layer (business logic)
│   ├── entities/                  # Domain entities
│   │   ├── conversation.py        # Conversation, Message, ChatResponse
│   │   ├── document.py           # DocumentChunk, RetrievalResult
│   │   └── form.py               # FormTemplate, FormData
│   ├── interfaces/               # Repository & Service interfaces (ports)
│   │   ├── repositories.py       # ConversationRepository, DocumentRepository
│   │   └── services.py           # EmbeddingService, LLMService, etc.
│   └── use_cases/                # Application business logic
│       └── chat_use_case.py      # Main chat processing logic
│
├── infrastructure/               # Infrastructure layer (adapters)
│   ├── logging/                  # Comprehensive logging system
│   │   ├── config.py            # Logging configuration
│   │   ├── formatters.py        # JSON structured logging
│   │   ├── context.py           # Request correlation IDs
│   │   └── middleware.py        # API request logging
│   ├── repositories/            # Repository implementations
│   │   ├── memory_conversation_repository.py
│   │   ├── weaviate_document_repository.py
│   │   └── memory_template_repository.py
│   └── services/                # Service implementations
│       ├── embedding_service.py
│       ├── llm_service.py
│       ├── intent_classification_service.py
│       ├── reranking_service.py
│       ├── metrics_service.py
│       └── cache_service.py
│
├── application/                  # Application layer
│   ├── config.py                # Centralized configuration
│   ├── dependencies.py          # Dependency injection container
│   └── main.py                  # Application entry point
│
└── api/                         # Presentation layer
    ├── main_new.py              # FastAPI app with clean architecture
    └── routers_new/             # API routers
        ├── chat.py
        ├── sessions.py
        ├── documents.py
        ├── system.py
        └── templates.py
```

## 🚀 Quick Start

### 1. Chạy API mới
```bash
# Development mode
python run_new_api.py --reload

# Production mode
python run_new_api.py --workers 4

# Custom configuration
python run_new_api.py --host 0.0.0.0 --port 8080 --log-level debug
```

### 2. API Endpoints v2.0
- **Base URL**: http://localhost:8000
- **Health**: `GET /health`
- **Docs**: `GET /docs`
- **Chat**: `POST /chat/message`
- **Sessions**: `POST /sessions`, `GET /sessions/{id}`
- **Documents**: `POST /documents/load`, `GET /documents/search`
- **System**: `GET /system/stats`, `GET /system/metrics`
- **Templates**: `GET /templates`, `GET /templates/{name}/fields`

## 📊 Logging & Monitoring

### Structured Logging
Tất cả logs được ghi theo format JSON structured với:
- **Correlation IDs**: Theo dõi request qua toàn bộ system
- **Context tracing**: Session IDs, user IDs
- **Performance metrics**: Request times, memory usage
- **Business metrics**: Intent distribution, form completion rates

### Log Files
```
logs/
├── app.log           # Application logs
├── error.log         # Error logs only
├── api.log           # API request/response logs
└── chat.log          # Chat interaction logs
```

### Metrics Collection
- **Counters**: API requests, chat messages, errors
- **Histograms**: Response times, document search results
- **Gauges**: Active sessions, memory usage, cache hit rates

## 🏗️ Key Improvements

### 1. **Clean Architecture**
- **Separation of concerns**: Domain logic độc lập với infrastructure
- **Dependency inversion**: Interfaces cho all external dependencies
- **Testability**: Easy to unit test business logic

### 2. **Comprehensive Logging**
- **Structured logs**: JSON format cho easy parsing
- **Correlation tracking**: Trace requests across all layers
- **Performance monitoring**: Track all operations
- **Error tracking**: Detailed error context và stack traces

### 3. **Dependency Injection**
- **Container pattern**: Centralized dependency management
- **Interface-based**: Easy to swap implementations
- **Lifecycle management**: Proper startup/shutdown handling

### 4. **Enhanced Monitoring**
- **Health checks**: Multi-level health monitoring
- **Metrics collection**: In-memory metrics với retention
- **Cache monitoring**: Cache hit rates và performance
- **System monitoring**: CPU, memory, disk usage

### 5. **Better Error Handling**
- **Graceful degradation**: System continues on partial failures
- **Detailed error context**: Rich error information for debugging
- **Retry logic**: Built-in retry for transient failures

## 🔧 Configuration

### Environment Variables
```bash
# Required API Keys
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key

# Optional Overrides
WEAVIATE_URL=http://localhost:8080
LOG_LEVEL=INFO
ENVIRONMENT=development
DEVICE=cuda
```

### Advanced Configuration
Chỉnh sửa `src/application/config.py` cho:
- Model parameters
- Timeout settings
- Cache configuration
- Logging levels
- Performance tuning

## 📈 Performance Monitoring

### Request Tracing
Mỗi request có unique correlation ID để trace qua toàn bộ system:
```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "correlation_id": "abc123ef",
  "session_id": "session_456",
  "message": "Chat message processed",
  "intent": "legal",
  "processing_time": 1.234
}
```

### Metrics Endpoints
- `GET /system/metrics` - Application metrics
- `GET /system/stats` - System statistics
- `GET /system/cache` - Cache performance
- `GET /system/health` - Health status

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src

# Run specific test
pytest tests/test_chat_use_case.py
```

### Integration Tests
```bash
# Test API endpoints
pytest tests/test_api_integration.py

# Test with real models
pytest tests/test_models_integration.py
```

## 🔍 Debugging

### Log Analysis
```bash
# View real-time logs
tail -f logs/app.log | jq '.'

# Filter by correlation ID
grep "abc123ef" logs/app.log | jq '.'

# Error logs only
tail -f logs/error.log | jq '.'
```

### Performance Analysis
```bash
# API performance
grep "request_end" logs/api.log | jq '.processing_time'

# Chat performance
grep "Chat message processed" logs/chat.log | jq '.processing_time'
```

## 🚧 Migration từ Old Architecture

### Backward Compatibility
- Old API endpoints vẫn hoạt động
- Gradual migration strategy
- Feature parity maintained

### Migration Steps
1. **Setup new environment**: Test với new API
2. **Validate functionality**: Ensure all features work
3. **Performance testing**: Compare với old system
4. **Switch over**: Update clients to use new endpoints

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **Architecture**: Xem code structure in `src/`
- **Configuration**: `src/application/config.py`
- **Logging**: `src/infrastructure/logging/`

## 🛠️ Development

### Adding New Features
1. **Define entities**: Add to `src/core/entities/`
2. **Create interfaces**: Add to `src/core/interfaces/`
3. **Implement use cases**: Add to `src/core/use_cases/`
4. **Create infrastructure**: Add to `src/infrastructure/`
5. **Add API endpoints**: Add to `src/api/routers_new/`

### Best Practices
- **Domain-first**: Start with entities và use cases
- **Interface-driven**: Define interfaces before implementations
- **Comprehensive logging**: Log all important operations
- **Error handling**: Handle all possible failure cases
- **Testing**: Write tests for all business logic