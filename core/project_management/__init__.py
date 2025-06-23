"""
VideoLingo 项目管理模块

提供多项目管理、版本控制、批量处理等专业影视制作功能
"""

from .project_manager import ProjectManager
from .project_templates import ProjectTemplateManager
from .progress_tracker import ProgressTracker

# 条件导入Streamlit相关组件
try:
    from .project_dashboard import create_project_dashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    def create_project_dashboard():
        raise ImportError("Streamlit not available. Install streamlit to use dashboard.")

__all__ = [
    'ProjectManager',
    'ProjectTemplateManager', 
    'ProgressTracker',
    'create_project_dashboard',
    'DASHBOARD_AVAILABLE'
]