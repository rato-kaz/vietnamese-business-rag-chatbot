from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from ..models import TemplateInfo, FormField
from ..dependencies import get_chatbot
from src.chatbot import ConversationalRAGChatbot

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("", response_model=List[TemplateInfo])
async def get_templates(
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get available form templates."""
    try:
        templates = chatbot.template_parser.get_all_form_fields()
        
        template_list = []
        for template_name, fields in templates.items():
            template_list.append(TemplateInfo(
                name=template_name,
                display_name=template_name.replace(".docx", "").replace("_", " ").title(),
                field_count=len(fields),
                required_fields=len([f for f in fields if f.get("required", False)])
            ))
        
        return template_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting templates: {str(e)}")


@router.get("/{template_name}/fields", response_model=List[FormField])
async def get_template_fields(
    template_name: str,
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get fields for a specific template."""
    try:
        fields = chatbot.template_parser.get_template_fields(template_name)
        
        if not fields:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
        
        return [
            FormField(
                field_name=field["field_name"],
                display_name=field["display_name"],
                field_type=field["field_type"],
                required=field.get("required", False),
                description=field.get("description", "")
            )
            for field in fields
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template fields: {str(e)}")


@router.get("/{template_name}")
async def get_template_info(
    template_name: str,
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get detailed information about a specific template."""
    try:
        templates = chatbot.template_parser.get_all_form_fields()
        
        if template_name not in templates:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
        
        fields = templates[template_name]
        required_fields = [f for f in fields if f.get("required", False)]
        optional_fields = [f for f in fields if not f.get("required", False)]
        
        # Group fields by type
        field_types = {}
        for field in fields:
            field_type = field.get("field_type", "text")
            if field_type not in field_types:
                field_types[field_type] = []
            field_types[field_type].append(field)
        
        return {
            "name": template_name,
            "display_name": template_name.replace(".docx", "").replace("_", " ").title(),
            "description": f"Template for {template_name.replace('.docx', '').replace('_', ' ')}",
            "total_fields": len(fields),
            "required_fields": len(required_fields),
            "optional_fields": len(optional_fields),
            "field_types": {k: len(v) for k, v in field_types.items()},
            "fields": fields
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template info: {str(e)}")


@router.post("/{template_name}/validate")
async def validate_template_data(
    template_name: str,
    data: Dict[str, Any],
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Validate form data against template requirements."""
    try:
        templates = chatbot.template_parser.get_all_form_fields()
        
        if template_name not in templates:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
        
        fields = templates[template_name]
        validation_results = []
        
        # Check each field
        for field in fields:
            field_name = field["field_name"]
            field_value = data.get(field_name)
            
            # Validate using template parser
            is_valid, error_message = chatbot.template_parser.validate_field_value(
                field_name, str(field_value) if field_value is not None else ""
            )
            
            validation_results.append({
                "field_name": field_name,
                "field_display_name": field["display_name"],
                "is_valid": is_valid,
                "error_message": error_message,
                "value": field_value
            })
        
        # Overall validation status
        all_valid = all(result["is_valid"] for result in validation_results)
        
        return {
            "template_name": template_name,
            "is_valid": all_valid,
            "validation_results": validation_results,
            "total_fields": len(validation_results),
            "valid_fields": len([r for r in validation_results if r["is_valid"]]),
            "invalid_fields": len([r for r in validation_results if not r["is_valid"]])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating template data: {str(e)}")


@router.get("/{template_name}/questions")
async def get_template_questions(
    template_name: str,
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Get form collection questions for a template."""
    try:
        templates = chatbot.template_parser.get_all_form_fields()
        
        if template_name not in templates:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
        
        fields = templates[template_name]
        questions = []
        
        for field in fields:
            if field.get("required", False):
                question = {
                    "field_name": field["field_name"],
                    "question": f"Vui lòng nhập {field['display_name'].lower()}:",
                    "field_type": field["field_type"],
                    "description": field.get("description", ""),
                    "required": field.get("required", False)
                }
                questions.append(question)
        
        return {
            "template_name": template_name,
            "questions": questions,
            "total_questions": len(questions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting template questions: {str(e)}")


@router.post("/{template_name}/generate")
async def generate_document(
    template_name: str,
    data: Dict[str, Any],
    chatbot: ConversationalRAGChatbot = Depends(get_chatbot)
):
    """Generate document from template and data."""
    try:
        # This is a placeholder for document generation
        # In a real implementation, you'd use the template to generate a .docx file
        
        templates = chatbot.template_parser.get_all_form_fields()
        
        if template_name not in templates:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")
        
        # Validate data first
        fields = templates[template_name]
        validation_results = []
        
        for field in fields:
            field_name = field["field_name"]
            field_value = data.get(field_name)
            
            if field.get("required", False) and not field_value:
                validation_results.append({
                    "field": field_name,
                    "error": "Required field is missing"
                })
        
        if validation_results:
            raise HTTPException(status_code=400, detail={
                "message": "Validation failed",
                "errors": validation_results
            })
        
        # Placeholder for document generation
        generated_document = {
            "template_name": template_name,
            "generated_at": "2024-01-15T10:30:00",
            "status": "success",
            "document_path": f"generated/{template_name}_{data.get('ten_cong_ty', 'company')}.docx",
            "data_used": data
        }
        
        return {
            "message": "Document generated successfully",
            "document": generated_document,
            "note": "This is a placeholder - implement actual document generation"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")