import os
import docx
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.core.interfaces.repositories import TemplateRepository
from src.core.entities.form import FormTemplate, FormField, FieldType
from src.infrastructure.logging.context import get_logger

logger = get_logger(__name__)


class MemoryTemplateRepository(TemplateRepository):
    """In-memory implementation of template repository."""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self._templates: Dict[str, FormTemplate] = {}
        
        # Load templates from directory
        self._load_templates()
    
    def _load_templates(self):
        """Load templates from directory."""
        try:
            if not self.templates_dir.exists():
                logger.warning(f"Templates directory not found: {self.templates_dir}")
                return
            
            # Predefined template configurations
            template_configs = {
                "danh_sach_chu_so_huu.docx": {
                    "display_name": "Danh sách chủ sở hữu",
                    "description": "Danh sách thông tin chủ sở hữu công ty",
                    "fields": [
                        {
                            "field_name": "chu_so_huu_ho_ten",
                            "display_name": "Họ và tên chủ sở hữu",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Họ và tên đầy đủ của chủ sở hữu công ty"
                        },
                        {
                            "field_name": "chu_so_huu_cccd",
                            "display_name": "Số CMND/CCCD",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Số chứng minh nhân dân hoặc căn cước công dân"
                        },
                        {
                            "field_name": "chu_so_huu_ngay_sinh",
                            "display_name": "Ngày sinh",
                            "field_type": FieldType.DATE,
                            "required": True,
                            "description": "Ngày sinh của chủ sở hữu (dd/mm/yyyy)"
                        },
                        {
                            "field_name": "chu_so_huu_dia_chi",
                            "display_name": "Địa chỉ thường trú",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Địa chỉ thường trú của chủ sở hữu"
                        },
                        {
                            "field_name": "chu_so_huu_dien_thoai",
                            "display_name": "Số điện thoại",
                            "field_type": FieldType.PHONE,
                            "required": False,
                            "description": "Số điện thoại liên hệ"
                        }
                    ]
                },
                "danh_sach_co_dong.docx": {
                    "display_name": "Danh sách cổ đông",
                    "description": "Danh sách thông tin cổ đông công ty",
                    "fields": [
                        {
                            "field_name": "co_dong_ho_ten",
                            "display_name": "Họ và tên cổ đông",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Họ và tên đầy đủ của cổ đông"
                        },
                        {
                            "field_name": "co_dong_cccd",
                            "display_name": "Số CMND/CCCD",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Số chứng minh nhân dân hoặc căn cước công dân"
                        },
                        {
                            "field_name": "co_dong_ty_le_von",
                            "display_name": "Tỷ lệ góp vốn (%)",
                            "field_type": FieldType.NUMBER,
                            "required": True,
                            "description": "Tỷ lệ phần trăm góp vốn của cổ đông"
                        },
                        {
                            "field_name": "co_dong_gia_tri_von",
                            "display_name": "Giá trị vốn góp (VNĐ)",
                            "field_type": FieldType.NUMBER,
                            "required": True,
                            "description": "Giá trị vốn góp bằng tiền (VNĐ)"
                        }
                    ]
                },
                "dieu_le_cong_ty.docx": {
                    "display_name": "Điều lệ công ty",
                    "description": "Thông tin điều lệ công ty",
                    "fields": [
                        {
                            "field_name": "ten_cong_ty",
                            "display_name": "Tên công ty",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Tên đầy đủ của công ty"
                        },
                        {
                            "field_name": "ten_cong_ty_tieng_anh",
                            "display_name": "Tên công ty (tiếng Anh)",
                            "field_type": FieldType.TEXT,
                            "required": False,
                            "description": "Tên công ty bằng tiếng Anh (nếu có)"
                        },
                        {
                            "field_name": "dia_chi_tru_so",
                            "display_name": "Địa chỉ trụ sở chính",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Địa chỉ đầy đủ của trụ sở chính công ty"
                        },
                        {
                            "field_name": "von_dieu_le",
                            "display_name": "Vốn điều lệ (VNĐ)",
                            "field_type": FieldType.NUMBER,
                            "required": True,
                            "description": "Vốn điều lệ của công ty (VNĐ)"
                        },
                        {
                            "field_name": "nganh_nghe_kinh_doanh",
                            "display_name": "Ngành nghề kinh doanh",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Mô tả chi tiết các ngành nghề kinh doanh"
                        }
                    ]
                },
                "giay_de_nghi.docx": {
                    "display_name": "Giấy đề nghị đăng ký doanh nghiệp",
                    "description": "Đơn đề nghị đăng ký doanh nghiệp",
                    "fields": [
                        {
                            "field_name": "nguoi_dai_dien",
                            "display_name": "Người đại diện pháp luật",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Họ tên người đại diện pháp luật"
                        },
                        {
                            "field_name": "chuc_vu_dai_dien",
                            "display_name": "Chức vụ",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Chức vụ của người đại diện (Giám đốc, Tổng Giám đốc, ...)"
                        },
                        {
                            "field_name": "ngay_lap_don",
                            "display_name": "Ngày lập đơn",
                            "field_type": FieldType.DATE,
                            "required": True,
                            "description": "Ngày lập đơn đăng ký (dd/mm/yyyy)"
                        }
                    ]
                },
                "giay_uy_quyen.docx": {
                    "display_name": "Giấy ủy quyền",
                    "description": "Giấy ủy quyền thực hiện thủ tục",
                    "fields": [
                        {
                            "field_name": "nguoi_uy_quyen",
                            "display_name": "Người ủy quyền",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Họ tên người ủy quyền"
                        },
                        {
                            "field_name": "nguoi_duoc_uy_quyen",
                            "display_name": "Người được ủy quyền",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Họ tên người được ủy quyền"
                        },
                        {
                            "field_name": "noi_dung_uy_quyen",
                            "display_name": "Nội dung ủy quyền",
                            "field_type": FieldType.TEXT,
                            "required": True,
                            "description": "Mô tả cụ thể những việc được ủy quyền"
                        }
                    ]
                }
            }
            
            # Create templates
            for template_name, config in template_configs.items():
                template_path = self.templates_dir / template_name
                
                # Check if template file exists
                if template_path.exists():
                    # Create form fields
                    fields = []
                    for field_config in config["fields"]:
                        field = FormField(
                            field_name=field_config["field_name"],
                            display_name=field_config["display_name"],
                            field_type=field_config["field_type"],
                            required=field_config["required"],
                            description=field_config["description"]
                        )
                        fields.append(field)
                    
                    # Create template
                    template = FormTemplate(
                        name=template_name,
                        display_name=config["display_name"],
                        description=config["description"],
                        fields=fields
                    )
                    
                    self._templates[template_name] = template
                    
                    logger.info(
                        "Template loaded",
                        extra={
                            "template_name": template_name,
                            "field_count": len(fields)
                        }
                    )
                else:
                    logger.warning(
                        "Template file not found",
                        extra={"template_path": str(template_path)}
                    )
            
            logger.info(
                "Templates loaded successfully",
                extra={"template_count": len(self._templates)}
            )
            
        except Exception as e:
            logger.error(
                "Failed to load templates",
                extra={"error": str(e)},
                exc_info=True
            )
    
    async def get_template(self, template_name: str) -> Optional[FormTemplate]:
        """Get template by name."""
        return self._templates.get(template_name)
    
    async def list_templates(self) -> List[FormTemplate]:
        """List all templates."""
        return list(self._templates.values())
    
    async def save_template(self, template: FormTemplate) -> None:
        """Save template."""
        self._templates[template.name] = template
        
        logger.info(
            "Template saved",
            extra={
                "template_name": template.name,
                "field_count": len(template.fields)
            }
        )