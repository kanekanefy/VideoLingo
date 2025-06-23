"""
Translation Version Management Module

Provides high-level interface for managing translation versions,
including creating, comparing, and managing translation iterations.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .version_storage import VersionStorage, TranslationVersion
from .translation_diff import TranslationDiffer, VersionDiff

class VersionManager:
    """High-level manager for translation versions."""
    
    def __init__(self, storage_dir: str = "version_storage"):
        self.storage = VersionStorage(storage_dir)
        self.differ = TranslationDiffer()
        self.auto_backup_enabled = True
        self.max_versions_per_project = 50
    
    def create_version(
        self,
        project_id: str,
        translation_data: Dict[str, Any],
        version_number: Optional[str] = None,
        description: str = "",
        tags: List[str] = None,
        auto_increment: bool = True
    ) -> TranslationVersion:
        """Create a new translation version."""
        
        if version_number is None and auto_increment:
            version_number = self._generate_next_version_number(project_id)
        elif version_number is None:
            version_number = "1.0.0"
        
        # Add metadata to translation data
        enhanced_data = {
            "segments": translation_data.get("segments", []),
            "metadata": {
                "source_language": translation_data.get("source_language", ""),
                "target_language": translation_data.get("target_language", ""),
                "translation_method": translation_data.get("translation_method", ""),
                "quality_settings": translation_data.get("quality_settings", {}),
                "created_with": "VideoLingo Version Control",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(enhanced_data)
        
        version = self.storage.save_version(
            project_id=project_id,
            version_number=version_number,
            content=enhanced_data,
            description=description,
            tags=tags or [],
            quality_score=quality_score
        )
        
        # Cleanup old versions if needed
        self._cleanup_old_versions(project_id)
        
        return version
    
    def get_version(self, version_id: str) -> Optional[TranslationVersion]:
        """Get a specific version by ID."""
        return self.storage.get_version(version_id)
    
    def list_project_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """List all versions for a project."""
        return self.storage.list_versions(project_id)
    
    def compare_versions(
        self,
        old_version_id: str,
        new_version_id: str
    ) -> Optional[VersionDiff]:
        """Compare two versions and return detailed differences."""
        
        old_version = self.storage.get_version(old_version_id)
        new_version = self.storage.get_version(new_version_id)
        
        if not old_version or not new_version:
            return None
        
        old_data = {
            'version_id': old_version.version_id,
            'version_number': old_version.version_number,
            'content': old_version.content
        }
        
        new_data = {
            'version_id': new_version.version_id,
            'version_number': new_version.version_number,
            'content': new_version.content
        }
        
        return self.differ.compare_versions(old_data, new_data)
    
    def restore_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Restore a version and return its translation data."""
        version = self.storage.get_version(version_id)
        
        if not version:
            return None
        
        return {
            "segments": version.content.get("segments", []),
            "metadata": version.content.get("metadata", {}),
            "version_info": {
                "version_id": version.version_id,
                "version_number": version.version_number,
                "created_at": version.created_at,
                "description": version.description
            }
        }
    
    def delete_version(self, version_id: str) -> bool:
        """Delete a specific version."""
        return self.storage.delete_version(version_id)
    
    def tag_version(self, version_id: str, tags: List[str]) -> bool:
        """Add tags to a version."""
        version = self.storage.get_version(version_id)
        if not version:
            return False
        
        # Update tags
        existing_tags = set(version.tags)
        new_tags = existing_tags.union(set(tags))
        
        # Re-save version with updated tags
        self.storage.save_version(
            project_id=version.project_id,
            version_number=version.version_number,
            content=version.content,
            description=version.description,
            tags=list(new_tags),
            quality_score=version.quality_score
        )
        
        return True
    
    def find_versions_by_tag(self, project_id: str, tag: str) -> List[Dict[str, Any]]:
        """Find versions by tag."""
        return self.storage.find_versions_by_tag(project_id, tag)
    
    def get_version_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive version statistics."""
        stats = self.storage.get_version_statistics(project_id)
        
        # Add additional analysis
        versions = self.storage.list_versions(project_id)
        if len(versions) >= 2:
            # Compare latest with previous
            latest = versions[0]
            previous = versions[1]
            
            diff = self.compare_versions(previous["version_id"], latest["version_id"])
            if diff:
                stats["latest_change_summary"] = diff.summary
                stats["latest_similarity"] = diff.overall_similarity
        
        return stats
    
    def export_version_history(self, project_id: str) -> Dict[str, Any]:
        """Export complete version history for a project."""
        versions = self.storage.list_versions(project_id)
        
        export_data = {
            "project_id": project_id,
            "export_timestamp": datetime.now().isoformat(),
            "total_versions": len(versions),
            "versions": []
        }
        
        for version_info in versions:
            version = self.storage.get_version(version_info["version_id"])
            if version:
                export_data["versions"].append({
                    "version_id": version.version_id,
                    "version_number": version.version_number,
                    "created_at": version.created_at,
                    "description": version.description,
                    "tags": version.tags,
                    "quality_score": version.quality_score,
                    "segment_count": version.segment_count
                })
        
        return export_data
    
    def _generate_next_version_number(self, project_id: str) -> str:
        """Generate next version number based on existing versions."""
        versions = self.storage.list_versions(project_id)
        
        if not versions:
            return "1.0.0"
        
        # Extract version numbers and find the highest
        version_numbers = []
        for version in versions:
            try:
                # Parse version number (e.g., "1.2.3")
                parts = version["version_number"].split(".")
                if len(parts) == 3:
                    major, minor, patch = map(int, parts)
                    version_numbers.append((major, minor, patch))
            except (ValueError, AttributeError):
                continue
        
        if not version_numbers:
            return "1.0.0"
        
        # Increment patch version of the highest version
        version_numbers.sort(reverse=True)
        highest = version_numbers[0]
        
        return f"{highest[0]}.{highest[1]}.{highest[2] + 1}"
    
    def _calculate_quality_score(self, translation_data: Dict[str, Any]) -> float:
        """Calculate quality score for translation data."""
        segments = translation_data.get("segments", [])
        
        if not segments:
            return 0.0
        
        # Simple quality metrics
        score = 0.0
        total_segments = len(segments)
        
        for segment in segments:
            text = segment.get("text", "")
            
            # Length score (reasonable length gets higher score)
            if 10 <= len(text) <= 200:
                score += 0.3
            elif len(text) > 0:
                score += 0.1
            
            # Character diversity score
            unique_chars = len(set(text.lower()))
            if unique_chars > 5:
                score += 0.3
            
            # Basic completion score
            if text.strip():
                score += 0.4
        
        return min(score / total_segments, 1.0) if total_segments > 0 else 0.0
    
    def _cleanup_old_versions(self, project_id: str):
        """Remove old versions if exceeding maximum limit."""
        if not self.auto_backup_enabled:
            return
        
        versions = self.storage.list_versions(project_id)
        
        if len(versions) > self.max_versions_per_project:
            # Keep the most recent versions and delete the oldest
            excess_count = len(versions) - self.max_versions_per_project
            oldest_versions = versions[-excess_count:]  # Get oldest versions
            
            for version in oldest_versions:
                # Don't delete tagged versions
                if not version.get("tags"):
                    self.storage.delete_version(version["version_id"])
    
    def create_branch(
        self,
        project_id: str,
        base_version_id: str,
        branch_name: str,
        description: str = ""
    ) -> Optional[TranslationVersion]:
        """Create a new branch from an existing version."""
        base_version = self.storage.get_version(base_version_id)
        
        if not base_version:
            return None
        
        # Create new version with branch tag
        tags = [f"branch:{branch_name}"] + base_version.tags
        
        return self.storage.save_version(
            project_id=project_id,
            version_number=f"{base_version.version_number}-{branch_name}",
            content=base_version.content,
            description=f"Branch '{branch_name}': {description}",
            tags=tags,
            quality_score=base_version.quality_score
        )