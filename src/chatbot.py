import yaml
from typing import Dict, List, Any, Optional, Tuple
from .intent_classifier import IntentClassifier
from .llm_clients import LLMManager
from .retriever import EnhancedRetriever
from .template_parser import TemplateParser
from .document_processor import DocumentProcessor


class ConversationalRAGChatbot:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the conversational RAG chatbot."""
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize components
        self.intent_classifier = IntentClassifier(config_path)
        self.llm_manager = LLMManager(config_path)
        self.retriever = EnhancedRetriever(config_path)
        self.template_parser = TemplateParser()
        self.document_processor = DocumentProcessor(config_path)
        
        # Conversation state
        self.conversation_history = []
        self.current_intent = None
        self.form_collection_state = {
            "active": False,
            "current_field_index": 0,
            "collected_data": {},
            "questions": []
        }
        
        # Initialize the system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the chatbot system."""
        print("Initializing Vietnamese Business Registration Chatbot...")
        
        # Load form questions for business intent
        self.form_collection_state["questions"] = self.template_parser.generate_form_collection_questions()
        
        print(f"Loaded {len(self.form_collection_state['questions'])} form fields")
        print("Chatbot initialized successfully!")
    
    def process_message(self, user_input: str) -> Dict[str, Any]:
        """
        Process user message and return response.
        
        Args:
            user_input: User's input message
            
        Returns:
            Dictionary containing response and metadata
        """
        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": self._get_timestamp()
        })
        
        # Check if we're in form collection mode
        if self.form_collection_state["active"]:
            return self._handle_form_collection(user_input)
        
        # Classify intent
        conversation_context = self._get_conversation_context()
        intent_result = self.intent_classifier.classify_with_confidence(
            user_input, 
            conversation_context
        )
        
        self.current_intent = intent_result["intent"]
        
        # Process based on intent
        if self.current_intent == "legal":
            response = self._handle_legal_question(user_input, conversation_context)
        elif self.current_intent == "business":
            response = self._handle_business_request(user_input)
        else:  # general
            response = self._handle_general_question(user_input, conversation_context)
        
        # Add bot response to conversation history
        self.conversation_history.append({
            "role": "assistant",
            "content": response["message"],
            "intent": self.current_intent,
            "timestamp": self._get_timestamp()
        })
        
        return response
    
    def _handle_legal_question(self, user_input: str, conversation_context: str) -> Dict[str, Any]:
        """Handle legal questions with RAG."""
        # Retrieve relevant documents
        retrieved_docs = self.retriever.retrieve_for_intent(
            user_input, 
            "legal", 
            conversation_context
        )
        
        if not retrieved_docs:
            message = """Xin lỗi, tôi không tìm thấy thông tin pháp luật liên quan đến câu hỏi của bạn. 
Bạn có thể đặt câu hỏi cụ thể hơn về luật, nghị định, thông tư liên quan đến đăng ký kinh doanh không?"""
            
            return {
                "message": message,
                "intent": "legal",
                "sources": [],
                "form_active": False
            }
        
        # Generate response using retrieved documents
        response_text = self.llm_manager.generate_legal_response(
            user_input, 
            retrieved_docs, 
            conversation_context
        )
        
        # Prepare sources information
        sources = []
        for doc in retrieved_docs[:3]:
            metadata = doc['metadata']
            source_info = {
                "document_type": metadata.get('document_type'),
                "document_number": metadata.get('document_number'),
                "chunk_title": metadata.get('chunk_title'),
                "score": doc.get('score', 0)
            }
            sources.append(source_info)
        
        return {
            "message": response_text,
            "intent": "legal",
            "sources": sources,
            "form_active": False
        }
    
    def _handle_business_request(self, user_input: str) -> Dict[str, Any]:
        """Handle business document generation requests."""
        # Start form collection process
        self.form_collection_state["active"] = True
        self.form_collection_state["current_field_index"] = 0
        self.form_collection_state["collected_data"] = {}
        
        message = """Tôi sẽ giúp bạn tạo bộ hồ sơ đăng ký kinh doanh. 
Tôi cần thu thập một số thông tin từ bạn.

Hãy bắt đầu với thông tin đầu tiên:"""
        
        # Get first question
        if self.form_collection_state["questions"]:
            first_question = self.form_collection_state["questions"][0]
            message += f"\n\n{first_question['question']}"
            if first_question.get('description'):
                message += f"\n📝 {first_question['description']}"
        
        return {
            "message": message,
            "intent": "business",
            "sources": [],
            "form_active": True,
            "current_field": self.form_collection_state["questions"][0]["field_name"] if self.form_collection_state["questions"] else None
        }
    
    def _handle_general_question(self, user_input: str, conversation_context: str) -> Dict[str, Any]:
        """Handle general consultation questions."""
        response_text = self.llm_manager.generate_general_response(
            user_input, 
            conversation_context
        )
        
        return {
            "message": response_text,
            "intent": "general",
            "sources": [],
            "form_active": False
        }
    
    def _handle_form_collection(self, user_input: str) -> Dict[str, Any]:
        """Handle form data collection process."""
        questions = self.form_collection_state["questions"]
        current_index = self.form_collection_state["current_field_index"]
        
        if current_index >= len(questions):
            # Form collection complete
            return self._complete_form_collection()
        
        current_question = questions[current_index]
        field_name = current_question["field_name"]
        
        # Validate user input
        is_valid, error_message = self.template_parser.validate_field_value(field_name, user_input)
        
        if not is_valid:
            message = f"❌ {error_message}\n\nVui lòng nhập lại {current_question['display_name'].lower()}:"
            return {
                "message": message,
                "intent": "business",
                "sources": [],
                "form_active": True,
                "current_field": field_name
            }
        
        # Save the input
        self.form_collection_state["collected_data"][field_name] = user_input
        
        # Move to next question
        self.form_collection_state["current_field_index"] += 1
        next_index = self.form_collection_state["current_field_index"]
        
        if next_index >= len(questions):
            return self._complete_form_collection()
        
        # Ask next question
        next_question = questions[next_index]
        message = f"✅ Đã lưu: {current_question['display_name']}\n\n"
        message += f"Tiếp theo: {next_question['question']}"
        
        if next_question.get('description'):
            message += f"\n📝 {next_question['description']}"
        
        return {
            "message": message,
            "intent": "business",
            "sources": [],
            "form_active": True,
            "current_field": next_question["field_name"]
        }
    
    def _complete_form_collection(self) -> Dict[str, Any]:
        """Complete the form collection process."""
        collected_data = self.form_collection_state["collected_data"]
        
        # Reset form state
        self.form_collection_state["active"] = False
        self.form_collection_state["current_field_index"] = 0
        self.form_collection_state["collected_data"] = {}
        
        # Generate summary of collected data
        summary = "🎉 Đã thu thập đủ thông tin! Dưới đây là tóm tắt:\n\n"
        
        for field_name, value in collected_data.items():
            # Find display name
            display_name = field_name
            for question in self.form_collection_state["questions"]:
                if question["field_name"] == field_name:
                    display_name = question["display_name"]
                    break
            
            summary += f"• {display_name}: {value}\n"
        
        summary += "\n📋 Bộ hồ sơ đăng ký kinh doanh đã được chuẩn bị với thông tin trên."
        summary += "\n\nBạn có muốn chỉnh sửa thông tin nào không? Hoặc có câu hỏi gì khác về quy trình đăng ký?"
        
        return {
            "message": summary,
            "intent": "business",
            "sources": [],
            "form_active": False,
            "collected_data": collected_data
        }
    
    def _get_conversation_context(self, max_history: int = 3) -> str:
        """Get recent conversation context."""
        if len(self.conversation_history) <= 1:
            return ""
        
        # Get last few exchanges
        recent_history = self.conversation_history[-max_history*2:]
        
        context_parts = []
        for entry in recent_history:
            role = "Người dùng" if entry["role"] == "user" else "Bot"
            context_parts.append(f"{role}: {entry['content']}")
        
        return "\n".join(context_parts)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history."""
        return self.conversation_history.copy()
    
    def clear_conversation(self):
        """Clear conversation history and reset state."""
        self.conversation_history = []
        self.current_intent = None
        self.form_collection_state = {
            "active": False,
            "current_field_index": 0,
            "collected_data": {},
            "questions": self.template_parser.generate_form_collection_questions()
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        retriever_stats = self.retriever.get_stats()
        
        return {
            "conversation_length": len(self.conversation_history),
            "current_intent": self.current_intent,
            "form_active": self.form_collection_state["active"],
            "available_templates": len(self.template_parser.templates),
            "retriever_stats": retriever_stats
        }
    
    def add_documents_to_knowledge_base(self, documents_directory: str) -> bool:
        """Add documents to the knowledge base."""
        try:
            # Process documents
            documents = self.document_processor.process_directory(documents_directory)
            
            if not documents:
                print("No documents found to add")
                return False
            
            # Add to retriever
            success = self.retriever.add_documents(documents)
            
            if success:
                stats = self.document_processor.get_document_stats(documents)
                print(f"Successfully added {stats['total_documents']} document chunks")
                print(f"Document types: {stats.get('document_types', {})}")
                print(f"Agencies: {stats.get('agencies', {})}")
            
            return success
            
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False