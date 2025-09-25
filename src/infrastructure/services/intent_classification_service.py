import asyncio
from typing import Dict, Any, Optional
from groq import Groq

from src.core.interfaces.services import IntentClassificationService
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class GroqIntentClassificationService(IntentClassificationService):
    """Groq-based intent classification service."""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "llama3-8b-8192",
        temperature: float = 0.1
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize client
        try:
            self.client = Groq(api_key=api_key)
            
            logger.info(
                "Intent classification service initialized",
                extra={
                    "model_name": model_name,
                    "temperature": temperature
                }
            )
        except Exception as e:
            logger.error(
                "Failed to initialize intent classification service",
                extra={
                    "model_name": model_name,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
        
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
    
    async def classify_intent(
        self,
        text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify user intent using Groq."""
        try:
            logger.debug(
                "Classifying intent",
                extra={
                    "text_length": len(text),
                    "has_context": bool(context)
                }
            )
            
            # Prepare the prompt
            context_part = f"Bối cảnh cuộc hội thoại trước:\n{context}\n\n" if context else ""
            user_prompt = f"""{context_part}Câu hỏi của người dùng: "{text}"

Phân loại ý định của câu hỏi này (chỉ trả về: legal, business, hoặc general):"""
            
            def _classify_sync():
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=10,
                    stream=False
                )
                return response.choices[0].message.content.strip().lower()
            
            # Run classification
            intent = await asyncio.get_event_loop().run_in_executor(
                None, _classify_sync
            )
            
            # Validate the intent
            if intent in self.intents:
                classified_intent = intent
                confidence = 0.9  # High confidence for valid classifications
            else:
                # Try to extract valid intent from response
                classified_intent = "general"  # Default
                confidence = 0.5  # Lower confidence for fallback
                
                for valid_intent in self.intents.keys():
                    if valid_intent in intent:
                        classified_intent = valid_intent
                        confidence = 0.7
                        break
                
                logger.warning(
                    "Invalid intent classification, using fallback",
                    extra={
                        "original_intent": intent,
                        "fallback_intent": classified_intent,
                        "text": text
                    }
                )
            
            result = {
                "intent": classified_intent,
                "description": self.intents[classified_intent],
                "confidence": confidence,
                "raw_response": intent
            }
            
            logger.debug(
                "Intent classified successfully",
                extra={
                    "text_length": len(text),
                    "intent": classified_intent,
                    "confidence": confidence
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to classify intent",
                extra={
                    "text_length": len(text),
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Return default intent on error
            return {
                "intent": "general",
                "description": self.intents["general"],
                "confidence": 0.0,
                "error": str(e)
            }