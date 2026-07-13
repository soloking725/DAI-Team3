"""
Trip details intake — country of origin, destination, and school.
Page: 10_Trip_Details.py
"""
import streamlit as st

from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared.vera_state import set_trip_details

st.set_page_config(page_title="Tell us about your trip - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu()

st.markdown(
    """
    <div style="max-width:420px;margin:2rem auto 0">
    <div style="text-align:center;margin-bottom:22px">
      <h1 style="margin:0 0 6px">Tell us about your trip</h1>
      <p style="font-size:14px;color:var(--text-secondary);margin:0">This helps Vera pull the right forms for your visa.</p>
    </div>
    </div>
    """,
    unsafe_allow_html=True,
)

ORIGIN_OPTIONS = ["", "India", "China", "Nigeria", "Brazil", "South Korea"]
DESTINATION_OPTIONS = ["", "United States", "United Kingdom", "Canada", "Germany", "Australia"]

_, center, _ = st.columns([1, 2, 1])
with center:
    with st.form("trip_details_form"):
        origin = st.selectbox("Country of origin", options=ORIGIN_OPTIONS, index=0)
        destination = st.selectbox("Country you're traveling to", options=DESTINATION_OPTIONS, index=0)
        school = st.text_input("School", placeholder="Search for your school")

        st.markdown(
            """
            <div style="background:var(--surface-1);border-radius:12px;padding:12px 14px;
                        display:flex;gap:10px;align-items:flex-start;margin:4px 0">
                <i class="ti ti-info-circle" style="font-size:16px;color:var(--text-muted);margin-top:2px"></i>
                <p style="font-size:13px;color:var(--text-secondary);margin:0">
                    Vera uses this to match you with the right visa type, like F-1, and the exact forms your country requires.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("Continue", use_container_width=True, type="primary")

    if submitted:
        if not destination or not school.strip():
            st.error("Please select a destination and enter your school.")
        else:
            set_trip_details(origin, destination, school.strip())
            st.switch_page("pages/12_School_Guide_Upload.py")
