# Changelog

All notable changes to the Vietnamese Business Registration RAG Chatbot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-01-15

### 🏗️ Major Architecture Refactor

#### Added
- **Clean Architecture**: Complete refactor following Clean Architecture principles
- **Comprehensive Logging**: Structured JSON logging with correlation IDs
- **Dependency Injection**: Container pattern for better testability
- **Metrics Collection**: In-memory metrics with performance tracking
- **Enhanced Error Handling**: Graceful degradation and detailed error context

#### New Core Features
- **Domain Entities**: `Conversation`, `Message`, `DocumentChunk`, `FormTemplate`
- **Use Cases**: Business logic separation in `ChatUseCase`
- **Interfaces**: Repository and Service ports for better abstraction
- **Context Tracing**: Request correlation across all layers

#### Infrastructure Improvements
- **Structured Logging**: JSON format with correlation IDs and context
- **Performance Monitoring**: Request timing and resource usage tracking
- **Cache Service**: In-memory caching with TTL and LRU eviction
- **Metrics Service**: Counters, histograms, and gauges collection

#### API Enhancements
- **New FastAPI Implementation**: Clean architecture-based API
- **Health Checks**: Multi-level health monitoring
- **System Metrics**: Runtime performance insights
- **Backward Compatibility**: Legacy API endpoints maintained

#### Developer Experience
- **Better Error Messages**: Rich error context for debugging
- **Comprehensive Documentation**: Architecture and API documentation
- **Development Tools**: New startup scripts and development helpers
- **Testing Foundation**: Structure for unit and integration tests

### Changed
- **Project Structure**: Reorganized following Clean Architecture
- **Configuration Management**: Centralized settings with environment support
- **Logging Format**: Migrated to structured JSON logging
- **Dependency Management**: Explicit dependency injection

### Deprecated
- Old API endpoints (still functional but marked for deprecation)
- Legacy configuration files

### Technical Details

#### New Directory Structure
```
src/
├── core/                    # Domain layer
│   ├── entities/           # Business entities
│   ├── interfaces/         # Repository & service interfaces
│   └── use_cases/          # Application business logic
├── infrastructure/         # Infrastructure layer
│   ├── logging/           # Comprehensive logging system
│   ├── repositories/      # Repository implementations
│   └── services/          # Service implementations
├── application/           # Application layer
│   ├── config.py         # Centralized configuration
│   └── dependencies.py   # Dependency injection
└── api/                   # Presentation layer
    └── routers_new/       # Clean architecture API routers
```

#### Performance Improvements
- **Request Tracing**: Correlation IDs for request tracking
- **Metrics Collection**: Performance insights and monitoring
- **Caching**: Intelligent caching for better response times
- **Resource Monitoring**: Memory and CPU usage tracking

#### Operational Improvements
- **Health Monitoring**: Comprehensive health checks
- **Error Tracking**: Detailed error context and stack traces
- **Log Management**: Structured logs with rotation
- **System Metrics**: Runtime performance insights

### Migration Guide
- Legacy API endpoints continue to work
- New endpoints available at the same base URL
- Configuration migrated to new centralized system
- Logging output changed to structured format

### Breaking Changes
- None (backward compatibility maintained)

---

## [1.0.0] - 2024-01-10

### Initial Release

#### Added
- **RAG Chatbot**: Vietnamese business registration consultation
- **Intent Classification**: Legal, business, and general intents
- **Document Processing**: Vietnamese legal document chunking
- **Vector Search**: Weaviate-based semantic search
- **Form Collection**: Interactive business registration form filling
- **Web Interface**: Streamlit-based user interface
- **API Backend**: FastAPI REST API
- **Multi-LLM Support**: Groq (Llama) and Gemini integration

#### Core Features
- **Vietnamese Language Support**: Specialized for Vietnamese business law
- **Legal Document RAG**: Search through laws, decrees, and circulars
- **Business Form Generation**: Interactive form collection workflow
- **Conversational Memory**: Session-based conversation tracking
- **Template System**: Business registration document templates

#### Technical Stack
- **Embedding**: bkai-foundation-models/vietnamese-bi-encoder
- **Reranking**: cross-encoder/multilingual-MiniLM-L-12-v2
- **Vector Store**: Weaviate
- **Intent Classification**: Llama via Groq API
- **Main LLM**: Gemini 2.0 Flash
- **Web Framework**: Streamlit + FastAPI

#### Deployment
- **Docker Support**: Docker Compose setup
- **Environment Configuration**: .env based configuration
- **Multiple Run Modes**: Web, API, CLI, and combined modes