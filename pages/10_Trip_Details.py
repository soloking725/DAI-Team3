"""
Trip details intake — country of origin, destination, and school.
Page: 10_Trip_Details.py
"""
import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared import auth
from shared.vera_state import get_vera_state, set_trip_details, set_profile
from shared.countries import ORIGIN_OPTIONS, DESTINATION_COUNTRIES
from shared.schools import SCHOOL_OPTIONS, OTHER

st.set_page_config(page_icon=FAVICON, page_title="Tell us about your trip - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

state = get_vera_state()
_profile = state.get("profile", {})
_trip = state.get("trip_details", {})

# Rendered before the login gate below so the nav is always reachable, even
# from the sign-in screen.
render_hamburger_menu(visa_type=_profile.get("visa_type") or "f-1")

# Onboarding is the first point where we persist anything, so it's where login is
# required in hosted mode. No-op in local mode.
auth.require_login("Sign in to start your timeline")

# app.py's "Get started" button decides where to route a visitor (here vs.
# straight to the timeline) based on whether they already have a profile —
# but in hosted mode, before login, that check runs against an anonymous,
# always-empty state (login hasn't happened yet, so there's no way to know
# about a returning student's real saved profile). That misroutes every
# returning student back through onboarding on every fresh session. Now that
# login has just resolved above, _profile reflects their real saved data, so
# catch the misroute here: if they already completed this step before, skip
# straight to their timeline instead of asking them to redo it. The one
# legitimate reason to see this form again despite already having a profile —
# explicitly clicking "Update my trip details" from the unsupported-visa-type
# page — sets _editing_trip_details first, so that path isn't caught by this.
if (
    _profile.get("name")
    and _profile.get("visa_type")
    and not st.session_state.pop("_editing_trip_details", False)
):
    st.switch_page("pages/04_Ask_a_Question.py")

st.markdown(
    """
    <div style="max-width:420px;margin:2rem auto 0">
    <div style="text-align:center;margin-bottom:22px">
      <h1 style="margin:0 0 6px">Tell us about your trip</h1>
      <p style="font-size:14px;color:var(--text-secondary);margin:0">This helps Vera personalize your timeline and pull the right forms.</p>
    </div>
    </div>
    """,
    unsafe_allow_html=True,
)

VISA_TYPE_OPTIONS = [
    ("", "Select your visa type"),
    ("f-1", "F-1 — Academic student visa"),
    ("h-1b", "H-1B — Specialty occupation worker"),
    ("other", "Other / not sure yet"),
]
STUDENT_VISA_TYPES = {"f-1"}

_, center, _ = st.columns([1, 2, 1])
with center:
    _visa_type_values = [v[0] for v in VISA_TYPE_OPTIONS]
    _visa_index = (
        _visa_type_values.index(_profile.get("visa_type"))
        if _profile.get("visa_type") in _visa_type_values else 0
    )
    _origin_index = (
        ORIGIN_OPTIONS.index(_trip.get("origin"))
        if _trip.get("origin") in ORIGIN_OPTIONS else 0
    )
    _school_value = _trip.get("school") or ""
    _school_index = SCHOOL_OPTIONS.index(_school_value) if _school_value in SCHOOL_OPTIONS else 0
    _school_other_default = _school_value if _school_index == 0 and _school_value else ""

    with st.form("trip_details_form"):
        name = st.text_input(
            "Your name", value=_profile.get("name") or "", placeholder="What should Vera call you?"
        )
        visa_type = st.selectbox(
            "Visa type you're pursuing",
            options=_visa_type_values,
            format_func=lambda v: dict(VISA_TYPE_OPTIONS)[v],
            index=_visa_index,
        )
        origin = st.selectbox("Country of origin", options=ORIGIN_OPTIONS, index=_origin_index)
        destination = st.selectbox(
            "Country you're traveling to", options=DESTINATION_COUNTRIES, index=0,
            disabled=True, help="Other destinations aren't supported yet.",
        )
        school_choice = st.selectbox(
            "School (if applicable)",
            options=SCHOOL_OPTIONS,
            index=_school_index,
            format_func=lambda s: s or "Select your school",
            help="Leave blank if this doesn't apply to your visa type.",
        )
        # Shown unconditionally rather than only when "Other" is picked: this is
        # inside st.form, which doesn't rerun on widget change, so a conditional
        # field wouldn't appear until after submit.
        school_other = st.text_input(
            "If your school isn't listed, type it here",
            value=_school_other_default,
            placeholder="Your school's name",
        )

        st.markdown(
            """
            <div style="background:var(--surface-1);border-radius:12px;padding:12px 14px;
                        display:flex;gap:10px;align-items:flex-start;margin:4px 0">
                <i class="ti ti-info-circle" style="font-size:16px;color:var(--text-muted);margin-top:2px"></i>
                <p style="font-size:13px;color:var(--text-secondary);margin:0">
                    Vera currently supports F-1 student visas to the United States in full detail.
                    Other visa types and destinations are recognized, but content for them is still on the way.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        submitted = st.form_submit_button("Continue", use_container_width=True, type="primary")

    if submitted:
        # A typed-in school wins over the dropdown, so picking "Other" and typing
        # a name works, and so does typing a name without touching the dropdown.
        school = school_other.strip() or (
            "" if school_choice in ("", OTHER) else school_choice
        )
        needs_school = visa_type in STUDENT_VISA_TYPES
        if not visa_type or not destination or (needs_school and not school):
            st.error(
                "Please select a visa type and a destination"
                + (", and enter your school." if needs_school else ".")
            )
        else:
            set_trip_details(origin, destination, school)
            set_profile(name.strip(), visa_type)

            is_supported = visa_type in STUDENT_VISA_TYPES and destination == "United States"
            if is_supported:
                st.switch_page("pages/11_Extenuating_Circumstances.py")
            else:
                st.switch_page("pages/16_Other_Visa_Coming_Soon.py")
