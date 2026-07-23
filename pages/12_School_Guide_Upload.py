"""
Wizard step between Extenuating Circumstances and the timeline: hands off to
whatever the school's DSO has published, rather than letting a student upload
their own copy of the guide.

Students previously could upload their own PDF here and have Vera extract
steps from it — but the DSO dashboard (pages/20_DSO_Dashboard.py) now does
that once for the whole college, and every student inherits the result
automatically (see pages/04_Ask_a_Question.py's add_timeline_steps call). A
self-serve upload duplicated that work and risked out-of-sync/incorrect
steps a student's own PDF might introduce, so this page no longer accepts
uploads at all — it just tells the student what's coming and lets them
continue.
Page: 12_School_Guide_Upload.py
"""
import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared.vera_state import get_vera_state
from shared import auth, config, db

state = get_vera_state()
render_hamburger_menu(visa_type=state.get("profile", {}).get("visa_type") or "f-1")

st.set_page_config(page_icon=FAVICON, page_title="Your school's visa guide - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

college = None
if config.is_supabase_configured():
    user = auth.require_login("Sign in to continue")
    college = db.get_college(user["college_id"]) if user and user.get("college_id") else None

_, center, _ = st.columns([1, 2, 1])
with center:
    if college and college.get("guide_steps"):
        st.markdown(
            """
            <div style="max-width:460px;margin:1.5rem auto 0;text-align:center">
              <h1 style="margin:0 0 6px">Your school's guide is already added</h1>
              <p style="font-size:14px;color:var(--text-secondary);margin:0">
                Your international office already uploaded a visa guide — its steps
                were added to your timeline automatically.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif college and college.get("guide_pdf_url"):
        st.markdown(
            f"""
            <div style="max-width:460px;margin:1.5rem auto 0;text-align:center">
              <h1 style="margin:0 0 6px">Your school's visa guide</h1>
              <p style="font-size:14px;color:var(--text-secondary);margin:0">
                Your international office shared a guide — you can view it any time
                from your timeline.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button(f"📄 View {college.get('name') or 'your school'}'s visa guide", college["guide_pdf_url"], use_container_width=True)
    else:
        st.markdown(
            """
            <div style="max-width:460px;margin:1.5rem auto 0;text-align:center">
              <h1 style="margin:0 0 6px">Your school's visa guide</h1>
              <p style="font-size:14px;color:var(--text-secondary);margin:0">
                Your international office hasn't added a guide yet. Once they do, any
                extra steps it covers will show up on your timeline automatically —
                no need to do anything here.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Continue to my timeline", use_container_width=True, type="primary"):
        st.switch_page("pages/04_Ask_a_Question.py")
