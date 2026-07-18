"""
Settings: reset your Vera progress.
Page: 15_Settings.py
"""
import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared.persistence import get_or_create_session_id, delete_session
from shared.vera_state import get_vera_state

st.set_page_config(page_icon=FAVICON, page_title="Settings - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu(visa_type=get_vera_state().get("profile", {}).get("visa_type") or "f-1")

st.markdown(
    """
    <div style="max-width:600px;margin:1.5rem auto 0">
      <h1 style="margin:0 0 12px">Settings</h1>
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6">
        Vera doesn't have accounts, so there isn't much to configure here yet.
      </p>
      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:16px">
        <p style="font-weight:500;margin:0 0 6px">Reset my progress</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0 0 12px">
          Clears your trip details, timeline, and chat history, and starts over from the welcome screen.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 2, 1])
with center:
    if st.button("Reset my progress", use_container_width=True):
        vid = get_or_create_session_id()
        delete_session(vid)
        for key in ("vera", "chat_history", "conversation_history", "request_timestamps"):
            st.session_state.pop(key, None)
        st.switch_page("app.py")
