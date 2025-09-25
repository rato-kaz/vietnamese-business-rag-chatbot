import os
import yaml
from typing import Dict, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class IntentClassifier:
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize intent classifier using Llama via Groq."""
        with open(config_path, 'r', encoding='utf-8') as file:
            self.config = yaml.safe_load(file)
        
        # Initialize Groq client
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        self.model_name = self.config['intent_classifier']['model_name']
        self.temperature = self.config['intent_classifier']['temperature']
        
        # Intent definitions
        self.intents = {
            "legal": "Câu hỏi về luật pháp, quy định, thông tư, nghị định liên quan đến đăng ký kinh doanh",
            "business": "Yêu cầu hỗ trợ tạo hồ sơ, giấy tờ đăng ký kinh doanh cụ thể",
            "general": "Tư vấn chung về thành lập doanh nghiệp, quy trình, hướng dẫn tổng quan"
        }
        
        # System prompt for intent classification
        self.system_prompt = f"""Bạn là một AI chuyên phân loại ý định (intent) của người dùng trong lĩnh vực đăng ký kinh doanh tại Việt Nam.

Có 3 loại ý định chính:
1. **legal**: {self.intents['legal']}
   - Ví dụ: "Điều 15 Luật Doanh nghiệp quy định gì?", "Thông tư 02/2023 có hiệu lực khi nào?"
   
2. **business**: {self.intents['business']}
   - Ví dụ: "Tôi muốn lập hồ sơ đăng ký công ty", "Hãy giúp tôi tạo đơn đăng ký kinh doanh"
   
3. **general**: {self.intents['general']}
   - Ví dụ: "Quy trình thành lập công ty như thế nào?", "Cần chuẩn bị gì để mở công ty?"

Hãy phân loại câu hỏi của người dùng và chỉ trả về một trong ba từ: legal, business, hoặc general"""
    
    def classify_intent(self, user_input: str, conversation_context: str = "") -> str:
        """
        Classify user intent using Llama model.
        
        Args:
            user_input: User's input text
            conversation_context: Previous conversation for context
            
        Returns:
            Intent classification: 'legal', 'business', or 'general'
        """
        try:
            # Prepare the prompt with context if available
            context_part = f"Bối cảnh cuộc hội thoại trước:\n{conversation_context}\n\n" if conversation_context else ""
            
            user_prompt = f"""{context_part}Câu hỏi của người dùng: "{user_input}"

Phân loại ý định của câu hỏi này (chỉ trả về: legal, business, hoặc general):"""

            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=10,  # Very short response needed
                stream=False
            )
            
            # Extract and clean the response
            intent = response.choices[0].message.content.strip().lower()
            
            # Validate the intent
            if intent in self.intents:
                return intent
            else:
                # Try to extract valid intent from response
                for valid_intent in self.intents.keys():
                    if valid_intent in intent:
                        return valid_intent
                
                # Default to general if no valid intent found
                print(f"Invalid intent classification: {intent}, defaulting to 'general'")
                return "general"
                
        except Exception as e:
            print(f"Error in intent classification: {e}")
            # Default to general intent on error
            return "general"
    
    def get_intent_description(self, intent: str) -> str:
        """Get description for a given intent."""
        return self.intents.get(intent, "Unknown intent")
    
    def classify_with_confidence(self, user_input: str, conversation_context: str = "") -> Dict[str, Any]:
        """
        Classify intent and provide additional information.
        
        Args:
            user_input: User's input text
            conversation_context: Previous conversation context
            
        Returns:
            Dictionary with intent, description, and metadata
        """
        intent = self.classify_intent(user_input, conversation_context)
        
        return {
            "intent": intent,
            "description": self.get_intent_description(intent),
            "user_input": user_input,
            "has_context": bool(conversation_context)
        }