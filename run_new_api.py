#!/usr/bin/env python3
"""
New FastAPI server runner using clean architecture.
"""

import os
import sys
import argparse
import uvicorn
from dotenv import load_dotenv

def main():
    """Main function to run new FastAPI server."""
    parser = argparse.ArgumentParser(description="Vietnamese Business Registration RAG Chatbot API v2.0")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--log-level", default="info", help="Log level")
    parser.add_argument("--env", default=".env", help="Environment file path")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(args.env)
    
    # Check required environment variables
    required_env_vars = ["GROQ_API_KEY", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in your .env file")
        return 1
    
    print("🚀 Starting Vietnamese Business Registration RAG Chatbot API v2.0...")
    print("🏗️ Using Clean Architecture with comprehensive logging")
    print(f"📍 Server will be available at: http://{args.host}:{args.port}")
    print(f"📚 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"📖 ReDoc Documentation: http://{args.host}:{args.port}/redoc")
    
    # Configuration for uvicorn
    config = {
        "app": "src.api.main_new:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "reload": args.reload,
    }
    
    # Add workers only for production (not with reload)
    if not args.reload and args.workers > 1:
        config["workers"] = args.workers
    
    try:
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n👋 Shutting down API server...")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())