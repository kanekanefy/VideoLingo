"""
Batch Processing Dashboard Module

Provides Streamlit UI for batch video processing management.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import streamlit as st
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from .batch_manager import BatchManager
from .task_queue import TaskStatus, TaskPriority

class BatchProcessingDashboard:
    """Streamlit dashboard for batch processing."""
    
    def __init__(self):
        if not STREAMLIT_AVAILABLE:
            raise ImportError("Streamlit and plotting libraries are required for the batch processing dashboard")
        
        self.batch_manager = BatchManager()
    
    def render_dashboard(self):
        """Render the complete batch processing dashboard."""
        
        st.title("🎬 批量视频处理")
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 任务概览",
            "➕ 创建批量任务", 
            "📊 项目管理",
            "⚙️ 系统监控",
            "📈 统计报告"
        ])
        
        with tab1:
            self._render_task_overview()
        
        with tab2:
            self._render_create_batch()
        
        with tab3:
            self._render_project_management()
        
        with tab4:
            self._render_system_monitoring()
        
        with tab5:
            self._render_statistics()
    
    def _render_task_overview(self):
        """Render task overview tab."""
        st.subheader("📋 任务队列概览")
        
        # Control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ 启动处理系统"):
                self.batch_manager.start_processing()
                st.success("处理系统已启动")
                st.rerun()
        
        with col2:
            if st.button("⏹️ 停止处理系统"):
                self.batch_manager.stop_processing()
                st.success("处理系统已停止")
                st.rerun()
        
        with col3:
            if st.button("🔄 刷新状态"):
                st.rerun()
        
        # System status
        system_status = self.batch_manager.get_system_status()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status_text = "🟢 运行中" if system_status["batch_processing_active"] else "🔴 已停止"
            st.metric("系统状态", status_text)
        
        with col2:
            scheduler_stats = system_status["scheduler_statistics"]
            st.metric("活跃工作线程", f"{scheduler_stats['busy_workers']}/{scheduler_stats['total_workers']}")
        
        with col3:
            queue_stats = system_status["queue_statistics"]
            running_tasks = queue_stats["by_status"].get("running", 0)
            pending_tasks = queue_stats["by_status"].get("pending", 0) + queue_stats["by_status"].get("queued", 0)
            st.metric("队列任务", f"{running_tasks}运行 / {pending_tasks}等待")
        
        with col4:
            st.metric("项目总数", system_status["total_projects"])
        
        # Recent tasks
        st.subheader("🕒 最近任务")
        
        all_tasks = self.batch_manager.task_queue.list_tasks()
        recent_tasks = all_tasks[:10]  # Show last 10 tasks
        
        if recent_tasks:
            task_data = []
            for task in recent_tasks:
                task_data.append({
                    "任务ID": task.task_id[:8],
                    "类型": task.task_type,
                    "项目": task.project_id,
                    "输入文件": os.path.basename(task.input_file),
                    "状态": task.status.value,
                    "进度": f"{task.progress_percentage:.1f}%",
                    "创建时间": task.created_at[:19]
                })
            
            df = pd.DataFrame(task_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("暂无任务")
        
        # Task status distribution
        if queue_stats["total_tasks"] > 0:
            st.subheader("📊 任务状态分布")
            
            status_data = queue_stats["by_status"]
            
            # Create pie chart
            labels = list(status_data.keys())
            values = list(status_data.values())
            
            fig = px.pie(
                values=values,
                names=labels,
                title="任务状态分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_create_batch(self):
        """Render create batch tab."""
        st.subheader("➕ 创建批量处理任务")
        
        # Processing type selection
        processing_type = st.selectbox(
            "处理类型",
            ["video_translation", "audio_extraction", "subtitle_generation", "video_transcoding"],
            format_func=lambda x: {
                "video_translation": "🎬 视频翻译",
                "audio_extraction": "🎵 音频提取",
                "subtitle_generation": "📝 字幕生成",
                "video_transcoding": "🎞️ 视频转码"
            }.get(x, x)
        )
        
        # File upload
        st.subheader("📁 选择视频文件")
        uploaded_files = st.file_uploader(
            "上传视频文件",
            type=['mp4', 'avi', 'mov', 'mkv', 'wmv'],
            accept_multiple_files=True
        )
        
        # Or input file paths
        st.write("**或者输入文件路径（每行一个）:**")
        file_paths_text = st.text_area(
            "文件路径",
            placeholder="/path/to/video1.mp4\n/path/to/video2.mp4",
            height=100
        )
        
        # Output configuration
        col1, col2 = st.columns(2)
        
        with col1:
            output_dir = st.text_input(
                "输出目录",
                value="./batch_output",
                help="处理后的文件将保存到此目录"
            )
            
            project_id = st.text_input(
                "项目ID（可选）",
                placeholder="留空自动生成",
                help="用于组织和跟踪批量任务"
            )
        
        with col2:
            priority = st.selectbox(
                "任务优先级",
                [TaskPriority.LOW, TaskPriority.NORMAL, TaskPriority.HIGH, TaskPriority.CRITICAL],
                index=1,
                format_func=lambda x: {
                    TaskPriority.LOW: "🟢 低",
                    TaskPriority.NORMAL: "🟡 普通",
                    TaskPriority.HIGH: "🟠 高",
                    TaskPriority.CRITICAL: "🔴 紧急"
                }[x]
            )
            
            tags_input = st.text_input(
                "标签（用逗号分隔）",
                placeholder="标签1, 标签2"
            )
        
        # Processing configuration
        st.subheader("⚙️ 处理配置")
        
        config_override = {}
        
        if processing_type == "video_translation":
            col1, col2 = st.columns(2)
            
            with col1:
                source_lang = st.selectbox("源语言", ["en", "zh", "ja", "ko", "fr", "de", "es"])
                target_lang = st.selectbox("目标语言", ["zh-CN", "en", "ja", "ko", "fr", "de", "es"])
                whisper_model = st.selectbox("Whisper模型", ["large-v3", "large-v3-turbo", "medium"])
            
            with col2:
                llm_model = st.selectbox("LLM模型", ["gpt-4", "claude-3-5-sonnet", "deepseek-v3"])
                tts_method = st.selectbox("TTS方法", ["azure_tts", "openai_tts", "edge_tts"])
                burn_subtitles = st.checkbox("烧录字幕", value=True)
            
            config_override = {
                "source_language": source_lang,
                "target_language": target_lang,
                "whisper_model": whisper_model,
                "llm_model": llm_model,
                "tts_method": tts_method,
                "burn_subtitles": burn_subtitles
            }
        
        elif processing_type == "audio_extraction":
            col1, col2 = st.columns(2)
            
            with col1:
                audio_format = st.selectbox("音频格式", ["wav", "mp3", "flac"])
                sample_rate = st.selectbox("采样率", [16000, 22050, 44100, 48000])
            
            with col2:
                channels = st.selectbox("声道数", [1, 2])
            
            config_override = {
                "format": audio_format,
                "sample_rate": sample_rate,
                "channels": channels
            }
        
        # Pipeline mode
        st.subheader("🔄 流水线模式")
        use_pipeline = st.checkbox("启用流水线处理", help="按顺序执行多个处理步骤")
        
        pipeline_stages = []
        if use_pipeline:
            available_stages = ["audio_extraction", "video_translation", "subtitle_generation", "video_transcoding"]
            selected_stages = st.multiselect("选择处理步骤", available_stages)
            pipeline_stages = selected_stages
        
        # Submit button
        if st.button("🚀 开始批量处理", type="primary"):
            # Collect video files
            video_files = []
            
            # From uploaded files
            if uploaded_files:
                # Save uploaded files temporarily
                temp_dir = "./temp_uploads"
                os.makedirs(temp_dir, exist_ok=True)
                
                for uploaded_file in uploaded_files:
                    temp_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    video_files.append(temp_path)
            
            # From file paths
            if file_paths_text.strip():
                paths = [p.strip() for p in file_paths_text.strip().split('\n') if p.strip()]
                video_files.extend(paths)
            
            if not video_files:
                st.error("请选择至少一个视频文件")
            else:
                tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
                
                try:
                    if use_pipeline and pipeline_stages:
                        # Pipeline processing
                        task_ids = self.batch_manager.add_pipeline_batch(
                            video_files=video_files,
                            output_directory=output_dir,
                            pipeline_stages=pipeline_stages,
                            project_id=project_id if project_id else None,
                            priority=priority
                        )
                        
                        total_tasks = sum(len(stage_tasks) for stage_tasks in task_ids.values())
                        st.success(f"✅ 成功创建流水线批量任务！")
                        st.info(f"📊 共创建 {total_tasks} 个任务，分布在 {len(pipeline_stages)} 个处理阶段")
                        
                        # Show stage breakdown
                        for stage, stage_task_ids in task_ids.items():
                            st.write(f"**{stage}:** {len(stage_task_ids)} 个任务")
                    
                    else:
                        # Single type processing
                        task_ids = self.batch_manager.add_video_batch(
                            video_files=video_files,
                            output_directory=output_dir,
                            project_id=project_id if project_id else None,
                            processing_type=processing_type,
                            config_override=config_override,
                            priority=priority,
                            tags=tags
                        )
                        
                        st.success(f"✅ 成功创建批量任务！")
                        st.info(f"📊 共添加 {len(task_ids)} 个任务到处理队列")
                    
                    # Start processing if not already running
                    system_status = self.batch_manager.get_system_status()
                    if not system_status["batch_processing_active"]:
                        if st.button("🚀 启动处理系统"):
                            self.batch_manager.start_processing()
                            st.success("处理系统已启动")
                    
                    st.rerun()
                
                except Exception as e:
                    st.error(f"创建批量任务失败: {e}")
    
    def _render_project_management(self):
        """Render project management tab."""
        st.subheader("📊 项目管理")
        
        # List all projects
        projects = self.batch_manager.list_batch_projects()
        
        if not projects:
            st.info("暂无批量处理项目")
            return
        
        # Project list
        for project in projects:
            with st.expander(f"📁 {project['project_id']} - {project['completion_rate']:.1f}% 完成"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("总任务数", project['task_count'])
                    st.metric("已完成", project['completed_count'])
                
                with col2:
                    st.metric("失败数", project['failed_count'])
                    st.metric("运行中", project['running_count'])
                
                with col3:
                    st.metric("完成率", f"{project['completion_rate']:.1f}%")
                    st.write(f"**任务类型:** {', '.join(project['task_types'])}")
                
                with col4:
                    st.write(f"**创建时间:** {project['created_at'][:19]}")
                
                # Project actions
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("📋 查看详情", key=f"details_{project['project_id']}"):
                        self._show_project_details(project['project_id'])
                
                with col2:
                    if st.button("🔄 重试失败", key=f"retry_{project['project_id']}"):
                        retried = self.batch_manager.retry_failed_tasks(project['project_id'])
                        st.success(f"重试了 {retried} 个失败任务")
                        st.rerun()
                
                with col3:
                    if st.button("🚫 取消项目", key=f"cancel_{project['project_id']}"):
                        cancelled = self.batch_manager.cancel_batch(project['project_id'])
                        st.success(f"取消了 {cancelled} 个任务")
                        st.rerun()
                
                with col4:
                    if st.button("📊 导出报告", key=f"export_{project['project_id']}"):
                        report = self.batch_manager.export_batch_report(project['project_id'])
                        
                        st.download_button(
                            label="下载报告",
                            data=json.dumps(report, ensure_ascii=False, indent=2),
                            file_name=f"batch_report_{project['project_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key=f"download_{project['project_id']}"
                        )
    
    def _render_system_monitoring(self):
        """Render system monitoring tab."""
        st.subheader("⚙️ 系统监控")
        
        # Real-time metrics
        system_status = self.batch_manager.get_system_status()
        scheduler_stats = system_status["scheduler_statistics"]
        
        # System resources
        st.subheader("💻 系统资源")
        
        resources = scheduler_stats.get("system_resources", {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_usage = resources.get("cpu_percent", 0)
            st.metric("CPU使用率", f"{cpu_usage:.1f}%")
            st.progress(cpu_usage / 100)
        
        with col2:
            memory_usage = resources.get("memory_percent", 0)
            st.metric("内存使用率", f"{memory_usage:.1f}%")
            st.progress(memory_usage / 100)
        
        with col3:
            disk_usage = resources.get("disk_usage", 0)
            st.metric("磁盘使用率", f"{disk_usage:.1f}%")
            st.progress(disk_usage / 100)
        
        # Worker status
        st.subheader("👷 工作线程状态")
        
        worker_status = self.batch_manager.scheduler.get_worker_status()
        
        if worker_status:
            worker_data = []
            for worker in worker_status:
                worker_data.append({
                    "工作线程ID": worker.worker_id,
                    "状态": worker.status.value,
                    "当前任务": worker.current_task[:8] if worker.current_task else "无",
                    "已完成": worker.tasks_completed,
                    "失败数": worker.tasks_failed,
                    "成功率": f"{worker.tasks_completed/(worker.tasks_completed+worker.tasks_failed)*100:.1f}%" if (worker.tasks_completed+worker.tasks_failed) > 0 else "N/A",
                    "最后活动": worker.last_activity[:19]
                })
            
            df = pd.DataFrame(worker_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("无活跃工作线程")
        
        # Queue statistics
        st.subheader("📊 队列统计")
        
        queue_stats = system_status["queue_statistics"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总任务数", queue_stats["total_tasks"])
        
        with col2:
            st.metric("成功率", f"{queue_stats.get('success_rate', 0):.1f}%")
        
        with col3:
            avg_exec_time = queue_stats.get("avg_execution_time", 0)
            st.metric("平均执行时间", f"{avg_exec_time:.1f}分钟")
        
        with col4:
            # Calculate throughput (tasks per hour)
            completed_tasks = queue_stats["by_status"].get("completed", 0)
            if avg_exec_time > 0:
                throughput = 60 / avg_exec_time  # tasks per hour
                st.metric("处理吞吐量", f"{throughput:.1f}任务/时")
            else:
                st.metric("处理吞吐量", "N/A")
    
    def _render_statistics(self):
        """Render statistics tab."""
        st.subheader("📈 统计报告")
        
        # Time range selection
        col1, col2 = st.columns(2)
        
        with col1:
            time_range = st.selectbox(
                "统计时间范围",
                ["今天", "本周", "本月", "全部时间"],
                index=3
            )
        
        with col2:
            task_type_filter = st.selectbox(
                "任务类型筛选",
                ["全部"] + ["video_translation", "audio_extraction", "subtitle_generation", "video_transcoding"]
            )
        
        # Get statistics
        all_tasks = self.batch_manager.task_queue.list_tasks()
        
        if task_type_filter != "全部":
            all_tasks = [t for t in all_tasks if t.task_type == task_type_filter]
        
        if not all_tasks:
            st.info("暂无统计数据")
            return
        
        # Task completion over time
        st.subheader("📊 任务完成趋势")
        
        completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED and t.completed_at]
        
        if completed_tasks:
            # Group by date
            completion_dates = {}
            for task in completed_tasks:
                date = task.completed_at[:10]  # YYYY-MM-DD
                completion_dates[date] = completion_dates.get(date, 0) + 1
            
            # Create time series chart
            dates = sorted(completion_dates.keys())
            counts = [completion_dates[date] for date in dates]
            
            fig = px.line(
                x=dates,
                y=counts,
                title="每日任务完成数量",
                labels={"x": "日期", "y": "完成任务数"}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Processing time analysis
        st.subheader("⏱️ 处理时间分析")
        
        tasks_with_duration = [t for t in completed_tasks if t.actual_duration]
        
        if tasks_with_duration:
            durations = [t.actual_duration for t in tasks_with_duration]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Duration histogram
                fig = px.histogram(
                    x=durations,
                    nbins=20,
                    title="处理时间分布",
                    labels={"x": "处理时间（分钟）", "y": "任务数量"}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Duration statistics
                avg_duration = sum(durations) / len(durations)
                min_duration = min(durations)
                max_duration = max(durations)
                
                st.metric("平均处理时间", f"{avg_duration:.1f} 分钟")
                st.metric("最短处理时间", f"{min_duration:.1f} 分钟")
                st.metric("最长处理时间", f"{max_duration:.1f} 分钟")
        
        # Task type breakdown
        st.subheader("📋 任务类型分析")
        
        type_counts = {}
        for task in all_tasks:
            task_type = task.task_type
            if task_type not in type_counts:
                type_counts[task_type] = {"total": 0, "completed": 0, "failed": 0}
            
            type_counts[task_type]["total"] += 1
            if task.status == TaskStatus.COMPLETED:
                type_counts[task_type]["completed"] += 1
            elif task.status == TaskStatus.FAILED:
                type_counts[task_type]["failed"] += 1
        
        # Create breakdown table
        breakdown_data = []
        for task_type, counts in type_counts.items():
            success_rate = (counts["completed"] / counts["total"] * 100) if counts["total"] > 0 else 0
            breakdown_data.append({
                "任务类型": task_type,
                "总数": counts["total"],
                "已完成": counts["completed"],
                "失败": counts["failed"],
                "成功率": f"{success_rate:.1f}%"
            })
        
        df = pd.DataFrame(breakdown_data)
        st.dataframe(df, use_container_width=True)
    
    def _show_project_details(self, project_id: str):
        """Show detailed project information."""
        st.subheader(f"📁 项目详情: {project_id}")
        
        batch_status = self.batch_manager.get_batch_status(project_id)
        
        if "error" in batch_status:
            st.error(batch_status["error"])
            return
        
        # Project summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总任务数", batch_status["total_tasks"])
            st.metric("已完成", batch_status["completed"])
        
        with col2:
            st.metric("失败数", batch_status["failed"])
            st.metric("运行中", batch_status["running"])
        
        with col3:
            st.metric("等待中", batch_status["pending"])
            st.metric("完成率", f"{batch_status['completion_rate']:.1f}%")
        
        with col4:
            st.metric("失败率", f"{batch_status['failure_rate']:.1f}%")
            remaining_time = batch_status["estimated_remaining_minutes"]
            if remaining_time > 60:
                time_text = f"{remaining_time//60:.1f}小时"
            else:
                time_text = f"{remaining_time}分钟"
            st.metric("预计剩余时间", time_text)
        
        # Progress bar
        st.progress(batch_status["overall_progress"] / 100, text=f"总体进度: {batch_status['overall_progress']:.1f}%")
        
        # Task list
        st.subheader("📋 任务列表")
        
        task_data = []
        for task in batch_status["tasks"]:
            task_data.append({
                "任务ID": task["task_id"][:8],
                "任务类型": task["task_type"],
                "输入文件": task["input_file"],
                "状态": task["status"],
                "进度": f"{task['progress']:.1f}%",
                "错误": task["error"][:50] + "..." if task["error"] and len(task["error"]) > 50 else task["error"] or ""
            })
        
        df = pd.DataFrame(task_data)
        st.dataframe(df, use_container_width=True)