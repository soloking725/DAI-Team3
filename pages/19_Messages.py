"""
Messages: direct messages with your DSO, and announcements/events from your
school — split out of the timeline page so neither has to compete with chat
+ timeline for scroll space.
Page: 19_Messages.py
"""
import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu, render_footer
from shared.messaging_ui import render_inbox
from shared import auth, db

st.set_page_config(page_icon=FAVICON, page_title="Messages - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu()

user = auth.require_login("Sign in to see your messages")

st.markdown("## Messages")

messages_tab, announcements_tab = st.tabs(["Messages", "Announcements"])

with messages_tab:
    if user and user.get("mode") == "hosted" and user.get("college_id"):
        dsos = db.get_dso_users(user["college_id"])
        if dsos:
            st.caption(
                "For logistics support, not legal advice — for legal questions, "
                "consult a licensed immigration attorney."
            )
            render_inbox(
                college_id=user["college_id"],
                current_user_id=user["id"],
                counterparts=dsos,
                state_key="student_inbox",
            )
        else:
            st.caption("No DSO is set up for your school yet.")
    else:
        st.caption("Messaging needs the hosted backend.")

with announcements_tab:
    college = None
    if user and user.get("mode") == "hosted" and user.get("college_id"):
        college = db.get_college(user["college_id"])
        events = db.list_upcoming_events(user["college_id"], limit=5)
        announcements = db.list_announcements(user["college_id"], limit=5)
        if events or announcements:
            st.caption(f"From {college.get('name') or 'your school'}" if college else "")
            for e in events:
                when = e["event_at"][:16].replace("T", " ")
                st.markdown(f"📅 **{when}** — {e['body']}")
            for a in announcements:
                if a.get("event_at"):
                    continue  # already shown above as an event
                st.markdown(f"- **{a['created_at'][:10]}** — {a['body']}")
        else:
            st.caption("No announcements yet.")
    else:
        st.caption("Announcements need the hosted backend.")

st.markdown(render_footer(), unsafe_allow_html=True)
