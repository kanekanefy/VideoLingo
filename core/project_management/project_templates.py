"""
项目模板管理系统

提供预设的项目模板，快速创建标准化项目配置
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from .project_manager import ProjectType

@dataclass
class ProjectTemplate:
    """项目模板数据类"""
    id: str
    name: str
    description: str
    project_type: ProjectType
    config: Dict
    tags: List[str]
    icon: str = "🎬"
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['project_type'] = self.project_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectTemplate':
        data['project_type'] = ProjectType(data['project_type'])
        return cls(**data)

class ProjectTemplateManager:
    """项目模板管理器"""
    
    def __init__(self, templates_dir: str = "core/project_management/templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化默认模板
        self._init_default_templates()
        
        # 加载所有模板
        self.templates = self._load_templates()
    
    def _init_default_templates(self):
        """初始化默认模板"""
        default_templates = [
            # 好莱坞电影模板
            {
                "id": "hollywood_movie",
                "name": "好莱坞电影",
                "description": "适用于好莱坞商业电影的高质量翻译模板，注重情感表达和文化本地化",
                "project_type": "movie",
                "icon": "🎭",
                "tags": ["电影", "商业", "好莱坞"],
                "config": {
                    "display_language": "zh-CN",
                    "api": {
                        "model": "claude-3-5-sonnet",
                        "max_workers": 6
                    },
                    "whisper": {
                        "model": "large-v3",
                        "runtime": "local"
                    },
                    "tts_method": "azure_tts",
                    "burn_subtitles": True,
                    "subtitle": {
                        "max_length": 42,
                        "target_multiplier": 1.0
                    },
                    "emotion_analysis_enabled": True,
                    "cultural_adaptation": True,
                    "terminology_strict": True,
                    "quality_threshold": 0.9
                }
            },
            
            # 独立电影模板
            {
                "id": "indie_film",
                "name": "独立电影",
                "description": "适用于独立电影和艺术片，保持原作风格和深层含义",
                "project_type": "movie",
                "icon": "🎨",
                "tags": ["电影", "独立", "艺术"],
                "config": {
                    "display_language": "zh-CN",
                    "api": {
                        "model": "gpt-4.1",
                        "max_workers": 4
                    },
                    "whisper": {
                        "model": "large-v3",
                        "runtime": "local"
                    },
                    "tts_method": "edge_tts",
                    "burn_subtitles": True,
                    "subtitle": {
                        "max_length": 50,
                        "target_multiplier": 1.1
                    },
                    "emotion_analysis_enabled": True,
                    "preserve_style": True,
                    "artistic_translation": True,
                    "quality_threshold": 0.85
                }
            },
            
            # 电视剧模板
            {
                "id": "tv_series",
                "name": "电视剧集",
                "description": "适用于电视剧和网络剧，支持多集批量处理和角色一致性",
                "project_type": "tv_series",
                "icon": "📺",
                "tags": ["电视剧", "剧集", "连续"],
                "config": {
                    "display_language": "zh-CN",
                    "api": {
                        "model": "deepseek-v3",
                        "max_workers": 8
                    },
                    "whisper": {
                        "model": "large-v3",
                        "runtime": "cloud"
                    },
                    "tts_method": "sf_cosyvoice2",
                    "burn_subtitles": True,
                    "subtitle": {
                        "max_length": 45,
                        "target_multiplier": 1.15
                    },
                    "batch_processing": True,
                    "character_consistency": True,
                    "episode_numbering": True,
                    "terminology_shared": True,
                    "quality_threshold": 0.8
                }
            },
            
            # 纪录片模板
            {
                "id": "documentary",
                "name": "纪录片",
                "description": "适用于纪录片翻译，注重准确性和专业术语",
                "project_type": "documentary",
                "icon": "📚",
                "tags": ["纪录片", "教育", "专业"],
                "config": {
                    "display_language": "zh-CN",
                    "api": {
                        "model": "gpt-4.1",
                        "max_workers": 4
                    },
                    "whisper": {
                        "model": "large-v3",
                        "runtime": "local"
                    },
                    "tts_method": "azure_tts",
                    "burn_subtitles": True,
                    "subtitle": {
                        "max_length": 60,
                        "target_multiplier": 1.2
                    },
                    "factual_accuracy": True,
                    "terminology_strict": True,
                    "professional_terms": True,
                    "preserve_narration_style": True,
                    "quality_threshold": 0.95
                }
            },
            
            # 动画片模板
            {
                "id": "animation",
                "name": "动画片",
                "description": "适用于动画电影和动画剧集，适配夸张表达和儿童友好内容",
                "project_type": "animation",
                "icon": "🎪",
                "tags": ["动画", "儿童", "家庭"],
                "config": {
                    "display_language": "zh-CN",
                    "api": {
                        "model": "gemini-2.0-flash",
                        "max_workers": 6
                    },
                    "whisper": {
                        "model": "large-v3",
                        "runtime": "local"
                    },
                    "tts_method": "sf_fish_tts",
                    "burn_subtitles": True,
                    "subtitle": {
                        "max_length": 35,
                        "target_multiplier": 0.9
                    },
                    "child_friendly": True,
                    "exaggerated_expressions": True,
                    "character_voices": True,
                    "family_appropriate": True,
                    "quality_threshold": 0.8
                }
            },
            
            # 广告片模板
            {
                "id": "commercial",
                "name": "广告片",
                "description": "适用于广告和宣传片，注重品牌信息和营销效果",
                "project_type": "commercial",
                "icon": "📢",
                "tags": ["广告", "营销", "品牌"],
                "config": {
                    "display_language": "zh-CN",
                    "api": {
                        "model": "claude-3-5-sonnet",
                        "max_workers": 4
                    },
                    "whisper": {
                        "model": "large-v3-turbo",
                        "runtime": "cloud"
                    },
                    "tts_method": "openai_tts",
                    "burn_subtitles": True,
                    "subtitle": {
                        "max_length": 30,
                        "target_multiplier": 0.8
                    },
                    "brand_consistency": True,
                    "marketing_optimization": True,
                    "call_to_action": True,
                    "quick_turnaround": True,
                    "quality_threshold": 0.85
                }
            },
            
            # 教育内容模板
            {
                "id": "educational",
                "name": "教育内容",
                "description": "适用于在线课程和教育视频，注重知识传达的准确性",
                "project_type": "educational",
                "icon": "🎓",
                "tags": ["教育", "课程", "学习"],
                "config": {
                    "display_language": "zh-CN",
                    "api": {
                        "model": "gpt-4.1",
                        "max_workers": 4
                    },
                    "whisper": {
                        "model": "large-v3",
                        "runtime": "local"
                    },
                    "tts_method": "azure_tts",
                    "burn_subtitles": True,
                    "subtitle": {
                        "max_length": 55,
                        "target_multiplier": 1.3
                    },
                    "educational_terms": True,
                    "clear_pronunciation": True,
                    "knowledge_accuracy": True,
                    "learning_optimization": True,
                    "quality_threshold": 0.92
                }
            }
        ]
        
        # 保存默认模板
        for template_data in default_templates:
            template_file = self.templates_dir / f"{template_data['id']}.json"
            if not template_file.exists():
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, ensure_ascii=False, indent=2)
    
    def _load_templates(self) -> Dict[str, ProjectTemplate]:
        """加载所有模板"""
        templates = {}
        
        for template_file in self.templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                template = ProjectTemplate.from_dict(data)
                templates[template.id] = template
                
            except Exception as e:
                print(f"加载模板失败 {template_file}: {e}")
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """获取指定模板"""
        return self.templates.get(template_id)
    
    def list_templates(self, 
                      project_type: Optional[ProjectType] = None,
                      tags: Optional[List[str]] = None) -> List[ProjectTemplate]:
        """列出模板"""
        templates = list(self.templates.values())
        
        # 按项目类型过滤
        if project_type:
            templates = [t for t in templates if t.project_type == project_type]
        
        # 按标签过滤
        if tags:
            templates = [t for t in templates 
                        if any(tag in t.tags for tag in tags)]
        
        return templates
    
    def create_custom_template(self, 
                             template_id: str,
                             name: str,
                             description: str,
                             project_type: ProjectType,
                             config: Dict,
                             tags: List[str] = None,
                             icon: str = "🎬") -> bool:
        """创建自定义模板"""
        
        if tags is None:
            tags = []
        
        # 检查ID是否已存在
        if template_id in self.templates:
            print(f"模板ID已存在: {template_id}")
            return False
        
        try:
            # 创建模板对象
            template = ProjectTemplate(
                id=template_id,
                name=name,
                description=description,
                project_type=project_type,
                config=config,
                tags=tags,
                icon=icon
            )
            
            # 保存到文件
            template_file = self.templates_dir / f"{template_id}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 添加到内存
            self.templates[template_id] = template
            
            print(f"✅ 自定义模板创建成功: {name}")
            return True
            
        except Exception as e:
            print(f"创建模板失败: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """删除自定义模板（不能删除系统模板）"""
        
        # 系统模板列表
        system_templates = [
            "hollywood_movie", "indie_film", "tv_series", 
            "documentary", "animation", "commercial", "educational"
        ]
        
        if template_id in system_templates:
            print("不能删除系统模板")
            return False
        
        if template_id not in self.templates:
            print("模板不存在")
            return False
        
        try:
            # 删除文件
            template_file = self.templates_dir / f"{template_id}.json"
            if template_file.exists():
                template_file.unlink()
            
            # 从内存中删除
            del self.templates[template_id]
            
            print(f"✅ 模板删除成功: {template_id}")
            return True
            
        except Exception as e:
            print(f"删除模板失败: {e}")
            return False
    
    def get_template_config(self, template_id: str) -> Dict:
        """获取模板配置"""
        template = self.get_template(template_id)
        return template.config if template else {}
    
    def get_templates_by_type(self, project_type: ProjectType) -> List[ProjectTemplate]:
        """按类型获取模板"""
        return [t for t in self.templates.values() if t.project_type == project_type]
    
    def search_templates(self, search_term: str) -> List[ProjectTemplate]:
        """搜索模板"""
        search_term = search_term.lower()
        results = []
        
        for template in self.templates.values():
            # 搜索名称、描述、标签
            search_fields = [
                template.name.lower(),
                template.description.lower(),
                " ".join(template.tags).lower()
            ]
            
            if any(search_term in field for field in search_fields):
                results.append(template)
        
        return results
    
    def get_template_statistics(self) -> Dict:
        """获取模板统计信息"""
        stats = {
            "total_templates": len(self.templates),
            "by_type": {},
            "popular_tags": {}
        }
        
        # 按类型统计
        for template in self.templates.values():
            type_name = template.project_type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            
            # 标签统计
            for tag in template.tags:
                stats["popular_tags"][tag] = stats["popular_tags"].get(tag, 0) + 1
        
        return stats