#!/usr/bin/env python3
"""
Batch Processing System Test Suite

Tests all functionality of the batch video processing system.
"""

import os
import sys
import json
import tempfile
import shutil
import time
import threading
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.batch_processing.task_queue import TaskQueue, TaskDefinition, TaskStatus, TaskPriority
from core.batch_processing.job_scheduler import JobScheduler
from core.batch_processing.batch_manager import BatchManager

class TestTaskQueue:
    """Test the task queue functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.queue = TaskQueue(self.temp_dir)
        
        # Sample config
        self.sample_config = {
            "source_language": "en",
            "target_language": "zh-CN",
            "quality": "high"
        }
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_and_get_task(self):
        """Test adding and retrieving tasks."""
        task_id = self.queue.add_task(
            task_type="video_translation",
            project_id="test_project",
            input_file="/test/video.mp4",
            output_dir="/test/output",
            config=self.sample_config,
            priority=TaskPriority.HIGH,
            tags=["test", "batch"]
        )
        
        assert task_id is not None
        assert len(task_id) == 12  # UUID shortened to 12 chars
        
        # Retrieve task
        task = self.queue.get_task(task_id)
        assert task is not None
        assert task.task_type == "video_translation"
        assert task.project_id == "test_project"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING
        assert "test" in task.tags
    
    def test_task_status_updates(self):
        """Test task status updates."""
        task_id = self.queue.add_task(
            "test_task", "proj", "/input", "/output", {}
        )
        
        # Update to running
        success = self.queue.update_task_status(task_id, TaskStatus.RUNNING, 25.0)
        assert success
        
        task = self.queue.get_task(task_id)
        assert task.status == TaskStatus.RUNNING
        assert task.progress_percentage == 25.0
        assert task.started_at is not None
        
        # Update to completed
        success = self.queue.update_task_status(task_id, TaskStatus.COMPLETED, 100.0)
        assert success
        
        task = self.queue.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress_percentage == 100.0
        assert task.completed_at is not None
        assert task.actual_duration is not None
    
    def test_get_next_task_priority(self):
        """Test task priority ordering."""
        # Add tasks with different priorities
        low_id = self.queue.add_task("test", "proj", "/low", "/out", {}, TaskPriority.LOW)
        high_id = self.queue.add_task("test", "proj", "/high", "/out", {}, TaskPriority.HIGH)
        normal_id = self.queue.add_task("test", "proj", "/normal", "/out", {}, TaskPriority.NORMAL)
        
        # Should get high priority first
        next_task = self.queue.get_next_task()
        assert next_task.task_id == high_id
        assert next_task.status == TaskStatus.QUEUED
        
        # Then normal priority
        next_task = self.queue.get_next_task()
        assert next_task.task_id == normal_id
        
        # Finally low priority
        next_task = self.queue.get_next_task()
        assert next_task.task_id == low_id
    
    def test_task_dependencies(self):
        """Test task dependency resolution."""
        # Create dependent tasks
        task1_id = self.queue.add_task("step1", "proj", "/input", "/out", {})
        task2_id = self.queue.add_task("step2", "proj", "/input", "/out", {}, dependencies=[task1_id])
        
        # Task2 should not be available until task1 is complete
        next_task = self.queue.get_next_task()
        assert next_task.task_id == task1_id
        
        # No more tasks should be available
        next_task = self.queue.get_next_task()
        assert next_task is None
        
        # Complete task1
        self.queue.update_task_status(task1_id, TaskStatus.COMPLETED)
        
        # Now task2 should be available
        next_task = self.queue.get_next_task()
        assert next_task.task_id == task2_id
    
    def test_cancel_task(self):
        """Test task cancellation."""
        task_id = self.queue.add_task("test", "proj", "/input", "/output", {})
        
        # Cancel the task
        success = self.queue.cancel_task(task_id)
        assert success
        
        task = self.queue.get_task(task_id)
        assert task.status == TaskStatus.CANCELLED
        assert task.completed_at is not None
    
    def test_retry_failed_task(self):
        """Test task retry functionality."""
        task_id = self.queue.add_task("test", "proj", "/input", "/output", {})
        
        # Mark as failed
        self.queue.update_task_status(task_id, TaskStatus.FAILED, error_message="Test error")
        
        task = self.queue.get_task(task_id)
        assert task.status == TaskStatus.FAILED
        assert task.retry_count == 0
        
        # Retry the task
        success = self.queue.retry_task(task_id)
        assert success
        
        task = self.queue.get_task(task_id)
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 1
        assert task.error_message is None
    
    def test_list_tasks_with_filters(self):
        """Test task listing with filters."""
        # Create various tasks
        self.queue.add_task("type1", "proj1", "/input1", "/out", {}, tags=["tag1"])
        self.queue.add_task("type2", "proj1", "/input2", "/out", {}, tags=["tag2"])
        self.queue.add_task("type1", "proj2", "/input3", "/out", {}, tags=["tag1"])
        
        # Filter by project
        proj1_tasks = self.queue.list_tasks(project_filter="proj1")
        assert len(proj1_tasks) == 2
        
        # Filter by type
        type1_tasks = self.queue.list_tasks(type_filter="type1")
        assert len(type1_tasks) == 2
        
        # Filter by tag
        tag1_tasks = self.queue.list_tasks(tag_filter="tag1")
        assert len(tag1_tasks) == 2

class TestJobScheduler:
    """Test the job scheduler functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.scheduler = JobScheduler(max_workers=2)
        
        # Custom test handler
        def test_handler(task):
            time.sleep(0.1)  # Simulate work
            return True
        
        self.scheduler.register_task_handler("test_task", test_handler)
    
    def teardown_method(self):
        """Cleanup test environment."""
        self.scheduler.stop()
    
    def test_scheduler_start_stop(self):
        """Test scheduler start/stop functionality."""
        assert not self.scheduler.is_running
        
        self.scheduler.start()
        assert self.scheduler.is_running
        
        # Wait a bit for workers to start
        time.sleep(0.5)
        workers = self.scheduler.get_worker_status()
        assert len(workers) <= self.scheduler.max_workers
        
        self.scheduler.stop()
        assert not self.scheduler.is_running
    
    def test_task_execution(self):
        """Test task execution by scheduler."""
        # Add a test task
        task_id = self.scheduler.task_queue.add_task(
            "test_task", "test_proj", "/input", "/output", {}
        )
        
        self.scheduler.start()
        
        # Wait for task to be processed
        start_time = time.time()
        while time.time() - start_time < 3:  # 3 second timeout
            task = self.scheduler.task_queue.get_task(task_id)
            if task.status == TaskStatus.COMPLETED:
                break
            time.sleep(0.1)
        
        task = self.scheduler.task_queue.get_task(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress_percentage == 100.0
    
    def test_multiple_task_execution(self):
        """Test execution of multiple tasks."""
        # Add multiple tasks (reduce count for faster testing)
        task_ids = []
        for i in range(3):
            task_id = self.scheduler.task_queue.add_task(
                "test_task", "test_proj", f"/input{i}", "/output", {}
            )
            task_ids.append(task_id)
        
        self.scheduler.start()
        
        # Wait for all tasks to complete
        start_time = time.time()
        while time.time() - start_time < 5:  # 5 second timeout
            completed_count = 0
            for task_id in task_ids:
                task = self.scheduler.task_queue.get_task(task_id)
                if task.status == TaskStatus.COMPLETED:
                    completed_count += 1
            
            if completed_count == len(task_ids):
                break
            time.sleep(0.1)
        
        # Verify all tasks completed
        for task_id in task_ids:
            task = self.scheduler.task_queue.get_task(task_id)
            assert task.status == TaskStatus.COMPLETED

class TestBatchManager:
    """Test the batch manager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = BatchManager()
        
        # Create dummy video files for testing
        self.video_files = []
        for i in range(3):
            video_path = os.path.join(self.temp_dir, f"test_video_{i}.mp4")
            with open(video_path, 'w') as f:
                f.write("dummy video content")
            self.video_files.append(video_path)
    
    def teardown_method(self):
        """Cleanup test environment."""
        self.manager.stop_processing()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_video_batch(self):
        """Test adding video batch."""
        output_dir = os.path.join(self.temp_dir, "output")
        
        task_ids = self.manager.add_video_batch(
            video_files=self.video_files,
            output_directory=output_dir,
            project_id="test_batch",
            processing_type="video_translation",
            priority=TaskPriority.HIGH,
            tags=["test", "batch"]
        )
        
        assert len(task_ids) == len(self.video_files)
        
        # Verify tasks were created
        for task_id in task_ids:
            task = self.manager.task_queue.get_task(task_id)
            assert task is not None
            assert task.project_id == "test_batch"
            assert task.task_type == "video_translation"
            assert task.priority == TaskPriority.HIGH
            assert "test" in task.tags
    
    def test_add_pipeline_batch(self):
        """Test adding pipeline batch."""
        output_dir = os.path.join(self.temp_dir, "pipeline_output")
        pipeline_stages = ["audio_extraction", "video_translation", "subtitle_generation"]
        
        stage_task_ids = self.manager.add_pipeline_batch(
            video_files=self.video_files,
            output_directory=output_dir,
            pipeline_stages=pipeline_stages,
            project_id="test_pipeline"
        )
        
        assert len(stage_task_ids) == len(pipeline_stages)
        
        # Verify tasks for each stage
        for stage in pipeline_stages:
            assert stage in stage_task_ids
            assert len(stage_task_ids[stage]) == len(self.video_files)
        
        # Verify dependencies
        for video_index in range(len(self.video_files)):
            audio_task_id = stage_task_ids["audio_extraction"][video_index]
            translation_task_id = stage_task_ids["video_translation"][video_index]
            subtitle_task_id = stage_task_ids["subtitle_generation"][video_index]
            
            # Translation should depend on audio extraction
            translation_task = self.manager.task_queue.get_task(translation_task_id)
            assert audio_task_id in translation_task.dependencies
            
            # Subtitle should depend on translation
            subtitle_task = self.manager.task_queue.get_task(subtitle_task_id)
            assert translation_task_id in subtitle_task.dependencies
    
    def test_get_batch_status(self):
        """Test getting batch status."""
        # Add a batch
        task_ids = self.manager.add_video_batch(
            video_files=self.video_files,
            output_directory=os.path.join(self.temp_dir, "output"),
            project_id="status_test"
        )
        
        # Get status
        status = self.manager.get_batch_status("status_test")
        
        assert status["project_id"] == "status_test"
        assert status["total_tasks"] == len(self.video_files)
        assert status["pending"] == len(self.video_files)
        assert status["completed"] == 0
        assert status["overall_progress"] == 0.0
        assert len(status["tasks"]) == len(self.video_files)
    
    def test_cancel_batch(self):
        """Test canceling a batch."""
        # Add a batch
        task_ids = self.manager.add_video_batch(
            video_files=self.video_files,
            output_directory=os.path.join(self.temp_dir, "output"),
            project_id="cancel_test"
        )
        
        # Cancel the batch
        cancelled_count = self.manager.cancel_batch("cancel_test")
        assert cancelled_count == len(self.video_files)
        
        # Verify tasks were cancelled
        for task_id in task_ids:
            task = self.manager.task_queue.get_task(task_id)
            assert task.status == TaskStatus.CANCELLED
    
    def test_list_batch_projects(self):
        """Test listing batch projects."""
        # Add multiple batches
        self.manager.add_video_batch(
            video_files=self.video_files[:2],
            output_directory=os.path.join(self.temp_dir, "output1"),
            project_id="project1"
        )
        
        self.manager.add_video_batch(
            video_files=self.video_files[2:],
            output_directory=os.path.join(self.temp_dir, "output2"),
            project_id="project2"
        )
        
        # List projects
        projects = self.manager.list_batch_projects()
        assert len(projects) == 2
        
        project_ids = [p["project_id"] for p in projects]
        assert "project1" in project_ids
        assert "project2" in project_ids
        
        # Verify task counts
        for project in projects:
            if project["project_id"] == "project1":
                assert project["task_count"] == 2
            elif project["project_id"] == "project2":
                assert project["task_count"] == 1
    
    def test_export_batch_report(self):
        """Test exporting batch report."""
        # Add a batch
        task_ids = self.manager.add_video_batch(
            video_files=self.video_files,
            output_directory=os.path.join(self.temp_dir, "output"),
            project_id="report_test",
            processing_type="video_translation"
        )
        
        # Export report
        report = self.manager.export_batch_report("report_test")
        
        assert "report_generated" in report
        assert "project_summary" in report
        assert "task_type_breakdown" in report
        assert "detailed_tasks" in report
        
        # Verify project summary
        summary = report["project_summary"]
        assert summary["project_id"] == "report_test"
        assert summary["total_tasks"] == len(self.video_files)
        
        # Verify task breakdown
        breakdown = report["task_type_breakdown"]
        assert "video_translation" in breakdown
        assert breakdown["video_translation"]["total"] == len(self.video_files)
        
        # Verify detailed tasks
        detailed_tasks = report["detailed_tasks"]
        assert len(detailed_tasks) == len(self.video_files)

def run_tests():
    """Run all batch processing tests."""
    print("🎬 Starting Batch Processing System Tests...")
    
    test_classes = [TestTaskQueue, TestJobScheduler, TestBatchManager]
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