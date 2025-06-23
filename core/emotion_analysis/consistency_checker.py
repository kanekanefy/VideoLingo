"""
Emotion Consistency Checker Module

Provides advanced consistency checking and cross-validation for emotion analysis.
"""

import json
import statistics
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .emotion_detector import EmotionDetector, EmotionAnalysisResult, EmotionLabel
from .emotion_analyzer import ProjectEmotionAnalysis, SegmentEmotionData

@dataclass
class ConsistencyIssue:
    """Represents a consistency issue."""
    issue_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    segment_ids: List[str]
    confidence: float
    suggested_fix: str

@dataclass
class ConsistencyReport:
    """Complete consistency analysis report."""
    project_id: str
    report_id: str
    generated_at: str
    overall_score: float
    issues: List[ConsistencyIssue]
    segment_scores: Dict[str, float]
    recommendations: List[str]
    quality_metrics: Dict[str, float]

class ConsistencyChecker:
    """Advanced emotion consistency checker."""
    
    def __init__(self):
        self.detector = EmotionDetector()
        
        # Consistency checking thresholds
        self.thresholds = {
            "emotion_similarity": 0.6,
            "sentiment_consistency": 0.7,
            "confidence_variance": 0.3,
            "keyword_preservation": 0.5,
            "context_awareness": 0.6
        }
        
        # Issue severity mapping
        self.severity_mapping = {
            "critical": {"min_score": 0.0, "max_score": 0.3},
            "high": {"min_score": 0.3, "max_score": 0.5},
            "medium": {"min_score": 0.5, "max_score": 0.7},
            "low": {"min_score": 0.7, "max_score": 1.0}
        }
    
    def check_project_consistency(self, analysis: ProjectEmotionAnalysis) -> ConsistencyReport:
        """Perform comprehensive consistency checking on a project."""
        
        # Run various consistency checks
        emotion_issues = self._check_emotion_consistency(analysis.segments)
        sentiment_issues = self._check_sentiment_consistency(analysis.segments)
        confidence_issues = self._check_confidence_consistency(analysis.segments)
        keyword_issues = self._check_keyword_preservation(analysis.segments)
        context_issues = self._check_context_consistency(analysis.segments)
        pattern_issues = self._check_pattern_consistency(analysis.segments)
        
        # Combine all issues
        all_issues = (emotion_issues + sentiment_issues + confidence_issues + 
                     keyword_issues + context_issues + pattern_issues)
        
        # Calculate segment-level consistency scores
        segment_scores = self._calculate_segment_scores(analysis.segments)
        
        # Calculate overall consistency score
        overall_score = self._calculate_overall_score(segment_scores, all_issues)
        
        # Generate recommendations
        recommendations = self._generate_consistency_recommendations(all_issues, overall_score)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(analysis.segments, all_issues)
        
        # Create report
        report = ConsistencyReport(
            project_id=analysis.project_id,
            report_id=f"consistency_{analysis.project_id}_{int(datetime.now().timestamp())}",
            generated_at=datetime.now().isoformat(),
            overall_score=overall_score,
            issues=all_issues,
            segment_scores=segment_scores,
            recommendations=recommendations,
            quality_metrics=quality_metrics
        )
        
        return report
    
    def _check_emotion_consistency(self, segments: List[SegmentEmotionData]) -> List[ConsistencyIssue]:
        """Check for emotion consistency issues."""
        issues = []
        
        for segment in segments:
            original_emotion = segment.original_emotion.primary_emotion.emotion
            translated_emotion = segment.translated_emotion.primary_emotion.emotion
            
            # Check for emotion category mismatches
            if self._are_conflicting_emotions(original_emotion, translated_emotion):
                confidence = 1.0 - segment.emotion_match_score
                
                issues.append(ConsistencyIssue(
                    issue_type="conflicting_emotions",
                    severity=self._determine_severity(confidence),
                    description=f"Conflicting emotions: {original_emotion.value} → {translated_emotion.value}",
                    segment_ids=[segment.segment_id],
                    confidence=confidence,
                    suggested_fix=f"Revise translation to maintain {original_emotion.value} emotion"
                ))
        
        # Check for emotion pattern breaks
        emotion_sequence_issues = self._check_emotion_sequence_consistency(segments)
        issues.extend(emotion_sequence_issues)
        
        return issues
    
    def _check_sentiment_consistency(self, segments: List[SegmentEmotionData]) -> List[ConsistencyIssue]:
        """Check for sentiment consistency issues."""
        issues = []
        
        sentiment_conflicts = []
        
        for segment in segments:
            original_sentiment = segment.original_emotion.overall_sentiment
            translated_sentiment = segment.translated_emotion.overall_sentiment
            
            if original_sentiment != translated_sentiment:
                sentiment_conflicts.append(segment)
        
        # If too many sentiment conflicts, create an issue
        if len(sentiment_conflicts) > len(segments) * 0.2:  # More than 20% conflicts
            confidence = len(sentiment_conflicts) / len(segments)
            
            issues.append(ConsistencyIssue(
                issue_type="widespread_sentiment_conflicts",
                severity=self._determine_severity(confidence),
                description=f"Sentiment conflicts in {len(sentiment_conflicts)} segments",
                segment_ids=[seg.segment_id for seg in sentiment_conflicts],
                confidence=confidence,
                suggested_fix="Review translation approach to preserve sentiment polarity"
            ))
        
        return issues
    
    def _check_confidence_consistency(self, segments: List[SegmentEmotionData]) -> List[ConsistencyIssue]:
        """Check for confidence consistency issues."""
        issues = []
        
        # Collect confidence scores
        original_confidences = [seg.original_emotion.primary_emotion.confidence for seg in segments]
        translated_confidences = [seg.translated_emotion.primary_emotion.confidence for seg in segments]
        
        # Check for large variance in confidence
        if len(translated_confidences) > 1:
            confidence_variance = statistics.variance(translated_confidences)
            
            if confidence_variance > self.thresholds["confidence_variance"]:
                low_confidence_segments = [
                    seg for seg in segments 
                    if seg.translated_emotion.primary_emotion.confidence < 0.4
                ]
                
                if low_confidence_segments:
                    issues.append(ConsistencyIssue(
                        issue_type="inconsistent_confidence",
                        severity=self._determine_severity(confidence_variance),
                        description=f"High variance in emotion detection confidence (σ²={confidence_variance:.3f})",
                        segment_ids=[seg.segment_id for seg in low_confidence_segments],
                        confidence=confidence_variance,
                        suggested_fix="Review low-confidence segments for ambiguous emotional content"
                    ))
        
        return issues
    
    def _check_keyword_preservation(self, segments: List[SegmentEmotionData]) -> List[ConsistencyIssue]:
        """Check for emotional keyword preservation issues."""
        issues = []
        
        segments_with_keyword_loss = []
        
        for segment in segments:
            original_keywords = set(segment.original_emotion.emotional_keywords)
            translated_keywords = set(segment.translated_emotion.emotional_keywords)
            
            if original_keywords:
                preservation_rate = len(translated_keywords) / len(original_keywords)
                
                if preservation_rate < self.thresholds["keyword_preservation"]:
                    segments_with_keyword_loss.append((segment, preservation_rate))
        
        if segments_with_keyword_loss:
            avg_preservation = sum(rate for _, rate in segments_with_keyword_loss) / len(segments_with_keyword_loss)
            confidence = 1.0 - avg_preservation
            
            issues.append(ConsistencyIssue(
                issue_type="poor_keyword_preservation",
                severity=self._determine_severity(confidence),
                description=f"Poor emotional keyword preservation in {len(segments_with_keyword_loss)} segments",
                segment_ids=[seg.segment_id for seg, _ in segments_with_keyword_loss],
                confidence=confidence,
                suggested_fix="Include emotional equivalents for lost keywords in target language"
            ))
        
        return issues
    
    def _check_context_consistency(self, segments: List[SegmentEmotionData]) -> List[ConsistencyIssue]:
        """Check for contextual consistency issues."""
        issues = []
        
        # Check for emotional flow consistency
        if len(segments) > 1:
            flow_breaks = self._detect_emotional_flow_breaks(segments)
            
            if flow_breaks:
                issues.append(ConsistencyIssue(
                    issue_type="emotional_flow_breaks",
                    severity="medium",
                    description=f"Emotional flow inconsistencies detected in {len(flow_breaks)} transitions",
                    segment_ids=[break_info["segment_id"] for break_info in flow_breaks],
                    confidence=len(flow_breaks) / (len(segments) - 1),
                    suggested_fix="Review segment transitions for emotional continuity"
                ))
        
        return issues
    
    def _check_pattern_consistency(self, segments: List[SegmentEmotionData]) -> List[ConsistencyIssue]:
        """Check for pattern consistency issues."""
        issues = []
        
        # Check for systematic emotion downgrades
        downgrades = []
        for segment in segments:
            original_intensity = segment.original_emotion.primary_emotion.intensity
            translated_intensity = segment.translated_emotion.primary_emotion.intensity
            
            if translated_intensity < original_intensity - 0.3:
                downgrades.append(segment)
        
        if len(downgrades) > len(segments) * 0.3:  # More than 30% downgraded
            issues.append(ConsistencyIssue(
                issue_type="systematic_emotion_downgrade",
                severity="high",
                description=f"Systematic emotion intensity reduction in {len(downgrades)} segments",
                segment_ids=[seg.segment_id for seg in downgrades],
                confidence=len(downgrades) / len(segments),
                suggested_fix="Review translation to preserve emotional intensity"
            ))
        
        return issues
    
    def _check_emotion_sequence_consistency(self, segments: List[SegmentEmotionData]) -> List[ConsistencyIssue]:
        """Check for emotion sequence consistency."""
        issues = []
        
        if len(segments) < 3:
            return issues
        
        # Look for patterns in emotion transitions
        original_sequence = [seg.original_emotion.primary_emotion.emotion for seg in segments]
        translated_sequence = [seg.translated_emotion.primary_emotion.emotion for seg in segments]
        
        # Check for major sequence disruptions
        disruptions = 0
        for i in range(len(segments) - 1):
            original_transition = (original_sequence[i], original_sequence[i + 1])
            translated_transition = (translated_sequence[i], translated_sequence[i + 1])
            
            if self._is_disruptive_transition(original_transition, translated_transition):
                disruptions += 1
        
        if disruptions > len(segments) * 0.2:  # More than 20% disruptions
            issues.append(ConsistencyIssue(
                issue_type="emotion_sequence_disruption",
                severity="medium",
                description=f"Emotional sequence disruptions in {disruptions} transitions",
                segment_ids=[segments[i].segment_id for i in range(len(segments) - 1)],
                confidence=disruptions / (len(segments) - 1),
                suggested_fix="Review emotional progression for narrative consistency"
            ))
        
        return issues
    
    def _are_conflicting_emotions(self, emotion1: EmotionLabel, emotion2: EmotionLabel) -> bool:
        """Check if two emotions are conflicting."""
        conflict_pairs = [
            (EmotionLabel.HAPPY, EmotionLabel.SAD),
            (EmotionLabel.HAPPY, EmotionLabel.ANGRY),
            (EmotionLabel.CALM, EmotionLabel.ANXIOUS),
            (EmotionLabel.EXCITED, EmotionLabel.CALM),
            (EmotionLabel.LOVING, EmotionLabel.ANGRY),
            (EmotionLabel.LOVING, EmotionLabel.DISGUSTED)
        ]
        
        return (emotion1, emotion2) in conflict_pairs or (emotion2, emotion1) in conflict_pairs
    
    def _detect_emotional_flow_breaks(self, segments: List[SegmentEmotionData]) -> List[Dict[str, Any]]:
        """Detect breaks in emotional flow between segments."""
        breaks = []
        
        for i in range(len(segments) - 1):
            current_seg = segments[i]
            next_seg = segments[i + 1]
            
            # Check if emotions are drastically different without justification
            original_similarity = self.detector.compare_emotions(
                current_seg.original_emotion, next_seg.original_emotion
            )["emotion_similarity"]
            
            translated_similarity = self.detector.compare_emotions(
                current_seg.translated_emotion, next_seg.translated_emotion
            )["emotion_similarity"]
            
            # If original has good flow but translation breaks it
            if original_similarity > 0.6 and translated_similarity < 0.3:
                breaks.append({
                    "segment_id": next_seg.segment_id,
                    "original_similarity": original_similarity,
                    "translated_similarity": translated_similarity,
                    "break_severity": original_similarity - translated_similarity
                })
        
        return breaks
    
    def _is_disruptive_transition(self, original_transition: Tuple, translated_transition: Tuple) -> bool:
        """Check if a translation disrupts emotional transition."""
        original_start, original_end = original_transition
        translated_start, translated_end = translated_transition
        
        # If original transition makes sense but translated doesn't
        original_compatible = not self._are_conflicting_emotions(original_start, original_end)
        translated_compatible = not self._are_conflicting_emotions(translated_start, translated_end)
        
        return original_compatible and not translated_compatible
    
    def _calculate_segment_scores(self, segments: List[SegmentEmotionData]) -> Dict[str, float]:
        """Calculate consistency scores for individual segments."""
        scores = {}
        
        for segment in segments:
            # Base score from emotion match
            emotion_score = segment.emotion_match_score
            
            # Penalize for consistency issues
            issue_penalty = len(segment.consistency_issues) * 0.1
            
            # Boost for high confidence
            confidence_boost = (
                segment.original_emotion.primary_emotion.confidence * 
                segment.translated_emotion.primary_emotion.confidence
            ) * 0.2
            
            final_score = max(0.0, min(1.0, emotion_score + confidence_boost - issue_penalty))
            scores[segment.segment_id] = final_score
        
        return scores
    
    def _calculate_overall_score(self, segment_scores: Dict[str, float], issues: List[ConsistencyIssue]) -> float:
        """Calculate overall consistency score."""
        if not segment_scores:
            return 0.0
        
        # Base score from segment averages
        base_score = sum(segment_scores.values()) / len(segment_scores)
        
        # Apply penalties for issues
        total_penalty = 0.0
        for issue in issues:
            severity_penalty = {
                "critical": 0.3,
                "high": 0.2,
                "medium": 0.1,
                "low": 0.05
            }.get(issue.severity, 0.1)
            
            total_penalty += severity_penalty * issue.confidence
        
        final_score = max(0.0, min(1.0, base_score - total_penalty))
        return final_score
    
    def _determine_severity(self, confidence: float) -> str:
        """Determine issue severity based on confidence score."""
        for severity, range_info in self.severity_mapping.items():
            if range_info["min_score"] <= confidence <= range_info["max_score"]:
                return severity
        return "medium"  # Default
    
    def _generate_consistency_recommendations(self, issues: List[ConsistencyIssue], overall_score: float) -> List[str]:
        """Generate recommendations based on consistency analysis."""
        recommendations = []
        
        # Overall score-based recommendations
        if overall_score < 0.4:
            recommendations.append(
                "Overall emotion consistency is very low. Consider comprehensive review of translation approach."
            )
        elif overall_score < 0.7:
            recommendations.append(
                "Emotion consistency needs improvement. Focus on preserving emotional tone."
            )
        
        # Issue-specific recommendations
        issue_counts = {}
        for issue in issues:
            issue_counts[issue.issue_type] = issue_counts.get(issue.issue_type, 0) + 1
        
        for issue_type, count in issue_counts.items():
            if issue_type == "conflicting_emotions" and count > 3:
                recommendations.append(
                    "Multiple conflicting emotions detected. Review emotion preservation strategies."
                )
            elif issue_type == "poor_keyword_preservation" and count > 0:
                recommendations.append(
                    "Emotional keywords are being lost in translation. Create emotion-focused glossary."
                )
            elif issue_type == "systematic_emotion_downgrade" and count > 0:
                recommendations.append(
                    "Emotions are consistently weakened in translation. Use stronger emotional language."
                )
        
        # Critical issues
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        if critical_issues:
            recommendations.append(
                f"Address {len(critical_issues)} critical emotion consistency issues immediately."
            )
        
        return recommendations
    
    def _calculate_quality_metrics(self, segments: List[SegmentEmotionData], issues: List[ConsistencyIssue]) -> Dict[str, float]:
        """Calculate detailed quality metrics."""
        if not segments:
            return {}
        
        # Basic metrics
        total_segments = len(segments)
        segments_with_issues = len([seg for seg in segments if seg.consistency_issues])
        
        # Emotion match statistics
        emotion_matches = sum(1 for seg in segments 
                            if seg.original_emotion.primary_emotion.emotion == 
                               seg.translated_emotion.primary_emotion.emotion)
        
        # Sentiment match statistics
        sentiment_matches = sum(1 for seg in segments 
                              if seg.original_emotion.overall_sentiment == 
                                 seg.translated_emotion.overall_sentiment)
        
        # Confidence statistics
        avg_original_confidence = sum(seg.original_emotion.primary_emotion.confidence for seg in segments) / total_segments
        avg_translated_confidence = sum(seg.translated_emotion.primary_emotion.confidence for seg in segments) / total_segments
        
        # Issue statistics
        critical_issues = len([issue for issue in issues if issue.severity == "critical"])
        high_issues = len([issue for issue in issues if issue.severity == "high"])
        
        return {
            "emotion_match_rate": emotion_matches / total_segments,
            "sentiment_match_rate": sentiment_matches / total_segments,
            "segments_with_issues_rate": segments_with_issues / total_segments,
            "avg_original_confidence": avg_original_confidence,
            "avg_translated_confidence": avg_translated_confidence,
            "confidence_drop": max(0, avg_original_confidence - avg_translated_confidence),
            "critical_issues_count": critical_issues,
            "high_issues_count": high_issues,
            "total_issues_count": len(issues)
        }