#!/usr/bin/env python3
"""
Main entry point for the Vietnamese Business Registration RAG Chatbot.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.web_interface import main as run_web_interface
from src.chatbot import ConversationalRAGChatbot


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Vietnamese Business Registration RAG Chatbot")
    parser.add_argument("--mode", choices=["web", "cli", "setup"], default="web",
                       help="Run mode: web interface, CLI, or setup")
    parser.add_argument("--load-docs", action="store_true",
                       help="Load documents into knowledge base")
    parser.add_argument("--config", default="config/config.yaml",
                       help="Path to configuration file")
    
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
    
    if args.mode == "web":
        print("🚀 Starting web interface...")
        run_web_interface()
    
    elif args.mode == "cli":
        print("💬 Starting CLI interface...")
        run_cli_interface(args.config, args.load_docs)
    
    elif args.mode == "setup":
        print("⚙️ Running setup...")
        run_setup(args.config, args.load_docs)
    
    return 0


def run_cli_interface(config_path: str, load_docs: bool):
    """Run CLI interface."""
    try:
        # Initialize chatbot
        print("Initializing chatbot...")
        chatbot = ConversationalRAGChatbot(config_path)
        
        # Load documents if requested
        if load_docs:
            print("Loading documents...")
            success = chatbot.add_documents_to_knowledge_base("data/documents/core")
            if success:
                print("✅ Documents loaded successfully!")
            else:
                print("❌ Failed to load documents")
        
        print("\n" + "="*50)
        print("🏢 Vietnamese Business Registration Chatbot")
        print("Type 'quit', 'exit', or 'bye' to exit")
        print("Type 'clear' to clear conversation history")
        print("Type 'stats' to see system statistics")
        print("="*50 + "\n")
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'clear':
                    chatbot.clear_conversation()
                    print("🗑️ Conversation cleared!")
                    continue
                
                elif user_input.lower() == 'stats':
                    stats = chatbot.get_system_stats()
                    print("\n📊 System Statistics:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                    print()
                    continue
                
                elif not user_input:
                    continue
                
                # Process message
                print("🤖 Bot: ", end="", flush=True)
                response = chatbot.process_message(user_input)
                
                print(response["message"])
                
                # Show intent and sources
                intent_emoji = {"legal": "🏛️", "business": "📋", "general": "💡"}.get(response["intent"], "❓")
                print(f"\n{intent_emoji} Intent: {response['intent']}")
                
                if response.get("sources"):
                    print("📚 Sources:")
                    for i, source in enumerate(response["sources"][:3], 1):
                        source_info = []
                        if source.get('document_type'):
                            source_info.append(source['document_type'])
                        if source.get('document_number'):
                            source_info.append(source['document_number'])
                        if source.get('chunk_title'):
                            source_info.append(source['chunk_title'])
                        
                        source_str = " - ".join(source_info) if source_info else f"Document {i}"
                        print(f"  {i}. {source_str}")
                
                if response.get("form_active"):
                    print("📝 Form collection active")
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return 1


def run_setup(config_path: str, load_docs: bool):
    """Run setup process."""
    print("🔧 Setting up Vietnamese Business Registration Chatbot...")
    
    try:
        # Initialize chatbot
        chatbot = ConversationalRAGChatbot(config_path)
        print("✅ Chatbot initialized")
        
        # Load documents
        if load_docs:
            print("📚 Loading documents into knowledge base...")
            success = chatbot.add_documents_to_knowledge_base("data/documents/core")
            if success:
                print("✅ Documents loaded successfully!")
            else:
                print("❌ Failed to load documents")
        
        # Test system
        print("🧪 Testing system...")
        test_response = chatbot.process_message("Xin chào!")
        if test_response:
            print("✅ System test passed")
        
        # Show statistics
        stats = chatbot.get_system_stats()
        print("\n📊 System Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Make sure Weaviate is running: docker run -p 8080:8080 --name weaviate semitechnologies/weaviate:latest")
        print("2. Run the web interface: python main.py --mode web")
        print("3. Or run CLI: python main.py --mode cli")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())