"""
Vera - Welcome screen
Entry point - app.py
"""
import logging
import streamlit as st

from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared.vera_state import get_vera_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Welcome to Vera",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

_profile = get_vera_state().get("profile", {})
render_hamburger_menu(visa_type=_profile.get("visa_type") or "f-1")

_name = (_profile.get("name") or "").strip()
_headline = f"Welcome back, {_name}" if _name else "Welcome to Vera"

st.markdown(
    f"""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                text-align:center;height:75vh;gap:18px">

      <div style="width:52px;height:52px;border-radius:50%;background:var(--bg-accent);
                  display:flex;align-items:center;justify-content:center">
        <i class="ti ti-message-circle-2" style="font-size:26px;color:var(--text-accent)"></i>
      </div>

      <div>
        <h1 style="margin:0 0 6px">{_headline}</h1>
        <p style="font-size:14px;color:var(--text-secondary);margin:0">Your visa help agent, one step at a time.</p>
      </div>

    </div>
    """,
    unsafe_allow_html=True,
)

_, center, _ = st.columns([2, 1, 2])
with center:
    st.markdown(
        """
        <style>
            div.st-key-get_started button {
                width:140px !important; height:140px !important; border-radius:50% !important;
                background:var(--bg-accent) !important; color:var(--text-accent) !important;
                border:none !important; font-weight:500 !important; font-size:14px !important;
                display:flex !important; flex-direction:column !important;
                align-items:center !important; justify-content:center !important;
                margin:0 auto !important;
            }
            div.st-key-get_started {
                display:flex !important; justify-content:center !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Get started →", use_container_width=False, key="get_started"):
        st.switch_page("pages/10_Trip_Details.py")
