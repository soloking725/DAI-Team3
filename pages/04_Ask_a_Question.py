"""
Your Timeline - Vera's main screen: compact chat on the left,
scrollable visa timeline on the right.
Page: 04_Ask_a_Question.py
"""
import streamlit as st

from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu, render_disclaimer, render_footer
from shared.chat_panel import render_chat_panel
from shared.timeline_ui import render_timeline
from shared.timeline import build_timeline, enrich_current_step, infer_visa_type
from shared.vera_state import get_vera_state, set_timeline, persist_vera_state

st.set_page_config(page_title="Your Timeline - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

state = get_vera_state()
visa_type = infer_visa_type(state["trip_details"])

render_hamburger_menu(visa_type=visa_type)
st.markdown(render_disclaimer(), unsafe_allow_html=True)

if not state["timeline"]:
    # Instant, no LLM calls — the skeleton is the canonical static template.
    set_timeline(build_timeline(state["trip_details"]))
    state = get_vera_state()

# Only the current step gets a constrained, grounded rewrite, and only once —
# keeps this to at most one LLM call per page load instead of one per step.
with st.spinner("Personalizing your current step..."):
    if enrich_current_step(state["timeline"], visa_type):
        persist_vera_state()

left, right = st.columns([1, 2.5], gap="medium")

with left:
    render_chat_panel()

with right:
    render_timeline(state["timeline"])

st.markdown(render_footer(), unsafe_allow_html=True)
