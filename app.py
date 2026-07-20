"""
Vera - Welcome screen
Entry point - app.py
"""
import html
import logging
import streamlit as st

from shared.branding import FAVICON
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
    page_icon=FAVICON,
    page_title="Welcome to Vera",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

_profile = get_vera_state().get("profile", {})
render_hamburger_menu(visa_type=_profile.get("visa_type") or "f-1")

_name = html.escape((_profile.get("name") or "").strip())
_headline = f"Welcome back, {_name}" if _name else "Welcome to Vera"

# Hero sits in normal flow (no fixed 75vh) so the Get started button below it is
# part of the same vertical rhythm and reads as centered, rather than being
# pushed a full viewport-height down the page.
st.markdown(
    f"""
    <div style="display:flex;flex-direction:column;align-items:center;
                text-align:center;gap:18px;margin-top:12vh">

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

st.markdown(
    """
    <style>
        div.st-key-get_started button {
            width:140px !important; height:140px !important; border-radius:50% !important;
            background:var(--bg-accent) !important; color:var(--text-accent) !important;
            border:none !important; font-weight:500 !important; font-size:14px !important;
            display:flex !important; flex-direction:column !important;
            align-items:center !important; justify-content:center !important;
        }
        /* Centering a Streamlit button takes two rules, not one: the element
           container shrink-wraps to the button's width (so it needs width:100%),
           and there's an inner .stButton wrapper between it and the <button>
           that also has to center its child. Styling only the outer container
           leaves the button pinned to the left edge. */
        div.st-key-get_started,
        div.st-key-get_started .stButton,
        div.st-key-staff_btn,
        div.st-key-staff_btn .stButton {
            width:100% !important;
            display:flex !important; justify-content:center !important;
        }
        div.st-key-get_started { margin-top: 28px; }
        div.st-key-staff_btn { margin-top: 18px; }
        div.st-key-staff_btn button {
            background:transparent !important; border:none !important;
            color:var(--text-muted) !important; font-size:13px !important;
            text-decoration:underline !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 2, 1])
with center:
    if st.button("Get started →", use_container_width=False, key="get_started"):
        st.switch_page("pages/10_Trip_Details.py")

    # Staff entry point. Students never need this, so it's deliberately quiet —
    # but it's the only way into the DSO dashboard, which isn't in the hamburger
    # menu (students should never see those links).
    if st.button("I'm school staff", key="staff_btn"):
        st.switch_page("pages/20_DSO_Dashboard.py")
