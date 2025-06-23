"""
VideoLingo 专业名词管理模块

此模块提供专业术语的提取、管理和一致性检查功能。
主要功能：
- 自动提取专业术语
- 术语库管理
- 术语一致性验证
- 术语编辑界面
"""

from .term_extractor import extract_terms, extract_terms_from_translation
from .term_manager import TermManager
from .term_validator import validate_terminology_consistency
from .term_editor import create_term_editor_interface

__all__ = [
    'extract_terms',
    'extract_terms_from_translation', 
    'TermManager',
    'validate_terminology_consistency',
    'create_term_editor_interface'
]