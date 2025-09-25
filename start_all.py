#!/usr/bin/env python3
"""
Unified starter for Vietnamese Business Registration RAG Chatbot.
Supports both Web Interface and FastAPI Backend.
"""

import os
import sys
import argparse
import subprocess
import threading
import time
from dotenv import load_dotenv

def main():
    """Main function to start the chatbot system."""
    parser = argparse.ArgumentParser(description="Vietnamese Business Registration RAG Chatbot - Unified Starter")
    parser.add_argument("--mode", choices=["web", "api", "both", "setup"], default="both",
                       help="Run mode: web interface, FastAPI, both, or setup")
    parser.add_argument("--api-port", type=int, default=8000, help="FastAPI port")
    parser.add_argument("--web-port", type=int, default=8501, help="Streamlit port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--load-docs", action="store_true", help="Load documents on startup")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_env_vars = ["GROQ_API_KEY", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        return 1
    
    print("🏢 Vietnamese Business Registration RAG Chatbot")
    print("=" * 55)
    
    if args.mode == "setup":
        return run_setup(args.load_docs)
    elif args.mode == "web":
        return run_web_only(args.web_port, args.load_docs)
    elif args.mode == "api":
        return run_api_only(args.api_port, args.reload, args.load_docs)
    elif args.mode == "both":
        return run_both(args.api_port, args.web_port, args.reload, args.load_docs)
    
    return 0


def run_setup(load_docs: bool):
    """Run setup process."""
    print("🔧 Running system setup...")
    
    try:
        cmd = [sys.executable, "setup_and_run.py"]
        if not load_docs:
            # Just run setup without auto-starting
            cmd = [sys.executable, "main.py", "--mode", "setup"]
            if load_docs:
                cmd.append("--load-docs")
        
        result = subprocess.run(cmd)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n👋 Setup interrupted")
        return 0


def run_web_only(port: int, load_docs: bool):
    """Run only web interface."""
    print(f"🌐 Starting Web Interface on port {port}...")
    
    try:
        # Set port environment variable for Streamlit
        os.environ["STREAMLIT_SERVER_PORT"] = str(port)
        
        cmd = [sys.executable, "main.py", "--mode", "web"]
        if load_docs:
            cmd.append("--load-docs")
        
        subprocess.run(cmd)
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped")
        return 0


def run_api_only(port: int, reload: bool, load_docs: bool):
    """Run only FastAPI backend."""
    print(f"🚀 Starting FastAPI Backend on port {port}...")
    
    try:
        cmd = [sys.executable, "run_api.py", "--port", str(port)]
        if reload:
            cmd.append("--reload")
        
        # Start API server
        api_process = subprocess.Popen(cmd)
        
        # Wait a bit for API to start
        time.sleep(3)
        
        # Load documents if requested
        if load_docs:
            print("📚 Loading documents...")
            import requests
            try:
                response = requests.post(f"http://localhost:{port}/documents/load")
                if response.status_code == 200:
                    print("✅ Documents loading started")
                else:
                    print("❌ Failed to start document loading")
            except Exception as e:
                print(f"❌ Error loading documents: {e}")
        
        # Wait for API process
        api_process.wait()
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
        return 0


def run_both(api_port: int, web_port: int, reload: bool, load_docs: bool):
    """Run both FastAPI and Web Interface."""
    print(f"🚀 Starting FastAPI Backend on port {api_port}...")
    print(f"🌐 Starting Web Interface on port {web_port}...")
    print("\nServices will be available at:")
    print(f"  - FastAPI: http://localhost:{api_port}")
    print(f"  - API Docs: http://localhost:{api_port}/docs")
    print(f"  - Web Interface: http://localhost:{web_port}")
    print("\n🛑 Press Ctrl+C to stop all services")
    
    processes = []
    
    try:
        # Start FastAPI
        api_cmd = [sys.executable, "run_api.py", "--port", str(api_port)]
        if reload:
            api_cmd.append("--reload")
        
        api_process = subprocess.Popen(api_cmd)
        processes.append(("FastAPI", api_process))
        
        # Wait for API to start
        print("⏳ Waiting for FastAPI to start...")
        time.sleep(5)
        
        # Load documents if requested
        if load_docs:
            print("📚 Loading documents...")
            import requests
            try:
                response = requests.post(f"http://localhost:{api_port}/documents/load")
                if response.status_code == 200:
                    print("✅ Documents loading started")
                else:
                    print("❌ Failed to start document loading")
            except Exception as e:
                print(f"❌ Error loading documents: {e}")
        
        # Start Web Interface
        os.environ["STREAMLIT_SERVER_PORT"] = str(web_port)
        web_cmd = [sys.executable, "main.py", "--mode", "web"]
        
        web_process = subprocess.Popen(web_cmd)
        processes.append(("Web Interface", web_process))
        
        print("✅ Both services started successfully!")
        print("\nMonitoring services... Press Ctrl+C to stop all")
        
        # Monitor processes
        while True:
            time.sleep(1)
            for name, process in processes:
                if process.poll() is not None:
                    print(f"❌ {name} stopped unexpectedly")
                    return 1
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        
        # Terminate all processes
        for name, process in processes:
            try:
                process.terminate()
                print(f"🛑 Stopped {name}")
            except:
                pass
        
        # Wait for processes to finish
        for name, process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔪 Force killed {name}")
        
        print("👋 All services stopped")
        return 0
    
    except Exception as e:
        print(f"❌ Error running services: {e}")
        
        # Clean up processes
        for name, process in processes:
            try:
                process.terminate()
            except:
                pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())