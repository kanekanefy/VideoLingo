"""
VideoLingo Version Control Module

This module provides version control functionality for translation management,
allowing users to track, compare, and manage different versions of translations.
"""

from typing import Optional

# Conditional imports to handle missing dependencies
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from .version_manager import VersionManager
    from .translation_diff import TranslationDiffer
    from .version_storage import VersionStorage
    VERSION_CONTROL_AVAILABLE = True
except ImportError as e:
    VERSION_CONTROL_AVAILABLE = False
    _import_error = str(e)

__all__ = [
    'VersionManager',
    'TranslationDiffer', 
    'VersionStorage',
    'VERSION_CONTROL_AVAILABLE',
    'STREAMLIT_AVAILABLE'
]

def get_version_manager() -> Optional['VersionManager']:
    """Get version manager instance if available."""
    if VERSION_CONTROL_AVAILABLE:
        return VersionManager()
    return None