import streamlit as st

def render_footer():
    """Render application footer"""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>📈 CMV Portfolio Management App v1.0 | Enhanced Portfolio Management System</p>
            <p>Made with ❤️ by @nopnopla.aivay | 
            <a href='https://www.instagram.com/nopnopla.aivay/' style='color: #2a5298;'>Instagram</a> | 
            <p style='color: #2a5298;'>For Support: vinhkhang378@gmail.com</p>  
        </div>
        """,
        unsafe_allow_html=True
    )
    