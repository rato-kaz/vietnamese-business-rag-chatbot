# 🚀 Git Setup Guide - Vietnamese Business Registration RAG Chatbot

## 📋 Checklist trước khi push

### ✅ Files đã tạo:
- `.gitignore` - Ignore unnecessary files
- `CHANGELOG.md` - Version history
- `CONTRIBUTING.md` - Development guidelines
- `README.md` - Updated với new architecture
- `README_NEW_ARCHITECTURE.md` - Detailed architecture docs

### ✅ Kiểm tra structure:
```
rag_chatbot/
├── .gitignore
├── .env.example
├── README.md
├── README_NEW_ARCHITECTURE.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── requirements.txt
├── main.py
├── run_api.py
├── run_new_api.py
├── start_all.py
├── start_new_system.py
├── src/
│   ├── core/              # New clean architecture
│   ├── infrastructure/    # Repositories & services  
│   ├── application/       # Config & dependencies
│   └── api/               # Old & new API
├── config/
├── data/
├── templates/
└── logs/                  # Will be ignored
```

## 🔧 Git Setup Commands

### 1. Initialize Git Repository
```bash
# Initialize git (if not already done)
git init

# Check status
git status
```

### 2. Configure Git (if first time)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3. Add Remote Repository
```bash
# Add your GitHub/GitLab repository
git remote add origin https://github.com/yourusername/your-repo-name.git

# Or if using SSH
git remote add origin git@github.com:yourusername/your-repo-name.git

# Verify remote
git remote -v
```

### 4. Initial Commit
```bash
# Add all files
git add .

# Check what will be committed
git status

# Create initial commit
git commit -m "feat: initial commit with clean architecture RAG chatbot

- Complete clean architecture implementation
- Comprehensive logging system with correlation IDs
- Vietnamese business registration chatbot
- RAG with Weaviate, Embedding, and Reranking
- Intent classification (legal, business, general)
- Form collection for business registration
- Both legacy and new architecture support
- Docker deployment ready
- Extensive documentation"

# Push to main branch
git push -u origin main
```

## 🌟 Alternative: Detailed Commit Strategy

Nếu bạn muốn commit theo từng feature:

### Step 1: Core Architecture
```bash
git add src/core/
git commit -m "feat(core): implement clean architecture domain layer

- Add domain entities (Conversation, Message, DocumentChunk, FormTemplate)
- Add repository and service interfaces (ports)
- Add ChatUseCase with comprehensive business logic
- Follow dependency inversion principle"
```

### Step 2: Infrastructure Layer
```bash
git add src/infrastructure/
git commit -m "feat(infrastructure): implement infrastructure adapters

- Add comprehensive logging system with JSON structured format
- Add correlation ID tracking and context management
- Add Weaviate document repository implementation
- Add embedding, LLM, and reranking services
- Add metrics and cache services
- Add memory-based repositories for development"
```

### Step 3: Application Layer
```bash
git add src/application/
git commit -m "feat(application): add application orchestration layer

- Add centralized configuration management
- Add dependency injection container
- Add application lifecycle management
- Support multiple environments (dev, staging, prod)"
```

### Step 4: API Layer
```bash
git add src/api/
git commit -m "feat(api): implement new FastAPI with clean architecture

- Add new API routers using clean architecture
- Add comprehensive request/response logging
- Add health checks and system monitoring
- Maintain backward compatibility with legacy API
- Add structured error handling"
```

### Step 5: Documentation & Scripts
```bash
git add README*.md CHANGELOG.md CONTRIBUTING.md .gitignore
git add start_new_system.py run_new_api.py
git commit -m "docs: add comprehensive documentation and deployment scripts

- Add new architecture documentation
- Add contributing guidelines
- Add changelog with version history
- Add deployment scripts for new architecture
- Add comparison between old and new systems"
```

### Step 6: Configuration & Setup
```bash
git add config/ requirements.txt *.py
git commit -m "feat(config): add configuration and deployment setup

- Update requirements with new dependencies
- Add Docker setup for new architecture
- Add unified startup scripts
- Support both legacy and new architecture modes"
```

### Final Push
```bash
git push origin main
```

## 🔍 Pre-Push Checklist

### ✅ Security Check:
```bash
# Make sure no sensitive data
grep -r "api_key\|password\|secret" . --exclude-dir=.git --exclude="*.md"

# Check .env is ignored
git status --ignored
```

### ✅ File Size Check:
```bash
# Check for large files
find . -size +50M -not -path "./.git/*"

# Check total repo size
du -sh .git
```

### ✅ Test Basic Functionality:
```bash
# Test if Python files are valid
python -m py_compile src/core/entities/conversation.py
python -m py_compile src/api/main_new.py

# Test imports
python -c "from src.application.config import settings; print('✅ Config OK')"
```

## 📝 Recommended Git Tags

After successful push, add version tag:

```bash
# Tag the release
git tag -a v2.0.0 -m "Release v2.0.0: Clean Architecture with Comprehensive Logging

Major Features:
- Clean Architecture implementation
- Comprehensive structured logging
- Vietnamese business registration RAG chatbot
- Dual architecture support (legacy + new)
- Production-ready deployment"

# Push tags
git push origin --tags
```

## 🌐 Create GitHub Repository

### If using GitHub:

1. **Go to GitHub** → New Repository
2. **Repository name**: `vietnamese-business-rag-chatbot`
3. **Description**: `Vietnamese Business Registration RAG Chatbot with Clean Architecture and Comprehensive Logging`
4. **Visibility**: Public/Private (your choice)
5. **Don't initialize** with README (we already have one)
6. **Create repository**

### Repository Settings:
- **Topics**: `vietnamese`, `rag`, `chatbot`, `clean-architecture`, `business-registration`, `llm`, `weaviate`
- **Website**: Your demo URL (if any)
- **License**: MIT (recommended)

## 🚀 Post-Push Steps

### 1. Verify Push Success
```bash
# Check remote repository
git remote show origin

# Verify all files pushed
git ls-tree -r --name-only HEAD
```

### 2. Setup GitHub Actions (Optional)
Create `.github/workflows/ci.yml` for automated testing:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - run: pip install -r requirements.txt
    - run: python -m pytest tests/
```

### 3. Update Repository Description
Add comprehensive README badges and description on GitHub.

## 🎉 Success!

Your Vietnamese Business Registration RAG Chatbot with Clean Architecture is now on Git!

**Repository Structure:**
- ✅ Clean Architecture implementation
- ✅ Comprehensive documentation  
- ✅ Both legacy and new systems
- ✅ Production-ready deployment
- ✅ Extensive logging and monitoring
- ✅ Developer-friendly setup