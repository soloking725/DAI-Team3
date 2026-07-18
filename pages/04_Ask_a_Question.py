"""
Your Timeline - Vera's main screen: compact chat on the left,
scrollable visa timeline on the right.
Page: 04_Ask_a_Question.py
"""
import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu, render_disclaimer, render_footer
from shared.chat_panel import render_chat_panel
from shared.timeline_ui import render_timeline, render_circumstances_card
from shared.timeline import build_timeline, infer_visa_type
from shared.vera_state import get_vera_state, set_timeline
from shared import auth

st.set_page_config(page_icon=FAVICON, page_title="Your Timeline - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

# The timeline is per-student persisted state, so it needs a signed-in user in
# hosted mode. No-op in local mode.
auth.require_login("Sign in to see your timeline")

state = get_vera_state()
visa_type = infer_visa_type(state["trip_details"])

render_hamburger_menu(visa_type=visa_type)

name = (state.get("profile", {}).get("name") or "").strip()
if name:
    st.markdown(f"<p style='font-size:14px;color:var(--text-secondary);margin:0.5rem 0 0'>Welcome back, {name}.</p>", unsafe_allow_html=True)

st.markdown(render_disclaimer(), unsafe_allow_html=True)

circumstances = state.get("extenuating_circumstances", {}).get("categories", [])
if circumstances:
    render_circumstances_card(circumstances, visa_type=visa_type)

if not state["timeline"]:
    # Instant, no LLM calls — steps come from the canonical static template,
    # with detail text already filled in from the precomputed enrichment
    # cache (see precompute_timeline_enrichment.py).
    set_timeline(build_timeline(state["trip_details"]))
    state = get_vera_state()

left, right = st.columns([1, 2.5], gap="medium")

with left:
    render_chat_panel()

with right:
    render_timeline(state["timeline"], visa_type=visa_type)

st.markdown(render_footer(), unsafe_allow_html=True)
