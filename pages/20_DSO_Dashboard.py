"""
DSO dashboard (B2B) — roster, per-student step override, announcements.
Page: 20_DSO_Dashboard.py

Admin-only: reachable only by users whose role is 'dso'. The 20-29 page range is
reserved for admin/DSO pages; this page is intentionally not in the hamburger
menu, so students never see it. Requires hosted mode (Supabase configured).
"""
import csv
import io

import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared import config, auth, db
from shared.timeline_data import TIMELINE_TEMPLATES

st.set_page_config(page_icon=FAVICON, page_title="DSO Dashboard - Vera", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)
render_hamburger_menu()

# --- Access gate ---------------------------------------------------------
if not config.is_supabase_configured():
    st.info(
        "The DSO dashboard needs the hosted backend. Set SUPABASE_URL, "
        "SUPABASE_ANON_KEY, and SUPABASE_SERVICE_KEY (see migrations/README.md)."
    )
    st.stop()

if not auth.is_logged_in():
    auth.render_login("Sign in — DSO access")
    st.stop()

user = auth.require_role("dso")
college_id = user["college_id"]

# Log that this DSO opened the roster — once per session, not on every rerun
# (every filter/widget interaction reruns the whole script).
if not st.session_state.get("_dso_roster_view_logged"):
    db.write_audit(user["id"], "view_roster", college_id)
    st.session_state["_dso_roster_view_logged"] = True

# --- Header --------------------------------------------------------------
st.markdown(f"## {user.get('college_name') or 'Your college'} — student roster")
st.caption(f"Signed in as {user['email']} · DSO")
if st.button("Log out"):
    auth.logout()
    st.rerun()

# --- School visa guide -----------------------------------------------------
st.markdown("### School visa guide")
st.caption("Link to your school's official visa guide (PDF or webpage) — students see it on their timeline.")
current_college = db.get_college(college_id) or {}
guide_url = st.text_input(
    "Guide URL",
    value=current_college.get("guide_pdf_url") or "",
    placeholder="https://your-school.edu/international/f1-guide.pdf",
)
if st.button("Save guide link") and guide_url.strip():
    db.set_college_guide_url(college_id, guide_url.strip())
    st.success("Saved.")
    st.rerun()

roster = db.list_students(college_id)
if not roster:
    st.info("No students have signed in yet.")
    st.stop()

# --- Summary stats ---------------------------------------------------------
visa_counts = {}
for r in roster:
    key = r["visa_type"] or "Unspecified"
    visa_counts[key] = visa_counts.get(key, 0) + 1
flagged_total = sum(1 for r in roster if r["flagged"])

s1, s2, s3 = st.columns(3)
s1.metric("Total students", len(roster))
s2.metric("Flagged circumstances", flagged_total)
s3.metric("Visa types", ", ".join(f"{k} ({v})" for k, v in sorted(visa_counts.items())) or "—")

# --- Filters -------------------------------------------------------------
search = st.text_input("Search by name or email", placeholder="e.g. jane@colby.edu")
c1, c2, c3 = st.columns(3)
with c1:
    step_options = ["All"] + sorted({r["current_step_key"] for r in roster if r["current_step_key"]})
    step_filter = st.selectbox("Current step", step_options)
with c2:
    status_options = ["All"] + sorted({r["current_step_status"] for r in roster if r["current_step_status"]})
    status_filter = st.selectbox("Step status", status_options)
with c3:
    only_flagged = st.checkbox("Only flagged circumstances")

search_lower = search.strip().lower()
filtered = [
    r for r in roster
    if (step_filter == "All" or r["current_step_key"] == step_filter)
    and (status_filter == "All" or r["current_step_status"] == status_filter)
    and (not only_flagged or r["flagged"])
    and (not search_lower or search_lower in r["name"].lower() or search_lower in r["email"].lower())
]

flagged_count = sum(1 for r in filtered if r["flagged"])
st.caption(f"{len(filtered)} of {len(roster)} students shown · {flagged_count} with flagged circumstances")

st.dataframe(
    [
        {
            "Name": r["name"],
            "Email": r["email"],
            "Visa": r["visa_type"],
            "Origin": r["origin_country"],
            "Current step": r["current_step_key"],
            "Status": r["current_step_status"],
            "Flagged": "⚑" if r["flagged"] else "",
            "Updated": r["updated_at"][:10] if r["updated_at"] else "",
        }
        for r in filtered
    ],
    use_container_width=True,
    hide_index=True,
)

_csv_buf = io.StringIO()
_writer = csv.DictWriter(
    _csv_buf,
    fieldnames=["name", "email", "visa_type", "origin_country", "current_step_key",
                "current_step_status", "flagged", "updated_at"],
)
_writer.writeheader()
_writer.writerows(filtered)
st.download_button(
    "Export shown roster (CSV)",
    data=_csv_buf.getvalue(),
    file_name="roster.csv",
    mime="text/csv",
)

# --- Per-student step override ------------------------------------------
st.markdown("### Update a student's step")
name_by_id = {r["user_id"]: f"{r['name'] or r['email']}" for r in roster}
sel_student = st.selectbox(
    "Student", list(name_by_id), format_func=lambda uid: name_by_id[uid]
)
sel_visa = next((r["visa_type"] for r in roster if r["user_id"] == sel_student), "") or "f-1"
template = TIMELINE_TEMPLATES.get(sel_visa, TIMELINE_TEMPLATES.get("f-1", []))
step_ids = [s["id"] for s in template]
oc1, oc2 = st.columns(2)
with oc1:
    sel_step = st.selectbox("Step", step_ids) if step_ids else None
with oc2:
    # "current" isn't a stored status — it's computed as the first incomplete
    # step — so the only statuses a DSO can set are these two.
    sel_status = st.selectbox("Set status to", ["upcoming", "complete"])
if sel_step and st.button("Apply override"):
    changed = db.dso_override_step(user["id"], college_id, sel_student, sel_step, sel_status)
    if changed:
        st.success(f"Updated {name_by_id[sel_student]} · {sel_step} → {sel_status}")
    else:
        st.warning(f"No change made — {name_by_id[sel_student]} has no '{sel_step}' step yet.")
    st.rerun()

# --- Direct message to a student ------------------------------------------
st.markdown("### Message a student")
st.caption(
    "For logistics support, not legal advice — for legal questions, direct the "
    "student to a licensed immigration attorney."
)
msg_student = st.selectbox(
    "Student", list(name_by_id), format_func=lambda uid: name_by_id[uid], key="_msg_student"
)
for m in db.list_thread(college_id, user["id"], msg_student):
    who = "You" if m["sender_id"] == user["id"] else name_by_id.get(msg_student, "Student")
    st.markdown(f"**{who}** · {m['created_at'][:16].replace('T', ' ')}  \n{m['body']}")
msg_body = st.text_area("Message", key="_msg_body", placeholder="e.g. Please stop by the office to sign your I-20.")
if st.button("Send message") and msg_body.strip():
    db.send_message(college_id, user["id"], msg_student, msg_body.strip())
    st.rerun()

# --- Announcements -------------------------------------------------------
st.markdown("### Post an announcement")
st.caption("Students see the latest announcements on their timeline.")
body = st.text_area("Message", placeholder="e.g. Reminder: SEVIS fee is due before your interview.")
if st.button("Post announcement") and body.strip():
    db.post_announcement(college_id, user["id"], body.strip())
    st.success("Posted.")
    st.rerun()

for a in db.list_announcements(college_id, limit=5):
    st.markdown(f"- **{a['created_at'][:10]}** — {a['body']}")
