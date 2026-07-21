"""
Your Timeline - Vera's main screen: compact chat on the left,
scrollable visa timeline on the right.
Page: 04_Ask_a_Question.py
"""
import html

import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu, render_disclaimer, render_footer, render_reminders_banner
from shared.reminders import compute_reminders, compute_custom_reminders
from shared.chat_panel import render_chat_panel
from shared.timeline_ui import render_timeline, render_circumstances_card
from shared.timeline import build_timeline, infer_visa_type, enrich_step_with_origin
from shared.vera_state import get_vera_state, set_timeline, add_timeline_steps, persist_vera_state
from shared import auth, db

st.set_page_config(page_icon=FAVICON, page_title="Your Timeline - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

state = get_vera_state()
visa_type = infer_visa_type(state["trip_details"], state.get("profile", {}).get("visa_type"))

# Rendered before the login gate below so the nav (and the way back to
# Home/Privacy/Help) is always reachable, even from the sign-in screen.
render_hamburger_menu(visa_type=visa_type)

# The timeline is per-student persisted state, so it needs a signed-in user in
# hosted mode. No-op in local mode.
user = auth.require_login("Sign in to see your timeline")

name = html.escape((state.get("profile", {}).get("name") or "").strip())
if name:
    st.markdown(f"<p style='font-size:14px;color:var(--text-secondary);margin:0.5rem 0 0'>Welcome back, {name}.</p>", unsafe_allow_html=True)

st.markdown(render_disclaimer(), unsafe_allow_html=True)

college = None
custom_reminders = []
if user and user.get("mode") == "hosted" and user.get("college_id"):
    college = db.get_college(user["college_id"])
    custom_reminders = db.list_custom_reminders(user["college_id"])
    if college and college.get("guide_pdf_url"):
        st.markdown(
            f"📄 [{college.get('name') or 'Your school'}'s visa guide]({college['guide_pdf_url']})"
        )

render_reminders_banner(
    compute_reminders(state.get("post_visa", {})) + compute_custom_reminders(custom_reminders)
)

if user and user.get("mode") == "hosted" and user.get("college_id"):
    events = db.list_upcoming_events(user["college_id"], limit=5)
    announcements = db.list_announcements(user["college_id"], limit=5)
    if events or announcements:
        with st.expander(f"Announcements from {college.get('name') or 'your school'}" if college else "Announcements", expanded=bool(events)):
            for e in events:
                when = e["event_at"][:16].replace("T", " ")
                st.markdown(f"📅 **{when}** — {e['body']}")
            for a in announcements:
                if a.get("event_at"):
                    continue  # already shown above as an event
                st.markdown(f"- **{a['created_at'][:10]}** — {a['body']}")

circumstances = state.get("extenuating_circumstances", {}).get("categories", [])
if circumstances:
    render_circumstances_card(circumstances, visa_type=visa_type)

if not state["timeline"]:
    # Instant, no LLM calls — steps come from the canonical static template,
    # with detail text already filled in from the precomputed enrichment
    # cache (see precompute_timeline_enrichment.py).
    set_timeline(build_timeline(state["trip_details"], state.get("profile", {}).get("visa_type")))
    state = get_vera_state()

# College-wide guide steps the DSO uploaded once for everyone (see
# pages/20_DSO_Dashboard.py) — dedupes by id, so re-running this is harmless,
# but gate on a flag anyway to avoid a disk write on every single rerun.
if college and college.get("guide_steps") and not state.get("_college_guide_applied"):
    add_timeline_steps(college["guide_steps"])
    state = get_vera_state()
    state["_college_guide_applied"] = True
    persist_vera_state()

# The general per-visa-type detail text is generic (precomputed once, shared
# across every student — see build_timeline's docstring). The one place the
# timeline currently reflects *this* student's actual situation is here: the
# first incomplete "interview" step gets a single live, confidence-gated
# rewrite grounded in their own origin country's embassy content (see
# ingest.py's ORIGIN_COUNTRY_SOURCE_URLS), tagged so it only ever runs once.
origin_country = (state.get("trip_details", {}) or {}).get("origin") or ""
current_step = next((s for s in state["timeline"] if s.get("status") != "complete"), None)
if current_step and origin_country and current_step.get("category") == "interview" \
        and not current_step.get("origin_enriched"):
    current_step["detail"] = enrich_step_with_origin(current_step, visa_type, origin_country)
    current_step["origin_enriched"] = True
    persist_vera_state()

total_steps = len(state["timeline"])
done_steps = sum(1 for s in state["timeline"] if s.get("status") == "complete")
if total_steps:
    st.progress(done_steps / total_steps, text=f"{done_steps} of {total_steps} steps complete")

with st.container(key="vera_main_row"):
    left, right = st.columns([1, 2.5], gap="medium")

    with left:
        render_chat_panel()

    with right:
        render_timeline(state["timeline"], visa_type=visa_type)

if user and user.get("mode") == "hosted" and user.get("college_id"):
    dsos = db.get_dso_users(user["college_id"])
    if dsos:
        st.markdown("### Messages from your DSO")
        st.caption(
            "For logistics support, not legal advice — for legal questions, "
            "consult a licensed immigration attorney."
        )
        dso_by_id = {d["id"]: d.get("name") or d.get("email") for d in dsos}
        dso_id = (
            dsos[0]["id"] if len(dsos) == 1
            else st.selectbox("DSO", list(dso_by_id), format_func=lambda uid: dso_by_id[uid])
        )
        for m in db.list_thread(user["college_id"], user["id"], dso_id):
            who = "You" if m["sender_id"] == user["id"] else dso_by_id.get(dso_id, "DSO")
            st.markdown(f"**{who}** · {m['created_at'][:16].replace('T', ' ')}  \n{m['body']}")
        reply = st.text_area("Your message", key="_student_msg_body")
        if st.button("Send") and reply.strip():
            db.send_message(user["college_id"], user["id"], dso_id, reply.strip())
            st.rerun()

st.markdown(render_footer(), unsafe_allow_html=True)
