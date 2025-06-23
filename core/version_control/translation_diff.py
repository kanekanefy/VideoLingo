"""
Translation Difference Analysis Module

Provides functionality to compare and visualize differences between translation versions.
"""

import difflib
import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class ChangeType(Enum):
    """Types of changes between versions."""
    ADDED = "added"
    DELETED = "deleted" 
    MODIFIED = "modified"
    UNCHANGED = "unchanged"

@dataclass
class SegmentDiff:
    """Difference information for a single segment."""
    segment_id: str
    change_type: ChangeType
    old_text: Optional[str]
    new_text: Optional[str]
    similarity_score: float
    position: int

@dataclass
class VersionDiff:
    """Complete difference analysis between two versions."""
    old_version_id: str
    new_version_id: str
    old_version_number: str
    new_version_number: str
    segment_diffs: List[SegmentDiff]
    summary: Dict[str, Any]
    overall_similarity: float

class TranslationDiffer:
    """Analyzes differences between translation versions."""
    
    def __init__(self):
        self.similarity_threshold = 0.8
    
    def compare_versions(
        self,
        old_version: Dict[str, Any],
        new_version: Dict[str, Any]
    ) -> VersionDiff:
        """Compare two translation versions and return detailed diff."""
        
        old_segments = old_version.get('content', {}).get('segments', [])
        new_segments = new_version.get('content', {}).get('segments', [])
        
        segment_diffs = self._compare_segments(old_segments, new_segments)
        summary = self._generate_summary(segment_diffs)
        overall_similarity = self._calculate_overall_similarity(segment_diffs)
        
        return VersionDiff(
            old_version_id=old_version['version_id'],
            new_version_id=new_version['version_id'],
            old_version_number=old_version['version_number'],
            new_version_number=new_version['version_number'],
            segment_diffs=segment_diffs,
            summary=summary,
            overall_similarity=overall_similarity
        )
    
    def _compare_segments(
        self,
        old_segments: List[Dict[str, Any]],
        new_segments: List[Dict[str, Any]]
    ) -> List[SegmentDiff]:
        """Compare individual segments between versions."""
        
        segment_diffs = []
        
        # Create segment ID mappings
        old_segments_map = {seg.get('id', i): seg for i, seg in enumerate(old_segments)}
        new_segments_map = {seg.get('id', i): seg for i, seg in enumerate(new_segments)}
        
        all_segment_ids = set(old_segments_map.keys()) | set(new_segments_map.keys())
        
        for i, segment_id in enumerate(sorted(all_segment_ids)):
            old_segment = old_segments_map.get(segment_id)
            new_segment = new_segments_map.get(segment_id)
            
            # Determine change type and similarity
            if old_segment and new_segment:
                old_text = old_segment.get('text', '')
                new_text = new_segment.get('text', '')
                
                if old_text == new_text:
                    change_type = ChangeType.UNCHANGED
                    similarity = 1.0
                else:
                    change_type = ChangeType.MODIFIED
                    similarity = self._calculate_text_similarity(old_text, new_text)
                
                segment_diff = SegmentDiff(
                    segment_id=str(segment_id),
                    change_type=change_type,
                    old_text=old_text,
                    new_text=new_text,
                    similarity_score=similarity,
                    position=i
                )
            
            elif old_segment and not new_segment:
                segment_diff = SegmentDiff(
                    segment_id=str(segment_id),
                    change_type=ChangeType.DELETED,
                    old_text=old_segment.get('text', ''),
                    new_text=None,
                    similarity_score=0.0,
                    position=i
                )
            
            else:  # new_segment and not old_segment
                segment_diff = SegmentDiff(
                    segment_id=str(segment_id),
                    change_type=ChangeType.ADDED,
                    old_text=None,
                    new_text=new_segment.get('text', ''),
                    similarity_score=0.0,
                    position=i
                )
            
            segment_diffs.append(segment_diff)
        
        return segment_diffs
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        # Use SequenceMatcher for similarity calculation
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def _generate_summary(self, segment_diffs: List[SegmentDiff]) -> Dict[str, Any]:
        """Generate summary statistics for the differences."""
        if not segment_diffs:
            return {
                "total_segments": 0,
                "unchanged": 0,
                "modified": 0,
                "added": 0,
                "deleted": 0,
                "change_percentage": 0.0
            }
        
        counts = {
            ChangeType.UNCHANGED: 0,
            ChangeType.MODIFIED: 0,
            ChangeType.ADDED: 0,
            ChangeType.DELETED: 0
        }
        
        for diff in segment_diffs:
            counts[diff.change_type] += 1
        
        total = len(segment_diffs)
        changed = counts[ChangeType.MODIFIED] + counts[ChangeType.ADDED] + counts[ChangeType.DELETED]
        
        return {
            "total_segments": total,
            "unchanged": counts[ChangeType.UNCHANGED],
            "modified": counts[ChangeType.MODIFIED],
            "added": counts[ChangeType.ADDED],
            "deleted": counts[ChangeType.DELETED],
            "change_percentage": (changed / total * 100) if total > 0 else 0.0
        }
    
    def _calculate_overall_similarity(self, segment_diffs: List[SegmentDiff]) -> float:
        """Calculate overall similarity score."""
        if not segment_diffs:
            return 1.0
        
        total_similarity = sum(diff.similarity_score for diff in segment_diffs)
        return total_similarity / len(segment_diffs)
    
    def get_detailed_diff_html(self, segment_diff: SegmentDiff) -> str:
        """Generate HTML diff view for a segment."""
        if segment_diff.change_type == ChangeType.UNCHANGED:
            return f'<div class="diff-unchanged">{segment_diff.old_text}</div>'
        
        elif segment_diff.change_type == ChangeType.ADDED:
            return f'<div class="diff-added">+ {segment_diff.new_text}</div>'
        
        elif segment_diff.change_type == ChangeType.DELETED:
            return f'<div class="diff-deleted">- {segment_diff.old_text}</div>'
        
        elif segment_diff.change_type == ChangeType.MODIFIED:
            # Generate word-level diff
            old_words = segment_diff.old_text.split() if segment_diff.old_text else []
            new_words = segment_diff.new_text.split() if segment_diff.new_text else []
            
            diff = difflib.unified_diff(old_words, new_words, lineterm='')
            
            html_parts = []
            html_parts.append('<div class="diff-modified">')
            html_parts.append(f'<div class="diff-old">- {segment_diff.old_text}</div>')
            html_parts.append(f'<div class="diff-new">+ {segment_diff.new_text}</div>')
            html_parts.append('</div>')
            
            return ''.join(html_parts)
        
        return ""
    
    def export_diff_report(self, version_diff: VersionDiff) -> Dict[str, Any]:
        """Export difference report in structured format."""
        return {
            "comparison_info": {
                "old_version": {
                    "id": version_diff.old_version_id,
                    "number": version_diff.old_version_number
                },
                "new_version": {
                    "id": version_diff.new_version_id,
                    "number": version_diff.new_version_number
                },
                "overall_similarity": version_diff.overall_similarity
            },
            "summary": version_diff.summary,
            "changes": [
                {
                    "segment_id": diff.segment_id,
                    "change_type": diff.change_type.value,
                    "old_text": diff.old_text,
                    "new_text": diff.new_text,
                    "similarity_score": diff.similarity_score,
                    "position": diff.position
                }
                for diff in version_diff.segment_diffs
                if diff.change_type != ChangeType.UNCHANGED
            ]
        }
    
    def find_similar_segments(
        self,
        segments: List[Dict[str, Any]],
        query_text: str,
        threshold: float = 0.7
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Find segments similar to query text."""
        results = []
        
        for segment in segments:
            text = segment.get('text', '')
            similarity = self._calculate_text_similarity(query_text, text)
            
            if similarity >= threshold:
                results.append((segment, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        return results