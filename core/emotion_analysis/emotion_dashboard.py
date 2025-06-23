"""
Emotion Analysis Dashboard Module

Provides Streamlit UI for emotion analysis and consistency checking.
"""

import json
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

from .emotion_analyzer import EmotionAnalyzer
from .consistency_checker import ConsistencyChecker
from .emotion_detector import EmotionLabel

class EmotionAnalysisDashboard:
    """Streamlit dashboard for emotion analysis."""
    
    def __init__(self):
        if not STREAMLIT_AVAILABLE:
            raise ImportError("Streamlit and plotting libraries are required for the emotion analysis dashboard")
        
        self.analyzer = EmotionAnalyzer()
        self.checker = ConsistencyChecker()
    
    def render_dashboard(self, project_id: str):
        """Render the complete emotion analysis dashboard."""
        
        st.title("🎭 情感分析和一致性检查")
        
        if not project_id:
            st.warning("请先选择一个项目")
            return
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 情感概览",
            "🔍 详细分析", 
            "⚖️ 一致性检查",
            "📈 情感趋势"
        ])
        
        with tab1:
            self._render_emotion_overview(project_id)
        
        with tab2:
            self._render_detailed_analysis(project_id)
        
        with tab3:
            self._render_consistency_check(project_id)
        
        with tab4:
            self._render_emotion_trends(project_id)
    
    def _render_emotion_overview(self, project_id: str):
        """Render emotion overview tab."""
        st.subheader("📊 项目情感概览")
        
        # Get project emotion summary
        summary = self.analyzer.get_project_emotion_summary(project_id)
        
        if summary["total_analyses"] == 0:
            st.info("该项目还没有进行情感分析")
            
            # Option to run new analysis
            if st.button("🎭 开始情感分析"):
                self._run_new_analysis(project_id)
            return
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("分析次数", summary["total_analyses"])
        
        with col2:
            latest_consistency = summary.get("latest_consistency")
            if latest_consistency is not None:
                st.metric("最新一致性", f"{latest_consistency:.2f}")
            else:
                st.metric("最新一致性", "N/A")
        
        with col3:
            avg_consistency = summary.get("average_consistency")
            if avg_consistency is not None:
                st.metric("平均一致性", f"{avg_consistency:.2f}")
            else:
                st.metric("平均一致性", "N/A")
        
        with col4:
            trend = summary.get("improvement_trend", "stable")
            trend_icon = {"improving": "📈", "declining": "📉", "stable": "➡️"}[trend]
            st.metric("趋势", f"{trend_icon} {trend}")
        
        # List recent analyses
        st.subheader("📋 分析历史")
        
        analyses = self.analyzer.list_project_analyses(project_id)
        
        if analyses:
            analysis_data = []
            for analysis in analyses[:10]:  # Show last 10
                analysis_data.append({
                    "分析ID": analysis["analysis_id"][-8:],
                    "创建时间": analysis["created_at"][:19],
                    "一致性评分": f"{analysis['overall_consistency']:.2f}",
                    "片段数量": analysis["segments_count"],
                    "质量问题": analysis["quality_issues_count"]
                })
            
            df = pd.DataFrame(analysis_data)
            st.dataframe(df, use_container_width=True)
            
            # Quick analysis option
            selected_analysis = st.selectbox(
                "选择分析查看详情",
                analyses,
                format_func=lambda x: f"{x['analysis_id'][-8:]} - {x['created_at'][:19]}"
            )
            
            if st.button("📊 查看详细分析"):
                st.session_state.selected_analysis_id = selected_analysis["analysis_id"]
                st.rerun()
        
        # New analysis section
        st.subheader("➕ 新建分析")
        
        if st.button("🎭 运行新的情感分析"):
            self._run_new_analysis(project_id)
    
    def _render_detailed_analysis(self, project_id: str):
        """Render detailed analysis tab."""
        st.subheader("🔍 详细情感分析")
        
        # Check if analysis is selected
        selected_analysis_id = st.session_state.get("selected_analysis_id")
        
        if not selected_analysis_id:
            st.info("请先在情感概览中选择一个分析")
            return
        
        # Load analysis
        analysis = self.analyzer.load_analysis(selected_analysis_id)
        if not analysis:
            st.error("无法加载选定的分析")
            return
        
        # Analysis summary
        st.subheader(f"📋 分析摘要 - {selected_analysis_id[-8:]}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总体一致性", f"{analysis.overall_consistency:.2f}")
        
        with col2:
            st.metric("分析片段数", len(analysis.segments))
        
        with col3:
            st.metric("质量问题数", len(analysis.quality_issues))
        
        with col4:
            st.metric("语言对", f"{analysis.source_language} → {analysis.target_language}")
        
        # Emotion distribution
        st.subheader("📊 情感分布")
        
        if analysis.emotion_distribution:
            # Create pie chart
            emotions = list(analysis.emotion_distribution.keys())
            counts = list(analysis.emotion_distribution.values())
            
            fig = px.pie(
                values=counts,
                names=emotions,
                title="原文情感分布"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Segment details
        st.subheader("📝 片段详情")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            filter_emotion = st.selectbox(
                "按情感筛选",
                ["全部"] + [emotion.value for emotion in EmotionLabel]
            )
        
        with col2:
            filter_issues = st.selectbox(
                "按问题筛选",
                ["全部", "有问题", "无问题"]
            )
        
        # Filter segments
        filtered_segments = analysis.segments
        
        if filter_emotion != "全部":
            filtered_segments = [
                seg for seg in filtered_segments 
                if seg.original_emotion.primary_emotion.emotion.value == filter_emotion
            ]
        
        if filter_issues == "有问题":
            filtered_segments = [seg for seg in filtered_segments if seg.consistency_issues]
        elif filter_issues == "无问题":
            filtered_segments = [seg for seg in filtered_segments if not seg.consistency_issues]
        
        # Display segments
        for i, segment in enumerate(filtered_segments[:20]):  # Show first 20
            with st.expander(f"片段 {segment.segment_id} - {segment.original_emotion.primary_emotion.emotion.value}"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**原文:**")
                    st.write(segment.original_text)
                    st.write(f"**情感:** {segment.original_emotion.primary_emotion.emotion.value}")
                    st.write(f"**情感强度:** {segment.original_emotion.primary_emotion.intensity:.2f}")
                    st.write(f"**整体情感:** {segment.original_emotion.overall_sentiment}")
                
                with col2:
                    st.write("**译文:**")
                    st.write(segment.translated_text)
                    st.write(f"**情感:** {segment.translated_emotion.primary_emotion.emotion.value}")
                    st.write(f"**情感强度:** {segment.translated_emotion.primary_emotion.intensity:.2f}")
                    st.write(f"**整体情感:** {segment.translated_emotion.overall_sentiment}")
                
                # Emotion match score
                st.write(f"**情感匹配度:** {segment.emotion_match_score:.2f}")
                
                # Issues and recommendations
                if segment.consistency_issues:
                    st.write("**一致性问题:**")
                    for issue in segment.consistency_issues:
                        st.write(f"- {issue}")
                
                if segment.recommendations:
                    st.write("**建议:**")
                    for rec in segment.recommendations:
                        st.write(f"- {rec}")
        
        # Overall recommendations
        if analysis.recommendations:
            st.subheader("💡 整体建议")
            for rec in analysis.recommendations:
                st.write(f"- {rec}")
    
    def _render_consistency_check(self, project_id: str):
        """Render consistency check tab."""
        st.subheader("⚖️ 情感一致性检查")
        
        # Get latest analysis
        analyses = self.analyzer.list_project_analyses(project_id)
        
        if not analyses:
            st.info("请先运行情感分析")
            return
        
        latest_analysis = self.analyzer.load_analysis(analyses[0]["analysis_id"])
        if not latest_analysis:
            st.error("无法加载最新分析")
            return
        
        # Run consistency check
        if st.button("🔍 运行一致性检查"):
            with st.spinner("正在进行一致性检查..."):
                consistency_report = self.checker.check_project_consistency(latest_analysis)
                st.session_state.consistency_report = consistency_report
        
        # Display consistency report
        if "consistency_report" in st.session_state:
            report = st.session_state.consistency_report
            
            # Overall score
            st.subheader("📊 一致性评分")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                score_color = "green" if report.overall_score > 0.7 else "orange" if report.overall_score > 0.4 else "red"
                st.markdown(f"<h2 style='color: {score_color}'>{report.overall_score:.2f}</h2>", unsafe_allow_html=True)
                st.write("总体一致性评分")
            
            with col2:
                st.metric("总问题数", len(report.issues))
            
            with col3:
                critical_issues = len([issue for issue in report.issues if issue.severity == "critical"])
                st.metric("严重问题", critical_issues)
            
            # Quality metrics
            st.subheader("📈 质量指标")
            
            metrics = report.quality_metrics
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("情感匹配率", f"{metrics.get('emotion_match_rate', 0):.2%}")
            
            with col2:
                st.metric("情感匹配率", f"{metrics.get('sentiment_match_rate', 0):.2%}")
            
            with col3:
                st.metric("问题片段率", f"{metrics.get('segments_with_issues_rate', 0):.2%}")
            
            with col4:
                st.metric("信心度下降", f"{metrics.get('confidence_drop', 0):.2f}")
            
            # Issues breakdown
            if report.issues:
                st.subheader("⚠️ 一致性问题")
                
                # Group issues by severity
                issues_by_severity = {}
                for issue in report.issues:
                    if issue.severity not in issues_by_severity:
                        issues_by_severity[issue.severity] = []
                    issues_by_severity[issue.severity].append(issue)
                
                # Display issues by severity
                severity_order = ["critical", "high", "medium", "low"]
                severity_colors = {
                    "critical": "🔴",
                    "high": "🟠", 
                    "medium": "🟡",
                    "low": "🟢"
                }
                
                for severity in severity_order:
                    if severity in issues_by_severity:
                        st.write(f"**{severity_colors[severity]} {severity.upper()} 问题:**")
                        
                        for issue in issues_by_severity[severity]:
                            with st.expander(f"{issue.issue_type} - 置信度: {issue.confidence:.2f}"):
                                st.write(f"**描述:** {issue.description}")
                                st.write(f"**影响片段:** {len(issue.segment_ids)} 个")
                                st.write(f"**建议修复:** {issue.suggested_fix}")
                                
                                if len(issue.segment_ids) <= 10:
                                    st.write(f"**片段ID:** {', '.join(issue.segment_ids)}")
            
            # Segment scores
            st.subheader("📊 片段评分")
            
            if report.segment_scores:
                # Create score distribution
                scores = list(report.segment_scores.values())
                
                fig = px.histogram(
                    x=scores,
                    nbins=20,
                    title="片段一致性评分分布",
                    labels={"x": "一致性评分", "y": "片段数量"}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show low-scoring segments
                low_scoring = [(seg_id, score) for seg_id, score in report.segment_scores.items() if score < 0.5]
                
                if low_scoring:
                    st.write(f"**低分片段 (< 0.5):** {len(low_scoring)} 个")
                    
                    low_scoring.sort(key=lambda x: x[1])  # Sort by score
                    
                    for seg_id, score in low_scoring[:10]:  # Show worst 10
                        st.write(f"- 片段 {seg_id}: {score:.2f}")
            
            # Recommendations
            if report.recommendations:
                st.subheader("💡 改进建议")
                
                for i, rec in enumerate(report.recommendations, 1):
                    st.write(f"{i}. {rec}")
    
    def _render_emotion_trends(self, project_id: str):
        """Render emotion trends tab."""
        st.subheader("📈 情感趋势分析")
        
        analyses = self.analyzer.list_project_analyses(project_id)
        
        if len(analyses) < 2:
            st.info("需要至少2次分析才能显示趋势")
            return
        
        # Consistency trend
        st.subheader("🔄 一致性趋势")
        
        dates = [analysis["created_at"][:10] for analysis in reversed(analyses)]
        consistency_scores = [analysis["overall_consistency"] for analysis in reversed(analyses)]
        
        fig = px.line(
            x=dates,
            y=consistency_scores,
            title="情感一致性趋势",
            labels={"x": "日期", "y": "一致性评分"},
            markers=True
        )
        fig.update_layout(yaxis_range=[0, 1])
        st.plotly_chart(fig, use_container_width=True)
        
        # Quality issues trend
        st.subheader("⚠️ 质量问题趋势")
        
        issue_counts = [analysis["quality_issues_count"] for analysis in reversed(analyses)]
        
        fig = px.bar(
            x=dates,
            y=issue_counts,
            title="质量问题数量趋势",
            labels={"x": "日期", "y": "问题数量"}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Improvement suggestions based on trends
        st.subheader("📊 趋势分析")
        
        if len(consistency_scores) >= 3:
            recent_trend = consistency_scores[-3:]
            if all(recent_trend[i] <= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                st.success("✅ 一致性评分呈上升趋势！")
            elif all(recent_trend[i] >= recent_trend[i+1] for i in range(len(recent_trend)-1)):
                st.warning("⚠️ 一致性评分呈下降趋势，需要注意")
            else:
                st.info("ℹ️ 一致性评分较为稳定")
        
        # Best and worst analyses
        best_analysis = max(analyses, key=lambda x: x["overall_consistency"])
        worst_analysis = min(analyses, key=lambda x: x["overall_consistency"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success(f"**最佳分析:** {best_analysis['analysis_id'][-8:]}")
            st.write(f"一致性: {best_analysis['overall_consistency']:.2f}")
            st.write(f"日期: {best_analysis['created_at'][:10]}")
        
        with col2:
            st.error(f"**最差分析:** {worst_analysis['analysis_id'][-8:]}")
            st.write(f"一致性: {worst_analysis['overall_consistency']:.2f}")
            st.write(f"日期: {worst_analysis['created_at'][:10]}")
    
    def _run_new_analysis(self, project_id: str):
        """Run a new emotion analysis."""
        st.info("新的情感分析功能需要集成到项目工作流中")
        
        # This would typically integrate with the project management system
        # to get translation data and run analysis
        
        # Placeholder for now
        with st.form("analysis_config"):
            st.write("**分析配置**")
            
            source_lang = st.selectbox("源语言", ["en", "zh", "ja", "ko", "fr", "de", "es"])
            target_lang = st.selectbox("目标语言", ["zh-CN", "en", "ja", "ko", "fr", "de", "es"])
            
            analysis_name = st.text_input("分析名称", placeholder="可选，用于标识此次分析")
            
            if st.form_submit_button("🎭 开始分析"):
                st.info("此功能需要与项目管理系统集成后才能使用")
                # TODO: Integrate with project management to get actual translation data
                # translation_data = get_project_translation_data(project_id)
                # analysis = self.analyzer.analyze_project_emotions(
                #     project_id, translation_data, source_lang, target_lang
                # )
                # st.success(f"分析完成！分析ID: {analysis.analysis_id}")
                # st.rerun()