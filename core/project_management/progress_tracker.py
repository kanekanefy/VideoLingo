"""
进度跟踪器

跟踪项目各个阶段的进度，提供里程碑管理和进度可视化
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"           # 待开始
    IN_PROGRESS = "in_progress"   # 进行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"       # 已取消

class TaskPriority(Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Task:
    """任务数据类"""
    id: str
    name: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    progress: float  # 0.0 - 1.0
    estimated_duration: Optional[int] = None  # 预估时长（分钟）
    actual_duration: Optional[int] = None     # 实际时长（分钟）
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = None            # 依赖的任务ID
    assigned_to: str = "system"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        data['status'] = TaskStatus(data['status'])
        data['priority'] = TaskPriority(data['priority'])
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)

@dataclass
class Milestone:
    """里程碑数据类"""
    id: str
    name: str
    description: str
    target_date: datetime
    completed_date: Optional[datetime] = None
    progress: float = 0.0
    tasks: List[str] = None  # 包含的任务ID列表
    
    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
    
    @property
    def is_completed(self) -> bool:
        return self.completed_date is not None
    
    @property
    def is_overdue(self) -> bool:
        return not self.is_completed and datetime.now() > self.target_date
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['target_date'] = self.target_date.isoformat()
        if self.completed_date:
            data['completed_date'] = self.completed_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Milestone':
        data['target_date'] = datetime.fromisoformat(data['target_date'])
        if data.get('completed_date'):
            data['completed_date'] = datetime.fromisoformat(data['completed_date'])
        return cls(**data)

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, project_id: str, projects_root: str = "projects"):
        self.project_id = project_id
        self.project_dir = Path(projects_root) / project_id
        self.progress_file = self.project_dir / "progress.json"
        
        # 加载进度数据
        self.tasks: Dict[str, Task] = {}
        self.milestones: Dict[str, Milestone] = {}
        self._load_progress()
        
        # 初始化默认任务流程
        if not self.tasks:
            self._init_default_workflow()
    
    def _load_progress(self):
        """加载进度数据"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 加载任务
                for task_data in data.get('tasks', []):
                    task = Task.from_dict(task_data)
                    self.tasks[task.id] = task
                
                # 加载里程碑
                for milestone_data in data.get('milestones', []):
                    milestone = Milestone.from_dict(milestone_data)
                    self.milestones[milestone.id] = milestone
                    
            except Exception as e:
                print(f"加载进度数据失败: {e}")
    
    def _save_progress(self):
        """保存进度数据"""
        try:
            data = {
                'tasks': [task.to_dict() for task in self.tasks.values()],
                'milestones': [milestone.to_dict() for milestone in self.milestones.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存进度数据失败: {e}")
    
    def _init_default_workflow(self):
        """初始化默认工作流程"""
        
        # 定义标准视频翻译工作流程
        default_tasks = [
            # 准备阶段
            {
                "id": "setup_project",
                "name": "项目设置",
                "description": "配置项目参数和初始化环境",
                "priority": TaskPriority.HIGH,
                "estimated_duration": 10,
                "tags": ["setup"]
            },
            {
                "id": "upload_video",
                "name": "上传视频文件",
                "description": "上传或下载待翻译的视频文件",
                "priority": TaskPriority.HIGH,
                "estimated_duration": 15,
                "dependencies": ["setup_project"],
                "tags": ["upload"]
            },
            
            # 转录阶段
            {
                "id": "audio_preprocessing",
                "name": "音频预处理",
                "description": "音频分离和降噪处理",
                "priority": TaskPriority.MEDIUM,
                "estimated_duration": 30,
                "dependencies": ["upload_video"],
                "tags": ["audio", "preprocessing"]
            },
            {
                "id": "speech_recognition",
                "name": "语音识别",
                "description": "使用WhisperX进行语音转文字",
                "priority": TaskPriority.HIGH,
                "estimated_duration": 60,
                "dependencies": ["audio_preprocessing"],
                "tags": ["whisper", "transcription"]
            },
            {
                "id": "text_segmentation",
                "name": "文本分句",
                "description": "NLP和LLM智能分句处理",
                "priority": TaskPriority.MEDIUM,
                "estimated_duration": 20,
                "dependencies": ["speech_recognition"],
                "tags": ["nlp", "segmentation"]
            },
            
            # 翻译阶段
            {
                "id": "content_analysis",
                "name": "内容分析",
                "description": "总结内容主题和提取术语",
                "priority": TaskPriority.MEDIUM,
                "estimated_duration": 25,
                "dependencies": ["text_segmentation"],
                "tags": ["analysis", "terminology"]
            },
            {
                "id": "translation",
                "name": "翻译处理",
                "description": "多步骤高质量翻译",
                "priority": TaskPriority.HIGH,
                "estimated_duration": 90,
                "dependencies": ["content_analysis"],
                "tags": ["translation", "llm"]
            },
            {
                "id": "terminology_check",
                "name": "术语检查",
                "description": "术语一致性检查和修正",
                "priority": TaskPriority.MEDIUM,
                "estimated_duration": 15,
                "dependencies": ["translation"],
                "tags": ["terminology", "quality"]
            },
            
            # 字幕阶段
            {
                "id": "subtitle_timing",
                "name": "字幕时间轴",
                "description": "生成精确的字幕时间轴",
                "priority": TaskPriority.HIGH,
                "estimated_duration": 30,
                "dependencies": ["terminology_check"],
                "tags": ["subtitle", "timing"]
            },
            {
                "id": "subtitle_generation",
                "name": "字幕生成",
                "description": "生成最终字幕文件",
                "priority": TaskPriority.MEDIUM,
                "estimated_duration": 20,
                "dependencies": ["subtitle_timing"],
                "tags": ["subtitle", "generation"]
            },
            
            # 配音阶段 (可选)
            {
                "id": "voice_cloning",
                "name": "声音克隆",
                "description": "提取和克隆原始声音特征",
                "priority": TaskPriority.LOW,
                "estimated_duration": 45,
                "dependencies": ["subtitle_generation"],
                "tags": ["tts", "voice"]
            },
            {
                "id": "audio_generation",
                "name": "音频生成",
                "description": "生成配音音频文件",
                "priority": TaskPriority.MEDIUM,
                "estimated_duration": 60,
                "dependencies": ["voice_cloning"],
                "tags": ["tts", "audio"]
            },
            {
                "id": "audio_mixing",
                "name": "音频合成",
                "description": "将配音与原视频合成",
                "priority": TaskPriority.MEDIUM,
                "estimated_duration": 25,
                "dependencies": ["audio_generation"],
                "tags": ["audio", "mixing"]
            },
            
            # 完成阶段
            {
                "id": "quality_review",
                "name": "质量审核",
                "description": "最终质量检查和验收",
                "priority": TaskPriority.HIGH,
                "estimated_duration": 30,
                "dependencies": ["audio_mixing"],
                "tags": ["quality", "review"]
            },
            {
                "id": "output_packaging",
                "name": "输出打包",
                "description": "打包输出文件和生成报告",
                "priority": TaskPriority.LOW,
                "estimated_duration": 10,
                "dependencies": ["quality_review"],
                "tags": ["output", "packaging"]
            }
        ]
        
        # 创建任务
        for task_data in default_tasks:
            task = Task(
                id=task_data["id"],
                name=task_data["name"],
                description=task_data["description"],
                status=TaskStatus.PENDING,
                priority=task_data["priority"],
                progress=0.0,
                estimated_duration=task_data["estimated_duration"],
                dependencies=task_data.get("dependencies", []),
                tags=task_data.get("tags", [])
            )
            self.tasks[task.id] = task
        
        # 创建里程碑
        milestones_data = [
            {
                "id": "transcription_complete",
                "name": "转录完成",
                "description": "语音识别和文本分句完成",
                "tasks": ["speech_recognition", "text_segmentation"],
                "days_offset": 1
            },
            {
                "id": "translation_complete", 
                "name": "翻译完成",
                "description": "翻译和术语检查完成",
                "tasks": ["translation", "terminology_check"],
                "days_offset": 3
            },
            {
                "id": "subtitle_complete",
                "name": "字幕完成",
                "description": "字幕生成和时间轴对齐完成",
                "tasks": ["subtitle_timing", "subtitle_generation"],
                "days_offset": 4
            },
            {
                "id": "dubbing_complete",
                "name": "配音完成",
                "description": "配音生成和音频合成完成",
                "tasks": ["audio_generation", "audio_mixing"],
                "days_offset": 6
            },
            {
                "id": "project_complete",
                "name": "项目完成",
                "description": "所有任务完成，项目交付",
                "tasks": ["quality_review", "output_packaging"],
                "days_offset": 7
            }
        ]
        
        # 创建里程碑
        base_date = datetime.now()
        for milestone_data in milestones_data:
            target_date = base_date + timedelta(days=milestone_data["days_offset"])
            milestone = Milestone(
                id=milestone_data["id"],
                name=milestone_data["name"],
                description=milestone_data["description"],
                target_date=target_date,
                tasks=milestone_data["tasks"]
            )
            self.milestones[milestone.id] = milestone
        
        # 保存初始化数据
        self._save_progress()
    
    def start_task(self, task_id: str) -> bool:
        """开始任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # 检查依赖任务是否完成
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if dep_task.status != TaskStatus.COMPLETED:
                    print(f"依赖任务未完成: {dep_task.name}")
                    return False
        
        # 开始任务
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        task.progress = 0.1  # 设置初始进度
        
        self._save_progress()
        print(f"✅ 任务已开始: {task.name}")
        return True
    
    def update_task_progress(self, task_id: str, progress: float, message: str = "") -> bool:
        """更新任务进度"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.progress = max(0.0, min(1.0, progress))
        
        # 如果进度达到100%，自动完成任务
        if task.progress >= 1.0:
            self.complete_task(task_id)
        else:
            self._save_progress()
        
        if message:
            print(f"📊 {task.name}: {progress*100:.1f}% - {message}")
        
        return True
    
    def complete_task(self, task_id: str, success: bool = True) -> bool:
        """完成任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now()
        task.progress = 1.0 if success else task.progress
        
        # 计算实际耗时
        if task.started_at:
            duration = (task.completed_at - task.started_at).total_seconds() / 60
            task.actual_duration = int(duration)
        
        # 检查并更新里程碑
        self._update_milestones()
        
        self._save_progress()
        
        status_text = "完成" if success else "失败"
        print(f"✅ 任务已{status_text}: {task.name}")
        return True
    
    def _update_milestones(self):
        """更新里程碑进度"""
        for milestone in self.milestones.values():
            if milestone.is_completed:
                continue
            
            # 计算里程碑进度
            total_tasks = len(milestone.tasks)
            completed_tasks = 0
            total_progress = 0.0
            
            for task_id in milestone.tasks:
                if task_id in self.tasks:
                    task = self.tasks[task_id]
                    total_progress += task.progress
                    if task.status == TaskStatus.COMPLETED:
                        completed_tasks += 1
            
            # 更新里程碑进度
            milestone.progress = total_progress / total_tasks if total_tasks > 0 else 0.0
            
            # 检查是否完成
            if completed_tasks == total_tasks:
                milestone.completed_date = datetime.now()
                print(f"🎉 里程碑达成: {milestone.name}")
    
    def get_project_progress(self) -> Dict:
        """获取项目整体进度"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for task in self.tasks.values() 
                            if task.status == TaskStatus.COMPLETED)
        in_progress_tasks = sum(1 for task in self.tasks.values() 
                              if task.status == TaskStatus.IN_PROGRESS)
        failed_tasks = sum(1 for task in self.tasks.values() 
                         if task.status == TaskStatus.FAILED)
        
        # 计算总体进度
        total_progress = sum(task.progress for task in self.tasks.values())
        overall_progress = total_progress / total_tasks if total_tasks > 0 else 0.0
        
        # 预估剩余时间
        estimated_remaining = self._estimate_remaining_time()
        
        return {
            "overall_progress": overall_progress,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "pending_tasks": total_tasks - completed_tasks - in_progress_tasks - failed_tasks,
            "failed_tasks": failed_tasks,
            "total_tasks": total_tasks,
            "estimated_remaining_minutes": estimated_remaining,
            "milestones_completed": sum(1 for m in self.milestones.values() if m.is_completed),
            "milestones_overdue": sum(1 for m in self.milestones.values() if m.is_overdue),
            "total_milestones": len(self.milestones)
        }
    
    def _estimate_remaining_time(self) -> int:
        """预估剩余时间（分钟）"""
        remaining_minutes = 0
        
        for task in self.tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                if task.estimated_duration:
                    remaining_for_task = task.estimated_duration * (1 - task.progress)
                    remaining_minutes += remaining_for_task
        
        return int(remaining_minutes)
    
    def get_next_tasks(self) -> List[Task]:
        """获取下一步可执行的任务"""
        available_tasks = []
        
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # 检查依赖是否满足
                dependencies_met = all(
                    self.tasks.get(dep_id, Task("", "", "", TaskStatus.FAILED, TaskPriority.LOW, 0.0)).status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                
                if dependencies_met:
                    available_tasks.append(task)
        
        # 按优先级排序
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3
        }
        
        available_tasks.sort(key=lambda t: priority_order[t.priority])
        return available_tasks
    
    def get_critical_path(self) -> List[str]:
        """获取关键路径（影响项目完成时间的任务链）"""
        # 简化的关键路径计算
        # 这里返回最长的依赖链
        
        def get_task_chain_duration(task_id: str, visited: set) -> int:
            if task_id in visited or task_id not in self.tasks:
                return 0
            
            visited.add(task_id)
            task = self.tasks[task_id]
            
            max_dep_duration = 0
            for dep_id in task.dependencies:
                dep_duration = get_task_chain_duration(dep_id, visited.copy())
                max_dep_duration = max(max_dep_duration, dep_duration)
            
            return max_dep_duration + (task.estimated_duration or 0)
        
        # 找到最长的链
        max_duration = 0
        critical_tasks = []
        
        for task_id in self.tasks:
            duration = get_task_chain_duration(task_id, set())
            if duration > max_duration:
                max_duration = duration
                # 这里简化返回，实际实现需要记录路径
        
        return critical_tasks
    
    def get_task_statistics(self) -> Dict:
        """获取任务统计信息"""
        stats = {
            "by_status": {},
            "by_priority": {},
            "by_tags": {},
            "duration_accuracy": {},
            "overdue_tasks": []
        }
        
        # 按状态统计
        for task in self.tasks.values():
            status = task.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            priority = task.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
            
            # 标签统计
            for tag in task.tags:
                stats["by_tags"][tag] = stats["by_tags"].get(tag, 0) + 1
            
            # 时长准确性分析
            if task.estimated_duration and task.actual_duration:
                accuracy = abs(task.estimated_duration - task.actual_duration) / task.estimated_duration
                if accuracy <= 0.1:
                    category = "accurate"
                elif accuracy <= 0.3:
                    category = "moderate"
                else:
                    category = "inaccurate"
                
                stats["duration_accuracy"][category] = stats["duration_accuracy"].get(category, 0) + 1
        
        return stats