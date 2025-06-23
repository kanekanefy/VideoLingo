"""
术语编辑界面

为Streamlit提供术语管理和编辑的用户界面组件
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from .term_manager import TermManager
from .term_extractor import extract_terms_from_translation
from .term_validator import TermValidator

def create_term_editor_interface():
    """创建术语编辑器界面"""
    st.header("🔧 专业名词管理")
    
    # 初始化术语管理器
    if 'term_manager' not in st.session_state:
        st.session_state.term_manager = TermManager()
    
    term_manager = st.session_state.term_manager
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 手动管理", "🤖 自动提取", "📊 统计报告", "📥📤 导入导出", "⚙️ 设置"
    ])
    
    with tab1:
        _manual_term_management(term_manager)
    
    with tab2:
        _auto_term_extraction(term_manager)
    
    with tab3:
        _statistics_report(term_manager)
    
    with tab4:
        _import_export_interface(term_manager)
    
    with tab5:
        _settings_interface(term_manager)

def _manual_term_management(term_manager: TermManager):
    """手动术语管理界面"""
    st.subheader("手动添加/编辑术语")
    
    # 添加新术语
    with st.expander("➕ 添加新术语", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            source_term = st.text_input("原文术语", key="add_source")
            category = st.selectbox("分类", 
                                  ["技术术语", "人名", "地名", "品牌", "产品", "其他"],
                                  key="add_category")
        
        with col2:
            target_term = st.text_input("翻译术语", key="add_target")
            priority = st.slider("优先级", 1, 5, 1, key="add_priority")
        
        notes = st.text_area("备注", key="add_notes")
        
        if st.button("添加术语", type="primary"):
            if source_term and target_term:
                success = term_manager.add_term(source_term, target_term, category, priority, notes)
                if success:
                    st.success("术语添加成功！")
                    st.rerun()
                else:
                    st.error("术语添加失败")
            else:
                st.error("请填写原文术语和翻译术语")
    
    # 显示现有术语
    st.subheader("现有术语库")
    
    all_terms = term_manager.get_all_terms()
    if not all_terms:
        st.info("术语库为空，请添加术语或使用自动提取功能")
        return
    
    # 搜索和过滤
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 搜索术语", key="search_terms")
    with col2:
        filter_category = st.selectbox("筛选分类", 
                                     ["全部"] + term_manager.get_categories(),
                                     key="filter_category")
    
    # 构建显示数据
    display_data = []
    for source, target in all_terms.items():
        category = term_manager.custom_terms["categories"].get(source, "general")
        priority = term_manager.custom_terms["priorities"].get(source, 1)
        notes = term_manager.custom_terms["notes"].get(source, "")
        
        # 应用搜索和过滤
        if search_term and search_term.lower() not in source.lower() and search_term.lower() not in target.lower():
            continue
        if filter_category != "全部" and category != filter_category:
            continue
        
        display_data.append({
            "原文": source,
            "翻译": target,
            "分类": category,
            "优先级": priority,
            "备注": notes
        })
    
    if display_data:
        df = pd.DataFrame(display_data)
        
        # 使用可编辑的数据表格
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "优先级": st.column_config.SliderColumn(
                    "优先级",
                    help="术语优先级（1-5）",
                    min_value=1,
                    max_value=5,
                    step=1,
                    format="%d"
                ),
                "分类": st.column_config.SelectboxColumn(
                    "分类",
                    help="术语分类",
                    options=["技术术语", "人名", "地名", "品牌", "产品", "其他"]
                )
            },
            key="term_editor"
        )
        
        # 保存修改
        if st.button("💾 保存修改"):
            _save_term_edits(term_manager, df, edited_df)
    else:
        st.info("没有找到匹配的术语")

def _auto_term_extraction(term_manager: TermManager):
    """自动术语提取界面"""
    st.subheader("自动提取专业术语")
    
    # 检查是否有翻译数据
    source_file = "output/log/split_by_meaning.txt"
    target_file = "output/log/translated_chunks.txt"
    
    import os
    if not (os.path.exists(source_file) and os.path.exists(target_file)):
        st.warning("请先完成视频翻译，然后再使用自动提取功能")
        return
    
    if st.button("🤖 开始自动提取", type="primary"):
        with st.spinner("正在提取专业术语..."):
            try:
                # 读取翻译数据
                with open(source_file, 'r', encoding='utf-8') as f:
                    source_chunks = f.read().strip().split('\n')
                
                with open(target_file, 'r', encoding='utf-8') as f:
                    target_chunks = f.read().strip().split('\n')
                
                # 提取术语
                extraction_result = extract_terms_from_translation(source_chunks, target_chunks)
                
                # 保存提取结果
                term_manager.update_auto_extracted_terms(extraction_result)
                
                st.success("术语提取完成！")
                st.rerun()
                
            except Exception as e:
                st.error(f"提取失败: {e}")
    
    # 显示建议的术语
    suggested_terms = term_manager.get_suggested_terms()
    if suggested_terms:
        st.subheader("建议的术语对")
        
        for i, term_pair in enumerate(suggested_terms[:20]):  # 只显示前20个
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.text(term_pair["source"])
            with col2:
                st.text(term_pair["target"])
            with col3:
                st.text(f"{term_pair['confidence']:.2f}")
            with col4:
                if st.button("添加", key=f"add_suggested_{i}"):
                    success = term_manager.add_term(
                        term_pair["source"], 
                        term_pair["target"],
                        "自动提取"
                    )
                    if success:
                        st.success("已添加到术语库")
                        st.rerun()

def _statistics_report(term_manager: TermManager):
    """统计报告界面"""
    st.subheader("术语库统计")
    
    stats = term_manager.get_statistics()
    
    # 基本统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总术语数", stats["total_terms"])
    with col2:
        st.metric("建议术语数", stats["suggested_terms_count"])
    with col3:
        st.metric("近7天修改", stats["recent_changes"])
    
    # 分类统计
    if stats["categories"]:
        st.subheader("分类分布")
        category_df = pd.DataFrame(
            list(stats["categories"].items()),
            columns=["分类", "数量"]
        )
        st.bar_chart(category_df.set_index("分类"))
    
    # 验证报告
    st.subheader("一致性检查")
    
    # 检查是否有翻译数据可以验证
    target_file = "output/log/translated_chunks.txt"
    if os.path.exists(target_file):
        if st.button("🔍 运行一致性检查"):
            with st.spinner("检查中..."):
                try:
                    with open(target_file, 'r', encoding='utf-8') as f:
                        target_chunks = f.read().strip().split('\n')
                    
                    validator = TermValidator(term_manager)
                    validation_result = validator.validate_terminology_consistency(target_chunks)
                    
                    if validation_result["inconsistencies"]:
                        st.warning(f"发现 {len(validation_result['inconsistencies'])} 个不一致的术语")
                        for issue in validation_result["inconsistencies"]:
                            st.write(f"- **{issue['term']}**: 期望 '{issue['expected']}'，但发现 {issue['found_translations']}")
                    else:
                        st.success("术语使用一致！")
                        
                except Exception as e:
                    st.error(f"检查失败: {e}")
    else:
        st.info("需要翻译数据才能进行一致性检查")

def _import_export_interface(term_manager: TermManager):
    """导入导出界面"""
    st.subheader("导入/导出术语库")
    
    # 导出功能
    st.write("### 📤 导出术语库")
    if st.button("导出为Excel", type="primary"):
        export_path = "output/terminology/exported_terms.xlsx"
        success = term_manager.export_to_excel(export_path)
        if success:
            st.success(f"导出成功: {export_path}")
            # 提供下载链接
            with open(export_path, "rb") as file:
                st.download_button(
                    label="📥 下载Excel文件",
                    data=file.read(),
                    file_name="terminology.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.error("导出失败")
    
    # 导入功能
    st.write("### 📥 导入术语库")
    uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'])
    
    if uploaded_file:
        # 保存上传的文件
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # 预览文件内容
        try:
            preview_df = pd.read_excel(tmp_path)
            st.write("文件预览:")
            st.dataframe(preview_df.head())
            
            if st.button("确认导入"):
                success = term_manager.import_from_excel(tmp_path)
                if success:
                    st.success("导入成功！")
                    st.rerun()
                else:
                    st.error("导入失败，请检查文件格式")
        except Exception as e:
            st.error(f"文件读取失败: {e}")
        
        # 清理临时文件
        os.unlink(tmp_path)

def _settings_interface(term_manager: TermManager):
    """设置界面"""
    st.subheader("术语管理设置")
    
    # 清理选项
    st.write("### 🧹 数据清理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("清空自动提取的术语", type="secondary"):
            if st.confirm("确定要清空所有自动提取的术语吗？"):
                term_manager.auto_terms = {
                    "version": "1.0",
                    "extracted_at": "",
                    "suggested_pairs": [],
                    "term_frequency": {},
                    "important_terms": []
                }
                term_manager._save_auto_terms()
                st.success("自动提取术语已清空")
                st.rerun()
    
    with col2:
        if st.button("清空术语历史", type="secondary"):
            if st.confirm("确定要清空术语修改历史吗？"):
                term_manager.term_history = []
                term_manager._save_term_history()
                st.success("术语历史已清空")
                st.rerun()
    
    # 显示历史记录
    if term_manager.term_history:
        st.write("### 📋 最近修改历史")
        recent_history = term_manager.term_history[-10:]  # 显示最近10条
        for record in reversed(recent_history):
            timestamp = record["timestamp"][:19].replace('T', ' ')
            action = record["action"]
            term = record["source_term"]
            st.text(f"{timestamp} - {action}: {term}")

def _save_term_edits(term_manager: TermManager, original_df: pd.DataFrame, edited_df: pd.DataFrame):
    """保存术语编辑"""
    try:
        changes_made = False
        
        # 比较数据框的变化
        for idx, (orig_row, edit_row) in enumerate(zip(original_df.itertuples(), edited_df.itertuples())):
            orig_source = orig_row.原文
            
            # 检查是否有变化
            if (orig_row.翻译 != edit_row.翻译 or 
                orig_row.分类 != edit_row.分类 or 
                orig_row.优先级 != edit_row.优先级 or 
                orig_row.备注 != edit_row.备注):
                
                # 更新术语
                term_manager.update_term(
                    orig_source,
                    edit_row.翻译,
                    edit_row.分类,
                    edit_row.优先级,
                    edit_row.备注
                )
                changes_made = True
        
        if changes_made:
            st.success("修改已保存！")
            st.rerun()
        else:
            st.info("没有检测到修改")
            
    except Exception as e:
        st.error(f"保存失败: {e}")