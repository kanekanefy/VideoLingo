"""
专业名词提取器

从原文和翻译文本中自动提取专业术语、人名、地名、品牌名等
"""

import re
import json
from typing import List, Dict, Set, Tuple
from collections import Counter
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("Warning: spacy not available, some terminology extraction features will be limited")

# from core.utils import *  # 暂时注释掉，避免循环导入

class TermExtractor:
    def __init__(self):
        self.nlp_en = None
        self.nlp_zh = None
        self._load_models()
        
    def _load_models(self):
        """加载NLP模型"""
        if not SPACY_AVAILABLE:
            return
            
        try:
            self.nlp_en = spacy.load("en_core_web_md")
        except (OSError, AttributeError):
            print("Warning: English spaCy model not found. Some features may be limited.")
            
        try:
            self.nlp_zh = spacy.load("zh_core_web_md")
        except (OSError, AttributeError):
            print("Warning: Chinese spaCy model not found. Some features may be limited.")
    
    def extract_named_entities(self, text: str, language: str = "en") -> List[Dict]:
        """提取命名实体（人名、地名、组织名等）"""
        nlp = self.nlp_en if language == "en" else self.nlp_zh
        if not nlp:
            return []
            
        doc = nlp(text)
        entities = []
        
        for ent in doc.ents:
            # 过滤有用的实体类型
            if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART"]:
                entities.append({
                    "text": ent.text.strip(),
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        
        return entities
    
    def extract_technical_terms(self, text: str, min_length: int = 3) -> List[str]:
        """提取技术术语（大写词、复合词等）"""
        terms = []
        
        # 1. 提取全大写的词（可能是缩写或技术术语）
        uppercase_pattern = r'\b[A-Z]{2,}\b'
        uppercase_terms = re.findall(uppercase_pattern, text)
        terms.extend(uppercase_terms)
        
        # 2. 提取首字母大写的专业词汇
        capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        capitalized_terms = re.findall(capitalized_pattern, text)
        # 过滤掉句首词
        filtered_caps = [term for term in capitalized_terms 
                        if not re.match(r'^[A-Z][a-z]+\s', text) or term != capitalized_terms[0]]
        terms.extend(filtered_caps)
        
        # 3. 提取连字符词汇
        hyphenated_pattern = r'\b[a-zA-Z]+-[a-zA-Z]+(?:-[a-zA-Z]+)*\b'
        hyphenated_terms = re.findall(hyphenated_pattern, text)
        terms.extend(hyphenated_terms)
        
        # 4. 提取数字+单位的组合
        unit_pattern = r'\b\d+(?:\.\d+)?\s*[a-zA-Z]{1,4}\b'
        unit_terms = re.findall(unit_pattern, text)
        terms.extend(unit_terms)
        
        # 去重并过滤长度
        unique_terms = list(set([term.strip() for term in terms if len(term.strip()) >= min_length]))
        
        return unique_terms
    
    def extract_terms_from_pair(self, source_text: str, target_text: str, 
                               source_lang: str = "en", target_lang: str = "zh") -> Dict:
        """从源文本和目标文本对中提取术语"""
        result = {
            "source_entities": self.extract_named_entities(source_text, source_lang),
            "target_entities": self.extract_named_entities(target_text, target_lang),
            "source_technical": self.extract_technical_terms(source_text),
            "target_technical": self.extract_technical_terms(target_text),
            "potential_pairs": []
        }
        
        # 尝试匹配可能的术语对
        source_terms = [ent["text"] for ent in result["source_entities"]] + result["source_technical"]
        target_terms = [ent["text"] for ent in result["target_entities"]] + result["target_technical"]
        
        # 简单的位置匹配（基于在文本中的相对位置）
        for i, s_term in enumerate(source_terms):
            for j, t_term in enumerate(target_terms):
                # 如果术语在各自文本中的相对位置接近，可能是对应的
                if abs(i / len(source_terms) - j / len(target_terms)) < 0.3:
                    result["potential_pairs"].append({
                        "source": s_term,
                        "target": t_term,
                        "confidence": 1 - abs(i / len(source_terms) - j / len(target_terms))
                    })
        
        return result

def extract_terms(text: str, language: str = "en") -> Dict:
    """从单个文本中提取术语"""
    extractor = TermExtractor()
    entities = extractor.extract_named_entities(text, language)
    technical = extractor.extract_technical_terms(text)
    
    return {
        "entities": entities,
        "technical_terms": technical,
        "all_terms": [ent["text"] for ent in entities] + technical
    }

def extract_terms_from_translation(source_chunks: List[str], target_chunks: List[str],
                                 source_lang: str = "en", target_lang: str = "zh") -> Dict:
    """从翻译对中批量提取术语"""
    extractor = TermExtractor()
    all_results = []
    term_frequency = Counter()
    
    for source, target in zip(source_chunks, target_chunks):
        if source and target:
            pair_result = extractor.extract_terms_from_pair(source, target, source_lang, target_lang)
            all_results.append(pair_result)
            
            # 统计术语频率
            for term in pair_result["source_technical"]:
                term_frequency[term] += 1
            for ent in pair_result["source_entities"]:
                term_frequency[ent["text"]] += 1
    
    # 提取高频术语作为重要术语
    important_terms = [term for term, freq in term_frequency.most_common(20) if freq > 1]
    
    return {
        "results": all_results,
        "term_frequency": dict(term_frequency),
        "important_terms": important_terms,
        "suggested_pairs": _extract_suggested_pairs(all_results)
    }

def _extract_suggested_pairs(all_results: List[Dict]) -> List[Dict]:
    """从所有结果中提取建议的术语对"""
    pair_counts = Counter()
    
    for result in all_results:
        for pair in result["potential_pairs"]:
            key = (pair["source"], pair["target"])
            pair_counts[key] += pair["confidence"]
    
    # 返回置信度最高的术语对
    suggested = []
    for (source, target), score in pair_counts.most_common(50):
        if score > 0.5:  # 只返回置信度较高的
            suggested.append({
                "source": source,
                "target": target,
                "confidence": score,
                "frequency": len([r for r in all_results 
                               if any(p["source"] == source and p["target"] == target 
                                     for p in r["potential_pairs"])])
            })
    
    return suggested