import streamlit as st

from frontend.utils.config import STREAMLIT_CONFIG

st.set_page_config(**STREAMLIT_CONFIG)

from frontend.styles.main import MAIN_CSS
from frontend.utils.helpers import init_session_state
from frontend.components.auth import render_login_page
from frontend.components.footer import render_footer
from frontend.components.dashboard import render_dashboard


st.markdown(MAIN_CSS, unsafe_allow_html=True)


def main():
    init_session_state()

    if not st.session_state.authenticated:
        render_login_page()
    else:
        render_dashboard()

    render_footer()

if __name__ == "__main__":
    main()
