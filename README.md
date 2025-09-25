# Vietnamese Business Registration RAG Chatbot

🏢 **Chatbot RAG chuyên tư vấn đăng ký kinh doanh tại Việt Nam**

Hệ thống chatbot thông minh sử dụng công nghệ RAG (Retrieval-Augmented Generation) để tư vấn về luật pháp, quy định và hỗ trợ tạo hồ sơ đăng ký kinh doanh tại Việt Nam.

## ✨ Tính năng chính

### 🎯 Intent Classification (Phân loại ý định)
- **Legal** 🏛️: Trả lời câu hỏi về luật, nghị định, thông tư liên quan đến đăng ký kinh doanh
- **Business** 📋: Hỗ trợ tạo bộ hồ sơ đăng ký kinh doanh bằng cách thu thập thông tin từ user
- **General** 💡: Tư vấn chung về quy trình thành lập doanh nghiệp

### 🧠 AI Models
- **Intent Classifier**: Llama qua Groq API
- **Main LLM**: Gemini 2.0 Flash cho generation
- **Embedding**: `bkai-foundation-models/vietnamese-bi-encoder`
- **Reranking**: `cross-encoder/multilingual-MiniLM-L-12-v2`

### 📚 Knowledge Base
- **Vector Store**: Weaviate local
- **Documents**: Luật, Nghị định, Thông tư, Quyết định về đăng ký kinh doanh
- **Chunking**: Tự động phân chia theo điều, mục trong văn bản pháp luật
- **Metadata**: Trích xuất đầy đủ thông tin như số văn bản, ngày ban hành, cơ quan ban hành

### 💬 Conversational RAG
- **Memory**: Lưu lịch sử hội thoại trong session
- **Context Awareness**: Tham khảo ngữ cảnh câu hỏi trước
- **Form Collection**: Thu thập thông tin step-by-step để tạo hồ sơ

## 🚀 Cài đặt nhanh

### Yêu cầu hệ thống
- Python 3.9+
- Docker
- CUDA (khuyến nghị cho embedding và reranking)
- API Keys: Groq và Gemini

### 1. Setup tự động - Web Interface
```bash
# Clone repository
git clone <repository-url>
cd rag_chatbot

# Copy và cấu hình .env
cp .env.example .env
# Sửa .env với API keys của bạn

# Chạy script setup tự động (Web Interface)
python setup_and_run.py
```

### 2. Setup FastAPI Backend
```bash
# Chạy FastAPI server
python run_api.py --reload

# Hoặc sử dụng script
bash scripts/start_api.sh    # Linux/Mac
scripts\start_api.bat        # Windows

# API sẽ chạy tại: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### 2. Setup thủ công

```bash
# 1. Cài đặt dependencies
pip install -r requirements.txt

# 2. Khởi động Weaviate
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
  -e DEFAULT_VECTORIZER_MODULE=none \
  semitechnologies/weaviate:1.21.2

# 3. Load documents và khởi tạo hệ thống
python main.py --mode setup --load-docs

# 4. Chạy web interface
python main.py --mode web
```

### 3. Sử dụng Docker Compose

#### Web Interface + Weaviate
```bash
# Khởi động toàn bộ hệ thống (Web)
docker-compose up -d

# Xem logs
docker-compose logs -f chatbot
```

#### FastAPI + Weaviate + Redis
```bash
# Khởi động FastAPI backend với full stack
docker-compose -f docker-compose.api.yml up -d

# Xem logs
docker-compose -f docker-compose.api.yml logs -f api
```

## 📁 Cấu trúc thư mục

```
rag_chatbot/
├── src/
│   ├── document_processor.py    # Xử lý văn bản .docx, trích xuất metadata
│   ├── vector_store.py         # Weaviate integration
│   ├── retriever.py           # RAG retrieval với reranking
│   ├── intent_classifier.py   # Phân loại ý định với Llama
│   ├── llm_clients.py         # Groq và Gemini API clients
│   ├── template_parser.py     # Đọc templates form đăng ký
│   ├── chatbot.py            # Main chatbot logic
│   └── web_interface.py      # Streamlit interface
├── data/
│   └── documents/core/       # Văn bản pháp luật (.docx)
├── templates/               # Templates form đăng ký (.docx)
├── config/
│   └── config.yaml         # Cấu hình hệ thống
├── .env                   # API keys
├── main.py               # Entry point (Web/CLI)
├── run_api.py            # FastAPI server runner
├── setup_and_run.py      # Setup script (Web)
├── docker-compose.yml    # Docker setup (Web)
├── docker-compose.api.yml # Docker setup (API)
├── API_DOCUMENTATION.md  # API docs
└── scripts/              # Startup scripts
```

## ⚙️ Cấu hình

### Environment Variables (.env)
```bash
# API Keys
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Weaviate
WEAVIATE_URL=http://localhost:8080

# Models
EMBEDDING_MODEL=bkai-foundation-models/vietnamese-bi-encoder
RERANK_MODEL=cross-encoder/multilingual-MiniLM-L-12-v2
DEVICE=cuda
```

### Config YAML (config/config.yaml)
Cấu hình chi tiết cho:
- Vector store settings
- Model parameters
- Document processing
- Retrieval settings
- Intent classification

## 🎯 Sử dụng

### 1. Web Interface (Streamlit)
1. Mở trình duyệt: `http://localhost:8501`
2. Chat với bot bằng tiếng Việt
3. Hỏi về luật pháp hoặc yêu cầu tạo hồ sơ đăng ký

### 2. FastAPI Backend
1. API Server: `http://localhost:8000`
2. Interactive Docs: `http://localhost:8000/docs`
3. ReDoc: `http://localhost:8000/redoc`

### 3. CLI Interface
```bash
python main.py --mode cli
```

### 4. API Usage
```python
import requests

# Tạo session
session = requests.post("http://localhost:8000/sessions").json()
session_id = session["session_id"]

# Gửi message
response = requests.post("http://localhost:8000/chat/message", json={
    "message": "Điều 15 Luật Doanh nghiệp quy định gì?",
    "session_id": session_id
})
print(response.json())
```

### Ví dụ câu hỏi

**Legal Intent:**
- "Điều 15 Luật Doanh nghiệp quy định gì về vốn điều lệ?"
- "Thông tư 02/2023 có hiệu lực từ khi nào?"

**Business Intent:**
- "Tôi muốn tạo hồ sơ đăng ký công ty"
- "Hãy giúp tôi lập đơn đăng ký kinh doanh"

**General Intent:**
- "Quy trình thành lập công ty như thế nào?"
- "Cần chuẩn bị gì để mở công ty?"

## 📊 Metadata Schema

Hệ thống tự động trích xuất metadata từ văn bản:

```json
{
    "source": "file.docx",
    "document_number": "130/2017/TT-BTC",
    "document_type": "Thông tư",
    "document_title": "Tiêu đề văn bản",
    "issue_date": "04/12/2017",
    "issuing_agency": "Bộ Tài chính",
    "effective_date": "20/01/2018",
    "article_code": "Điều 1",
    "khoan_code": "1.",
    "chunk_title": "Điều 1 - 1."
}
```

## 🔧 Development

### Thêm documents
```python
from src.chatbot import ConversationalRAGChatbot

chatbot = ConversationalRAGChatbot()
chatbot.add_documents_to_knowledge_base("path/to/documents")
```

### Xem thống kê
```python
stats = chatbot.get_system_stats()
print(stats)
```

## 🐛 Troubleshooting

### Weaviate không khởi động
```bash
# Kiểm tra Docker
docker ps

# Restart Weaviate
docker restart weaviate

# Xem logs
docker logs weaviate
```

### CUDA issues
```bash
# Kiểm tra CUDA
nvidia-smi

# Chuyển về CPU trong config.yaml
device: "cpu"
```

### API errors
- Kiểm tra API keys trong .env
- Verify quota limits của Groq và Gemini

## 📄 License

MIT License

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Submit pull request

## 📋 Quick Commands

### 🆕 New Clean Architecture (Recommended)
```bash
# Chạy API với clean architecture
python start_new_system.py --mode new --reload

# Setup và chạy hệ thống mới
python start_new_system.py --mode new --setup

# So sánh cả 2 architectures
python start_new_system.py --mode both --reload
```

### 🔄 Legacy Commands
```bash
# Chạy cả Web + API (old)
python start_all.py --mode both

# Chỉ chạy Web Interface  
python start_all.py --mode web

# Chỉ chạy FastAPI Backend (old)
python start_all.py --mode api --reload

# Với Docker
docker-compose -f docker-compose.api.yml up -d  # API + Weaviate + Redis
docker-compose up -d                            # Web + Weaviate
```

## 📖 Documentation

- **🆕 New Architecture**: [README_NEW_ARCHITECTURE.md](README_NEW_ARCHITECTURE.md)
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **System Config**: `config/config.yaml`

## 🔄 Architecture

### 🆕 New Clean Architecture
```
┌─────────────────────────────────────┐
│           Presentation Layer        │
│  ┌─────────────┐  ┌─────────────┐   │
│  │   Web UI    │  │  FastAPI    │   │
│  │  :8501      │  │  :8000      │   │
│  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────┘
                    │
┌─────────────────────────────────────┐
│          Application Layer          │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ Use Cases   │  │Dependencies │   │
│  │             │  │Container    │   │
│  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────┘
                    │
┌─────────────────────────────────────┐
│            Core Domain              │
│  ┌─────────────┐  ┌─────────────┐   │
│  │  Entities   │  │ Interfaces  │   │
│  │             │  │   (Ports)   │   │
│  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────┘
                    │
┌─────────────────────────────────────┐
│        Infrastructure Layer        │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ Repositories│  │  Services   │   │
│  │  Weaviate   │  │ LLM/Embed   │   │
│  │  Memory     │  │ Logging     │   │
│  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────┘
```

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: README.md + API_DOCUMENTATION.md
- **Config**: config/config.yaml comments
- **API Schema**: http://localhost:8000/openapi.json