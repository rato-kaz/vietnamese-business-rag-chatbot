#!/bin/bash

# Vietnamese Business Registration RAG Chatbot API Startup Script

set -e

echo "🚀 Starting Vietnamese Business Registration RAG Chatbot API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys and run again."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port is already in use"
        return 1
    fi
    return 0
}

# Check required ports
echo "🔍 Checking required ports..."
if ! check_port 8000; then
    echo "Please stop the service using port 8000 or use a different port"
    exit 1
fi

if ! check_port 8080; then
    echo "Please stop the service using port 8080 (Weaviate)"
    exit 1
fi

# Start Weaviate first
echo "📦 Starting Weaviate..."
if ! docker ps | grep -q weaviate; then
    docker run -d \
        --name weaviate \
        -p 8080:8080 \
        -e QUERY_DEFAULTS_LIMIT=25 \
        -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
        -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
        -e DEFAULT_VECTORIZER_MODULE=none \
        -e ENABLE_MODULES= \
        -e CLUSTER_HOSTNAME=node1 \
        semitechnologies/weaviate:1.21.2
    
    echo "⏳ Waiting for Weaviate to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
            echo "✅ Weaviate is ready!"
            break
        fi
        echo "⏳ Still waiting... ($i/30)"
        sleep 2
    done
    
    if [ $i -eq 30 ]; then
        echo "❌ Weaviate failed to start"
        exit 1
    fi
else
    echo "✅ Weaviate is already running"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Start API server
echo "🚀 Starting API server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📖 ReDoc Documentation: http://localhost:8000/redoc"
echo ""
echo "🛑 Press Ctrl+C to stop the server"

# Development mode with auto-reload
python run_api.py --reload

echo "👋 API server stopped"