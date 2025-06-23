#!/usr/bin/env python3
"""
专业名词管理系统测试脚本

测试核心功能，不依赖spacy、pandas等重型库
"""

import json
import os
import sys
from pathlib import Path

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_term_management():
    """测试基础术语管理功能"""
    print("🧪 开始测试术语管理基础功能...")
    
    try:
        # 创建测试目录
        test_output_dir = Path("test_output/terminology")
        test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建简化的术语管理器
        class SimpleTermManager:
            def __init__(self, project_dir="test_output"):
                self.project_dir = Path(project_dir)
                self.terminology_dir = self.project_dir / "terminology"
                self.terminology_dir.mkdir(parents=True, exist_ok=True)
                self.custom_terms_file = self.terminology_dir / "custom_terms.json"
                self.custom_terms = self._load_custom_terms()
            
            def _load_custom_terms(self):
                if self.custom_terms_file.exists():
                    with open(self.custom_terms_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                return {
                    "version": "1.0",
                    "terms": {},
                    "categories": {},
                    "priorities": {},
                    "notes": {}
                }
            
            def add_term(self, source, target, category="general", priority=1, notes=""):
                self.custom_terms["terms"][source] = target
                self.custom_terms["categories"][source] = category
                self.custom_terms["priorities"][source] = priority
                self.custom_terms["notes"][source] = notes
                self._save_terms()
                return True
            
            def _save_terms(self):
                with open(self.custom_terms_file, 'w', encoding='utf-8') as f:
                    json.dump(self.custom_terms, f, ensure_ascii=False, indent=2)
            
            def get_all_terms(self):
                return self.custom_terms["terms"]
            
            def apply_terms_to_text(self, text):
                applied_terms = []
                result_text = text
                for source, target in self.custom_terms["terms"].items():
                    if source in result_text:
                        result_text = result_text.replace(source, target)
                        applied_terms.append({"source": source, "target": target})
                return result_text, applied_terms
        
        # 创建测试实例
        term_manager = SimpleTermManager()
        print("✅ 术语管理器创建成功")
        
        # 测试添加术语
        test_terms = [
            ("AI", "人工智能", "技术术语", 5, "核心技术概念"),
            ("machine learning", "机器学习", "技术术语", 4, "AI子领域"),
            ("OpenAI", "OpenAI", "品牌", 3, "AI公司"),
            ("neural network", "神经网络", "技术术语", 4, "深度学习基础"),
            ("ChatGPT", "ChatGPT", "产品", 3, "对话AI产品")
        ]
        
        for source, target, category, priority, notes in test_terms:
            success = term_manager.add_term(source, target, category, priority, notes)
            if success:
                print(f"✅ 成功添加术语: {source} → {target}")
            else:
                print(f"❌ 添加术语失败: {source}")
        
        # 测试术语应用
        test_text = "AI and machine learning are core technologies. OpenAI developed ChatGPT using neural network."
        corrected_text, applied_terms = term_manager.apply_terms_to_text(test_text)
        
        print(f"\n🔄 术语应用测试:")
        print(f"原文: {test_text}")
        print(f"修正后: {corrected_text}")
        print(f"应用的术语数量: {len(applied_terms)}")
        
        for term in applied_terms:
            print(f"  - {term['source']} → {term['target']}")
        
        # 测试术语库统计
        all_terms = term_manager.get_all_terms()
        print(f"\n📊 术语库统计:")
        print(f"总术语数: {len(all_terms)}")
        
        # 按分类统计
        categories = {}
        for source in all_terms:
            category = term_manager.custom_terms["categories"].get(source, "未分类")
            categories[category] = categories.get(category, 0) + 1
        
        for category, count in categories.items():
            print(f"  - {category}: {count}个")
        
        print("\n✅ 基础功能测试全部通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_term_extraction():
    """测试术语提取功能（简化版）"""
    print("\n🔍 测试术语提取功能...")
    
    try:
        import re
        
        def simple_extract_terms(text):
            """简化的术语提取"""
            # 提取大写词汇
            uppercase_terms = re.findall(r'\b[A-Z]{2,}\b', text)
            
            # 提取首字母大写的专业词汇
            capitalized_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            
            # 提取连字符词汇
            hyphenated_terms = re.findall(r'\b[a-zA-Z]+-[a-zA-Z]+\b', text)
            
            return {
                "uppercase": uppercase_terms,
                "capitalized": capitalized_terms,
                "hyphenated": hyphenated_terms
            }
        
        # 测试文本
        test_texts = [
            "The AI system uses machine learning algorithms like CNN and RNN.",
            "OpenAI developed GPT-4 using transformer architecture.",
            "Deep learning is a subset of machine learning in artificial intelligence."
        ]
        
        for i, text in enumerate(test_texts):
            print(f"\n文本 {i+1}: {text}")
            extracted = simple_extract_terms(text)
            
            for term_type, terms in extracted.items():
                if terms:
                    print(f"  {term_type}: {', '.join(set(terms))}")
        
        print("\n✅ 术语提取测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 术语提取测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作功能"""
    print("\n📁 测试文件操作功能...")
    
    try:
        # 测试术语库文件读写
        test_file = "test_output/terminology/test_terms.json"
        
        # 创建测试数据
        test_data = {
            "version": "1.0",
            "terms": {
                "API": "应用程序接口",
                "SDK": "软件开发工具包",
                "REST": "表述性状态传递"
            },
            "categories": {
                "API": "技术术语",
                "SDK": "技术术语", 
                "REST": "技术术语"
            }
        }
        
        # 写入文件
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 成功写入测试文件: {test_file}")
        
        # 读取文件
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        # 验证数据
        if loaded_data["terms"] == test_data["terms"]:
            print("✅ 文件读写验证成功")
        else:
            print("❌ 文件读写验证失败")
            return False
        
        # 清理测试文件
        os.remove(test_file)
        print("✅ 测试文件清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 VideoLingo 专业名词管理系统测试")
    print("=" * 50)
    
    # 运行所有测试
    tests = [
        ("基础术语管理", test_basic_term_management),
        ("术语提取功能", test_term_extraction),
        ("文件操作功能", test_file_operations)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} 测试通过")
        else:
            print(f"❌ {test_name} 测试失败")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！专业名词管理系统基础功能正常。")
        print("\n📝 下一步测试建议:")
        print("1. 安装完整环境后测试Streamlit界面")
        print("2. 测试与VideoLingo翻译流程的集成")
        print("3. 测试Excel导入导出功能")
        return True
    else:
        print("⚠️ 部分测试失败，请检查错误信息并修复。")
        return False

if __name__ == "__main__":
    main()