"""
项目管理器

负责项目的创建、管理、搜索、归档等核心功能
"""

import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class ProjectStatus(Enum):
    """项目状态枚举"""
    CREATED = "created"           # 已创建
    IN_PROGRESS = "in_progress"   # 进行中
    TRANSLATING = "translating"   # 翻译中
    REVIEWING = "reviewing"       # 审核中
    COMPLETED = "completed"       # 已完成
    ARCHIVED = "archived"         # 已归档
    PAUSED = "paused"            # 已暂停

class ProjectType(Enum):
    """项目类型枚举"""
    MOVIE = "movie"              # 电影
    TV_SERIES = "tv_series"      # 电视剧
    DOCUMENTARY = "documentary"   # 纪录片
    ANIMATION = "animation"       # 动画
    COMMERCIAL = "commercial"     # 广告
    EDUCATIONAL = "educational"   # 教育
    OTHER = "other"              # 其他

@dataclass
class ProjectMetadata:
    """项目元数据"""
    id: str
    name: str
    description: str
    project_type: ProjectType
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    
    # 源信息
    source_language: str
    target_languages: List[str]
    
    # 项目配置
    config: Dict[str, Any]
    
    # 标签和分类
    tags: List[str]
    category: str
    
    # 创建者信息
    created_by: str
    
    # 统计信息
    total_duration: Optional[float] = None
    progress_percentage: float = 0.0
    
    # 版本信息
    current_version: str = "1.0.0"
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['project_type'] = self.project_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectMetadata':
        """从字典创建"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['project_type'] = ProjectType(data['project_type'])
        data['status'] = ProjectStatus(data['status'])
        return cls(**data)

class ProjectManager:
    """项目管理器"""
    
    def __init__(self, projects_root: str = "projects"):
        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(exist_ok=True)
        
        # 项目索引文件
        self.index_file = self.projects_root / "projects_index.json"
        self.projects_index = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict]:
        """加载项目索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载项目索引失败: {e}")
                return {}
        return {}
    
    def _save_index(self):
        """保存项目索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.projects_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存项目索引失败: {e}")
    
    def create_project(self, 
                      name: str,
                      description: str = "",
                      project_type: ProjectType = ProjectType.MOVIE,
                      source_language: str = "en",
                      target_languages: List[str] = None,
                      tags: List[str] = None,
                      category: str = "general",
                      created_by: str = "user",
                      template_id: str = None,
                      config_override: Dict = None) -> str:
        """创建新项目"""
        
        if target_languages is None:
            target_languages = ["zh-CN"]
        if tags is None:
            tags = []
        
        # 生成项目ID
        project_id = str(uuid.uuid4())
        
        # 创建项目目录
        project_dir = self.projects_root / project_id
        project_dir.mkdir(exist_ok=True)
        
        # 创建项目子目录
        subdirs = [
            "input",          # 输入文件
            "output",         # 输出文件
            "versions",       # 版本历史
            "batches",        # 批量任务
            "emotions",       # 情感分析
            "terminology",    # 术语库
            "temp",           # 临时文件
            "logs"            # 日志文件
        ]
        
        for subdir in subdirs:
            (project_dir / subdir).mkdir(exist_ok=True)
        
        # 加载模板配置
        base_config = self._get_default_config()
        if template_id:
            template_config = self._load_template_config(template_id)
            base_config.update(template_config)
        
        # 应用配置覆盖
        if config_override:
            base_config.update(config_override)
        
        # 创建项目元数据
        now = datetime.now()
        metadata = ProjectMetadata(
            id=project_id,
            name=name,
            description=description,
            project_type=project_type,
            status=ProjectStatus.CREATED,
            created_at=now,
            updated_at=now,
            source_language=source_language,
            target_languages=target_languages,
            config=base_config,
            tags=tags,
            category=category,
            created_by=created_by
        )
        
        # 保存项目元数据
        metadata_file = project_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 更新项目索引
        self.projects_index[project_id] = {
            "name": name,
            "project_type": project_type.value,
            "status": ProjectStatus.CREATED.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "tags": tags,
            "category": category
        }
        self._save_index()
        
        print(f"✅ 项目创建成功: {name} (ID: {project_id})")
        return project_id
    
    def get_project(self, project_id: str) -> Optional[ProjectMetadata]:
        """获取项目信息"""
        project_dir = self.projects_root / project_id
        metadata_file = project_dir / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ProjectMetadata.from_dict(data)
        except Exception as e:
            print(f"加载项目失败: {e}")
            return None
    
    def update_project(self, project_id: str, updates: Dict) -> bool:
        """更新项目信息"""
        metadata = self.get_project(project_id)
        if not metadata:
            return False
        
        try:
            # 更新元数据
            for key, value in updates.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
            
            metadata.updated_at = datetime.now()
            
            # 保存更新
            project_dir = self.projects_root / project_id
            metadata_file = project_dir / "metadata.json"
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新索引
            if project_id in self.projects_index:
                index_updates = {
                    "name": metadata.name,
                    "status": metadata.status.value,
                    "updated_at": metadata.updated_at.isoformat(),
                    "tags": metadata.tags,
                    "category": metadata.category
                }
                self.projects_index[project_id].update(index_updates)
                self._save_index()
            
            return True
            
        except Exception as e:
            print(f"更新项目失败: {e}")
            return False
    
    def delete_project(self, project_id: str, permanent: bool = False) -> bool:
        """删除项目"""
        if permanent:
            # 永久删除
            project_dir = self.projects_root / project_id
            if project_dir.exists():
                shutil.rmtree(project_dir)
            
            # 从索引中删除
            if project_id in self.projects_index:
                del self.projects_index[project_id]
                self._save_index()
            
            print(f"✅ 项目已永久删除: {project_id}")
            return True
        else:
            # 归档删除
            return self.update_project(project_id, {"status": ProjectStatus.ARCHIVED})
    
    def list_projects(self, 
                     status: Optional[ProjectStatus] = None,
                     project_type: Optional[ProjectType] = None,
                     tags: Optional[List[str]] = None,
                     category: Optional[str] = None,
                     search_term: Optional[str] = None) -> List[Dict]:
        """列出项目"""
        
        projects = []
        
        for project_id, index_data in self.projects_index.items():
            # 状态过滤
            if status and ProjectStatus(index_data["status"]) != status:
                continue
            
            # 类型过滤
            if project_type and ProjectType(index_data["project_type"]) != project_type:
                continue
            
            # 标签过滤
            if tags:
                project_tags = set(index_data.get("tags", []))
                if not any(tag in project_tags for tag in tags):
                    continue
            
            # 分类过滤
            if category and index_data.get("category") != category:
                continue
            
            # 搜索词过滤
            if search_term:
                search_fields = [
                    index_data.get("name", ""),
                    " ".join(index_data.get("tags", [])),
                    index_data.get("category", "")
                ]
                if not any(search_term.lower() in field.lower() for field in search_fields):
                    continue
            
            # 添加项目ID
            project_data = index_data.copy()
            project_data["id"] = project_id
            projects.append(project_data)
        
        # 按更新时间排序
        projects.sort(key=lambda x: x["updated_at"], reverse=True)
        return projects
    
    def get_project_path(self, project_id: str) -> Path:
        """获取项目目录路径"""
        return self.projects_root / project_id
    
    def set_active_project(self, project_id: str) -> bool:
        """设置活动项目"""
        metadata = self.get_project(project_id)
        if not metadata:
            return False
        
        # 保存当前活动项目ID
        active_file = self.projects_root / "active_project.txt"
        with open(active_file, 'w') as f:
            f.write(project_id)
        
        return True
    
    def get_active_project(self) -> Optional[str]:
        """获取当前活动项目ID"""
        active_file = self.projects_root / "active_project.txt"
        if active_file.exists():
            try:
                with open(active_file, 'r') as f:
                    return f.read().strip()
            except:
                pass
        return None
    
    def _get_default_config(self) -> Dict:
        """获取默认项目配置"""
        return {
            "display_language": "zh-CN",
            "api": {
                "key": "your-api-key",
                "base_url": "https://yunwu.ai",
                "model": "gpt-4.1-2025-04-14"
            },
            "whisper": {
                "model": "large-v3",
                "language": "en",
                "runtime": "local"
            },
            "tts_method": "azure_tts",
            "burn_subtitles": True,
            "max_workers": 4,
            "terminology_enabled": True,
            "emotion_analysis_enabled": True,
            "version_control_enabled": True
        }
    
    def _load_template_config(self, template_id: str) -> Dict:
        """加载模板配置"""
        # 这里将在project_templates.py中实现
        return {}
    
    def get_project_statistics(self) -> Dict:
        """获取项目统计信息"""
        stats = {
            "total_projects": len(self.projects_index),
            "by_status": {},
            "by_type": {},
            "by_category": {},
            "recent_activity": []
        }
        
        # 按状态统计
        for project_data in self.projects_index.values():
            status = project_data["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            project_type = project_data["project_type"]
            stats["by_type"][project_type] = stats["by_type"].get(project_type, 0) + 1
            
            category = project_data.get("category", "general")
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        
        # 最近活动
        recent_projects = sorted(
            [(pid, data) for pid, data in self.projects_index.items()],
            key=lambda x: x[1]["updated_at"],
            reverse=True
        )[:5]
        
        stats["recent_activity"] = [
            {
                "id": pid,
                "name": data["name"],
                "status": data["status"],
                "updated_at": data["updated_at"]
            }
            for pid, data in recent_projects
        ]
        
        return stats