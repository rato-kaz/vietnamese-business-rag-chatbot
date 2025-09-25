#!/usr/bin/env python3
"""
Setup and run script for Vietnamese Business Registration RAG Chatbot.
This script handles the complete setup process including Weaviate and document loading.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path


def check_docker():
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is installed")
            return True
        else:
            print("❌ Docker is not installed")
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed")
        return False


def start_weaviate():
    """Start Weaviate using Docker."""
    print("🚀 Starting Weaviate...")
    
    # Check if Weaviate container already exists
    result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=weaviate', '--format', '{{.Names}}'], 
                          capture_output=True, text=True)
    
    if 'weaviate' in result.stdout:
        print("📦 Weaviate container exists, starting...")
        subprocess.run(['docker', 'start', 'weaviate'])
    else:
        print("📦 Creating new Weaviate container...")
        cmd = [
            'docker', 'run', '-d',
            '--name', 'weaviate',
            '-p', '8080:8080',
            '-e', 'QUERY_DEFAULTS_LIMIT=25',
            '-e', 'AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true',
            '-e', 'PERSISTENCE_DATA_PATH=/var/lib/weaviate',
            '-e', 'DEFAULT_VECTORIZER_MODULE=none',
            '-e', 'ENABLE_MODULES=',
            '-e', 'CLUSTER_HOSTNAME=node1',
            'semitechnologies/weaviate:1.21.2'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to start Weaviate: {result.stderr}")
            return False
    
    # Wait for Weaviate to be ready
    print("⏳ Waiting for Weaviate to be ready...")
    for i in range(30):
        try:
            response = requests.get('http://localhost:8080/v1/.well-known/ready', timeout=5)
            if response.status_code == 200:
                print("✅ Weaviate is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(2)
        print(f"⏳ Still waiting... ({i+1}/30)")
    
    print("❌ Weaviate failed to start or is not responding")
    return False


def install_requirements():
    """Install Python requirements."""
    print("📦 Installing Python requirements...")
    
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Requirements installed successfully")
            return True
        else:
            print(f"❌ Failed to install requirements: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing requirements: {e}")
        return False


def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please copy .env.example to .env and fill in your API keys:")
        print("  cp .env.example .env")
        print("  # Edit .env file with your GROQ_API_KEY and GEMINI_API_KEY")
        return False
    
    # Check if required variables are set
    required_vars = ['GROQ_API_KEY', 'GEMINI_API_KEY']
    missing_vars = []
    
    with open(env_file, 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=your_" in content or f"{var}=" not in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or invalid API keys in .env: {', '.join(missing_vars)}")
        print("Please update your .env file with valid API keys")
        return False
    
    print("✅ .env file is properly configured")
    return True


def load_documents():
    """Load documents into the knowledge base."""
    print("📚 Loading documents into knowledge base...")
    
    try:
        result = subprocess.run([sys.executable, 'main.py', '--mode', 'setup', '--load-docs'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Documents loaded successfully")
            print(result.stdout)
            return True
        else:
            print(f"❌ Failed to load documents: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error loading documents: {e}")
        return False


def start_web_interface():
    """Start the web interface."""
    print("🌐 Starting web interface...")
    print("📌 Open your browser and go to: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([sys.executable, 'main.py', '--mode', 'web'])
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")


def main():
    """Main setup and run function."""
    print("🏢 Vietnamese Business Registration RAG Chatbot Setup")
    print("=" * 55)
    
    # Step 1: Check Docker
    if not check_docker():
        print("\n❌ Setup failed: Docker is required")
        print("Please install Docker and try again")
        return 1
    
    # Step 2: Check .env file
    if not check_env_file():
        print("\n❌ Setup failed: .env file configuration required")
        return 1
    
    # Step 3: Install requirements
    if not install_requirements():
        print("\n❌ Setup failed: Could not install requirements")
        return 1
    
    # Step 4: Start Weaviate
    if not start_weaviate():
        print("\n❌ Setup failed: Could not start Weaviate")
        return 1
    
    # Step 5: Load documents
    if not load_documents():
        print("\n⚠️ Warning: Could not load documents")
        print("You can try loading them later from the web interface")
    
    print("\n🎉 Setup completed successfully!")
    print("\n" + "=" * 55)
    
    # Step 6: Start web interface
    start_web_interface()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())