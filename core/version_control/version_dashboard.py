"""
Version Control Dashboard Module

Provides Streamlit UI for translation version management and comparison.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from .version_manager import VersionManager
from .translation_diff import ChangeType

class VersionControlDashboard:
    """Streamlit dashboard for version control."""
    
    def __init__(self):
        if not STREAMLIT_AVAILABLE:
            raise ImportError("Streamlit is required for the version control dashboard")
        
        self.version_manager = VersionManager()
    
    def render_dashboard(self, project_id: str):
        """Render the complete version control dashboard."""
        
        st.title("🔄 翻译版本管理")
        
        if not project_id:
            st.warning("请先选择一个项目")
            return
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 版本列表", 
            "🔍 版本对比", 
            "📊 统计分析",
            "⚙️ 版本操作"
        ])
        
        with tab1:
            self._render_version_list(project_id)
        
        with tab2:
            self._render_version_comparison(project_id)
        
        with tab3:
            self._render_statistics(project_id)
        
        with tab4:
            self._render_version_operations(project_id)
    
    def _render_version_list(self, project_id: str):
        """Render version list tab."""
        st.subheader("📋 项目版本列表")
        
        versions = self.version_manager.list_project_versions(project_id)
        
        if not versions:
            st.info("该项目还没有任何版本")
            return
        
        # Version list with filters
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input("🔍 搜索版本描述", "")
        
        with col2:
            tag_filter = st.selectbox("🏷️ 按标签筛选", ["全部"] + self._get_all_tags(versions))
        
        # Filter versions
        filtered_versions = versions
        
        if search_query:
            filtered_versions = [
                v for v in filtered_versions 
                if search_query.lower() in v.get("description", "").lower()
            ]
        
        if tag_filter != "全部":
            filtered_versions = [
                v for v in filtered_versions 
                if tag_filter in v.get("tags", [])
            ]
        
        # Display versions
        for version in filtered_versions:
            with st.expander(f"版本 {version['version_number']} - {version.get('description', '无描述')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**创建时间:** {version['created_at'][:19]}")
                    st.write(f"**片段数量:** {version['segment_count']}")
                
                with col2:
                    quality = version.get('quality_score')
                    if quality is not None:
                        st.write(f"**质量评分:** {quality:.2f}")
                    
                    tags = version.get('tags', [])
                    if tags:
                        st.write(f"**标签:** {', '.join(tags)}")
                
                with col3:
                    if st.button(f"查看详情", key=f"view_{version['version_id']}"):
                        self._show_version_details(version['version_id'])
                    
                    if st.button(f"恢复此版本", key=f"restore_{version['version_id']}"):
                        self._restore_version(project_id, version['version_id'])
    
    def _render_version_comparison(self, project_id: str):
        """Render version comparison tab."""
        st.subheader("🔍 版本对比分析")
        
        versions = self.version_manager.list_project_versions(project_id)
        
        if len(versions) < 2:
            st.info("至少需要2个版本才能进行对比")
            return
        
        # Version selection
        col1, col2 = st.columns(2)
        
        version_options = [f"{v['version_number']} ({v['version_id'][:8]})" for v in versions]
        
        with col1:
            old_version_idx = st.selectbox("选择旧版本", range(len(versions)), format_func=lambda x: version_options[x])
        
        with col2:
            new_version_idx = st.selectbox("选择新版本", range(len(versions)), format_func=lambda x: version_options[x])
        
        if old_version_idx == new_version_idx:
            st.warning("请选择不同的版本进行对比")
            return
        
        old_version = versions[old_version_idx]
        new_version = versions[new_version_idx]
        
        if st.button("🔍 开始对比"):
            self._show_version_diff(old_version['version_id'], new_version['version_id'])
    
    def _render_statistics(self, project_id: str):
        """Render statistics tab."""
        st.subheader("📊 版本统计分析")
        
        stats = self.version_manager.get_version_statistics(project_id)
        
        if stats['total_versions'] == 0:
            st.info("没有版本数据可供分析")
            return
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总版本数", stats['total_versions'])
        
        with col2:
            st.metric("最新版本", stats.get('latest_version', 'N/A'))
        
        with col3:
            avg_quality = stats.get('average_quality')
            if avg_quality is not None:
                st.metric("平均质量", f"{avg_quality:.2f}")
            else:
                st.metric("平均质量", "N/A")
        
        with col4:
            latest_similarity = stats.get('latest_similarity')
            if latest_similarity is not None:
                st.metric("最新相似度", f"{latest_similarity:.2f}")
            else:
                st.metric("最新相似度", "N/A")
        
        # Latest change summary
        if 'latest_change_summary' in stats:
            st.subheader("📈 最新变更摘要")
            summary = stats['latest_change_summary']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("修改", summary['modified'])
            with col2:
                st.metric("新增", summary['added'])
            with col3:
                st.metric("删除", summary['deleted'])
            with col4:
                st.metric("变更率", f"{summary['change_percentage']:.1f}%")
        
        # Common tags
        common_tags = stats.get('common_tags', [])
        if common_tags:
            st.subheader("🏷️ 常用标签")
            st.write(", ".join(common_tags))
    
    def _render_version_operations(self, project_id: str):
        """Render version operations tab."""
        st.subheader("⚙️ 版本操作")
        
        # Create new version
        with st.expander("➕ 创建新版本"):
            st.write("**从JSON文件创建版本**")
            
            uploaded_file = st.file_uploader("上传翻译JSON文件", type=['json'])
            version_number = st.text_input("版本号 (可选)", placeholder="自动生成")
            description = st.text_area("版本描述")
            tags_input = st.text_input("标签 (用逗号分隔)", placeholder="例如: 初稿, 审校")
            
            if uploaded_file and st.button("创建版本"):
                try:
                    translation_data = json.load(uploaded_file)
                    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]
                    
                    version = self.version_manager.create_version(
                        project_id=project_id,
                        translation_data=translation_data,
                        version_number=version_number if version_number else None,
                        description=description,
                        tags=tags
                    )
                    
                    st.success(f"版本 {version.version_number} 创建成功！")
                    st.rerun()
                
                except Exception as e:
                    st.error(f"创建版本失败: {str(e)}")
        
        # Export version history
        with st.expander("📤 导出版本历史"):
            if st.button("导出为JSON"):
                history = self.version_manager.export_version_history(project_id)
                
                st.download_button(
                    label="下载版本历史",
                    data=json.dumps(history, ensure_ascii=False, indent=2),
                    file_name=f"version_history_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Delete versions
        with st.expander("🗑️ 删除版本"):
            st.warning("⚠️ 删除操作不可恢复，请谨慎操作")
            
            versions = self.version_manager.list_project_versions(project_id)
            if versions:
                version_to_delete = st.selectbox(
                    "选择要删除的版本",
                    versions,
                    format_func=lambda x: f"{x['version_number']} - {x.get('description', '无描述')}"
                )
                
                if st.button("确认删除", type="secondary"):
                    if self.version_manager.delete_version(version_to_delete['version_id']):
                        st.success("版本删除成功")
                        st.rerun()
                    else:
                        st.error("删除失败")
    
    def _get_all_tags(self, versions: List[Dict[str, Any]]) -> List[str]:
        """Get all unique tags from versions."""
        all_tags = set()
        for version in versions:
            all_tags.update(version.get('tags', []))
        return sorted(list(all_tags))
    
    def _show_version_details(self, version_id: str):
        """Show detailed information about a version."""
        version = self.version_manager.get_version(version_id)
        if not version:
            st.error("版本不存在")
            return
        
        st.subheader(f"版本详情: {version.version_number}")
        
        # Metadata
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**版本ID:** {version.version_id}")
            st.write(f"**创建时间:** {version.created_at}")
            st.write(f"**创建者:** {version.created_by}")
        
        with col2:
            st.write(f"**描述:** {version.description}")
            st.write(f"**片段数量:** {version.segment_count}")
            if version.quality_score:
                st.write(f"**质量评分:** {version.quality_score:.2f}")
        
        if version.tags:
            st.write(f"**标签:** {', '.join(version.tags)}")
        
        # Content preview
        segments = version.content.get('segments', [])[:5]  # Show first 5 segments
        if segments:
            st.subheader("内容预览 (前5个片段)")
            for i, segment in enumerate(segments):
                st.write(f"**{i+1}.** {segment.get('text', '')}")
    
    def _show_version_diff(self, old_version_id: str, new_version_id: str):
        """Show detailed comparison between two versions."""
        diff = self.version_manager.compare_versions(old_version_id, new_version_id)
        
        if not diff:
            st.error("无法比较版本")
            return
        
        st.subheader(f"版本对比: {diff.old_version_number} → {diff.new_version_number}")
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("修改", diff.summary['modified'])
        with col2:
            st.metric("新增", diff.summary['added'])
        with col3:
            st.metric("删除", diff.summary['deleted'])
        with col4:
            st.metric("相似度", f"{diff.overall_similarity:.2f}")
        
        # Detailed changes
        st.subheader("详细变更")
        
        # Filter options
        change_filter = st.selectbox(
            "显示变更类型",
            ["全部", "仅修改", "仅新增", "仅删除"]
        )
        
        for diff_item in diff.segment_diffs:
            if change_filter == "仅修改" and diff_item.change_type != ChangeType.MODIFIED:
                continue
            elif change_filter == "仅新增" and diff_item.change_type != ChangeType.ADDED:
                continue
            elif change_filter == "仅删除" and diff_item.change_type != ChangeType.DELETED:
                continue
            elif change_filter == "全部" and diff_item.change_type == ChangeType.UNCHANGED:
                continue
            
            self._render_segment_diff(diff_item)
    
    def _render_segment_diff(self, diff_item):
        """Render a single segment difference."""
        change_icons = {
            ChangeType.ADDED: "➕",
            ChangeType.DELETED: "➖", 
            ChangeType.MODIFIED: "✏️",
            ChangeType.UNCHANGED: "✅"
        }
        
        change_colors = {
            ChangeType.ADDED: "🟢",
            ChangeType.DELETED: "🔴",
            ChangeType.MODIFIED: "🟡",
            ChangeType.UNCHANGED: "⚪"
        }
        
        icon = change_icons.get(diff_item.change_type, "❓")
        color = change_colors.get(diff_item.change_type, "⚪")
        
        with st.expander(f"{icon} 片段 {diff_item.segment_id} {color}"):
            if diff_item.change_type == ChangeType.ADDED:
                st.success(f"**新增:** {diff_item.new_text}")
            
            elif diff_item.change_type == ChangeType.DELETED:
                st.error(f"**删除:** {diff_item.old_text}")
            
            elif diff_item.change_type == ChangeType.MODIFIED:
                st.error(f"**旧文本:** {diff_item.old_text}")
                st.success(f"**新文本:** {diff_item.new_text}")
                st.info(f"**相似度:** {diff_item.similarity_score:.2f}")
    
    def _restore_version(self, project_id: str, version_id: str):
        """Restore a version."""
        restored_data = self.version_manager.restore_version(version_id)
        
        if restored_data:
            st.success("版本恢复成功！")
            
            # Create new version from restored data
            version = self.version_manager.create_version(
                project_id=project_id,
                translation_data=restored_data,
                description=f"恢复自版本 {restored_data['version_info']['version_number']}",
                tags=["恢复", "自动创建"]
            )
            
            st.info(f"已创建新版本: {version.version_number}")
            st.rerun()
        else:
            st.error("恢复失败")