"""
Help: find a licensed immigration attorney.
Page: 13_Help_Find_a_Lawyer.py
"""
import streamlit as st

from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu, render_disclaimer
from shared.config import AILA_ATTORNEY_FINDER, LEGAL_ADVICE_REFUSAL
from shared.vera_state import get_vera_state

st.set_page_config(page_title="Find a lawyer - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu(visa_type=get_vera_state().get("profile", {}).get("visa_type") or "f-1")
st.markdown(render_disclaimer(), unsafe_allow_html=True)

st.markdown(
    f"""
    <div style="max-width:600px;margin:1.5rem auto 0">
      <h1 style="margin:0 0 12px">Find an immigration attorney</h1>
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6">
        {LEGAL_ADVICE_REFUSAL}
      </p>
      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:16px">
        <p style="font-weight:500;margin:0 0 6px">American Immigration Lawyers Association (AILA)</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0 0 10px">
          A national directory of licensed immigration attorneys, searchable by location and practice area.
        </p>
        <a href="{AILA_ATTORNEY_FINDER}" target="_blank">{AILA_ATTORNEY_FINDER}</a>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
