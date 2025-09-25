# Vietnamese Business Registration RAG Chatbot API

## 🚀 FastAPI Backend Documentation

### API Overview
RESTful API backend cho hệ thống RAG Chatbot tư vấn đăng ký kinh doanh tại Việt Nam.

**Base URL**: `http://localhost:8000`  
**API Documentation**: `http://localhost:8000/docs`  
**ReDoc**: `http://localhost:8000/redoc`

---

## 🏃‍♂️ Quick Start

### 1. Chạy API Server
```bash
# Development mode với auto-reload
python run_api.py --reload

# Production mode
python run_api.py --workers 4

# Custom host và port
python run_api.py --host 0.0.0.0 --port 8080
```

### 2. Test API
```bash
# Health check
curl http://localhost:8000/health

# Tạo session mới
curl -X POST http://localhost:8000/sessions

# Gửi message
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Xin chào", "session_id": "your-session-id"}'
```

---

## 📋 API Endpoints

### 🏥 Health & System

#### `GET /health`
Health check endpoint
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "1.0.0"
}
```

#### `GET /system/stats`
Thống kê hệ thống
```json
{
  "active_sessions": 5,
  "total_documents": 150,
  "available_templates": 5,
  "system_uptime": "2h 30m",
  "memory_usage": "45% (2GB / 8GB)"
}
```

#### `GET /system/info`
Thông tin chi tiết hệ thống

#### `GET /system/models`
Thông tin các models đã load

---

### 💬 Chat Endpoints

#### `POST /chat/message`
Gửi message đến chatbot
```json
{
  "message": "Điều 15 Luật Doanh nghiệp quy định gì?",
  "session_id": "session_123",
  "context": "optional context"
}
```

**Response:**
```json
{
  "session_id": "session_123",
  "message": "Theo Điều 15 Luật Doanh nghiệp...",
  "intent": "legal",
  "sources": [
    {
      "document_type": "Luật",
      "document_number": "68/2014/QH13",
      "chunk_title": "Điều 15",
      "score": 0.95
    }
  ],
  "form_active": false,
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `POST /chat/stream`
Stream response cho real-time experience

#### `POST /chat/batch`
Xử lý nhiều messages cùng lúc

#### `GET /chat/suggestions`
Lấy gợi ý câu hỏi
- Query params: `session_id`

#### `POST /chat/export`
Export lịch sử hội thoại
- Query params: `session_id`, `format` (json/text)

#### `POST /chat/feedback`
Gửi feedback cho response

---

### 🔐 Session Management

#### `POST /sessions`
Tạo session mới
```json
{
  "session_id": "uuid-string",
  "created_at": "2024-01-15T10:30:00",
  "status": "active"
}
```

#### `GET /sessions/{session_id}`
Thông tin session

#### `DELETE /sessions/{session_id}`
Xóa session

#### `POST /sessions/{session_id}/clear`
Xóa lịch sử chat

#### `GET /sessions/{session_id}/history`
Lấy lịch sử chat
- Query params: `limit`, `offset`

#### `GET /sessions/{session_id}/stats`
Thống kê session

#### `POST /sessions/{session_id}/reset`
Reset session hoàn toàn

#### `GET /sessions`
List tất cả sessions active

---

### 📚 Document Management

#### `POST /documents/load`
Load documents vào knowledge base

#### `GET /documents/stats`
Thống kê documents
```json
{
  "total_documents": 150,
  "embedding_model": "bkai-foundation-models/vietnamese-bi-encoder",
  "reranker_model": "cross-encoder/multilingual-MiniLM-L-12-v2",
  "collection_name": "LegalDocuments"
}
```

#### `POST /documents/upload`
Upload documents mới
- Body: multipart/form-data với files

#### `GET /documents/search`
Tìm kiếm documents
- Query params: `query`, `top_k`

#### `DELETE /documents/clear`
Xóa tất cả documents

#### `GET /documents/types`
Các loại documents có sẵn

#### `GET /documents/agencies`
Các cơ quan ban hành

---

### 📋 Template Management

#### `GET /templates`
List tất cả templates
```json
[
  {
    "name": "danh_sach_chu_so_huu.docx",
    "display_name": "Danh Sách Chủ Sở Hữu",
    "field_count": 5,
    "required_fields": 4
  }
]
```

#### `GET /templates/{template_name}`
Thông tin chi tiết template

#### `GET /templates/{template_name}/fields`
Danh sách fields của template
```json
[
  {
    "field_name": "chu_so_huu_ho_ten",
    "display_name": "Họ và tên chủ sở hữu",
    "field_type": "text",
    "required": true,
    "description": "Họ và tên đầy đủ của chủ sở hữu công ty"
  }
]
```

#### `GET /templates/{template_name}/questions`
Câu hỏi form collection

#### `POST /templates/{template_name}/validate`
Validate dữ liệu với template

#### `POST /templates/{template_name}/generate`
Generate document từ template

---

### 🎯 Intent Classification

#### `POST /classify-intent`
Phân loại ý định
```json
{
  "text": "Tôi muốn tạo hồ sơ đăng ký công ty",
  "context": "optional"
}
```

**Response:**
```json
{
  "intent": "business",
  "description": "Yêu cầu hỗ trợ tạo hồ sơ...",
  "confidence": 0.95
}
```

---

## 🔧 Configuration

### Environment Variables
```bash
# API Keys
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

# Weaviate
WEAVIATE_URL=http://localhost:8080

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

### Custom Settings
Chỉnh sửa `src/api/config.py` cho các cấu hình nâng cao.

---

## 🧪 Testing

### Chạy Tests
```bash
# Chạy tất cả tests
pytest tests/

# Chạy tests với coverage
pytest tests/ --cov=src/api

# Chạy test cụ thể
pytest tests/test_api.py::test_chat_message
```

### Manual Testing
```bash
# Test với curl
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Xin chào", "session_id": "test-123"}'

# Test với Python requests
import requests

response = requests.post(
    "http://localhost:8000/chat/message",
    json={"message": "Xin chào", "session_id": "test-123"}
)
print(response.json())
```

---

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t rag-chatbot-api .

# Run container
docker run -p 8000:8000 rag-chatbot-api

# With Docker Compose
docker-compose up -d
```

### Production Deployment
```bash
# Với Gunicorn
gunicorn src.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# Với systemd service
sudo systemctl start rag-chatbot-api
```

---

## 📊 Monitoring

### Metrics Endpoints
- `/system/health` - Health check
- `/system/stats` - System statistics
- `/system/info` - Detailed system info
- `/system/logs` - Application logs

### Request Headers
- `X-Request-ID` - Unique request identifier
- `X-Process-Time` - Request processing time
- `X-RateLimit-*` - Rate limiting info

---

## 🐛 Troubleshooting

### Common Issues

**API không start được:**
```bash
# Kiểm tra port có bị chiếm không
netstat -tulpn | grep 8000

# Kiểm tra environment variables
env | grep -E "(GROQ|GEMINI)_API_KEY"
```

**Weaviate connection error:**
```bash
# Kiểm tra Weaviate đang chạy
curl http://localhost:8080/v1/.well-known/ready

# Restart Weaviate
docker restart weaviate
```

**Memory issues:**
```bash
# Kiểm tra memory usage
curl http://localhost:8000/system/info

# Force garbage collection
curl -X POST http://localhost:8000/system/gc
```

---

## 🔐 Security

### Rate Limiting
- 100 requests per hour per IP
- Headers: `X-RateLimit-*`

### Input Validation
- Tất cả input được validate với Pydantic
- File upload bị giới hạn kích thước và type

### Error Handling
- Không expose sensitive information
- Consistent error response format

---

## 📈 Performance

### Optimizations
- Async/await cho tất cả I/O operations
- Connection pooling cho Weaviate
- Background tasks cho heavy operations
- Caching cho static data

### Scaling
- Horizontal scaling với multiple workers
- Session management với Redis (future)
- Load balancing support

---

## 🤝 Integration Examples

### JavaScript/React
```javascript
const response = await fetch('http://localhost:8000/chat/message', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: 'Xin chào',
    session_id: sessionId
  })
});
```

### Python Client
```python
import requests

class ChatbotClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session_id = self.create_session()
    
    def create_session(self):
        response = requests.post(f"{self.base_url}/sessions")
        return response.json()["session_id"]
    
    def send_message(self, message):
        response = requests.post(
            f"{self.base_url}/chat/message",
            json={"message": message, "session_id": self.session_id}
        )
        return response.json()
```

---

## 📚 API Schema

Xem chi tiết API schema tại:
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`
- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`