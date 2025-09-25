import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..entities.conversation import Conversation, Message, MessageRole, ChatResponse, IntentType
from ..entities.document import RetrievalResult
from ..entities.form import FormCollectionState, FormTemplate
from ..interfaces.repositories import ConversationRepository, DocumentRepository, TemplateRepository
from ..interfaces.services import (
    IntentClassificationService, 
    LLMService, 
    RerankingService,
    MetricsService,
    CacheService
)

logger = logging.getLogger(__name__)


class ChatUseCase:
    """Use case for chat interactions."""
    
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        document_repo: DocumentRepository,
        template_repo: TemplateRepository,
        intent_service: IntentClassificationService,
        llm_service: LLMService,
        reranking_service: RerankingService,
        metrics_service: MetricsService,
        cache_service: Optional[CacheService] = None
    ):
        self.conversation_repo = conversation_repo
        self.document_repo = document_repo
        self.template_repo = template_repo
        self.intent_service = intent_service
        self.llm_service = llm_service
        self.reranking_service = reranking_service
        self.metrics_service = metrics_service
        self.cache_service = cache_service
    
    async def process_message(
        self, 
        conversation_id: str, 
        user_message: str,
        form_state: Optional[FormCollectionState] = None
    ) -> ChatResponse:
        """Process user message and generate response."""
        start_time = datetime.now()
        
        try:
            logger.info(
                "Processing message",
                extra={
                    "conversation_id": conversation_id,
                    "message_length": len(user_message),
                    "form_active": form_state.is_active if form_state else False
                }
            )
            
            # Get or create conversation
            conversation = await self.conversation_repo.get_conversation(conversation_id)
            if not conversation:
                conversation = Conversation(id=conversation_id)
                logger.info(f"Created new conversation: {conversation_id}")
            
            # Add user message
            user_msg = Message(
                role=MessageRole.USER,
                content=user_message,
                timestamp=datetime.now()
            )
            conversation.add_message(user_msg)
            
            # Handle form collection if active
            if form_state and form_state.is_active:
                response = await self._handle_form_collection(
                    conversation, user_message, form_state
                )
            else:
                # Classify intent
                context = conversation.get_context()
                intent_result = await self.intent_service.classify_intent(
                    user_message, context
                )
                intent = IntentType(intent_result["intent"])
                
                logger.info(
                    "Intent classified",
                    extra={
                        "conversation_id": conversation_id,
                        "intent": intent.value,
                        "confidence": intent_result.get("confidence", 0.0)
                    }
                )
                
                # Generate response based on intent
                if intent == IntentType.LEGAL:
                    response = await self._handle_legal_question(
                        conversation, user_message, context
                    )
                elif intent == IntentType.BUSINESS:
                    response = await self._handle_business_request(
                        conversation, user_message
                    )
                else:
                    response = await self._handle_general_question(
                        conversation, user_message, context
                    )
                
                response.intent = intent
            
            # Add bot response to conversation
            bot_msg = Message(
                role=MessageRole.ASSISTANT,
                content=response.message,
                intent=response.intent,
                metadata=response.metadata,
                timestamp=datetime.now()
            )
            conversation.add_message(bot_msg)
            
            # Save conversation
            await self.conversation_repo.save_conversation(conversation)
            
            # Record metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            await self.metrics_service.record_histogram(
                "chat.processing_time", 
                processing_time,
                tags={
                    "intent": response.intent.value if response.intent else "unknown",
                    "form_active": str(response.form_active)
                }
            )
            await self.metrics_service.increment_counter(
                "chat.messages_processed",
                tags={"intent": response.intent.value if response.intent else "unknown"}
            )
            
            logger.info(
                "Message processed successfully",
                extra={
                    "conversation_id": conversation_id,
                    "intent": response.intent.value if response.intent else None,
                    "processing_time": processing_time,
                    "response_length": len(response.message)
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Error processing message",
                extra={
                    "conversation_id": conversation_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            
            await self.metrics_service.increment_counter(
                "chat.errors",
                tags={"error_type": type(e).__name__}
            )
            
            # Return error response
            return ChatResponse(
                message="Xin lỗi, tôi gặp lỗi khi xử lý tin nhắn của bạn. Vui lòng thử lại.",
                metadata={"error": True, "error_message": str(e)}
            )
    
    async def _handle_legal_question(
        self, 
        conversation: Conversation, 
        query: str, 
        context: str
    ) -> ChatResponse:
        """Handle legal questions with RAG."""
        try:
            # Search relevant documents
            search_results = await self.document_repo.search_chunks(
                query=query,
                top_k=10,
                filters={"document_type": ["Luật", "Nghị định", "Thông tư", "Quyết định"]}
            )
            
            if not search_results:
                return ChatResponse(
                    message="Xin lỗi, tôi không tìm thấy thông tin pháp luật liên quan đến câu hỏi của bạn.",
                    metadata={"no_results": True}
                )
            
            # Rerank documents
            reranked_results = await self.reranking_service.rerank_documents(
                query, search_results[:5]
            )
            
            # Prepare context for LLM
            context_parts = []
            sources = []
            
            for result in reranked_results[:3]:
                chunk = result.chunk
                metadata = chunk.metadata
                
                source_info = []
                if metadata.document_type:
                    source_info.append(metadata.document_type.value)
                if metadata.document_number:
                    source_info.append(metadata.document_number)
                if metadata.chunk_title:
                    source_info.append(metadata.chunk_title)
                
                source_str = " - ".join(source_info) if source_info else "Tài liệu"
                context_parts.append(f"**{source_str}:**\n{chunk.content}\n")
                
                sources.append({
                    "document_type": metadata.document_type.value if metadata.document_type else None,
                    "document_number": metadata.document_number,
                    "chunk_title": metadata.chunk_title,
                    "score": result.rerank_score or result.score
                })
            
            # Generate response
            rag_context = "\n".join(context_parts)
            prompt = f"""Dựa trên các tài liệu pháp luật được cung cấp, hãy trả lời câu hỏi của người dùng một cách chính xác và chi tiết.

Lưu ý:
- Trích dẫn cụ thể các điều luật, thông tư, nghị định liên quan
- Giải thích rõ ràng các quy định
- Nếu có nhiều quan điểm hoặc thay đổi theo thời gian, hãy làm rõ
- Sử dụng tiếng Việt chính thức

Lịch sử hội thoại: {context}

Câu hỏi: {query}"""
            
            response_text = await self.llm_service.generate_response(
                prompt, rag_context
            )
            
            return ChatResponse(
                message=response_text,
                sources=sources,
                metadata={
                    "search_results_count": len(search_results),
                    "reranked_results_count": len(reranked_results)
                }
            )
            
        except Exception as e:
            logger.error(
                "Error handling legal question",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def _handle_business_request(
        self, 
        conversation: Conversation, 
        query: str
    ) -> ChatResponse:
        """Handle business document generation requests."""
        try:
            # Get available templates
            templates = await self.template_repo.list_templates()
            
            if not templates:
                return ChatResponse(
                    message="Xin lỗi, hiện tại chưa có template nào để tạo hồ sơ.",
                    metadata={"no_templates": True}
                )
            
            # For now, use the first template - in future, could classify which template needed
            template = templates[0]
            
            message = f"""Tôi sẽ giúp bạn tạo bộ hồ sơ đăng ký kinh doanh ({template.display_name}).
Tôi cần thu thập một số thông tin từ bạn.

Hãy bắt đầu với thông tin đầu tiên:"""
            
            required_fields = template.get_required_fields()
            if required_fields:
                first_field = required_fields[0]
                message += f"\n\n{first_field.display_name}: "
                if first_field.description:
                    message += f"\n📝 {first_field.description}"
            
            return ChatResponse(
                message=message,
                form_active=True,
                current_field=required_fields[0].field_name if required_fields else None,
                metadata={
                    "template_name": template.name,
                    "total_fields": len(required_fields)
                }
            )
            
        except Exception as e:
            logger.error(
                "Error handling business request",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def _handle_general_question(
        self, 
        conversation: Conversation, 
        query: str, 
        context: str
    ) -> ChatResponse:
        """Handle general consultation questions."""
        try:
            prompt = f"""Hãy tư vấn cho người dùng về thành lập doanh nghiệp tại Việt Nam.
Cung cấp thông tin hữu ích, thực tế và dễ hiểu về quy trình, thủ tục, và lưu ý quan trọng.

Lịch sử hội thoại: {context}

Câu hỏi: {query}"""
            
            response_text = await self.llm_service.generate_response(prompt)
            
            return ChatResponse(
                message=response_text,
                metadata={"general_consultation": True}
            )
            
        except Exception as e:
            logger.error(
                "Error handling general question",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def _handle_form_collection(
        self, 
        conversation: Conversation, 
        user_input: str,
        form_state: FormCollectionState
    ) -> ChatResponse:
        """Handle form data collection process."""
        try:
            current_field = form_state.get_current_field()
            if not current_field:
                return ChatResponse(
                    message="Lỗi: Không tìm thấy field hiện tại.",
                    form_active=False,
                    metadata={"error": True}
                )
            
            # Get template for validation
            template = await self.template_repo.get_template(form_state.template_name)
            if not template:
                return ChatResponse(
                    message="Lỗi: Không tìm thấy template.",
                    form_active=False,
                    metadata={"error": True}
                )
            
            # Validate user input
            is_valid, error_message = await self._validate_field_value(
                current_field.field_name, user_input, template
            )
            
            if not is_valid:
                return ChatResponse(
                    message=f"❌ {error_message}\n\nVui lòng nhập lại {current_field.display_name.lower()}:",
                    form_active=True,
                    current_field=current_field.field_name,
                    metadata={"validation_error": True}
                )
            
            # Save the input
            form_state.form_data.set_field_value(current_field.field_name, user_input)
            
            # Move to next field
            next_field = form_state.move_to_next_field()
            
            if form_state.is_complete():
                # Form collection complete
                form_state.is_active = False
                
                summary = "🎉 Đã thu thập đủ thông tin! Dưới đây là tóm tắt:\n\n"
                for field_name, value in form_state.form_data.data.items():
                    field = template.get_field_by_name(field_name)
                    display_name = field.display_name if field else field_name
                    summary += f"• {display_name}: {value}\n"
                
                summary += "\n📋 Bộ hồ sơ đăng ký kinh doanh đã được chuẩn bị với thông tin trên."
                summary += "\n\nBạn có muốn chỉnh sửa thông tin nào không?"
                
                return ChatResponse(
                    message=summary,
                    form_active=False,
                    collected_data=form_state.form_data.data,
                    metadata={"form_completed": True}
                )
            
            # Ask next question
            message = f"✅ Đã lưu: {current_field.display_name}\n\n"
            message += f"Tiếp theo: {next_field.display_name}"
            
            if next_field.description:
                message += f"\n📝 {next_field.description}"
            
            return ChatResponse(
                message=message,
                form_active=True,
                current_field=next_field.field_name,
                metadata={
                    "field_completed": current_field.field_name,
                    "progress": f"{form_state.current_field_index}/{len(form_state.questions)}"
                }
            )
            
        except Exception as e:
            logger.error(
                "Error handling form collection",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    async def _validate_field_value(
        self, 
        field_name: str, 
        value: str, 
        template: FormTemplate
    ) -> tuple[bool, str]:
        """Validate field value."""
        field = template.get_field_by_name(field_name)
        if not field:
            return True, ""
        
        # Required field validation
        if field.required and not value.strip():
            return False, "Trường này là bắt buộc"
        
        # Type-specific validation
        if field.field_type.value == "date":
            import re
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', value):
                return False, "Định dạng ngày không đúng. Vui lòng nhập theo format dd/mm/yyyy"
        
        elif field.field_type.value == "number":
            try:
                float(value.replace(",", "").replace(".", ""))
            except ValueError:
                return False, "Giá trị phải là số"
        
        elif field.field_type.value == "email":
            import re
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
                return False, "Định dạng email không đúng"
        
        return True, ""