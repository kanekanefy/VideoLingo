"""
项目仪表板UI

为Streamlit提供项目管理的用户界面组件
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .project_manager import ProjectManager, ProjectStatus, ProjectType
from .project_templates import ProjectTemplateManager
from .progress_tracker import ProgressTracker, TaskStatus, TaskPriority

def create_project_dashboard():
    """创建项目管理仪表板"""
    
    st.title("🎬 VideoLingo 项目管理")
    
    # 初始化管理器
    if 'project_manager' not in st.session_state:
        st.session_state.project_manager = ProjectManager()
    if 'template_manager' not in st.session_state:
        st.session_state.template_manager = ProjectTemplateManager()
    
    project_manager = st.session_state.project_manager
    template_manager = st.session_state.template_manager
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 项目概览", "➕ 创建项目", "📁 项目列表", "📈 项目详情", "⚙️ 模板管理"
    ])
    
    with tab1:
        _project_overview(project_manager)
    
    with tab2:
        _create_project_interface(project_manager, template_manager)
    
    with tab3:
        _project_list_interface(project_manager)
    
    with tab4:
        _project_details_interface(project_manager)
    
    with tab5:
        _template_management_interface(template_manager)

def _project_overview(project_manager: ProjectManager):
    """项目概览界面"""
    st.header("项目概览")
    
    # 获取统计数据
    stats = project_manager.get_project_statistics()
    
    # 显示关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总项目数", stats["total_projects"])
    
    with col2:
        in_progress = stats["by_status"].get("in_progress", 0)
        st.metric("进行中", in_progress)
    
    with col3:
        completed = stats["by_status"].get("completed", 0)
        st.metric("已完成", completed)
    
    with col4:
        if stats["total_projects"] > 0:
            completion_rate = completed / stats["total_projects"] * 100
            st.metric("完成率", f"{completion_rate:.1f}%")
        else:
            st.metric("完成率", "0%")
    
    # 项目状态分布图表
    if stats["by_status"]:
        st.subheader("项目状态分布")
        
        # 创建饼图数据
        status_labels = []
        status_values = []
        status_colors = {
            "created": "#FFA500",
            "in_progress": "#1E90FF", 
            "translating": "#32CD32",
            "reviewing": "#FFD700",
            "completed": "#228B22",
            "archived": "#808080",
            "paused": "#DC143C"
        }
        
        for status, count in stats["by_status"].items():
            status_labels.append(status)
            status_values.append(count)
        
        fig = px.pie(
            values=status_values,
            names=status_labels,
            title="项目状态分布",
            color_discrete_map=status_colors
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 项目类型分布
    if stats["by_type"]:
        st.subheader("项目类型分布")
        
        type_df = pd.DataFrame(
            list(stats["by_type"].items()),
            columns=["类型", "数量"]
        )
        
        fig = px.bar(
            type_df,
            x="类型",
            y="数量",
            title="项目类型分布",
            color="数量",
            color_continuous_scale="viridis"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 最近活动
    if stats["recent_activity"]:
        st.subheader("最近活动")
        
        for activity in stats["recent_activity"]:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 2])
                
                with col1:
                    st.write(f"**{activity['name']}**")
                
                with col2:
                    status_colors = {
                        "created": "🆕",
                        "in_progress": "🔄",
                        "translating": "🔤",
                        "reviewing": "👀",
                        "completed": "✅",
                        "archived": "📦",
                        "paused": "⏸️"
                    }
                    st.write(f"{status_colors.get(activity['status'], '❓')} {activity['status']}")
                
                with col3:
                    updated_time = datetime.fromisoformat(activity['updated_at'])
                    time_diff = datetime.now() - updated_time
                    
                    if time_diff.days > 0:
                        st.write(f"{time_diff.days} 天前")
                    elif time_diff.seconds > 3600:
                        hours = time_diff.seconds // 3600
                        st.write(f"{hours} 小时前")
                    else:
                        minutes = time_diff.seconds // 60
                        st.write(f"{minutes} 分钟前")

def _create_project_interface(project_manager: ProjectManager, template_manager: ProjectTemplateManager):
    """创建项目界面"""
    st.header("创建新项目")
    
    with st.form("create_project_form"):
        # 基本信息
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("项目名称", placeholder="输入项目名称")
            source_language = st.selectbox(
                "源语言",
                ["en", "zh", "ja", "ko", "fr", "de", "es", "ru"],
                index=0
            )
            
        with col2:
            project_type = st.selectbox(
                "项目类型",
                options=[t.value for t in ProjectType],
                format_func=lambda x: {
                    "movie": "电影",
                    "tv_series": "电视剧",
                    "documentary": "纪录片", 
                    "animation": "动画",
                    "commercial": "广告",
                    "educational": "教育",
                    "other": "其他"
                }.get(x, x)
            )
            
            target_languages = st.multiselect(
                "目标语言",
                ["zh-CN", "zh-TW", "ja", "ko", "en", "fr", "de", "es"],
                default=["zh-CN"]
            )
        
        # 项目描述
        description = st.text_area("项目描述", placeholder="描述项目的内容和要求")
        
        # 模板选择
        st.subheader("选择项目模板")
        
        # 获取适合的模板
        project_type_enum = ProjectType(project_type)
        available_templates = template_manager.get_templates_by_type(project_type_enum)
        
        if available_templates:
            template_options = {"无模板": None}
            for template in available_templates:
                template_options[f"{template.icon} {template.name}"] = template.id
            
            selected_template_key = st.selectbox(
                "项目模板",
                options=list(template_options.keys())
            )
            selected_template = template_options[selected_template_key]
            
            # 显示模板描述
            if selected_template:
                template = template_manager.get_template(selected_template)
                if template:
                    st.info(f"📝 {template.description}")
        else:
            selected_template = None
            st.info("该项目类型暂无可用模板")
        
        # 标签和分类
        col1, col2 = st.columns(2)
        with col1:
            tags = st.text_input("标签", placeholder="用逗号分隔多个标签").split(",")
            tags = [tag.strip() for tag in tags if tag.strip()]
        
        with col2:
            category = st.selectbox(
                "分类",
                ["general", "commercial", "entertainment", "education", "documentary"]
            )
        
        # 提交按钮
        submit_button = st.form_submit_button("创建项目", type="primary")
        
        if submit_button:
            if not project_name:
                st.error("请输入项目名称")
            else:
                try:
                    project_id = project_manager.create_project(
                        name=project_name,
                        description=description,
                        project_type=project_type_enum,
                        source_language=source_language,
                        target_languages=target_languages,
                        tags=tags,
                        category=category,
                        template_id=selected_template
                    )
                    
                    st.success(f"✅ 项目创建成功！")
                    st.info(f"项目ID: {project_id}")
                    
                    # 设置为活动项目
                    project_manager.set_active_project(project_id)
                    
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"创建项目失败: {e}")

def _project_list_interface(project_manager: ProjectManager):
    """项目列表界面"""
    st.header("项目列表")
    
    # 过滤器
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox(
            "状态过滤",
            ["全部"] + [s.value for s in ProjectStatus]
        )
    
    with col2:
        type_filter = st.selectbox(
            "类型过滤", 
            ["全部"] + [t.value for t in ProjectType]
        )
    
    with col3:
        search_term = st.text_input("搜索", placeholder="搜索项目名称...")
    
    with col4:
        sort_by = st.selectbox("排序", ["更新时间", "创建时间", "名称"])
    
    # 获取项目列表
    status = None if status_filter == "全部" else ProjectStatus(status_filter)
    project_type = None if type_filter == "全部" else ProjectType(type_filter)
    
    projects = project_manager.list_projects(
        status=status,
        project_type=project_type,
        search_term=search_term if search_term else None
    )
    
    if not projects:
        st.info("没有找到匹配的项目")
        return
    
    # 显示项目卡片
    for project_data in projects:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.subheader(project_data["name"])
                st.caption(f"ID: {project_data['id']}")
                
                # 显示标签
                if project_data.get("tags"):
                    tag_str = " ".join([f"`{tag}`" for tag in project_data["tags"]])
                    st.markdown(tag_str)
            
            with col2:
                # 项目类型图标
                type_icons = {
                    "movie": "🎬",
                    "tv_series": "📺", 
                    "documentary": "📚",
                    "animation": "🎪",
                    "commercial": "📢",
                    "educational": "🎓",
                    "other": "❓"
                }
                project_type_val = project_data.get("project_type", "other")
                st.write(f"{type_icons.get(project_type_val, '❓')} {project_type_val}")
            
            with col3:
                # 状态指示器
                status_colors = {
                    "created": "🆕",
                    "in_progress": "🔄",
                    "translating": "🔤", 
                    "reviewing": "👀",
                    "completed": "✅",
                    "archived": "📦",
                    "paused": "⏸️"
                }
                status_val = project_data.get("status", "created")
                st.write(f"{status_colors.get(status_val, '❓')} {status_val}")
            
            with col4:
                # 操作按钮
                if st.button("打开", key=f"open_{project_data['id']}"):
                    project_manager.set_active_project(project_data['id'])
                    st.session_state.selected_project_id = project_data['id']
                    st.success(f"已切换到项目: {project_data['name']}")
            
            st.divider()

def _project_details_interface(project_manager: ProjectManager):
    """项目详情界面"""
    st.header("项目详情")
    
    # 获取当前活动项目
    active_project_id = project_manager.get_active_project()
    
    if not active_project_id:
        st.info("请先选择一个项目")
        return
    
    # 加载项目详情
    project = project_manager.get_project(active_project_id)
    if not project:
        st.error("项目不存在")
        return
    
    # 项目基本信息
    st.subheader(f"📁 {project.name}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("项目状态", project.status.value)
        st.metric("项目类型", project.project_type.value)
    
    with col2:
        st.metric("源语言", project.source_language)
        st.metric("目标语言", ", ".join(project.target_languages))
    
    with col3:
        created_date = project.created_at.strftime("%Y-%m-%d")
        st.metric("创建日期", created_date)
        st.metric("当前版本", project.current_version)
    
    if project.description:
        st.write("**项目描述:**")
        st.write(project.description)
    
    # 进度跟踪
    st.subheader("📈 项目进度")
    
    try:
        progress_tracker = ProgressTracker(active_project_id)
        progress_data = progress_tracker.get_project_progress()
        
        # 总体进度
        overall_progress = progress_data["overall_progress"]
        st.progress(overall_progress, text=f"总体进度: {overall_progress*100:.1f}%")
        
        # 进度详情
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("已完成任务", progress_data["completed_tasks"])
        
        with col2:
            st.metric("进行中任务", progress_data["in_progress_tasks"])
        
        with col3:
            st.metric("待开始任务", progress_data["pending_tasks"])
        
        with col4:
            remaining_time = progress_data["estimated_remaining_minutes"]
            if remaining_time > 60:
                time_text = f"{remaining_time//60:.1f} 小时"
            else:
                time_text = f"{remaining_time} 分钟"
            st.metric("预估剩余时间", time_text)
        
        # 下一步任务
        next_tasks = progress_tracker.get_next_tasks()
        if next_tasks:
            st.subheader("🎯 下一步任务")
            
            for task in next_tasks[:3]:  # 显示前3个任务
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{task.name}**")
                        st.caption(task.description)
                    
                    with col2:
                        priority_colors = {
                            "critical": "🔴",
                            "high": "🟠", 
                            "medium": "🟡",
                            "low": "🟢"
                        }
                        priority_icon = priority_colors.get(task.priority.value, "⚪")
                        st.write(f"{priority_icon} {task.priority.value}")
                    
                    with col3:
                        if st.button("开始", key=f"start_task_{task.id}"):
                            if progress_tracker.start_task(task.id):
                                st.success(f"已开始任务: {task.name}")
                                st.rerun()
                            else:
                                st.error("启动任务失败")
        
        # 里程碑进度
        milestones = list(progress_tracker.milestones.values())
        if milestones:
            st.subheader("🏁 项目里程碑")
            
            for milestone in milestones:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{milestone.name}**")
                    st.progress(milestone.progress, text=f"{milestone.progress*100:.1f}%")
                    st.caption(milestone.description)
                
                with col2:
                    if milestone.is_completed:
                        st.success("✅ 已完成")
                    elif milestone.is_overdue:
                        st.error("⏰ 已逾期")
                    else:
                        target_date = milestone.target_date.strftime("%m-%d")
                        st.info(f"📅 {target_date}")
    
    except Exception as e:
        st.error(f"加载进度数据失败: {e}")
    
    # 项目操作
    st.subheader("🔧 项目操作")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 查看详细进度"):
            st.info("详细进度界面开发中...")
    
    with col2:
        if st.button("📝 编辑项目"):
            st.info("项目编辑界面开发中...")
    
    with col3:
        if st.button("📦 归档项目"):
            if project_manager.update_project(active_project_id, {"status": ProjectStatus.ARCHIVED}):
                st.success("项目已归档")
                st.rerun()
    
    with col4:
        if st.button("🗑️ 删除项目", type="secondary"):
            if st.confirm("确定要删除这个项目吗？此操作不可恢复。"):
                if project_manager.delete_project(active_project_id, permanent=True):
                    st.success("项目已删除")
                    st.rerun()

def _template_management_interface(template_manager: ProjectTemplateManager):
    """模板管理界面"""
    st.header("项目模板管理")
    
    # 模板统计
    stats = template_manager.get_template_statistics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总模板数", stats["total_templates"])
    with col2:
        st.metric("电影模板", stats["by_type"].get("movie", 0))
    with col3:
        st.metric("电视剧模板", stats["by_type"].get("tv_series", 0))
    
    # 模板列表
    st.subheader("📋 可用模板")
    
    templates = template_manager.list_templates()
    
    for template in templates:
        with st.expander(f"{template.icon} {template.name}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**描述:** {template.description}")
                st.write(f"**类型:** {template.project_type.value}")
                if template.tags:
                    tag_str = " ".join([f"`{tag}`" for tag in template.tags])
                    st.markdown(f"**标签:** {tag_str}")
            
            with col2:
                st.write("**主要配置:**")
                config = template.config
                
                # 显示关键配置项
                if "api" in config:
                    st.text(f"模型: {config['api'].get('model', 'N/A')}")
                if "whisper" in config:
                    st.text(f"Whisper: {config['whisper'].get('model', 'N/A')}")
                if "tts_method" in config:
                    st.text(f"TTS: {config['tts_method']}")
                
                # 特殊功能标记
                special_features = []
                if config.get("emotion_analysis_enabled"):
                    special_features.append("🎭 情感分析")
                if config.get("cultural_adaptation"):
                    special_features.append("🌍 文化适配")
                if config.get("terminology_strict"):
                    special_features.append("📚 严格术语")
                
                if special_features:
                    st.write("**特色功能:**")
                    for feature in special_features:
                        st.text(feature)
    
    # 创建自定义模板
    st.subheader("➕ 创建自定义模板")
    
    with st.expander("创建新模板"):
        with st.form("create_template_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                template_id = st.text_input("模板ID", placeholder="template_id")
                template_name = st.text_input("模板名称", placeholder="我的自定义模板")
                template_type = st.selectbox("模板类型", [t.value for t in ProjectType])
            
            with col2:
                template_icon = st.text_input("图标", value="🎬")
                template_tags = st.text_input("标签", placeholder="用逗号分隔").split(",")
                template_tags = [tag.strip() for tag in template_tags if tag.strip()]
            
            template_desc = st.text_area("模板描述", placeholder="描述这个模板的用途和特点")
            
            # 配置编辑（简化版）
            st.write("**基础配置:**")
            col1, col2 = st.columns(2)
            
            with col1:
                api_model = st.selectbox("LLM模型", 
                    ["gpt-4.1", "claude-3-5-sonnet", "deepseek-v3", "gemini-2.0-flash"])
                whisper_model = st.selectbox("Whisper模型", 
                    ["large-v3", "large-v3-turbo"])
            
            with col2:
                tts_method = st.selectbox("TTS方法", 
                    ["azure_tts", "openai_tts", "edge_tts", "sf_cosyvoice2"])
                max_workers = st.slider("并发数", 1, 8, 4)
            
            # 特殊功能开关
            st.write("**特殊功能:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                emotion_analysis = st.checkbox("情感分析")
                cultural_adaptation = st.checkbox("文化适配") 
            
            with col2:
                terminology_strict = st.checkbox("严格术语")
                batch_processing = st.checkbox("批量处理")
            
            with col3:
                burn_subtitles = st.checkbox("字幕烧录", value=True)
                quality_threshold = st.slider("质量阈值", 0.5, 1.0, 0.8)
            
            if st.form_submit_button("创建模板"):
                if not template_id or not template_name:
                    st.error("请填写模板ID和名称")
                else:
                    # 构建配置
                    config = {
                        "api": {"model": api_model},
                        "whisper": {"model": whisper_model},
                        "tts_method": tts_method,
                        "max_workers": max_workers,
                        "burn_subtitles": burn_subtitles,
                        "emotion_analysis_enabled": emotion_analysis,
                        "cultural_adaptation": cultural_adaptation,
                        "terminology_strict": terminology_strict,
                        "batch_processing": batch_processing,
                        "quality_threshold": quality_threshold
                    }
                    
                    try:
                        success = template_manager.create_custom_template(
                            template_id=template_id,
                            name=template_name,
                            description=template_desc,
                            project_type=ProjectType(template_type),
                            config=config,
                            tags=template_tags,
                            icon=template_icon
                        )
                        
                        if success:
                            st.success("✅ 自定义模板创建成功！")
                            st.rerun()
                        else:
                            st.error("创建模板失败")
                    
                    except Exception as e:
                        st.error(f"创建模板失败: {e}")