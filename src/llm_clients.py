import os
import yaml
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize Gemini client."""
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        self.model_name = self.config['main_llm']['model_name']
        self.temperature = self.config['main_llm']['temperature']
        self.max_tokens = self.config['main_llm']['max_tokens']
        
        # Initialize the model
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        """
        Generate response using Gemini.
        
        Args:
            prompt: User prompt
            context: Additional context for the response
            
        Returns:
            Generated response
        """
        try:
            # Prepare the full prompt
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            return response.text
            
        except Exception as e:
            print(f"Error generating response with Gemini: {e}")
            return "Xin lỗi, tôi gặp lỗi khi tạo phản hồi. Vui lòng thử lại."
    
    def _prepare_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Prepare the full prompt with context."""
        base_prompt = """Bạn là một chatbot chuyên tư vấn về đăng ký kinh doanh tại Việt Nam. 
Bạn có kiến thức sâu về luật pháp, quy định, và quy trình thành lập doanh nghiệp.

Hãy trả lời câu hỏi một cách chính xác, hữu ích và dễ hiểu. 
Sử dụng tiếng Việt và cung cấp thông tin cụ thể, thực tế."""
        
        if context:
            full_prompt = f"{base_prompt}\n\nThông tin tham khảo:\n{context}\n\nCâu hỏi: {prompt}"
        else:
            full_prompt = f"{base_prompt}\n\nCâu hỏi: {prompt}"
        
        return full_prompt


class GroqClient:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize Groq client for Llama."""
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize Groq client
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        self.model_name = self.config['intent_classifier']['model_name']
        self.temperature = self.config['intent_classifier']['temperature']
    
    def process_input(self, user_input: str, task: str = "general") -> str:
        """
        Process user input for various tasks using Llama.
        
        Args:
            user_input: User's input
            task: Type of processing task
            
        Returns:
            Processed result
        """
        try:
            if task == "intent_classification":
                return self._classify_intent(user_input)
            elif task == "query_enhancement":
                return self._enhance_query(user_input)
            else:
                return self._general_processing(user_input)
                
        except Exception as e:
            print(f"Error processing input with Groq: {e}")
            return user_input  # Return original input on error
    
    def _classify_intent(self, user_input: str) -> str:
        """Classify user intent (handled by IntentClassifier)."""
        # This is handled by the IntentClassifier class
        return "general"
    
    def _enhance_query(self, user_input: str) -> str:
        """Enhance user query for better retrieval."""
        system_prompt = """Bạn là AI chuyên cải thiện câu truy vấn tìm kiếm về luật pháp và đăng ký kinh doanh.
Hãy viết lại câu hỏi để tìm kiếm thông tin pháp luật hiệu quả hơn, giữ nguyên ý nghĩa và ngôn ngữ tiếng Việt."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Cải thiện câu truy vấn: {user_input}"}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error enhancing query: {e}")
            return user_input
    
    def _general_processing(self, user_input: str) -> str:
        """General text processing."""
        return user_input


class LLMManager:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize LLM manager with both Gemini and Groq clients."""
        self.gemini_client = GeminiClient(config_path)
        self.groq_client = GroqClient(config_path)
    
    def generate_legal_response(self, query: str, retrieved_docs: List[Dict], conversation_history: str = "") -> str:
        """Generate response for legal questions using retrieved documents."""
        # Prepare context from retrieved documents
        context_parts = []
        for i, doc in enumerate(retrieved_docs[:3], 1):
            metadata = doc['metadata']
            source_info = []
            
            if metadata.get('document_type'):
                source_info.append(metadata['document_type'])
            if metadata.get('document_number'):
                source_info.append(metadata['document_number'])
            if metadata.get('chunk_title'):
                source_info.append(metadata['chunk_title'])
            
            source_str = " - ".join(source_info) if source_info else f"Tài liệu {i}"
            context_parts.append(f"**{source_str}:**\n{doc['content']}\n")
        
        context = "\n".join(context_parts) if context_parts else ""
        
        # Prepare prompt for legal questions
        legal_prompt = f"""Dựa trên các tài liệu pháp luật được cung cấp, hãy trả lời câu hỏi của người dùng một cách chính xác và chi tiết.

Lưu ý:
- Trích dẫn cụ thể các điều luật, thông tư, nghị định liên quan
- Giải thích rõ ràng các quy định
- Nếu có nhiều quan điểm hoặc thay đổi theo thời gian, hãy làm rõ
- Sử dụng tiếng Việt chính thức

{f"Lịch sử hội thoại: {conversation_history}" if conversation_history else ""}

Câu hỏi: {query}"""
        
        return self.gemini_client.generate_response(legal_prompt, context)
    
    def generate_general_response(self, query: str, conversation_history: str = "") -> str:
        """Generate response for general business consultation."""
        general_prompt = f"""Hãy tư vấn cho người dùng về thành lập doanh nghiệp tại Việt Nam.
Cung cấp thông tin hữu ích, thực tế và dễ hiểu về quy trình, thủ tục, và lưu ý quan trọng.

{f"Lịch sử hội thoại: {conversation_history}" if conversation_history else ""}

Câu hỏi: {query}"""
        
        return self.gemini_client.generate_response(general_prompt)
    
    def enhance_query(self, query: str) -> str:
        """Enhance user query for better retrieval."""
        return self.groq_client.process_input(query, task="query_enhancement")