"""
VideoLingo Batch Processing Module

This module provides batch processing capabilities for handling multiple videos
in parallel, with task queuing, progress monitoring, and resource management.
"""

from typing import Optional

# Conditional imports to handle missing dependencies
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from .batch_manager import BatchManager
    from .task_queue import TaskQueue, TaskStatus
    from .job_scheduler import JobScheduler
    BATCH_PROCESSING_AVAILABLE = True
except ImportError as e:
    BATCH_PROCESSING_AVAILABLE = False
    _import_error = str(e)

__all__ = [
    'BatchManager',
    'TaskQueue',
    'TaskStatus', 
    'JobScheduler',
    'BATCH_PROCESSING_AVAILABLE',
    'STREAMLIT_AVAILABLE'
]

def get_batch_manager() -> Optional['BatchManager']:
    """Get batch manager instance if available."""
    if BATCH_PROCESSING_AVAILABLE:
        return BatchManager()
    return None