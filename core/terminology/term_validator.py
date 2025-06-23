"""
术语一致性验证器

检查翻译文本中的术语一致性，标识不一致的术语使用
"""

import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from .term_manager import TermManager

class TermValidator:
    def __init__(self, term_manager: TermManager):
        self.term_manager = term_manager
        
    def validate_terminology_consistency(self, text_chunks: List[str]) -> Dict:
        """验证多个文本块中的术语一致性"""
        all_terms = self.term_manager.get_all_terms()
        
        # 统计每个术语在文本中的使用情况
        term_usage = defaultdict(list)  # {source_term: [used_translations]}
        term_positions = defaultdict(list)  # {source_term: [(chunk_index, position)]}
        
        for chunk_idx, chunk in enumerate(text_chunks):
            if not chunk:
                continue
                
            for source_term, expected_translation in all_terms.items():
                # 查找源术语的使用
                source_pattern = r'\\b' + re.escape(source_term) + r'\\b'
                source_matches = list(re.finditer(source_pattern, chunk, re.IGNORECASE))
                
                for match in source_matches:
                    term_positions[source_term].append((chunk_idx, match.start()))
                
                # 查找目标术语的使用
                target_pattern = r'\\b' + re.escape(expected_translation) + r'\\b'
                target_matches = list(re.finditer(target_pattern, chunk, re.IGNORECASE))
                
                for match in target_matches:
                    term_usage[source_term].append({
                        "translation": expected_translation,
                        "chunk_index": chunk_idx,
                        "position": match.start(),
                        "is_correct": True
                    })
        
        # 检查不一致的使用
        inconsistencies = []
        for source_term, usage_list in term_usage.items():
            if len(set(item["translation"] for item in usage_list)) > 1:
                inconsistencies.append({
                    "term": source_term,
                    "expected": all_terms[source_term],
                    "found_translations": list(set(item["translation"] for item in usage_list)),
                    "usage_count": len(usage_list),
                    "positions": [(item["chunk_index"], item["position"]) for item in usage_list]
                })
        
        return {
            "inconsistencies": inconsistencies,
            "term_usage_stats": dict(term_usage),
            "total_terms_checked": len(all_terms),
            "terms_with_issues": len(inconsistencies)
        }
    
    def check_missing_terms(self, source_chunks: List[str], target_chunks: List[str]) -> Dict:
        """检查翻译中遗漏的术语"""
        all_terms = self.term_manager.get_all_terms()
        missing_terms = []
        
        for chunk_idx, (source_chunk, target_chunk) in enumerate(zip(source_chunks, target_chunks)):
            if not source_chunk or not target_chunk:
                continue
                
            for source_term, expected_translation in all_terms.items():
                # 检查源文本中是否包含术语
                source_pattern = r'\\b' + re.escape(source_term) + r'\\b'
                if re.search(source_pattern, source_chunk, re.IGNORECASE):
                    # 检查目标文本中是否有对应翻译
                    target_pattern = r'\\b' + re.escape(expected_translation) + r'\\b'
                    if not re.search(target_pattern, target_chunk, re.IGNORECASE):
                        missing_terms.append({
                            "source_term": source_term,
                            "expected_translation": expected_translation,
                            "chunk_index": chunk_idx,
                            "source_text": source_chunk[:100] + "..." if len(source_chunk) > 100 else source_chunk,
                            "target_text": target_chunk[:100] + "..." if len(target_chunk) > 100 else target_chunk
                        })
        
        return {
            "missing_terms": missing_terms,
            "total_missing": len(missing_terms)
        }
    
    def suggest_term_corrections(self, text: str) -> List[Dict]:
        """建议术语修正"""
        all_terms = self.term_manager.get_all_terms()
        suggestions = []
        
        for source_term, correct_translation in all_terms.items():
            # 查找可能的错误使用
            source_pattern = r'\\b' + re.escape(source_term) + r'\\b'
            matches = list(re.finditer(source_pattern, text, re.IGNORECASE))
            
            for match in matches:
                # 检查附近是否有错误的翻译
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end]
                
                # 如果上下文中没有正确的翻译，建议添加
                target_pattern = r'\\b' + re.escape(correct_translation) + r'\\b'
                if not re.search(target_pattern, context, re.IGNORECASE):
                    suggestions.append({
                        "source_term": source_term,
                        "suggested_translation": correct_translation,
                        "position": match.start(),
                        "context": context,
                        "confidence": 0.8
                    })
        
        return suggestions
    
    def get_term_coverage_report(self, source_chunks: List[str], target_chunks: List[str]) -> Dict:
        """生成术语覆盖率报告"""
        all_terms = self.term_manager.get_all_terms()
        
        # 统计术语使用情况
        used_terms = set()
        unused_terms = set()
        correct_usage = 0
        total_usage = 0
        
        for source_chunk, target_chunk in zip(source_chunks, target_chunks):
            if not source_chunk or not target_chunk:
                continue
                
            for source_term, expected_translation in all_terms.items():
                source_pattern = r'\\b' + re.escape(source_term) + r'\\b'
                target_pattern = r'\\b' + re.escape(expected_translation) + r'\\b'
                
                source_found = bool(re.search(source_pattern, source_chunk, re.IGNORECASE))
                target_found = bool(re.search(target_pattern, target_chunk, re.IGNORECASE))
                
                if source_found:
                    used_terms.add(source_term)
                    total_usage += 1
                    if target_found:
                        correct_usage += 1
        
        unused_terms = set(all_terms.keys()) - used_terms
        
        coverage_rate = len(used_terms) / len(all_terms) if all_terms else 0
        accuracy_rate = correct_usage / total_usage if total_usage > 0 else 0
        
        return {
            "total_terms_in_library": len(all_terms),
            "used_terms": len(used_terms),
            "unused_terms": len(unused_terms),
            "coverage_rate": coverage_rate,
            "accuracy_rate": accuracy_rate,
            "used_terms_list": list(used_terms),
            "unused_terms_list": list(unused_terms)
        }


def validate_terminology_consistency(text_chunks: List[str], 
                                   term_manager: TermManager = None) -> Dict:
    """验证术语一致性的便捷函数"""
    if term_manager is None:
        term_manager = TermManager()
    
    validator = TermValidator(term_manager)
    return validator.validate_terminology_consistency(text_chunks)