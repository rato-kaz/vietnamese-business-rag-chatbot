from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from src.application.dependencies import get_container
from src.infrastructure.logging.context import get_logger
from src.api.models import TemplateInfo, FormField

logger = get_logger(__name__)
router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("", response_model=List[TemplateInfo])
async def get_templates():
    """Get available form templates."""
    try:
        container = get_container()
        template_repo = container.get_template_repo()
        
        templates = await template_repo.list_templates()
        
        template_list = []
        for template in templates:
            template_list.append(TemplateInfo(
                name=template.name,
                display_name=template.display_name,
                field_count=len(template.fields),
                required_fields=len(template.get_required_fields())
            ))
        
        logger.debug(
            "Templates retrieved",
            extra={"template_count": len(template_list)}
        )
        
        return template_list
        
    except Exception as e:
        logger.error(
            "Failed to get templates",
            extra={"error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error getting templates: {str(e)}"
        )


@router.get("/{template_name}/fields", response_model=List[FormField])
async def get_template_fields(template_name: str):
    """Get fields for a specific template."""
    try:
        container = get_container()
        template_repo = container.get_template_repo()
        
        template = await template_repo.get_template(template_name)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_name} not found"
            )
        
        fields = []
        for field in template.fields:
            fields.append(FormField(
                field_name=field.field_name,
                display_name=field.display_name,
                field_type=field.field_type,
                required=field.required,
                description=field.description
            ))
        
        logger.debug(
            "Template fields retrieved",
            extra={
                "template_name": template_name,
                "field_count": len(fields)
            }
        )
        
        return fields
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get template fields",
            extra={
                "template_name": template_name,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error getting template fields: {str(e)}"
        )


@router.get("/{template_name}")
async def get_template_info(template_name: str):
    """Get detailed information about a specific template."""
    try:
        container = get_container()
        template_repo = container.get_template_repo()
        
        template = await template_repo.get_template(template_name)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_name} not found"
            )
        
        required_fields = template.get_required_fields()
        optional_fields = [f for f in template.fields if not f.required]
        
        # Group fields by type
        field_types = {}
        for field in template.fields:
            field_type = field.field_type.value
            if field_type not in field_types:
                field_types[field_type] = []
            field_types[field_type].append(field)
        
        template_info = {
            "name": template.name,
            "display_name": template.display_name,
            "description": template.description,
            "total_fields": len(template.fields),
            "required_fields": len(required_fields),
            "optional_fields": len(optional_fields),
            "field_types": {k: len(v) for k, v in field_types.items()},
            "fields": [field.to_dict() for field in template.fields],
            "created_at": template.created_at.isoformat()
        }
        
        logger.debug(
            "Template info retrieved",
            extra={
                "template_name": template_name,
                "template_info": template_info
            }
        )
        
        return template_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get template info",
            extra={
                "template_name": template_name,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error getting template info: {str(e)}"
        )


@router.post("/{template_name}/validate")
async def validate_template_data(
    template_name: str,
    data: Dict[str, Any]
):
    """Validate form data against template requirements."""
    try:
        container = get_container()
        template_repo = container.get_template_repo()
        
        template = await template_repo.get_template(template_name)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_name} not found"
            )
        
        validation_results = []
        
        # Validate each field
        for field in template.fields:
            field_name = field.field_name
            field_value = data.get(field_name)
            
            # Basic validation
            is_valid = True
            error_message = ""
            
            # Required field validation
            if field.required and (field_value is None or str(field_value).strip() == ""):
                is_valid = False
                error_message = "Trường này là bắt buộc"
            
            # Type-specific validation
            elif field_value is not None and str(field_value).strip():
                if field.field_type.value == "date":
                    import re
                    if not re.match(r'^\d{2}/\d{2}/\d{4}$', str(field_value)):
                        is_valid = False
                        error_message = "Định dạng ngày không đúng. Vui lòng nhập theo format dd/mm/yyyy"
                
                elif field.field_type.value == "number":
                    try:
                        float(str(field_value).replace(",", "").replace(".", ""))
                    except ValueError:
                        is_valid = False
                        error_message = "Giá trị phải là số"
                
                elif field.field_type.value == "email":
                    import re
                    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', str(field_value)):
                        is_valid = False
                        error_message = "Định dạng email không đúng"
            
            validation_results.append({
                "field_name": field_name,
                "field_display_name": field.display_name,
                "is_valid": is_valid,
                "error_message": error_message,
                "value": field_value
            })
        
        # Overall validation status
        all_valid = all(result["is_valid"] for result in validation_results)
        
        result = {
            "template_name": template_name,
            "is_valid": all_valid,
            "validation_results": validation_results,
            "total_fields": len(validation_results),
            "valid_fields": len([r for r in validation_results if r["is_valid"]]),
            "invalid_fields": len([r for r in validation_results if not r["is_valid"]])
        }
        
        logger.info(
            "Template data validated",
            extra={
                "template_name": template_name,
                "is_valid": all_valid,
                "total_fields": len(validation_results)
            }
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to validate template data",
            extra={
                "template_name": template_name,
                "error": str(e)
            },
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Error validating template data: {str(e)}"
        )