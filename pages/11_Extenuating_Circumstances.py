"""
Extenuating circumstances intake — an optional, skippable step so Vera
knows about anything (a prior denial, SEVIS issue, hardship, emergency,
delayed documents) that should shape the guidance it surfaces later.
Page: 11_Extenuating_Circumstances.py
"""
import streamlit as st

from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared.vera_state import get_vera_state, set_extenuating_circumstances
from shared.circumstances import CIRCUMSTANCE_CATEGORIES

st.set_page_config(page_title="Anything else Vera should know? - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

state = get_vera_state()
render_hamburger_menu(visa_type=state.get("profile", {}).get("visa_type") or "f-1")

st.markdown(
    """
    <div style="max-width:460px;margin:1.5rem auto 0">
    <div style="text-align:center;margin-bottom:22px">
      <h1 style="margin:0 0 6px">Anything making this more complicated?</h1>
      <p style="font-size:14px;color:var(--text-secondary);margin:0">
        Optional — but if any of these apply, Vera can surface guidance specific to your situation.
        This tool still can't give legal advice; for anything serious, an immigration attorney should review your case.
      </p>
    </div>
    </div>
    """,
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 2, 1])
with center:
    with st.form("extenuating_circumstances_form"):
        selected = []
        for cat in CIRCUMSTANCE_CATEGORIES:
            if st.checkbox(cat["label"], key=f"circ_{cat['id']}"):
                selected.append(cat["id"])

        notes = st.text_area(
            "Anything else you'd like to add (optional)",
            placeholder="A few details help Vera point you to the right guidance.",
        )

        col_skip, col_continue = st.columns(2)
        with col_skip:
            skipped = st.form_submit_button("Skip for now", use_container_width=True)
        with col_continue:
            submitted = st.form_submit_button("Continue", use_container_width=True, type="primary")

    if skipped:
        set_extenuating_circumstances([], "")
        st.switch_page("pages/12_School_Guide_Upload.py")
    elif submitted:
        set_extenuating_circumstances(selected, notes.strip())
        st.switch_page("pages/12_School_Guide_Upload.py")
