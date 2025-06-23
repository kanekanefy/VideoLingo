"""
Job Scheduler Module

Manages the execution of queued tasks with worker threads and resource management.
"""

import threading
import time
import os
import subprocess
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .task_queue import TaskQueue, TaskDefinition, TaskStatus, TaskPriority

class WorkerStatus(Enum):
    """Worker thread status."""
    IDLE = "idle"
    BUSY = "busy"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class WorkerInfo:
    """Information about a worker thread."""
    worker_id: str
    status: WorkerStatus
    current_task: Optional[str]
    capabilities: List[str]
    created_at: str
    last_activity: str
    tasks_completed: int
    tasks_failed: int

class JobScheduler:
    """Manages task execution with worker threads."""
    
    def __init__(self, max_workers: int = 4, max_cpu_usage: float = 80.0, max_memory_usage: float = 85.0):
        self.task_queue = TaskQueue()
        self.max_workers = max_workers
        self.max_cpu_usage = max_cpu_usage
        self.max_memory_usage = max_memory_usage
        
        self.workers: Dict[str, WorkerInfo] = {}
        self.worker_threads: Dict[str, threading.Thread] = {}
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Task execution callbacks
        self.task_handlers: Dict[str, Callable] = {}
        
        # Register default task handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default task handlers."""
        self.task_handlers = {
            "video_translation": self._handle_video_translation,
            "audio_extraction": self._handle_audio_extraction,
            "subtitle_generation": self._handle_subtitle_generation,
            "video_transcoding": self._handle_video_transcoding
        }
    
    def register_task_handler(self, task_type: str, handler: Callable[[TaskDefinition], bool]):
        """Register a custom task handler."""
        self.task_handlers[task_type] = handler
    
    def start(self):
        """Start the job scheduler."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        print(f"🚀 Job scheduler started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the job scheduler."""
        self.is_running = False
        
        # Stop all workers
        for worker_id in list(self.workers.keys()):
            self._stop_worker(worker_id)
        
        # Wait for scheduler thread
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        print("🛑 Job scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                # Check system resources
                if not self._check_system_resources():
                    time.sleep(10)  # Wait before checking again
                    continue
                
                # Manage workers
                self._manage_workers()
                
                # Assign tasks to idle workers
                self._assign_tasks()
                
                # Cleanup finished workers
                self._cleanup_workers()
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"❌ Scheduler error: {e}")
                time.sleep(5)
    
    def _check_system_resources(self) -> bool:
        """Check if system resources are available for new tasks."""
        if not PSUTIL_AVAILABLE:
            # If psutil is not available, assume resources are available
            return True
            
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.max_cpu_usage:
                return False
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.max_memory_usage:
                return False
            
            return True
            
        except Exception:
            # If we can't check resources, assume they're available
            return True
    
    def _manage_workers(self):
        """Manage worker threads."""
        with self.lock:
            active_workers = len([w for w in self.workers.values() if w.status != WorkerStatus.STOPPED])
            
            # Start new workers if needed
            if active_workers < self.max_workers:
                needed_workers = self.max_workers - active_workers
                for _ in range(needed_workers):
                    self._start_worker()
    
    def _start_worker(self):
        """Start a new worker thread."""
        worker_id = f"worker_{len(self.workers)+1}_{int(time.time())}"
        
        worker_info = WorkerInfo(
            worker_id=worker_id,
            status=WorkerStatus.IDLE,
            current_task=None,
            capabilities=["video_translation", "audio_extraction", "subtitle_generation", "video_transcoding"],
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat(),
            tasks_completed=0,
            tasks_failed=0
        )
        
        worker_thread = threading.Thread(target=self._worker_loop, args=(worker_id,), daemon=True)
        
        with self.lock:
            self.workers[worker_id] = worker_info
            self.worker_threads[worker_id] = worker_thread
        
        worker_thread.start()
        print(f"👷 Started worker: {worker_id}")
    
    def _stop_worker(self, worker_id: str):
        """Stop a specific worker."""
        with self.lock:
            if worker_id in self.workers:
                self.workers[worker_id].status = WorkerStatus.STOPPED
            
            # Cancel current task if running
            worker = self.workers.get(worker_id)
            if worker and worker.current_task:
                self.task_queue.cancel_task(worker.current_task)
    
    def _worker_loop(self, worker_id: str):
        """Main worker loop."""
        while self.is_running:
            try:
                with self.lock:
                    if worker_id not in self.workers:
                        break
                    
                    worker = self.workers[worker_id]
                    if worker.status == WorkerStatus.STOPPED:
                        break
                
                # Get next task
                task = self.task_queue.get_next_task(worker.capabilities)
                
                if task:
                    self._execute_task(worker_id, task)
                else:
                    # No tasks available, wait
                    time.sleep(5)
                
            except Exception as e:
                print(f"❌ Worker {worker_id} error: {e}")
                with self.lock:
                    if worker_id in self.workers:
                        self.workers[worker_id].status = WorkerStatus.ERROR
                time.sleep(10)
    
    def _execute_task(self, worker_id: str, task: TaskDefinition):
        """Execute a task."""
        try:
            # Update worker status
            with self.lock:
                worker = self.workers[worker_id]
                worker.status = WorkerStatus.BUSY
                worker.current_task = task.task_id
                worker.last_activity = datetime.now().isoformat()
            
            # Update task status
            self.task_queue.update_task_status(task.task_id, TaskStatus.RUNNING)
            
            print(f"🔄 Worker {worker_id} starting task {task.task_id} ({task.task_type})")
            
            # Execute task
            handler = self.task_handlers.get(task.task_type)
            if not handler:
                raise Exception(f"No handler for task type: {task.task_type}")
            
            success = handler(task)
            
            if success:
                self.task_queue.update_task_status(task.task_id, TaskStatus.COMPLETED, 100.0)
                print(f"✅ Worker {worker_id} completed task {task.task_id}")
                
                with self.lock:
                    worker.tasks_completed += 1
            else:
                self.task_queue.update_task_status(task.task_id, TaskStatus.FAILED, 
                                                 error_message="Task handler returned False")
                print(f"❌ Worker {worker_id} failed task {task.task_id}")
                
                with self.lock:
                    worker.tasks_failed += 1
            
        except Exception as e:
            error_msg = str(e)
            self.task_queue.update_task_status(task.task_id, TaskStatus.FAILED, error_message=error_msg)
            print(f"❌ Worker {worker_id} failed task {task.task_id}: {error_msg}")
            
            with self.lock:
                worker.tasks_failed += 1
        
        finally:
            # Reset worker status
            with self.lock:
                if worker_id in self.workers:
                    worker = self.workers[worker_id]
                    worker.status = WorkerStatus.IDLE
                    worker.current_task = None
                    worker.last_activity = datetime.now().isoformat()
    
    def _assign_tasks(self):
        """Assign tasks to idle workers."""
        with self.lock:
            idle_workers = [w for w in self.workers.values() if w.status == WorkerStatus.IDLE]
        
        # Tasks will be picked up by workers in their main loop
        # This method can be used for more sophisticated assignment logic if needed
        pass
    
    def _cleanup_workers(self):
        """Cleanup stopped worker threads."""
        with self.lock:
            stopped_workers = [wid for wid, w in self.workers.items() if w.status == WorkerStatus.STOPPED]
            
            for worker_id in stopped_workers:
                # Wait for thread to finish
                if worker_id in self.worker_threads:
                    thread = self.worker_threads[worker_id]
                    if not thread.is_alive():
                        del self.worker_threads[worker_id]
                        del self.workers[worker_id]
                        print(f"🗑️ Cleaned up stopped worker: {worker_id}")
    
    def get_worker_status(self) -> List[WorkerInfo]:
        """Get status of all workers."""
        with self.lock:
            return list(self.workers.values())
    
    def get_scheduler_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        with self.lock:
            workers = list(self.workers.values())
        
        queue_stats = self.task_queue.get_queue_statistics()
        
        return {
            "scheduler_running": self.is_running,
            "total_workers": len(workers),
            "active_workers": len([w for w in workers if w.status != WorkerStatus.STOPPED]),
            "busy_workers": len([w for w in workers if w.status == WorkerStatus.BUSY]),
            "idle_workers": len([w for w in workers if w.status == WorkerStatus.IDLE]),
            "total_tasks_completed": sum(w.tasks_completed for w in workers),
            "total_tasks_failed": sum(w.tasks_failed for w in workers),
            "queue_statistics": queue_stats,
            "system_resources": self._get_system_resources()
        }
    
    def _get_system_resources(self) -> Dict[str, float]:
        """Get current system resource usage."""
        if not PSUTIL_AVAILABLE:
            return {"cpu_percent": 0, "memory_percent": 0, "disk_usage": 0}
            
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if os.path.exists('/') else 0
            }
        except Exception:
            return {"cpu_percent": 0, "memory_percent": 0, "disk_usage": 0}
    
    # Default task handlers
    def _handle_video_translation(self, task: TaskDefinition) -> bool:
        """Handle video translation task."""
        print(f"🎬 Processing video translation: {task.input_file}")
        
        # Simulate video translation process
        stages = ["audio_extraction", "transcription", "translation", "tts_generation", "video_mixing"]
        
        for i, stage in enumerate(stages):
            progress = (i + 1) / len(stages) * 100
            self.task_queue.update_task_status(task.task_id, TaskStatus.RUNNING, progress)
            print(f"  📊 {stage}: {progress:.1f}%")
            
            # Simulate processing time
            time.sleep(2)
        
        return True
    
    def _handle_audio_extraction(self, task: TaskDefinition) -> bool:
        """Handle audio extraction task."""
        print(f"🎵 Extracting audio: {task.input_file}")
        
        # Simulate audio extraction
        for i in range(10):
            progress = (i + 1) / 10 * 100
            self.task_queue.update_task_status(task.task_id, TaskStatus.RUNNING, progress)
            time.sleep(0.5)
        
        return True
    
    def _handle_subtitle_generation(self, task: TaskDefinition) -> bool:
        """Handle subtitle generation task."""
        print(f"📝 Generating subtitles: {task.input_file}")
        
        # Simulate subtitle generation
        for i in range(8):
            progress = (i + 1) / 8 * 100
            self.task_queue.update_task_status(task.task_id, TaskStatus.RUNNING, progress)
            time.sleep(0.3)
        
        return True
    
    def _handle_video_transcoding(self, task: TaskDefinition) -> bool:
        """Handle video transcoding task."""
        print(f"🎞️ Transcoding video: {task.input_file}")
        
        # Simulate video transcoding
        for i in range(15):
            progress = (i + 1) / 15 * 100
            self.task_queue.update_task_status(task.task_id, TaskStatus.RUNNING, progress)
            time.sleep(0.2)
        
        return True