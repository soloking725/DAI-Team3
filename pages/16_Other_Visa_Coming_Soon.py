"""
Shown when a user's visa type or destination isn't one Vera has full
content for yet (currently: F-1/J-1/M-1 to the United States).
Page: 16_Other_Visa_Coming_Soon.py
"""
import streamlit as st

from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu, render_source_citations
from shared.vera_state import get_vera_state

st.set_page_config(page_title="Coming soon - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

state = get_vera_state()
profile = state.get("profile", {})
trip = state.get("trip_details", {})
visa_type = profile.get("visa_type") or ""
destination = trip.get("destination") or ""
name = (profile.get("name") or "").strip()

render_hamburger_menu(visa_type=visa_type or "f-1")

VISA_LABELS = {"h-1b": "H-1B", "other": "that visa type"}
visa_label = VISA_LABELS.get(visa_type, "that visa type")

greeting = f"Hi {name}, " if name else ""
support_phrase = ("Support for " + visa_label) if visa_type else "Support for other visa types"
destination_phrase = " and destinations outside the US" if destination and destination != "United States" else ""
# Built as one concatenated string (not a multi-line f-string) — a conditional
# piece resolving to "" mid-block would otherwise leave a whitespace-only line,
# which CommonMark parses as an indented code block (see CLAUDE.md).
body = (
    f"{greeting}Vera currently gives full, sourced guidance for F-1, J-1, and M-1 student visas "
    f"to the United States. {support_phrase}{destination_phrase} is on the roadmap, but isn't ready "
    "yet — Vera won't guess at steps or requirements it can't verify."
)

st.markdown(
    f"""
    <div style="max-width:560px;margin:2rem auto 0;text-align:center">
      <div style="width:52px;height:52px;border-radius:50%;background:var(--bg-accent);
                  display:flex;align-items:center;justify-content:center;margin:0 auto 14px">
        <i class="ti ti-hourglass" style="font-size:26px;color:var(--text-accent)"></i>
      </div>
      <h1 style="margin:0 0 8px">Vera doesn't cover this yet</h1>
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6">{body}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 2, 1])
with center:
    if visa_type == "h-1b":
        st.markdown(
            render_source_citations([
                {
                    "url": "https://www.uscis.gov/working-in-the-united-states/h-1b-specialty-occupations",
                    "title": "USCIS - H-1B Specialty Occupations",
                    "agency": "USCIS",
                    "section": "Overview",
                },
            ]),
            unsafe_allow_html=True,
        )
    st.markdown(
        """
        <p style="font-size:13px;color:var(--text-muted);text-align:center;margin-top:12px">
            Meanwhile, you can still explore Vera's F-1/J-1/M-1 guidance and forms from the menu,
            or update your visa type in Settings if this was a mistake.
        </p>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Update my trip details", use_container_width=True):
        st.switch_page("pages/10_Trip_Details.py")
