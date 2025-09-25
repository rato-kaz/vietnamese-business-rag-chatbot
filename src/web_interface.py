import streamlit as st
import yaml
from typing import Dict, Any
import time
from .chatbot import ConversationalRAGChatbot


class StreamlitWebInterface:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize Streamlit web interface."""
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize chatbot if not in session state
        if 'chatbot' not in st.session_state:
            st.session_state.chatbot = ConversationalRAGChatbot(config_path)
        
        self.chatbot = st.session_state.chatbot
        
        # Initialize session state variables
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'system_initialized' not in st.session_state:
            st.session_state.system_initialized = False
    
    def run(self):
        """Run the Streamlit web interface."""
        st.set_page_config(
            page_title=self.config['web_interface']['title'],
            page_icon="🏢",
            layout="wide"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .main-header h1 {
            color: white;
            text-align: center;
            margin: 0;
        }
        .chat-message {
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            border-left: 4px solid #2a5298;
        }
        .user-message {
            background-color: #f0f2f6;
            border-left-color: #ff6b6b;
        }
        .bot-message {
            background-color: #e8f4f8;
            border-left-color: #2a5298;
        }
        .intent-badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-left: 1rem;
        }
        .intent-legal {
            background-color: #ff6b6b;
            color: white;
        }
        .intent-business {
            background-color: #4ecdc4;
            color: white;
        }
        .intent-general {
            background-color: #45b7d1;
            color: white;
        }
        .source-info {
            background-color: #f8f9fa;
            padding: 0.5rem;
            border-radius: 5px;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown("""
        <div class="main-header">
            <h1>🏢 RAG Chatbot - Đăng ký Kinh doanh Việt Nam</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Sidebar
        self._render_sidebar()
        
        # Main chat interface
        self._render_chat_interface()
        
        # Initialize system on first run
        if not st.session_state.system_initialized:
            self._initialize_system()
    
    def _render_sidebar(self):
        """Render the sidebar with system information and controls."""
        with st.sidebar:
            st.header("🛠️ Hệ thống")
            
            # System stats
            try:
                stats = self.chatbot.get_system_stats()
                
                st.subheader("📊 Thống kê")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Tin nhắn", stats.get('conversation_length', 0))
                    st.metric("Templates", stats.get('available_templates', 0))
                
                with col2:
                    st.metric("Tài liệu", stats.get('retriever_stats', {}).get('total_documents', 0))
                    if stats.get('current_intent'):
                        st.metric("Intent hiện tại", stats['current_intent'])
                
                # Form status
                if stats.get('form_active'):
                    st.success("🔄 Đang thu thập form")
                else:
                    st.info("💬 Chế độ chat")
                
            except Exception as e:
                st.error(f"Lỗi thống kê: {e}")
            
            # Controls
            st.subheader("⚙️ Điều khiển")
            
            if st.button("🗑️ Xóa lịch sử chat"):
                self.chatbot.clear_conversation()
                st.session_state.messages = []
                st.success("Đã xóa lịch sử!")
                st.experimental_rerun()
            
            if st.button("📥 Load tài liệu"):
                with st.spinner("Đang tải tài liệu..."):
                    success = self.chatbot.add_documents_to_knowledge_base("data/documents/core")
                    if success:
                        st.success("Tải tài liệu thành công!")
                    else:
                        st.error("Lỗi tải tài liệu!")
            
            # Intent explanation
            st.subheader("🎯 Loại câu hỏi")
            st.markdown("""
            **Legal** 🏛️: Hỏi về luật, nghị định, thông tư
            
            **Business** 📋: Tạo hồ sơ đăng ký kinh doanh
            
            **General** 💡: Tư vấn chung về thành lập DN
            """)
    
    def _render_chat_interface(self):
        """Render the main chat interface."""
        # Display chat history
        for message in st.session_state.messages:
            self._display_message(message)
        
        # Chat input
        if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
            self._process_user_input(prompt)
    
    def _display_message(self, message: Dict[str, Any]):
        """Display a single message."""
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f'<div class="chat-message user-message">{message["content"]}</div>', 
                           unsafe_allow_html=True)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                # Bot message with intent badge
                intent = message.get("intent", "general")
                intent_class = f"intent-{intent}"
                intent_text = {
                    "legal": "Pháp luật",
                    "business": "Kinh doanh", 
                    "general": "Tổng quát"
                }.get(intent, intent)
                
                st.markdown(f"""
                <div class="chat-message bot-message">
                    {message["content"]}
                    <span class="intent-badge {intent_class}">{intent_text}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Display sources if available
                if message.get("sources"):
                    with st.expander("📚 Tài liệu tham khảo"):
                        for i, source in enumerate(message["sources"], 1):
                            source_text = f"**{i}. {source.get('document_type', 'Tài liệu')}**"
                            if source.get('document_number'):
                                source_text += f" - {source['document_number']}"
                            if source.get('chunk_title'):
                                source_text += f"\n{source['chunk_title']}"
                            if source.get('score'):
                                source_text += f"\n*Độ tin cậy: {source['score']:.2f}*"
                            
                            st.markdown(source_text)
                
                # Display form status if active
                if message.get("form_active"):
                    st.info("📝 Đang thu thập thông tin form...")
    
    def _process_user_input(self, user_input: str):
        """Process user input and generate response."""
        # Add user message
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": time.strftime("%H:%M:%S")
        }
        st.session_state.messages.append(user_message)
        
        # Display user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(f'<div class="chat-message user-message">{user_input}</div>', 
                       unsafe_allow_html=True)
        
        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Đang suy nghĩ..."):
                try:
                    response = self.chatbot.process_message(user_input)
                    
                    # Display response
                    intent = response.get("intent", "general")
                    intent_class = f"intent-{intent}"
                    intent_text = {
                        "legal": "Pháp luật",
                        "business": "Kinh doanh",
                        "general": "Tổng quát"
                    }.get(intent, intent)
                    
                    st.markdown(f"""
                    <div class="chat-message bot-message">
                        {response["message"]}
                        <span class="intent-badge {intent_class}">{intent_text}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display sources if available
                    if response.get("sources"):
                        with st.expander("📚 Tài liệu tham khảo"):
                            for i, source in enumerate(response["sources"], 1):
                                source_text = f"**{i}. {source.get('document_type', 'Tài liệu')}**"
                                if source.get('document_number'):
                                    source_text += f" - {source['document_number']}"
                                if source.get('chunk_title'):
                                    source_text += f"\n{source['chunk_title']}"
                                if source.get('score'):
                                    source_text += f"\n*Độ tin cậy: {source['score']:.2f}*"
                                
                                st.markdown(source_text)
                    
                    # Display form status if active
                    if response.get("form_active"):
                        st.info("📝 Đang thu thập thông tin form...")
                    
                    # Add bot message to history
                    bot_message = {
                        "role": "assistant",
                        "content": response["message"],
                        "intent": response.get("intent"),
                        "sources": response.get("sources", []),
                        "form_active": response.get("form_active", False),
                        "timestamp": time.strftime("%H:%M:%S")
                    }
                    st.session_state.messages.append(bot_message)
                    
                except Exception as e:
                    st.error(f"Lỗi xử lý: {e}")
                    # Add error message
                    error_message = {
                        "role": "assistant",
                        "content": f"Xin lỗi, có lỗi xảy ra: {e}",
                        "intent": "error",
                        "sources": [],
                        "form_active": False,
                        "timestamp": time.strftime("%H:%M:%S")
                    }
                    st.session_state.messages.append(error_message)
    
    def _initialize_system(self):
        """Initialize the system on first run."""
        with st.spinner("Đang khởi tạo hệ thống..."):
            try:
                # Load documents if available
                self.chatbot.add_documents_to_knowledge_base("data/documents/core")
                st.session_state.system_initialized = True
                st.success("Hệ thống đã sẵn sàng!")
                
                # Add welcome message
                welcome_message = {
                    "role": "assistant",
                    "content": """👋 Xin chào! Tôi là chatbot hỗ trợ đăng ký kinh doanh tại Việt Nam.

Tôi có thể giúp bạn:
🏛️ **Tra cứu pháp luật**: Hỏi về luật, nghị định, thông tư liên quan đến đăng ký kinh doanh
📋 **Tạo hồ sơ**: Hướng dẫn và thu thập thông tin để tạo bộ hồ sơ đăng ký
💡 **Tư vấn chung**: Giải đáp về quy trình thành lập doanh nghiệp

Hãy bắt đầu bằng cách đặt câu hỏi!""",
                    "intent": "general",
                    "sources": [],
                    "form_active": False,
                    "timestamp": time.strftime("%H:%M:%S")
                }
                st.session_state.messages.append(welcome_message)
                
            except Exception as e:
                st.error(f"Lỗi khởi tạo: {e}")


def main():
    """Main function to run the web interface."""
    interface = StreamlitWebInterface()
    interface.run()


if __name__ == "__main__":
    main()