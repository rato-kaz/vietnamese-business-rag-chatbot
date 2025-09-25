import asyncio
from typing import Optional, AsyncGenerator
import google.generativeai as genai
from groq import Groq

from src.core.interfaces.services import LLMService
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class GeminiLLMService(LLMService):
    """Gemini implementation of LLM service."""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Configure Gemini
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            
            logger.info(
                "Gemini LLM service initialized",
                extra={
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
        except Exception as e:
            logger.error(
                "Failed to initialize Gemini LLM service",
                extra={
                    "model_name": model_name,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using Gemini."""
        try:
            logger.debug(
                "Generating response with Gemini",
                extra={
                    "prompt_length": len(prompt),
                    "has_context": bool(context),
                    "context_length": len(context) if context else 0
                }
            )
            
            # Prepare full prompt
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Generate response
            def _generate_sync():
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                    )
                )
                return response.text
            
            # Run in thread pool to avoid blocking
            response_text = await asyncio.get_event_loop().run_in_executor(
                None, _generate_sync
            )
            
            logger.debug(
                "Response generated successfully",
                extra={
                    "prompt_length": len(prompt),
                    "response_length": len(response_text)
                }
            )
            
            return response_text
            
        except Exception as e:
            logger.error(
                "Failed to generate response with Gemini",
                extra={
                    "prompt_length": len(prompt),
                    "error": str(e)
                },
                exc_info=True
            )
            return "Xin lỗi, tôi gặp lỗi khi tạo phản hồi. Vui lòng thử lại."
    
    async def stream_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response using Gemini."""
        try:
            logger.debug(
                "Streaming response with Gemini",
                extra={
                    "prompt_length": len(prompt),
                    "has_context": bool(context)
                }
            )
            
            # Prepare full prompt
            full_prompt = self._prepare_prompt(prompt, context)
            
            # For now, simulate streaming by yielding chunks
            # In future, implement actual streaming when Gemini supports it
            response_text = await self.generate_response(prompt, context, **kwargs)
            
            # Yield response in chunks
            chunk_size = 50
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.1)  # Small delay for streaming effect
                
        except Exception as e:
            logger.error(
                "Failed to stream response with Gemini",
                extra={
                    "prompt_length": len(prompt),
                    "error": str(e)
                },
                exc_info=True
            )
            yield "Xin lỗi, tôi gặp lỗi khi tạo phản hồi."
    
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


class GroqLLMService(LLMService):
    """Groq implementation of LLM service."""
    
    def __init__(
        self,
        api_key: str,
        model_name: str = "llama3-8b-8192",
        temperature: float = 0.1,
        max_tokens: int = 1024
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize client
        try:
            self.client = Groq(api_key=api_key)
            
            logger.info(
                "Groq LLM service initialized",
                extra={
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
        except Exception as e:
            logger.error(
                "Failed to initialize Groq LLM service",
                extra={
                    "model_name": model_name,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate response using Groq."""
        try:
            logger.debug(
                "Generating response with Groq",
                extra={
                    "prompt_length": len(prompt),
                    "has_context": bool(context)
                }
            )
            
            # Prepare messages
            messages = []
            if context:
                messages.append({
                    "role": "system",
                    "content": context
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Generate response
            def _generate_sync():
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message.content
            
            # Run in thread pool
            response_text = await asyncio.get_event_loop().run_in_executor(
                None, _generate_sync
            )
            
            logger.debug(
                "Response generated successfully",
                extra={
                    "prompt_length": len(prompt),
                    "response_length": len(response_text)
                }
            )
            
            return response_text
            
        except Exception as e:
            logger.error(
                "Failed to generate response with Groq",
                extra={
                    "prompt_length": len(prompt),
                    "error": str(e)
                },
                exc_info=True
            )
            return "Xin lỗi, tôi gặp lỗi khi tạo phản hồi. Vui lòng thử lại."
    
    async def stream_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response using Groq."""
        try:
            logger.debug(
                "Streaming response with Groq",
                extra={
                    "prompt_length": len(prompt),
                    "has_context": bool(context)
                }
            )
            
            # Prepare messages
            messages = []
            if context:
                messages.append({
                    "role": "system",
                    "content": context
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Stream response
            def _stream_sync():
                return self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    stream=True
                )
            
            # Get streaming response
            stream = await asyncio.get_event_loop().run_in_executor(
                None, _stream_sync
            )
            
            # Yield chunks
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    await asyncio.sleep(0.01)  # Small delay
                    
        except Exception as e:
            logger.error(
                "Failed to stream response with Groq",
                extra={
                    "prompt_length": len(prompt),
                    "error": str(e)
                },
                exc_info=True
            )
            yield "Xin lỗi, tôi gặp lỗi khi tạo phản hồi."