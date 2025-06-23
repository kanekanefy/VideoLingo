"""
Emotion Analysis Module

High-level interface for emotion analysis and management in video translation projects.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

from .emotion_detector import EmotionDetector, EmotionAnalysisResult, EmotionLabel, EmotionScore

@dataclass
class SegmentEmotionData:
    """Emotion data for a translation segment."""
    segment_id: str
    original_text: str
    translated_text: str
    original_emotion: EmotionAnalysisResult
    translated_emotion: EmotionAnalysisResult
    emotion_match_score: float
    consistency_issues: List[str]
    recommendations: List[str]

@dataclass
class ProjectEmotionAnalysis:
    """Complete emotion analysis for a project."""
    project_id: str
    analysis_id: str
    created_at: str
    source_language: str
    target_language: str
    segments: List[SegmentEmotionData]
    overall_consistency: float
    emotion_distribution: Dict[str, int]
    quality_issues: List[Dict[str, Any]]
    recommendations: List[str]

class EmotionAnalyzer:
    """High-level emotion analysis manager."""
    
    def __init__(self, storage_dir: str = "emotion_analysis"):
        self.detector = EmotionDetector()
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Analysis thresholds
        self.consistency_threshold = 0.7
        self.emotion_match_threshold = 0.6
        self.quality_thresholds = {
            "low_confidence": 0.4,
            "emotion_mismatch": 0.5,
            "sentiment_conflict": 0.3
        }
    
    def analyze_project_emotions(
        self,
        project_id: str,
        translation_data: Dict[str, Any],
        source_language: str = "en",
        target_language: str = "zh-CN"
    ) -> ProjectEmotionAnalysis:
        """Analyze emotions for an entire translation project."""
        
        segments = translation_data.get("segments", [])
        if not segments:
            raise ValueError("No segments found in translation data")
        
        # Analyze each segment
        segment_emotions = []
        for segment in segments:
            segment_emotion = self._analyze_segment_emotion(
                segment, source_language, target_language
            )
            segment_emotions.append(segment_emotion)
        
        # Calculate overall metrics
        overall_consistency = self._calculate_overall_consistency(segment_emotions)
        emotion_distribution = self._calculate_emotion_distribution(segment_emotions)
        quality_issues = self._identify_quality_issues(segment_emotions)
        recommendations = self._generate_recommendations(segment_emotions, quality_issues)
        
        # Create analysis result
        analysis = ProjectEmotionAnalysis(
            project_id=project_id,
            analysis_id=f"emotion_{project_id}_{int(datetime.now().timestamp())}",
            created_at=datetime.now().isoformat(),
            source_language=source_language,
            target_language=target_language,
            segments=segment_emotions,
            overall_consistency=overall_consistency,
            emotion_distribution=emotion_distribution,
            quality_issues=quality_issues,
            recommendations=recommendations
        )
        
        # Save analysis
        self._save_analysis(analysis)
        
        return analysis
    
    def _analyze_segment_emotion(
        self,
        segment: Dict[str, Any],
        source_language: str,
        target_language: str
    ) -> SegmentEmotionData:
        """Analyze emotion for a single segment."""
        
        segment_id = str(segment.get("id", "unknown"))
        original_text = segment.get("original_text", segment.get("text", ""))
        translated_text = segment.get("translated_text", segment.get("translation", ""))
        
        if not original_text or not translated_text:
            # Create default emotion data for missing text
            default_emotion = EmotionAnalysisResult(
                text="",
                primary_emotion=EmotionScore(EmotionLabel.NEUTRAL, 0.0, 0.0, []),
                secondary_emotions=[],
                overall_sentiment="neutral",
                emotional_keywords=[],
                analysis_timestamp=datetime.now().timestamp()
            )
            
            return SegmentEmotionData(
                segment_id=segment_id,
                original_text=original_text,
                translated_text=translated_text,
                original_emotion=default_emotion,
                translated_emotion=default_emotion,
                emotion_match_score=0.0,
                consistency_issues=["Missing text for analysis"],
                recommendations=["Provide complete text for accurate emotion analysis"]
            )
        
        # Analyze emotions
        original_emotion = self.detector.detect_emotion(original_text, source_language)
        translated_emotion = self.detector.detect_emotion(translated_text, target_language)
        
        # Calculate emotion match score
        emotion_comparison = self.detector.compare_emotions(original_emotion, translated_emotion)
        emotion_match_score = emotion_comparison["emotion_similarity"]
        
        # Identify consistency issues
        consistency_issues = self._identify_segment_issues(
            original_emotion, translated_emotion, emotion_comparison
        )
        
        # Generate recommendations
        recommendations = self._generate_segment_recommendations(
            original_emotion, translated_emotion, consistency_issues
        )
        
        return SegmentEmotionData(
            segment_id=segment_id,
            original_text=original_text,
            translated_text=translated_text,
            original_emotion=original_emotion,
            translated_emotion=translated_emotion,
            emotion_match_score=emotion_match_score,
            consistency_issues=consistency_issues,
            recommendations=recommendations
        )
    
    def _identify_segment_issues(
        self,
        original_emotion: EmotionAnalysisResult,
        translated_emotion: EmotionAnalysisResult,
        comparison: Dict[str, Any]
    ) -> List[str]:
        """Identify consistency issues for a segment."""
        issues = []
        
        # Check primary emotion match
        if not comparison["primary_emotion_match"]:
            issues.append(
                f"Primary emotion mismatch: {original_emotion.primary_emotion.emotion.value} "
                f"→ {translated_emotion.primary_emotion.emotion.value}"
            )
        
        # Check sentiment match
        if not comparison["sentiment_match"]:
            issues.append(
                f"Sentiment mismatch: {original_emotion.overall_sentiment} "
                f"→ {translated_emotion.overall_sentiment}"
            )
        
        # Check confidence differences
        if comparison["confidence_diff"] > 0.4:
            issues.append(
                f"Large confidence difference: {comparison['confidence_diff']:.2f}"
            )
        
        # Check low emotion similarity
        if comparison["emotion_similarity"] < self.emotion_match_threshold:
            issues.append(
                f"Low emotion similarity: {comparison['emotion_similarity']:.2f}"
            )
        
        # Check for lost emotional keywords
        original_keywords = set(original_emotion.emotional_keywords)
        translated_keywords = set(translated_emotion.emotional_keywords)
        lost_keywords = original_keywords - translated_keywords
        
        if len(lost_keywords) > 0:
            issues.append(f"Lost emotional keywords: {', '.join(list(lost_keywords)[:3])}")
        
        return issues
    
    def _generate_segment_recommendations(
        self,
        original_emotion: EmotionAnalysisResult,
        translated_emotion: EmotionAnalysisResult,
        issues: List[str]
    ) -> List[str]:
        """Generate recommendations for improving emotion consistency."""
        recommendations = []
        
        if any("Primary emotion mismatch" in issue for issue in issues):
            recommendations.append(
                f"Consider revising translation to better convey {original_emotion.primary_emotion.emotion.value} emotion"
            )
        
        if any("Sentiment mismatch" in issue for issue in issues):
            recommendations.append(
                f"Adjust translation to maintain {original_emotion.overall_sentiment} sentiment"
            )
        
        if any("Lost emotional keywords" in issue for issue in issues):
            recommendations.append(
                "Include emotional equivalents for lost keywords in target language"
            )
        
        if any("Low emotion similarity" in issue for issue in issues):
            recommendations.append(
                "Review translation for emotional tone preservation"
            )
        
        # Suggest specific emotional words if confidence is low
        if translated_emotion.primary_emotion.confidence < 0.5:
            recommendations.append(
                "Consider using stronger emotional language to convey intended feeling"
            )
        
        return recommendations
    
    def _calculate_overall_consistency(self, segment_emotions: List[SegmentEmotionData]) -> float:
        """Calculate overall emotion consistency score."""
        if not segment_emotions:
            return 0.0
        
        total_score = sum(seg.emotion_match_score for seg in segment_emotions)
        return total_score / len(segment_emotions)
    
    def _calculate_emotion_distribution(self, segment_emotions: List[SegmentEmotionData]) -> Dict[str, int]:
        """Calculate distribution of emotions across segments."""
        distribution = {}
        
        for segment in segment_emotions:
            primary_emotion = segment.original_emotion.primary_emotion.emotion.value
            distribution[primary_emotion] = distribution.get(primary_emotion, 0) + 1
        
        return distribution
    
    def _identify_quality_issues(self, segment_emotions: List[SegmentEmotionData]) -> List[Dict[str, Any]]:
        """Identify overall quality issues in the project."""
        issues = []
        
        # Calculate statistics
        total_segments = len(segment_emotions)
        segments_with_issues = len([seg for seg in segment_emotions if seg.consistency_issues])
        low_confidence_segments = len([
            seg for seg in segment_emotions 
            if seg.translated_emotion.primary_emotion.confidence < self.quality_thresholds["low_confidence"]
        ])
        
        # Issue: High percentage of segments with problems
        if segments_with_issues / total_segments > 0.3:
            issues.append({
                "type": "high_inconsistency",
                "severity": "high",
                "description": f"{segments_with_issues}/{total_segments} segments have emotion consistency issues",
                "affected_segments": segments_with_issues
            })
        
        # Issue: Many low-confidence emotion detections
        if low_confidence_segments / total_segments > 0.2:
            issues.append({
                "type": "low_confidence",
                "severity": "medium",
                "description": f"{low_confidence_segments} segments have low emotion detection confidence",
                "affected_segments": low_confidence_segments
            })
        
        # Issue: Dominant emotion loss
        original_emotions = [seg.original_emotion.primary_emotion.emotion for seg in segment_emotions]
        translated_emotions = [seg.translated_emotion.primary_emotion.emotion for seg in segment_emotions]
        
        from collections import Counter
        original_counts = Counter(original_emotions)
        translated_counts = Counter(translated_emotions)
        
        for emotion, original_count in original_counts.items():
            translated_count = translated_counts.get(emotion, 0)
            loss_rate = (original_count - translated_count) / original_count
            
            if loss_rate > 0.5 and original_count >= 3:
                issues.append({
                    "type": "emotion_loss",
                    "severity": "high",
                    "description": f"Significant loss of {emotion.value} emotion in translation",
                    "emotion": emotion.value,
                    "loss_rate": loss_rate
                })
        
        return issues
    
    def _generate_recommendations(
        self,
        segment_emotions: List[SegmentEmotionData],
        quality_issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate overall recommendations for the project."""
        recommendations = []
        
        # Recommendations based on quality issues
        for issue in quality_issues:
            if issue["type"] == "high_inconsistency":
                recommendations.append(
                    "Review translations for emotional tone preservation. "
                    "Consider using emotion-aware translation guidelines."
                )
            
            elif issue["type"] == "low_confidence":
                recommendations.append(
                    "Many segments have ambiguous emotional content. "
                    "Consider clarifying emotional expressions in translation."
                )
            
            elif issue["type"] == "emotion_loss":
                recommendations.append(
                    f"Focus on preserving {issue['emotion']} emotion in translation. "
                    f"Review cultural adaptation of emotional expressions."
                )
        
        # General recommendations based on consistency score
        overall_consistency = self._calculate_overall_consistency(segment_emotions)
        
        if overall_consistency < 0.5:
            recommendations.append(
                "Overall emotion consistency is low. Consider comprehensive review of translation approach."
            )
        elif overall_consistency < 0.7:
            recommendations.append(
                "Emotion consistency can be improved. Focus on emotional keyword preservation."
            )
        
        # Specific recommendations for frequent issues
        common_issues = {}
        for segment in segment_emotions:
            for issue in segment.consistency_issues:
                issue_type = issue.split(":")[0]
                common_issues[issue_type] = common_issues.get(issue_type, 0) + 1
        
        for issue_type, count in common_issues.items():
            if count >= len(segment_emotions) * 0.2:  # If issue affects 20% or more segments
                if issue_type == "Primary emotion mismatch":
                    recommendations.append(
                        "Frequent primary emotion mismatches detected. "
                        "Review emotion preservation strategies."
                    )
                elif issue_type == "Sentiment mismatch":
                    recommendations.append(
                        "Frequent sentiment conflicts detected. "
                        "Ensure positive/negative tone consistency."
                    )
        
        return recommendations
    
    def _save_analysis(self, analysis: ProjectEmotionAnalysis):
        """Save emotion analysis to storage."""
        analysis_file = self.storage_dir / f"{analysis.analysis_id}.json"
        
        # Convert to serializable format
        analysis_data = asdict(analysis)
        
        # Handle datetime serialization
        analysis_data["created_at"] = analysis.created_at
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2, default=str)
    
    def load_analysis(self, analysis_id: str) -> Optional[ProjectEmotionAnalysis]:
        """Load emotion analysis from storage."""
        analysis_file = self.storage_dir / f"{analysis_id}.json"
        
        if not analysis_file.exists():
            return None
        
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct the analysis object
            # Note: This is simplified - full reconstruction would need to rebuild nested objects
            return ProjectEmotionAnalysis(**data)
        
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return None
    
    def list_project_analyses(self, project_id: str) -> List[Dict[str, Any]]:
        """List all emotion analyses for a project."""
        analyses = []
        
        for analysis_file in self.storage_dir.glob("*.json"):
            try:
                with open(analysis_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get("project_id") == project_id:
                    analyses.append({
                        "analysis_id": data["analysis_id"],
                        "created_at": data["created_at"],
                        "overall_consistency": data.get("overall_consistency", 0),
                        "segments_count": len(data.get("segments", [])),
                        "quality_issues_count": len(data.get("quality_issues", []))
                    })
            
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        
        # Sort by creation time (newest first)
        analyses.sort(key=lambda x: x["created_at"], reverse=True)
        
        return analyses
    
    def get_project_emotion_summary(self, project_id: str) -> Dict[str, Any]:
        """Get emotion analysis summary for a project."""
        analyses = self.list_project_analyses(project_id)
        
        if not analyses:
            return {
                "project_id": project_id,
                "total_analyses": 0,
                "latest_consistency": None,
                "average_consistency": None,
                "improvement_trend": None
            }
        
        latest_analysis = analyses[0]
        consistency_scores = []
        
        # Get detailed data for trend analysis
        for analysis_info in analyses:
            consistency_scores.append(analysis_info["overall_consistency"])
        
        # Calculate trend
        improvement_trend = "stable"
        if len(consistency_scores) >= 2:
            recent_avg = sum(consistency_scores[:3]) / min(3, len(consistency_scores))
            older_avg = sum(consistency_scores[-3:]) / min(3, len(consistency_scores))
            
            if recent_avg > older_avg + 0.1:
                improvement_trend = "improving"
            elif recent_avg < older_avg - 0.1:
                improvement_trend = "declining"
        
        return {
            "project_id": project_id,
            "total_analyses": len(analyses),
            "latest_consistency": latest_analysis["overall_consistency"],
            "average_consistency": sum(consistency_scores) / len(consistency_scores),
            "improvement_trend": improvement_trend,
            "latest_analysis_id": latest_analysis["analysis_id"]
        }