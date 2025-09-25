from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid


class FieldType(str, Enum):
    """Form field types."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"


@dataclass
class FormField:
    """Form field definition."""
    field_name: str
    display_name: str
    field_type: FieldType = FieldType.TEXT
    required: bool = False
    description: str = ""
    validation_pattern: Optional[str] = None
    default_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field_name": self.field_name,
            "display_name": self.display_name,
            "field_type": self.field_type.value,
            "required": self.required,
            "description": self.description,
            "validation_pattern": self.validation_pattern,
            "default_value": self.default_value
        }


@dataclass
class FormTemplate:
    """Form template definition."""
    name: str
    display_name: str
    description: str = ""
    fields: List[FormField] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_required_fields(self) -> List[FormField]:
        """Get required fields."""
        return [field for field in self.fields if field.required]
    
    def get_field_by_name(self, field_name: str) -> Optional[FormField]:
        """Get field by name."""
        for field in self.fields:
            if field.field_name == field_name:
                return field
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "fields": [field.to_dict() for field in self.fields],
            "field_count": len(self.fields),
            "required_fields": len(self.get_required_fields()),
            "created_at": self.created_at.isoformat()
        }


@dataclass
class FormData:
    """Form data collection."""
    template_name: str
    data: Dict[str, Any] = field(default_factory=dict)
    validation_errors: Dict[str, str] = field(default_factory=dict)
    is_complete: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def set_field_value(self, field_name: str, value: Any) -> None:
        """Set field value."""
        self.data[field_name] = value
        self.updated_at = datetime.now()
        
        # Clear validation error if exists
        if field_name in self.validation_errors:
            del self.validation_errors[field_name]
    
    def set_validation_error(self, field_name: str, error: str) -> None:
        """Set validation error for field."""
        self.validation_errors[field_name] = error
        self.updated_at = datetime.now()
    
    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.validation_errors.clear()
        self.updated_at = datetime.now()
    
    def has_validation_errors(self) -> bool:
        """Check if has validation errors."""
        return len(self.validation_errors) > 0
    
    def get_completion_percentage(self, template: FormTemplate) -> float:
        """Get form completion percentage."""
        required_fields = template.get_required_fields()
        if not required_fields:
            return 100.0
        
        completed_fields = 0
        for field in required_fields:
            if field.field_name in self.data and self.data[field.field_name]:
                completed_fields += 1
        
        return (completed_fields / len(required_fields)) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_name": self.template_name,
            "data": self.data,
            "validation_errors": self.validation_errors,
            "is_complete": self.is_complete,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class FormCollectionState:
    """State for form data collection process."""
    template_name: str
    current_field_index: int = 0
    questions: List[FormField] = field(default_factory=list)
    form_data: FormData = field(default_factory=FormData)
    is_active: bool = False
    
    def get_current_field(self) -> Optional[FormField]:
        """Get current field being collected."""
        if 0 <= self.current_field_index < len(self.questions):
            return self.questions[self.current_field_index]
        return None
    
    def move_to_next_field(self) -> Optional[FormField]:
        """Move to next field."""
        self.current_field_index += 1
        return self.get_current_field()
    
    def is_complete(self) -> bool:
        """Check if form collection is complete."""
        return self.current_field_index >= len(self.questions)
    
    def reset(self) -> None:
        """Reset form collection state."""
        self.current_field_index = 0
        self.form_data = FormData(template_name=self.template_name)
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "template_name": self.template_name,
            "current_field_index": self.current_field_index,
            "total_fields": len(self.questions),
            "is_active": self.is_active,
            "is_complete": self.is_complete(),
            "current_field": self.get_current_field().to_dict() if self.get_current_field() else None,
            "form_data": self.form_data.to_dict()
        }