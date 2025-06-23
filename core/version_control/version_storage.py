"""
Translation Version Storage Module

Handles storage and retrieval of translation versions with metadata.
"""

import json
import os
import hashlib
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path

@dataclass
class TranslationVersion:
    """Translation version metadata."""
    version_id: str
    project_id: str
    version_number: str
    content: Dict[str, Any]
    created_at: str
    created_by: str
    description: str
    content_hash: str
    segment_count: int
    quality_score: Optional[float] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class VersionStorage:
    """Manages storage and retrieval of translation versions."""
    
    def __init__(self, storage_dir: str = "version_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.versions_index_file = self.storage_dir / "versions_index.json"
        self._ensure_index()
    
    def _ensure_index(self):
        """Ensure versions index file exists."""
        if not self.versions_index_file.exists():
            self._save_index({})
    
    def _load_index(self) -> Dict[str, Any]:
        """Load versions index."""
        try:
            with open(self.versions_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_index(self, index: Dict[str, Any]):
        """Save versions index."""
        with open(self.versions_index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _generate_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate hash for translation content."""
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()[:16]
    
    def _generate_version_id(self, project_id: str, version_number: str) -> str:
        """Generate unique version ID."""
        timestamp = str(int(time.time() * 1000))
        combined = f"{project_id}_{version_number}_{timestamp}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def save_version(
        self,
        project_id: str,
        version_number: str,
        content: Dict[str, Any],
        description: str = "",
        created_by: str = "user",
        tags: List[str] = None,
        quality_score: Optional[float] = None
    ) -> TranslationVersion:
        """Save a new translation version."""
        
        content_hash = self._generate_content_hash(content)
        version_id = self._generate_version_id(project_id, version_number)
        
        version = TranslationVersion(
            version_id=version_id,
            project_id=project_id,
            version_number=version_number,
            content=content,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            description=description,
            content_hash=content_hash,
            segment_count=len(content.get('segments', [])),
            quality_score=quality_score,
            tags=tags or []
        )
        
        # Save version content
        version_file = self.storage_dir / f"{version_id}.json"
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(version), f, ensure_ascii=False, indent=2)
        
        # Update index
        index = self._load_index()
        if project_id not in index:
            index[project_id] = {}
        
        index[project_id][version_id] = {
            "version_number": version_number,
            "created_at": version.created_at,
            "description": description,
            "content_hash": content_hash,
            "segment_count": version.segment_count,
            "quality_score": quality_score,
            "tags": tags or []
        }
        
        self._save_index(index)
        return version
    
    def get_version(self, version_id: str) -> Optional[TranslationVersion]:
        """Get a specific version by ID."""
        version_file = self.storage_dir / f"{version_id}.json"
        
        if not version_file.exists():
            return None
        
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return TranslationVersion(**data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return None
    
    def list_versions(self, project_id: str) -> List[Dict[str, Any]]:
        """List all versions for a project."""
        index = self._load_index()
        project_versions = index.get(project_id, {})
        
        versions = []
        for version_id, metadata in project_versions.items():
            versions.append({
                "version_id": version_id,
                **metadata
            })
        
        # Sort by creation time (newest first)
        versions.sort(key=lambda x: x["created_at"], reverse=True)
        return versions
    
    def delete_version(self, version_id: str) -> bool:
        """Delete a version."""
        version_file = self.storage_dir / f"{version_id}.json"
        
        if not version_file.exists():
            return False
        
        # Remove from index
        index = self._load_index()
        for project_id, versions in index.items():
            if version_id in versions:
                del versions[version_id]
                break
        
        self._save_index(index)
        
        # Remove file
        version_file.unlink()
        return True
    
    def get_latest_version(self, project_id: str) -> Optional[TranslationVersion]:
        """Get the latest version for a project."""
        versions = self.list_versions(project_id)
        if not versions:
            return None
        
        latest = versions[0]  # Already sorted by creation time
        return self.get_version(latest["version_id"])
    
    def find_versions_by_tag(self, project_id: str, tag: str) -> List[Dict[str, Any]]:
        """Find versions by tag."""
        versions = self.list_versions(project_id)
        return [v for v in versions if tag in v.get("tags", [])]
    
    def get_version_statistics(self, project_id: str) -> Dict[str, Any]:
        """Get version statistics for a project."""
        versions = self.list_versions(project_id)
        
        if not versions:
            return {
                "total_versions": 0,
                "latest_version": None,
                "average_quality": None,
                "common_tags": []
            }
        
        # Calculate statistics
        quality_scores = [v["quality_score"] for v in versions if v["quality_score"] is not None]
        all_tags = []
        for v in versions:
            all_tags.extend(v.get("tags", []))
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        common_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_versions": len(versions),
            "latest_version": versions[0]["version_number"],
            "average_quality": sum(quality_scores) / len(quality_scores) if quality_scores else None,
            "common_tags": [tag for tag, count in common_tags]
        }