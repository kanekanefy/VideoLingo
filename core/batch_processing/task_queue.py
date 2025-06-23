"""
Task Queue Management Module

Manages task queuing, scheduling, and execution for batch processing.
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from enum import Enum
import uuid
import queue

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class TaskDefinition:
    """Definition of a processing task."""
    task_id: str
    task_type: str
    project_id: str
    input_file: str
    output_dir: str
    config: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    estimated_duration: int = 0  # minutes
    actual_duration: Optional[int] = None
    progress_percentage: float = 0.0
    dependencies: List[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []

class TaskQueue:
    """Manages task queue and execution."""
    
    def __init__(self, storage_dir: str = "batch_processing"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.queue_file = self.storage_dir / "task_queue.json"
        self.lock = threading.Lock()
        self.task_callbacks: Dict[str, Callable] = {}
        self._running_tasks: Dict[str, threading.Thread] = {}
        
        # Load existing queue
        self._load_queue()
    
    def _load_queue(self):
        """Load task queue from storage."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = {
                        task_id: TaskDefinition(**task_data)
                        for task_id, task_data in data.items()
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                self.tasks = {}
        else:
            self.tasks = {}
    
    def _save_queue(self):
        """Save task queue to storage."""
        with self.lock:
            data = {
                task_id: asdict(task) for task_id, task in self.tasks.items()
            }
            
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def add_task(
        self,
        task_type: str,
        project_id: str,
        input_file: str,
        output_dir: str,
        config: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[str] = None,
        tags: List[str] = None,
        estimated_duration: int = 60
    ) -> str:
        """Add a new task to the queue."""
        
        task_id = str(uuid.uuid4())[:12]
        
        task = TaskDefinition(
            task_id=task_id,
            task_type=task_type,
            project_id=project_id,
            input_file=input_file,
            output_dir=output_dir,
            config=config,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now().isoformat(),
            dependencies=dependencies or [],
            tags=tags or [],
            estimated_duration=estimated_duration
        )
        
        with self.lock:
            self.tasks[task_id] = task
            self._save_queue()
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        """Get a specific task by ID."""
        return self.tasks.get(task_id)
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """Update task status and progress."""
        
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.status = status
            
            if progress is not None:
                task.progress_percentage = min(100.0, max(0.0, progress))
            
            if error_message:
                task.error_message = error_message
            
            # Update timestamps
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now().isoformat()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                if not task.completed_at:
                    task.completed_at = datetime.now().isoformat()
                
                # Calculate actual duration
                if task.started_at:
                    start_time = datetime.fromisoformat(task.started_at)
                    end_time = datetime.fromisoformat(task.completed_at)
                    duration = (end_time - start_time).total_seconds() / 60
                    task.actual_duration = int(duration)
            
            self._save_queue()
            return True
    
    def get_next_task(self, worker_capabilities: List[str] = None) -> Optional[TaskDefinition]:
        """Get the next task to execute based on priority and dependencies."""
        
        with self.lock:
            # Filter available tasks
            available_tasks = []
            
            for task in self.tasks.values():
                # Skip if not pending/queued
                if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED]:
                    continue
                
                # Check worker capabilities
                if worker_capabilities and task.task_type not in worker_capabilities:
                    continue
                
                # Check dependencies
                if task.dependencies:
                    deps_met = all(
                        self.tasks.get(dep_id, TaskDefinition("", "", "", "", "", {}, TaskPriority.NORMAL, TaskStatus.FAILED, "")).status == TaskStatus.COMPLETED
                        for dep_id in task.dependencies
                    )
                    if not deps_met:
                        continue
                
                available_tasks.append(task)
            
            if not available_tasks:
                return None
            
            # Sort by priority (highest first), then by creation time (oldest first)
            available_tasks.sort(
                key=lambda t: (-t.priority.value, t.created_at)
            )
            
            # Mark task as queued and return
            next_task = available_tasks[0]
            next_task.status = TaskStatus.QUEUED
            self._save_queue()
            
            return next_task
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return False  # Cannot cancel finished tasks
            
            # Stop running task if needed
            if task_id in self._running_tasks:
                # Note: In a real implementation, you'd need to implement task interruption
                pass
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now().isoformat()
            self._save_queue()
            
            return True
    
    def retry_task(self, task_id: str) -> bool:
        """Retry a failed task."""
        
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if task.status != TaskStatus.FAILED:
                return False
            
            if task.retry_count >= task.max_retries:
                return False
            
            # Reset task for retry
            task.status = TaskStatus.PENDING
            task.retry_count += 1
            task.started_at = None
            task.completed_at = None
            task.error_message = None
            task.progress_percentage = 0.0
            
            self._save_queue()
            return True
    
    def list_tasks(
        self,
        status_filter: Optional[TaskStatus] = None,
        project_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        tag_filter: Optional[str] = None
    ) -> List[TaskDefinition]:
        """List tasks with optional filters."""
        
        tasks = list(self.tasks.values())
        
        # Apply filters
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        
        if project_filter:
            tasks = [t for t in tasks if t.project_id == project_filter]
        
        if type_filter:
            tasks = [t for t in tasks if t.task_type == type_filter]
        
        if tag_filter:
            tasks = [t for t in tasks if tag_filter in t.tags]
        
        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks
    
    def get_queue_statistics(self) -> Dict[str, Any]:
        """Get queue statistics."""
        
        stats = {
            "total_tasks": len(self.tasks),
            "by_status": {},
            "by_type": {},
            "by_priority": {},
            "avg_wait_time": 0,
            "avg_execution_time": 0,
            "success_rate": 0
        }
        
        # Count by status
        for task in self.tasks.values():
            status = task.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # Count by type
        for task in self.tasks.values():
            task_type = task.task_type
            stats["by_type"][task_type] = stats["by_type"].get(task_type, 0) + 1
        
        # Count by priority
        for task in self.tasks.values():
            priority = task.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
        
        # Calculate averages and success rate
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
        
        if completed_tasks:
            # Average execution time
            exec_times = [t.actual_duration for t in completed_tasks if t.actual_duration]
            if exec_times:
                stats["avg_execution_time"] = sum(exec_times) / len(exec_times)
        
        # Success rate
        finished_tasks = completed_tasks + failed_tasks
        if finished_tasks:
            stats["success_rate"] = len(completed_tasks) / len(finished_tasks) * 100
        
        return stats
    
    def clear_completed_tasks(self, older_than_days: int = 7):
        """Clear completed tasks older than specified days."""
        
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        with self.lock:
            tasks_to_remove = []
            
            for task_id, task in self.tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    if task.completed_at:
                        completion_date = datetime.fromisoformat(task.completed_at)
                        if completion_date < cutoff_date:
                            tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
            
            if tasks_to_remove:
                self._save_queue()
            
            return len(tasks_to_remove)
    
    def estimate_queue_time(self, task_id: str) -> int:
        """Estimate how long until a task will start execution (in minutes)."""
        
        task = self.get_task(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return 0
        
        # Get tasks ahead in queue
        ahead_tasks = []
        for t in self.tasks.values():
            if (t.status in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING] and
                (t.priority.value > task.priority.value or 
                 (t.priority.value == task.priority.value and t.created_at < task.created_at))):
                ahead_tasks.append(t)
        
        # Estimate total time for tasks ahead
        total_time = 0
        for ahead_task in ahead_tasks:
            if ahead_task.status == TaskStatus.RUNNING:
                # Use remaining time for running tasks
                elapsed = 0
                if ahead_task.started_at:
                    start_time = datetime.fromisoformat(ahead_task.started_at)
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                
                remaining = max(0, ahead_task.estimated_duration - elapsed)
                total_time += remaining
            else:
                total_time += ahead_task.estimated_duration
        
        return int(total_time)