"""
Streamlit术语管理界面组件

在主界面中提供术语管理功能
"""

import streamlit as st
import os
from core.terminology.term_editor import create_term_editor_interface
from core.terminology.term_manager import TermManager
from core.utils import load_key

def terminology_management_section():
    """术语管理部分"""
    st.header("🔧 专业名词管理")
    
    with st.container(border=True):
        st.markdown("""
        <p style='font-size: 20px;'>
        专业名词管理功能：
        <p style='font-size: 20px;'>
            1. 自动提取视频中的专业术语<br>
            2. 手动添加和编辑术语对照<br>
            3. 确保翻译中术语的一致性<br>
            4. 支持术语库的导入导出
        """, unsafe_allow_html=True)
        
        # 检查是否已有翻译数据
        translated_file = "output/log/translated_chunks.txt"
        has_translation = os.path.exists(translated_file)
        
        if not has_translation:
            st.info("💡 请先完成视频翻译，然后再进行术语管理")
            st.markdown("术语管理功能需要翻译数据作为基础，完成翻译后可以：")
            st.markdown("- 自动提取翻译中的专业术语")
            st.markdown("- 调整术语翻译以提高一致性")
            st.markdown("- 重新生成使用正确术语的翻译")
        else:
            # 显示术语管理界面
            create_term_editor_interface()
            
            # 重新翻译按钮
            st.subheader("🔄 应用术语重新翻译")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("使用更新的术语库重新翻译视频内容")
            with col2:
                if st.button("🚀 重新翻译", type="primary"):
                    retranslate_with_updated_terms()

def retranslate_with_updated_terms():
    """使用更新的术语重新翻译"""
    try:
        # 导入翻译函数
        from core._4_2_translate import translate_all
        
        with st.spinner("正在使用更新的术语重新翻译..."):
            # 执行翻译
            translate_all()
            
        st.success("重新翻译完成！术语已应用到翻译中。")
        st.balloons()
        
    except Exception as e:
        st.error(f"重新翻译失败: {e}")

def show_terminology_preview():
    """显示术语预览"""
    try:
        term_manager = TermManager()
        stats = term_manager.get_statistics()
        
        if stats["total_terms"] > 0:
            st.metric("术语库", f"{stats['total_terms']} 个术语")
            
            # 显示最近几个术语
            all_terms = term_manager.get_all_terms()
            recent_terms = list(all_terms.items())[:3]
            
            for source, target in recent_terms:
                st.text(f"{source} → {target}")
                
            if len(all_terms) > 3:
                st.text("...")
        else:
            st.text("术语库为空")
            
    except Exception as e:
        st.text("术语库未初始化")