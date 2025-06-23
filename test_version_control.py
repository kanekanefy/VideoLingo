#!/usr/bin/env python3
"""
Version Control System Test Suite

Tests all functionality of the translation version management system.
"""

import os
import sys
import json
# import pytest  # Not required for this test runner
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.version_control.version_storage import VersionStorage, TranslationVersion
from core.version_control.version_manager import VersionManager
from core.version_control.translation_diff import TranslationDiffer, ChangeType

class TestVersionStorage:
    """Test the version storage functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = VersionStorage(self.temp_dir)
        
        # Sample translation data
        self.sample_translation = {
            "segments": [
                {"id": "1", "text": "Hello world", "start": 0.0, "end": 2.0},
                {"id": "2", "text": "How are you?", "start": 2.0, "end": 4.0}
            ],
            "metadata": {
                "source_language": "en",
                "target_language": "zh-CN"
            }
        }
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_retrieve_version(self):
        """Test saving and retrieving versions."""
        # Save version
        version = self.storage.save_version(
            project_id="test_project",
            version_number="1.0.0", 
            content=self.sample_translation,
            description="Initial version",
            tags=["initial", "test"]
        )
        
        assert version.project_id == "test_project"
        assert version.version_number == "1.0.0"
        assert version.description == "Initial version"
        assert "initial" in version.tags
        assert version.segment_count == 2
        
        # Retrieve version
        retrieved = self.storage.get_version(version.version_id)
        assert retrieved is not None
        assert retrieved.version_id == version.version_id
        assert retrieved.content == self.sample_translation
    
    def test_list_versions(self):
        """Test listing project versions."""
        # Create multiple versions
        v1 = self.storage.save_version("proj1", "1.0.0", self.sample_translation, "Version 1")
        v2 = self.storage.save_version("proj1", "1.1.0", self.sample_translation, "Version 2")
        v3 = self.storage.save_version("proj2", "1.0.0", self.sample_translation, "Other project")
        
        # List versions for project 1
        versions = self.storage.list_versions("proj1")
        assert len(versions) == 2
        
        # Should be sorted by creation time (newest first)
        assert versions[0]["version_number"] == "1.1.0"
        assert versions[1]["version_number"] == "1.0.0"
        
        # List versions for project 2
        versions_p2 = self.storage.list_versions("proj2")
        assert len(versions_p2) == 1
        assert versions_p2[0]["version_number"] == "1.0.0"
    
    def test_delete_version(self):
        """Test version deletion."""
        version = self.storage.save_version("test", "1.0.0", self.sample_translation)
        
        # Verify version exists
        assert self.storage.get_version(version.version_id) is not None
        
        # Delete version
        success = self.storage.delete_version(version.version_id)
        assert success
        
        # Verify version is gone
        assert self.storage.get_version(version.version_id) is None
    
    def test_find_versions_by_tag(self):
        """Test finding versions by tag."""
        v1 = self.storage.save_version("proj", "1.0.0", self.sample_translation, tags=["stable", "release"])
        v2 = self.storage.save_version("proj", "1.1.0", self.sample_translation, tags=["beta"])
        v3 = self.storage.save_version("proj", "1.2.0", self.sample_translation, tags=["stable"])
        
        # Find stable versions
        stable_versions = self.storage.find_versions_by_tag("proj", "stable")
        assert len(stable_versions) == 2
        
        # Find beta versions
        beta_versions = self.storage.find_versions_by_tag("proj", "beta")
        assert len(beta_versions) == 1
        assert beta_versions[0]["version_number"] == "1.1.0"

class TestTranslationDiffer:
    """Test the translation difference analysis."""
    
    def setup_method(self):
        """Setup test environment."""
        self.differ = TranslationDiffer()
        
        # Sample version data
        self.old_version = {
            "version_id": "old_v1",
            "version_number": "1.0.0",
            "content": {
                "segments": [
                    {"id": "1", "text": "Hello world"},
                    {"id": "2", "text": "How are you?"},
                    {"id": "3", "text": "Goodbye"}
                ]
            }
        }
        
        self.new_version = {
            "version_id": "new_v2", 
            "version_number": "2.0.0",
            "content": {
                "segments": [
                    {"id": "1", "text": "Hello universe"},  # Modified
                    {"id": "2", "text": "How are you?"},     # Unchanged
                    {"id": "4", "text": "See you later"}     # Added (3 deleted)
                ]
            }
        }
    
    def test_compare_versions(self):
        """Test version comparison."""
        diff = self.differ.compare_versions(self.old_version, self.new_version)
        
        assert diff.old_version_id == "old_v1"
        assert diff.new_version_id == "new_v2"
        assert diff.old_version_number == "1.0.0"
        assert diff.new_version_number == "2.0.0"
        
        # Check summary
        summary = diff.summary
        assert summary["modified"] == 1  # Segment 1 modified
        assert summary["unchanged"] == 1  # Segment 2 unchanged
        assert summary["added"] == 1     # Segment 4 added
        assert summary["deleted"] == 1   # Segment 3 deleted
        assert summary["total_segments"] == 4
    
    def test_segment_differences(self):
        """Test individual segment differences."""
        diff = self.differ.compare_versions(self.old_version, self.new_version)
        
        # Find changes by segment ID
        changes_by_id = {d.segment_id: d for d in diff.segment_diffs}
        
        # Segment 1: Modified
        seg1_diff = changes_by_id["1"]
        assert seg1_diff.change_type == ChangeType.MODIFIED
        assert seg1_diff.old_text == "Hello world"
        assert seg1_diff.new_text == "Hello universe"
        assert 0 < seg1_diff.similarity_score < 1
        
        # Segment 2: Unchanged
        seg2_diff = changes_by_id["2"]
        assert seg2_diff.change_type == ChangeType.UNCHANGED
        assert seg2_diff.similarity_score == 1.0
        
        # Segment 3: Deleted
        seg3_diff = changes_by_id["3"]
        assert seg3_diff.change_type == ChangeType.DELETED
        assert seg3_diff.old_text == "Goodbye"
        assert seg3_diff.new_text is None
        
        # Segment 4: Added
        seg4_diff = changes_by_id["4"]
        assert seg4_diff.change_type == ChangeType.ADDED
        assert seg4_diff.old_text is None
        assert seg4_diff.new_text == "See you later"
    
    def test_text_similarity(self):
        """Test text similarity calculation."""
        # Identical text
        assert self.differ._calculate_text_similarity("hello", "hello") == 1.0
        
        # Empty strings
        assert self.differ._calculate_text_similarity("", "") == 1.0
        assert self.differ._calculate_text_similarity("hello", "") == 0.0
        
        # Similar text
        similarity = self.differ._calculate_text_similarity("Hello world", "Hello universe")
        assert 0 < similarity < 1
        
        # Completely different
        similarity = self.differ._calculate_text_similarity("Hello", "Goodbye")
        assert similarity < 0.5

class TestVersionManager:
    """Test the high-level version manager."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = VersionManager(self.temp_dir)
        
        self.sample_data = {
            "segments": [
                {"id": "1", "text": "Hello world", "start": 0.0, "end": 2.0},
                {"id": "2", "text": "How are you?", "start": 2.0, "end": 4.0}
            ],
            "source_language": "en",
            "target_language": "zh-CN"
        }
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_version_auto_increment(self):
        """Test automatic version number increment."""
        # First version
        v1 = self.manager.create_version(
            project_id="test_proj",
            translation_data=self.sample_data,
            description="First version"
        )
        assert v1.version_number == "1.0.0"
        
        # Second version (auto increment)
        v2 = self.manager.create_version(
            project_id="test_proj", 
            translation_data=self.sample_data,
            description="Second version"
        )
        assert v2.version_number == "1.0.1"
        
        # Third version (auto increment)
        v3 = self.manager.create_version(
            project_id="test_proj",
            translation_data=self.sample_data,
            description="Third version"
        )
        assert v3.version_number == "1.0.2"
    
    def test_compare_versions(self):
        """Test version comparison through manager."""
        # Create two versions
        v1 = self.manager.create_version("proj", self.sample_data, description="V1")
        
        modified_data = self.sample_data.copy()
        modified_data["segments"] = [
            {"id": "1", "text": "Hello universe", "start": 0.0, "end": 2.0},
            {"id": "2", "text": "How are you?", "start": 2.0, "end": 4.0}
        ]
        
        v2 = self.manager.create_version("proj", modified_data, description="V2")
        
        # Compare versions
        diff = self.manager.compare_versions(v1.version_id, v2.version_id)
        assert diff is not None
        assert diff.old_version_id == v1.version_id
        assert diff.new_version_id == v2.version_id
        assert diff.summary["modified"] == 1
        assert diff.summary["unchanged"] == 1
    
    def test_restore_version(self):
        """Test version restoration."""
        version = self.manager.create_version("proj", self.sample_data, description="Test")
        
        # Restore version
        restored = self.manager.restore_version(version.version_id)
        assert restored is not None
        assert restored["segments"] == self.sample_data["segments"]
        assert restored["version_info"]["version_id"] == version.version_id
    
    def test_version_statistics(self):
        """Test version statistics."""
        # Create multiple versions
        v1 = self.manager.create_version("proj", self.sample_data, tags=["stable"])
        v2 = self.manager.create_version("proj", self.sample_data, tags=["beta"])
        v3 = self.manager.create_version("proj", self.sample_data, tags=["stable", "release"])
        
        stats = self.manager.get_version_statistics("proj")
        assert stats["total_versions"] == 3
        assert stats["latest_version"] == v3.version_number
        assert "stable" in stats["common_tags"]
    
    def test_export_version_history(self):
        """Test version history export."""
        # Create versions
        v1 = self.manager.create_version("proj", self.sample_data, description="V1")
        v2 = self.manager.create_version("proj", self.sample_data, description="V2")
        
        # Export history
        history = self.manager.export_version_history("proj")
        assert history["project_id"] == "proj"
        assert history["total_versions"] == 2
        assert len(history["versions"]) == 2
        
        # Verify version data
        version_data = history["versions"]
        assert any(v["version_number"] == v1.version_number for v in version_data)
        assert any(v["version_number"] == v2.version_number for v in version_data)

def run_tests():
    """Run all version control tests."""
    print("🔄 Starting Version Control System Tests...")
    
    test_classes = [TestVersionStorage, TestTranslationDiffer, TestVersionManager]
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__} tests:")
        
        # Get test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for test_method in test_methods:
            total_tests += 1
            test_instance = test_class()
            
            try:
                # Setup
                if hasattr(test_instance, 'setup_method'):
                    test_instance.setup_method()
                
                # Run test
                getattr(test_instance, test_method)()
                
                print(f"  ✅ {test_method}")
                passed_tests += 1
                
            except Exception as e:
                print(f"  ❌ {test_method}: {str(e)}")
                failed_tests.append(f"{test_class.__name__}.{test_method}: {str(e)}")
            
            finally:
                # Cleanup
                if hasattr(test_instance, 'teardown_method'):
                    try:
                        test_instance.teardown_method()
                    except:
                        pass
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
        return False
    else:
        print(f"\n🎉 All tests passed!")
        return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)