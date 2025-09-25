#!/usr/bin/env python3
"""
Unified starter for Vietnamese Business Registration RAG Chatbot - New Architecture.
Supports both old and new architecture modes.
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
    parser = argparse.ArgumentParser(description="Vietnamese Business Registration RAG Chatbot - New Architecture")
    parser.add_argument("--mode", choices=["old", "new", "both"], default="new",
                       help="Architecture mode: old (legacy), new (clean architecture), both")
    parser.add_argument("--api-port", type=int, default=8000, help="API port")
    parser.add_argument("--web-port", type=int, default=8501, help="Web interface port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--load-docs", action="store_true", help="Load documents on startup")
    parser.add_argument("--setup", action="store_true", help="Run setup first")
    
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
    print("🏗️ New Clean Architecture with Comprehensive Logging")
    print("=" * 60)
    
    if args.setup:
        print("🔧 Running initial setup...")
        setup_result = run_setup()
        if setup_result != 0:
            print("❌ Setup failed")
            return setup_result
    
    if args.mode == "old":
        return run_old_architecture(args)
    elif args.mode == "new":
        return run_new_architecture(args)
    elif args.mode == "both":
        return run_both_architectures(args)
    
    return 0


def run_setup():
    """Run initial setup."""
    try:
        # Check if Weaviate is running
        import requests
        try:
            response = requests.get("http://localhost:8080/v1/.well-known/ready", timeout=5)
            if response.status_code == 200:
                print("✅ Weaviate is already running")
            else:
                print("⚠️ Weaviate is not ready")
        except requests.exceptions.RequestException:
            print("🚀 Starting Weaviate...")
            start_weaviate()
        
        return 0
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return 1


def start_weaviate():
    """Start Weaviate using Docker."""
    try:
        # Check if container exists
        result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=weaviate', '--format', '{{.Names}}'], 
                              capture_output=True, text=True)
        
        if 'weaviate' in result.stdout:
            print("📦 Starting existing Weaviate container...")
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
            subprocess.run(cmd, check=True)
        
        # Wait for Weaviate to be ready
        print("⏳ Waiting for Weaviate to be ready...")
        import requests
        for i in range(30):
            try:
                response = requests.get('http://localhost:8080/v1/.well-known/ready', timeout=5)
                if response.status_code == 200:
                    print("✅ Weaviate is ready!")
                    return
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            print(f"⏳ Still waiting... ({i+1}/30)")
        
        print("❌ Weaviate failed to start in time")
        
    except Exception as e:
        print(f"❌ Failed to start Weaviate: {e}")


def run_old_architecture(args):
    """Run old architecture."""
    print(f"🔄 Starting OLD architecture API on port {args.api_port}...")
    
    try:
        cmd = [sys.executable, "run_api.py", "--port", str(args.api_port)]
        if args.reload:
            cmd.append("--reload")
        
        subprocess.run(cmd)
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Old architecture stopped")
        return 0


def run_new_architecture(args):
    """Run new clean architecture."""
    print(f"🆕 Starting NEW clean architecture API on port {args.api_port}...")
    
    try:
        cmd = [sys.executable, "run_new_api.py", "--port", str(args.api_port)]
        if args.reload:
            cmd.append("--reload")
        
        subprocess.run(cmd)
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 New architecture stopped")
        return 0


def run_both_architectures(args):
    """Run both architectures for comparison."""
    old_port = args.api_port
    new_port = args.api_port + 1
    
    print(f"🔄 Starting OLD architecture API on port {old_port}...")
    print(f"🆕 Starting NEW architecture API on port {new_port}...")
    print("\nServices will be available at:")
    print(f"  - OLD API: http://localhost:{old_port}")
    print(f"  - NEW API: http://localhost:{new_port}")
    print(f"  - OLD Docs: http://localhost:{old_port}/docs")
    print(f"  - NEW Docs: http://localhost:{new_port}/docs")
    print("\n🛑 Press Ctrl+C to stop all services")
    
    processes = []
    
    try:
        # Start old architecture
        old_cmd = [sys.executable, "run_api.py", "--port", str(old_port)]
        if args.reload:
            old_cmd.append("--reload")
        
        old_process = subprocess.Popen(old_cmd)
        processes.append(("OLD API", old_process))
        
        # Wait a bit
        time.sleep(3)
        
        # Start new architecture
        new_cmd = [sys.executable, "run_new_api.py", "--port", str(new_port)]
        if args.reload:
            new_cmd.append("--reload")
        
        new_process = subprocess.Popen(new_cmd)
        processes.append(("NEW API", new_process))
        
        print("✅ Both architectures started successfully!")
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
    print("🚀 Vietnamese Business Registration RAG Chatbot")
    print("🏗️ Clean Architecture Starter")
    print()
    
    # Show usage examples
    print("Usage examples:")
    print("  python start_new_system.py --mode new --reload")
    print("  python start_new_system.py --mode both --setup")
    print("  python start_new_system.py --mode old --api-port 8001")
    print()
    
    sys.exit(main())