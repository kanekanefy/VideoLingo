"""
专业名词库管理器

管理术语库的存储、更新、导入导出等功能
"""

import json
import os
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
# from core.utils import *  # 暂时注释掉，避免循环导入

class TermManager:
    def __init__(self, project_dir: str = "output"):
        self.project_dir = Path(project_dir)
        self.terminology_dir = self.project_dir / "terminology"
        self.terminology_dir.mkdir(parents=True, exist_ok=True)
        
        # 术语库文件路径
        self.custom_terms_file = self.terminology_dir / "custom_terms.json"
        self.auto_terms_file = self.terminology_dir / "auto_extracted_terms.json"
        self.term_history_file = self.terminology_dir / "term_history.json"
        
        # 加载现有术语库
        self.custom_terms = self._load_custom_terms()
        self.auto_terms = self._load_auto_terms()
        self.term_history = self._load_term_history()
    
    def _load_custom_terms(self) -> Dict:
        """加载用户自定义术语库"""
        if self.custom_terms_file.exists():
            try:
                with open(self.custom_terms_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading custom terms: {e}")
        
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "terms": {},  # {source_term: target_term}
            "categories": {},  # {term: category}
            "priorities": {},  # {term: priority_level}
            "notes": {}  # {term: user_notes}
        }
    
    def _load_auto_terms(self) -> Dict:
        """加载自动提取的术语"""
        if self.auto_terms_file.exists():
            try:
                with open(self.auto_terms_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading auto terms: {e}")
        
        return {
            "version": "1.0",
            "extracted_at": datetime.now().isoformat(),
            "suggested_pairs": [],
            "term_frequency": {},
            "important_terms": []
        }
    
    def _load_term_history(self) -> List:
        """加载术语修改历史"""
        if self.term_history_file.exists():
            try:
                with open(self.term_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading term history: {e}")
        
        return []
    
    def save_all(self):
        """保存所有术语数据"""
        self._save_custom_terms()
        self._save_auto_terms()
        self._save_term_history()
    
    def _save_custom_terms(self):
        """保存自定义术语库"""
        self.custom_terms["updated_at"] = datetime.now().isoformat()
        with open(self.custom_terms_file, 'w', encoding='utf-8') as f:
            json.dump(self.custom_terms, f, ensure_ascii=False, indent=2)
    
    def _save_auto_terms(self):
        """保存自动提取术语"""
        with open(self.auto_terms_file, 'w', encoding='utf-8') as f:
            json.dump(self.auto_terms, f, ensure_ascii=False, indent=2)
    
    def _save_term_history(self):
        """保存术语历史"""
        with open(self.term_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.term_history, f, ensure_ascii=False, indent=2)
    
    def add_term(self, source_term: str, target_term: str, 
                 category: str = "general", priority: int = 1, notes: str = "") -> bool:
        """添加术语对"""
        try:
            # 记录历史
            self._add_to_history("add", source_term, target_term, category, priority, notes)
            
            # 添加到术语库
            self.custom_terms["terms"][source_term] = target_term
            if category:
                self.custom_terms["categories"][source_term] = category
            if priority != 1:
                self.custom_terms["priorities"][source_term] = priority
            if notes:
                self.custom_terms["notes"][source_term] = notes
            
            self._save_custom_terms()
            return True
        except Exception as e:
            print(f"Error adding term: {e}")
            return False
    
    def update_term(self, source_term: str, target_term: str = None, 
                   category: str = None, priority: int = None, notes: str = None) -> bool:
        """更新术语"""
        if source_term not in self.custom_terms["terms"]:
            return False
        
        try:
            old_data = {
                "target": self.custom_terms["terms"].get(source_term),
                "category": self.custom_terms["categories"].get(source_term, "general"),
                "priority": self.custom_terms["priorities"].get(source_term, 1),
                "notes": self.custom_terms["notes"].get(source_term, "")
            }
            
            # 更新数据
            if target_term is not None:
                self.custom_terms["terms"][source_term] = target_term
            if category is not None:
                self.custom_terms["categories"][source_term] = category
            if priority is not None:
                self.custom_terms["priorities"][source_term] = priority
            if notes is not None:
                self.custom_terms["notes"][source_term] = notes
            
            # 记录历史
            self._add_to_history("update", source_term, 
                               target_term or old_data["target"],
                               category or old_data["category"],
                               priority or old_data["priority"],
                               notes or old_data["notes"])
            
            self._save_custom_terms()
            return True
        except Exception as e:
            print(f"Error updating term: {e}")
            return False
    
    def delete_term(self, source_term: str) -> bool:
        """删除术语"""
        if source_term not in self.custom_terms["terms"]:
            return False
        
        try:
            # 记录历史
            self._add_to_history("delete", source_term, 
                               self.custom_terms["terms"][source_term])
            
            # 删除术语
            del self.custom_terms["terms"][source_term]
            self.custom_terms["categories"].pop(source_term, None)
            self.custom_terms["priorities"].pop(source_term, None)
            self.custom_terms["notes"].pop(source_term, None)
            
            self._save_custom_terms()
            return True
        except Exception as e:
            print(f"Error deleting term: {e}")
            return False
    
    def _add_to_history(self, action: str, source_term: str, target_term: str = "",
                       category: str = "", priority: int = 1, notes: str = ""):
        """添加历史记录"""
        self.term_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "source_term": source_term,
            "target_term": target_term,
            "category": category,
            "priority": priority,
            "notes": notes
        })
        
        # 只保留最近100条历史记录
        if len(self.term_history) > 100:
            self.term_history = self.term_history[-100:]
    
    def get_term_translation(self, source_term: str) -> Optional[str]:
        """获取术语翻译"""
        return self.custom_terms["terms"].get(source_term)
    
    def get_all_terms(self) -> Dict:
        """获取所有术语"""
        return self.custom_terms["terms"].copy()
    
    def get_terms_by_category(self, category: str) -> Dict:
        """按类别获取术语"""
        result = {}
        for term, translation in self.custom_terms["terms"].items():
            if self.custom_terms["categories"].get(term) == category:
                result[term] = translation
        return result
    
    def get_categories(self) -> List[str]:
        """获取所有类别"""
        return list(set(self.custom_terms["categories"].values()))
    
    def update_auto_extracted_terms(self, extraction_result: Dict):
        """更新自动提取的术语"""
        self.auto_terms = {
            "version": "1.0",
            "extracted_at": datetime.now().isoformat(),
            "suggested_pairs": extraction_result.get("suggested_pairs", []),
            "term_frequency": extraction_result.get("term_frequency", {}),
            "important_terms": extraction_result.get("important_terms", [])
        }
        self._save_auto_terms()
    
    def get_suggested_terms(self) -> List[Dict]:
        """获取建议的术语对"""
        return self.auto_terms.get("suggested_pairs", [])
    
    def import_from_excel(self, file_path: str) -> bool:
        """从Excel导入术语"""
        try:
            df = pd.read_excel(file_path)
            
            # 期望的列：source_term, target_term, category, priority, notes
            required_cols = ['source_term', 'target_term']
            if not all(col in df.columns for col in required_cols):
                print("Excel文件必须包含 'source_term' 和 'target_term' 列")
                return False
            
            for _, row in df.iterrows():
                source = str(row['source_term']).strip()
                target = str(row['target_term']).strip()
                
                if source and target:
                    category = str(row.get('category', 'imported')).strip()
                    priority = int(row.get('priority', 1))
                    notes = str(row.get('notes', '')).strip()
                    
                    self.add_term(source, target, category, priority, notes)
            
            return True
        except Exception as e:
            print(f"导入Excel失败: {e}")
            return False
    
    def export_to_excel(self, file_path: str) -> bool:
        """导出术语到Excel"""
        try:
            data = []
            for source, target in self.custom_terms["terms"].items():
                data.append({
                    'source_term': source,
                    'target_term': target,
                    'category': self.custom_terms["categories"].get(source, 'general'),
                    'priority': self.custom_terms["priorities"].get(source, 1),
                    'notes': self.custom_terms["notes"].get(source, '')
                })
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            return True
        except Exception as e:
            print(f"导出Excel失败: {e}")
            return False
    
    def apply_terms_to_text(self, text: str) -> Tuple[str, List[Dict]]:
        """将术语应用到文本中"""
        applied_terms = []
        result_text = text
        
        # 按照优先级排序术语（高优先级优先替换）
        sorted_terms = sorted(
            self.custom_terms["terms"].items(),
            key=lambda x: self.custom_terms["priorities"].get(x[0], 1),
            reverse=True
        )
        
        for source_term, target_term in sorted_terms:
            if source_term in result_text:
                # 使用正则表达式进行精确匹配（避免部分词匹配）
                import re
                pattern = r'\\b' + re.escape(source_term) + r'\\b'
                matches = re.findall(pattern, result_text, re.IGNORECASE)
                
                if matches:
                    result_text = re.sub(pattern, target_term, result_text, flags=re.IGNORECASE)
                    applied_terms.append({
                        "source": source_term,
                        "target": target_term,
                        "count": len(matches),
                        "category": self.custom_terms["categories"].get(source_term, "general")
                    })
        
        return result_text, applied_terms
    
    def get_statistics(self) -> Dict:
        """获取术语库统计信息"""
        categories = {}
        for term in self.custom_terms["terms"]:
            category = self.custom_terms["categories"].get(term, "general")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_terms": len(self.custom_terms["terms"]),
            "categories": categories,
            "last_updated": self.custom_terms.get("updated_at", ""),
            "suggested_terms_count": len(self.auto_terms.get("suggested_pairs", [])),
            "recent_changes": len([h for h in self.term_history 
                                 if (datetime.now() - datetime.fromisoformat(h["timestamp"])).days < 7])
        }