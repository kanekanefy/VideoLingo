"""
VideoLingo Emotion Analysis Module

This module provides AI-powered emotion analysis and consistency checking
for translation content, ensuring emotional tone preservation across languages.
"""

from typing import Optional

# Conditional imports to handle missing dependencies
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from .emotion_detector import EmotionDetector, EmotionLabel, EmotionScore
    from .emotion_analyzer import EmotionAnalyzer
    from .consistency_checker import ConsistencyChecker
    EMOTION_ANALYSIS_AVAILABLE = True
except ImportError as e:
    EMOTION_ANALYSIS_AVAILABLE = False
    _import_error = str(e)

__all__ = [
    'EmotionDetector',
    'EmotionLabel',
    'EmotionScore',
    'EmotionAnalyzer', 
    'ConsistencyChecker',
    'EMOTION_ANALYSIS_AVAILABLE',
    'STREAMLIT_AVAILABLE'
]

def get_emotion_analyzer() -> Optional['EmotionAnalyzer']:
    """Get emotion analyzer instance if available."""
    if EMOTION_ANALYSIS_AVAILABLE:
        return EmotionAnalyzer()
    return None