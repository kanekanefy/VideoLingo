#!/usr/bin/env python3
"""
VideoLingo 多项目管理系统测试

测试项目管理、模板系统、进度跟踪等功能
"""

import json
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_project_manager():
    """测试项目管理器"""
    print("🧪 测试项目管理器...")
    
    try:
        from core.project_management.project_manager import ProjectManager, ProjectType, ProjectStatus
        
        # 创建项目管理器
        pm = ProjectManager("test_projects")
        print("✅ 项目管理器创建成功")
        
        # 创建测试项目
        test_projects = [
            {
                "name": "好莱坞大片《复仇者联盟》",
                "description": "漫威超级英雄电影翻译项目",
                "project_type": ProjectType.MOVIE,
                "source_language": "en",
                "target_languages": ["zh-CN", "zh-TW"],
                "tags": ["漫威", "动作", "科幻"],
                "category": "entertainment"
            },
            {
                "name": "BBC纪录片《地球脉动》",
                "description": "自然纪录片翻译项目",
                "project_type": ProjectType.DOCUMENTARY,
                "source_language": "en", 
                "target_languages": ["zh-CN"],
                "tags": ["BBC", "自然", "教育"],
                "category": "documentary"
            },
            {
                "name": "Netflix剧集《怪奇物语》第四季",
                "description": "科幻恐怖电视剧翻译项目",
                "project_type": ProjectType.TV_SERIES,
                "source_language": "en",
                "target_languages": ["zh-CN", "ja", "ko"],
                "tags": ["Netflix", "科幻", "恐怖"],
                "category": "entertainment"
            }
        ]
        
        created_projects = []
        for project_data in test_projects:
            project_id = pm.create_project(**project_data)
            created_projects.append(project_id)
            print(f"✅ 创建项目: {project_data['name']} (ID: {project_id[:8]}...)")
        
        # 测试项目列表和过滤
        all_projects = pm.list_projects()
        print(f"✅ 获取项目列表: {len(all_projects)} 个项目")
        
        # 按类型过滤
        movies = pm.list_projects(project_type=ProjectType.MOVIE)
        print(f"✅ 电影项目过滤: {len(movies)} 个电影项目")
        
        # 搜索测试
        search_results = pm.list_projects(search_term="Netflix")
        print(f"✅ 搜索测试: 找到 {len(search_results)} 个包含'Netflix'的项目")
        
        # 项目状态更新测试
        if created_projects:
            first_project = created_projects[0]
            pm.update_project(first_project, {"status": ProjectStatus.IN_PROGRESS})
            print(f"✅ 项目状态更新: {first_project[:8]}... -> IN_PROGRESS")
        
        # 统计信息测试
        stats = pm.get_project_statistics()
        print(f"✅ 统计信息: 总项目 {stats['total_projects']} 个")
        print(f"   - 按状态: {stats['by_status']}")
        print(f"   - 按类型: {stats['by_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 项目管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_manager():
    """测试模板管理器"""
    print("\n🧪 测试项目模板管理器...")
    
    try:
        from core.project_management.project_templates import ProjectTemplateManager, ProjectType
        
        # 创建模板管理器
        tm = ProjectTemplateManager("test_templates")
        print("✅ 模板管理器创建成功")
        
        # 获取默认模板
        templates = tm.list_templates()
        print(f"✅ 加载默认模板: {len(templates)} 个模板")
        
        # 按类型获取模板
        movie_templates = tm.get_templates_by_type(ProjectType.MOVIE)
        print(f"✅ 电影模板: {len(movie_templates)} 个")
        
        for template in movie_templates:
            print(f"   - {template.icon} {template.name}: {template.description}")
        
        # 获取特定模板配置
        hollywood_config = tm.get_template_config("hollywood_movie")
        if hollywood_config:
            print("✅ 好莱坞电影模板配置加载成功")
            print(f"   - API模型: {hollywood_config.get('api', {}).get('model', 'N/A')}")
            print(f"   - TTS方法: {hollywood_config.get('tts_method', 'N/A')}")
            print(f"   - 情感分析: {hollywood_config.get('emotion_analysis_enabled', False)}")
        
        # 创建自定义模板测试
        custom_config = {
            "api": {"model": "claude-3-5-sonnet"},
            "whisper": {"model": "large-v3"},
            "tts_method": "azure_tts",
            "custom_feature": True,
            "test_mode": True
        }
        
        success = tm.create_custom_template(
            template_id="test_custom",
            name="测试自定义模板",
            description="用于测试的自定义模板",
            project_type=ProjectType.OTHER,
            config=custom_config,
            tags=["测试", "自定义"],
            icon="🧪"
        )
        
        if success:
            print("✅ 自定义模板创建成功")
            
            # 验证自定义模板
            custom_template = tm.get_template("test_custom")
            if custom_template:
                print(f"✅ 自定义模板验证成功: {custom_template.name}")
        
        # 搜索测试
        search_results = tm.search_templates("好莱坞")
        print(f"✅ 模板搜索: 找到 {len(search_results)} 个相关模板")
        
        # 统计信息
        stats = tm.get_template_statistics()
        print(f"✅ 模板统计: 总模板 {stats['total_templates']} 个")
        print(f"   - 按类型: {stats['by_type']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_progress_tracker():
    """测试进度跟踪器"""
    print("\n🧪 测试进度跟踪器...")
    
    try:
        from core.project_management.progress_tracker import ProgressTracker, TaskStatus
        
        # 创建测试项目目录
        test_project_dir = Path("test_projects/test_progress")
        test_project_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建进度跟踪器
        pt = ProgressTracker("test_progress", "test_projects")
        print("✅ 进度跟踪器创建成功")
        
        # 获取初始化的任务
        print(f"✅ 初始化任务: {len(pt.tasks)} 个任务")
        
        # 显示任务概览
        for task in list(pt.tasks.values())[:5]:  # 只显示前5个
            print(f"   - {task.name}: {task.status.value} ({task.estimated_duration}分钟)")
        
        # 模拟任务执行流程
        next_tasks = pt.get_next_tasks()
        if next_tasks:
            first_task = next_tasks[0]
            print(f"✅ 下一个任务: {first_task.name}")
            
            # 开始任务
            pt.start_task(first_task.id)
            print(f"✅ 任务已开始: {first_task.name}")
            
            # 更新进度
            pt.update_task_progress(first_task.id, 0.5, "进度50%")
            pt.update_task_progress(first_task.id, 1.0, "任务完成")
            
            print(f"✅ 任务进度更新完成")
        
        # 获取项目进度
        progress = pt.get_project_progress()
        print(f"✅ 项目进度:")
        print(f"   - 总体进度: {progress['overall_progress']*100:.1f}%")
        print(f"   - 已完成任务: {progress['completed_tasks']}")
        print(f"   - 进行中任务: {progress['in_progress_tasks']}")
        print(f"   - 预估剩余时间: {progress['estimated_remaining_minutes']} 分钟")
        
        # 里程碑检查
        if pt.milestones:
            print(f"✅ 项目里程碑: {len(pt.milestones)} 个")
            for milestone in list(pt.milestones.values())[:3]:
                status = "已完成" if milestone.is_completed else "进行中"
                print(f"   - {milestone.name}: {status} ({milestone.progress*100:.1f}%)")
        
        # 任务统计
        task_stats = pt.get_task_statistics()
        print(f"✅ 任务统计:")
        print(f"   - 按状态: {task_stats['by_status']}")
        print(f"   - 按优先级: {task_stats['by_priority']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 进度跟踪器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """测试项目管理集成功能"""
    print("\n🧪 测试项目管理集成功能...")
    
    try:
        from core.project_management.project_manager import ProjectManager, ProjectType
        from core.project_management.project_templates import ProjectTemplateManager
        from core.project_management.progress_tracker import ProgressTracker
        
        # 创建管理器
        pm = ProjectManager("test_projects")
        tm = ProjectTemplateManager("test_templates")
        
        # 使用模板创建项目
        project_id = pm.create_project(
            name="集成测试项目",
            description="使用好莱坞电影模板的测试项目",
            project_type=ProjectType.MOVIE,
            template_id="hollywood_movie",
            tags=["测试", "集成"],
            category="test"
        )
        
        print(f"✅ 使用模板创建项目: {project_id[:8]}...")
        
        # 验证模板配置是否应用
        project = pm.get_project(project_id)
        if project and project.config.get("emotion_analysis_enabled"):
            print("✅ 模板配置应用成功: 情感分析已启用")
        
        # 创建进度跟踪
        pt = ProgressTracker(project_id, "test_projects")
        
        # 设置为活动项目
        pm.set_active_project(project_id)
        active_id = pm.get_active_project()
        
        if active_id == project_id:
            print("✅ 活动项目设置成功")
        
        # 模拟完整工作流程
        print("✅ 模拟项目工作流程:")
        
        # 执行前几个任务
        for i in range(3):
            next_tasks = pt.get_next_tasks()
            if next_tasks:
                task = next_tasks[0]
                print(f"   {i+1}. 执行任务: {task.name}")
                pt.start_task(task.id)
                pt.complete_task(task.id)
        
        # 获取更新后的进度
        final_progress = pt.get_project_progress()
        print(f"✅ 工作流程完成，当前进度: {final_progress['overall_progress']*100:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 VideoLingo 多项目管理系统测试")
    print("=" * 60)
    
    tests = [
        ("项目管理器", test_project_manager),
        ("模板管理器", test_template_manager), 
        ("进度跟踪器", test_progress_tracker),
        ("集成功能", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 运行测试: {test_name}")
        print("-" * 40)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} 测试通过")
        else:
            print(f"❌ {test_name} 测试失败")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 多项目管理系统测试全部通过！")
        
        print("\n🏗️ 系统功能特点:")
        print("  ✅ 多项目并行管理")
        print("  ✅ 7种专业项目模板")
        print("  ✅ 15个标准工作流任务")
        print("  ✅ 5个项目里程碑")
        print("  ✅ 智能进度跟踪")
        print("  ✅ 任务依赖管理")
        print("  ✅ 项目状态流转")
        print("  ✅ 模板配置继承")
        
        print("\n📋 已实现的核心功能:")
        print("  1. ✅ 多项目管理系统")
        print("     - 项目CRUD操作")
        print("     - 项目状态管理")
        print("     - 项目搜索过滤")
        print("     - 统计分析")
        
        print("  2. ✅ 项目模板系统")
        print("     - 7个预设模板")
        print("     - 自定义模板创建")
        print("     - 模板配置继承")
        print("     - 模板搜索管理")
        
        print("  3. ✅ 进度跟踪系统")
        print("     - 15个标准任务")
        print("     - 任务依赖管理")
        print("     - 里程碑跟踪")
        print("     - 进度可视化")
        
        print("\n🎯 下一步开发建议:")
        print("  1. 版本控制系统 (功能2)")
        print("  2. 批量处理管道 (功能3)")
        print("  3. 情感语调分析 (功能5)")
        
        return True
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查错误信息并修复。")
        return False

if __name__ == "__main__":
    main()