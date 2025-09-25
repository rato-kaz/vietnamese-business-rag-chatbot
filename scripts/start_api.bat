@echo off
echo Starting Vietnamese Business Registration RAG Chatbot API...
echo.

REM Check if .env file exists
if not exist .env (
    echo .env file not found. Creating from template...
    copy .env.example .env
    echo.
    echo Please edit .env file with your API keys and run again.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

REM Start Weaviate
echo Starting Weaviate...
docker ps | findstr weaviate >nul
if errorlevel 1 (
    docker run -d --name weaviate -p 8080:8080 -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true -e PERSISTENCE_DATA_PATH=/var/lib/weaviate -e DEFAULT_VECTORIZER_MODULE=none semitechnologies/weaviate:1.21.2
    
    echo Waiting for Weaviate to be ready...
    timeout /t 10
) else (
    echo Weaviate is already running
)

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Start API server
echo.
echo Starting API server...
echo API will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python run_api.py --reload

pause