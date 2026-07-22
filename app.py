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

      <div class="vera-hero-icon" style="width:52px;height:52px;border-radius:50%;background:var(--bg-accent);
                  display:flex;align-items:center;justify-content:center;animation:vera-fade-up 0.5s ease-out both, vera-pulse-ring 2.8s ease-out 0.5s infinite">
        <i class="ti ti-message-circle-2" style="font-size:26px;color:var(--text-accent)"></i>
      </div>

      <div style="animation:vera-fade-up 0.5s ease-out 0.12s both">
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
        @keyframes vera-fade-up {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        /* A soft, occasional pulse ring on the header icon — a small sign of
           life on an otherwise static landing page, not a constant animation
           (2.8s period, so it reads as a heartbeat rather than a distraction). */
        @keyframes vera-pulse-ring {
            0% { box-shadow: 0 0 0 0 rgba(139,114,176,0.35); }
            70% { box-shadow: 0 0 0 14px rgba(139,114,176,0); }
            100% { box-shadow: 0 0 0 0 rgba(139,114,176,0); }
        }
        /* Both entry points are equal-weight circular bubbles side by side —
           students and staff are two front doors into the same app, not a
           primary action plus a quiet afterthought. */
        div.st-key-get_started button,
        div.st-key-staff_btn button {
            width:140px !important; height:140px !important; border-radius:50% !important;
            background:var(--bg-accent) !important; color:var(--text-accent) !important;
            border:none !important; font-weight:500 !important; font-size:14px !important;
            display:flex !important; flex-direction:column !important;
            align-items:center !important; justify-content:center !important;
            white-space:normal !important; text-align:center !important; line-height:1.3 !important;
            transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease !important;
        }
        div.st-key-get_started button:hover,
        div.st-key-staff_btn button:hover {
            transform: translateY(-5px) scale(1.04);
            box-shadow: 0 12px 28px rgba(91,67,128,0.22);
            background: var(--border-accent) !important;
        }
        div.st-key-get_started button:active,
        div.st-key-staff_btn button:active {
            transform: translateY(-1px) scale(0.97);
            box-shadow: 0 4px 10px rgba(91,67,128,0.18);
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
        div.st-key-bubble_row {
            margin-top: 28px;
            animation: vera-fade-up 0.5s ease-out 0.24s both;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

_has_profile = bool(_profile.get("name")) and bool(_profile.get("visa_type"))

_, center, _ = st.columns([1, 2, 1])
with center:
    with st.container(key="bubble_row"):
        col_student, col_staff = st.columns(2)
        with col_student:
            if st.button("Student", use_container_width=False, key="get_started"):
                # Returning students who already onboarded shouldn't be walked back
                # through Trip Details — their profile/timeline is already persisted
                # (per-account in hosted mode, per ?vid= session locally).
                if _has_profile:
                    st.switch_page("pages/04_Ask_a_Question.py")
                else:
                    st.switch_page("pages/10_Trip_Details.py")
        with col_staff:
            # Staff entry point — the only way into the DSO dashboard, which
            # isn't in the hamburger menu (students should never see those links).
            if st.button("I'm school staff", key="staff_btn"):
                st.switch_page("pages/20_DSO_Dashboard.py")
