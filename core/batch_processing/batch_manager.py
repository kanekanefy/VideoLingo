"""
Batch Processing Manager Module

High-level interface for managing batch video processing operations.
"""

import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .task_queue import TaskQueue, TaskDefinition, TaskStatus, TaskPriority
from .job_scheduler import JobScheduler

class BatchManager:
    """High-level manager for batch video processing."""
    
    def __init__(self, max_concurrent_jobs: int = 4):
        self.task_queue = TaskQueue()
        self.scheduler = JobScheduler(max_workers=max_concurrent_jobs)
        self.batch_storage_dir = Path("batch_processing")
        self.batch_storage_dir.mkdir(exist_ok=True)
        
        # Default processing configurations
        self.default_configs = {
            "video_translation": {
                "source_language": "en",
                "target_language": "zh-CN",
                "whisper_model": "large-v3",
                "llm_model": "gpt-4",
                "tts_method": "azure_tts",
                "burn_subtitles": True,
                "quality_threshold": 0.8
            },
            "audio_extraction": {
                "format": "wav",
                "sample_rate": 16000,
                "channels": 1
            },
            "subtitle_generation": {
                "format": "srt",
                "max_chars_per_line": 40,
                "max_lines": 2
            },
            "video_transcoding": {
                "output_format": "mp4",
                "video_codec": "h264",
                "audio_codec": "aac",
                "quality": "high"
            }
        }
    
    def start_processing(self):
        """Start the batch processing system."""
        self.scheduler.start()
    
    def stop_processing(self):
        """Stop the batch processing system."""
        self.scheduler.stop()
    
    def add_video_batch(
        self,
        video_files: List[str],
        output_directory: str,
        project_id: str = None,
        processing_type: str = "video_translation",
        config_override: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        tags: List[str] = None
    ) -> List[str]:
        """Add a batch of videos for processing."""
        
        if not project_id:
            project_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure output directory exists
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        
        # Merge configurations
        config = self.default_configs.get(processing_type, {}).copy()
        if config_override:
            config.update(config_override)
        
        task_ids = []
        
        for video_file in video_files:
            if not os.path.exists(video_file):
                print(f"⚠️ Warning: Video file not found: {video_file}")
                continue
            
            # Create individual output directory for this video
            video_name = Path(video_file).stem
            video_output_dir = Path(output_directory) / video_name
            video_output_dir.mkdir(exist_ok=True)
            
            # Estimate processing duration based on file size and type
            estimated_duration = self._estimate_processing_time(video_file, processing_type)
            
            # Add task to queue
            task_id = self.task_queue.add_task(
                task_type=processing_type,
                project_id=project_id,
                input_file=video_file,
                output_dir=str(video_output_dir),
                config=config,
                priority=priority,
                tags=tags or [],
                estimated_duration=estimated_duration
            )
            
            task_ids.append(task_id)
            print(f"📝 Added task {task_id}: {video_file}")
        
        print(f"🎬 Added {len(task_ids)} videos to batch processing queue")
        return task_ids
    
    def add_pipeline_batch(
        self,
        video_files: List[str],
        output_directory: str,
        pipeline_stages: List[str],
        project_id: str = None,
        config_overrides: Dict[str, Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> Dict[str, List[str]]:
        """Add a batch with multiple processing stages (pipeline)."""
        
        if not project_id:
            project_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        stage_task_ids = {}
        
        for video_file in video_files:
            video_name = Path(video_file).stem
            video_output_dir = Path(output_directory) / video_name
            video_output_dir.mkdir(parents=True, exist_ok=True)
            
            previous_task_ids = []
            
            for stage_index, stage in enumerate(pipeline_stages):
                # Get config for this stage
                config = self.default_configs.get(stage, {}).copy()
                if config_overrides and stage in config_overrides:
                    config.update(config_overrides[stage])
                
                # Estimate duration
                estimated_duration = self._estimate_processing_time(video_file, stage)
                
                # Add task with dependencies on previous stages
                task_id = self.task_queue.add_task(
                    task_type=stage,
                    project_id=project_id,
                    input_file=video_file,
                    output_dir=str(video_output_dir),
                    config=config,
                    priority=priority,
                    dependencies=previous_task_ids.copy(),
                    tags=[f"pipeline_stage_{stage_index+1}", f"video_{video_name}"],
                    estimated_duration=estimated_duration
                )
                
                if stage not in stage_task_ids:
                    stage_task_ids[stage] = []
                stage_task_ids[stage].append(task_id)
                
                previous_task_ids = [task_id]  # Next stage depends on this one
        
        print(f"🔄 Added pipeline batch with {len(pipeline_stages)} stages for {len(video_files)} videos")
        return stage_task_ids
    
    def get_batch_status(self, project_id: str) -> Dict[str, Any]:
        """Get status of a batch project."""
        
        tasks = self.task_queue.list_tasks(project_filter=project_id)
        
        if not tasks:
            return {"error": "Project not found"}
        
        # Calculate statistics
        total_tasks = len(tasks)
        completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in tasks if t.status == TaskStatus.FAILED])
        running = len([t for t in tasks if t.status == TaskStatus.RUNNING])
        pending = len([t for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.QUEUED]])
        
        # Calculate overall progress
        total_progress = sum(t.progress_percentage for t in tasks)
        overall_progress = total_progress / total_tasks if total_tasks > 0 else 0
        
        # Estimate remaining time
        running_tasks_time = sum(
            max(0, t.estimated_duration - ((datetime.now() - datetime.fromisoformat(t.started_at)).total_seconds() / 60))
            for t in tasks if t.status == TaskStatus.RUNNING and t.started_at
        )
        pending_tasks_time = sum(t.estimated_duration for t in tasks if t.status in [TaskStatus.PENDING, TaskStatus.QUEUED])
        estimated_remaining_time = running_tasks_time + pending_tasks_time
        
        return {
            "project_id": project_id,
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "running": running,
            "pending": pending,
            "overall_progress": overall_progress,
            "completion_rate": (completed / total_tasks * 100) if total_tasks > 0 else 0,
            "failure_rate": (failed / total_tasks * 100) if total_tasks > 0 else 0,
            "estimated_remaining_minutes": int(estimated_remaining_time),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "task_type": t.task_type,
                    "input_file": os.path.basename(t.input_file),
                    "status": t.status.value,
                    "progress": t.progress_percentage,
                    "error": t.error_message
                }
                for t in tasks
            ]
        }
    
    def cancel_batch(self, project_id: str) -> int:
        """Cancel all tasks in a batch project."""
        
        tasks = self.task_queue.list_tasks(project_filter=project_id)
        cancelled_count = 0
        
        for task in tasks:
            if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if self.task_queue.cancel_task(task.task_id):
                    cancelled_count += 1
        
        print(f"🚫 Cancelled {cancelled_count} tasks in project {project_id}")
        return cancelled_count
    
    def retry_failed_tasks(self, project_id: str) -> int:
        """Retry all failed tasks in a batch project."""
        
        failed_tasks = self.task_queue.list_tasks(
            project_filter=project_id,
            status_filter=TaskStatus.FAILED
        )
        
        retried_count = 0
        for task in failed_tasks:
            if self.task_queue.retry_task(task.task_id):
                retried_count += 1
        
        print(f"🔄 Retried {retried_count} failed tasks in project {project_id}")
        return retried_count
    
    def list_batch_projects(self) -> List[Dict[str, Any]]:
        """List all batch projects."""
        
        all_tasks = self.task_queue.list_tasks()
        
        # Group by project ID
        projects = {}
        for task in all_tasks:
            project_id = task.project_id
            if project_id not in projects:
                projects[project_id] = {
                    "project_id": project_id,
                    "created_at": task.created_at,
                    "task_count": 0,
                    "completed_count": 0,
                    "failed_count": 0,
                    "running_count": 0,
                    "task_types": set()
                }
            
            project = projects[project_id]
            project["task_count"] += 1
            project["task_types"].add(task.task_type)
            
            if task.status == TaskStatus.COMPLETED:
                project["completed_count"] += 1
            elif task.status == TaskStatus.FAILED:
                project["failed_count"] += 1
            elif task.status == TaskStatus.RUNNING:
                project["running_count"] += 1
            
            # Keep the earliest creation time
            if task.created_at < project["created_at"]:
                project["created_at"] = task.created_at
        
        # Convert to list and add computed fields
        project_list = []
        for project in projects.values():
            project["task_types"] = list(project["task_types"])
            project["completion_rate"] = (
                project["completed_count"] / project["task_count"] * 100
                if project["task_count"] > 0 else 0
            )
            project_list.append(project)
        
        # Sort by creation time (newest first)
        project_list.sort(key=lambda p: p["created_at"], reverse=True)
        
        return project_list
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        
        scheduler_stats = self.scheduler.get_scheduler_statistics()
        queue_stats = self.task_queue.get_queue_statistics()
        
        return {
            "batch_processing_active": self.scheduler.is_running,
            "scheduler_statistics": scheduler_stats,
            "queue_statistics": queue_stats,
            "total_projects": len(self.list_batch_projects())
        }
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, int]:
        """Clean up old batch processing data."""
        
        # Clean up completed tasks
        cleared_tasks = self.task_queue.clear_completed_tasks(days_old)
        
        # Clean up old output directories (implement if needed)
        cleared_dirs = 0
        
        return {
            "cleared_tasks": cleared_tasks,
            "cleared_directories": cleared_dirs
        }
    
    def export_batch_report(self, project_id: str) -> Dict[str, Any]:
        """Export detailed report for a batch project."""
        
        batch_status = self.get_batch_status(project_id)
        tasks = self.task_queue.list_tasks(project_filter=project_id)
        
        # Calculate detailed statistics
        task_types = {}
        processing_times = []
        
        for task in tasks:
            task_type = task.task_type
            if task_type not in task_types:
                task_types[task_type] = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "avg_duration": 0
                }
            
            task_types[task_type]["total"] += 1
            
            if task.status == TaskStatus.COMPLETED:
                task_types[task_type]["completed"] += 1
                if task.actual_duration:
                    processing_times.append(task.actual_duration)
            elif task.status == TaskStatus.FAILED:
                task_types[task_type]["failed"] += 1
        
        # Calculate average durations
        for task_type_stats in task_types.values():
            if task_type_stats["completed"] > 0:
                completed_tasks = [t for t in tasks if t.task_type == task_type and t.actual_duration]
                if completed_tasks:
                    total_duration = sum(t.actual_duration for t in completed_tasks)
                    task_type_stats["avg_duration"] = total_duration / len(completed_tasks)
        
        return {
            "report_generated": datetime.now().isoformat(),
            "project_summary": batch_status,
            "task_type_breakdown": task_types,
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
            "total_processing_time": sum(processing_times),
            "detailed_tasks": [
                {
                    "task_id": t.task_id,
                    "task_type": t.task_type,
                    "input_file": t.input_file,
                    "output_dir": t.output_dir,
                    "status": t.status.value,
                    "created_at": t.created_at,
                    "started_at": t.started_at,
                    "completed_at": t.completed_at,
                    "estimated_duration": t.estimated_duration,
                    "actual_duration": t.actual_duration,
                    "progress": t.progress_percentage,
                    "error_message": t.error_message,
                    "retry_count": t.retry_count
                }
                for t in tasks
            ]
        }
    
    def _estimate_processing_time(self, video_file: str, processing_type: str) -> int:
        """Estimate processing time based on file size and type."""
        
        try:
            file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
        except OSError:
            file_size_mb = 100  # Default assumption
        
        # Base time estimates per MB (in minutes)
        time_per_mb = {
            "video_translation": 0.5,  # Full translation is complex
            "audio_extraction": 0.05,  # Simple extraction
            "subtitle_generation": 0.3,  # Text processing
            "video_transcoding": 0.1    # Re-encoding
        }
        
        base_time = time_per_mb.get(processing_type, 0.2) * file_size_mb
        
        # Add minimum time and round up
        return max(5, int(base_time) + 1)