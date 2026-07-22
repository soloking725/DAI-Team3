"""
DSO dashboard (B2B) — roster, per-student step override, announcements.
Page: 20_DSO_Dashboard.py

Admin-only: reachable only by users whose role is 'dso'. The 20-29 page range is
reserved for admin/DSO pages; this page is intentionally not in the hamburger
menu, so students never see it. Requires hosted mode (Supabase configured).
"""
import csv
import datetime
import io

import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared import config, auth, db
from shared.timeline_data import TIMELINE_TEMPLATES
from shared.pdf_guide import extract_steps_from_pdf, PdfExtractionError
from shared.config import MAX_PDF_UPLOAD_MB

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

st.markdown("#### Extra steps from your guide PDF")
st.caption(
    "Upload your school's visa guide once here — Vera extracts any explicit "
    "action items and every student at your college gets them added to their "
    "timeline automatically, instead of each student uploading their own copy."
)
existing_guide_steps = current_college.get("guide_steps") or []
if existing_guide_steps:
    st.caption(f"Currently live for your students: {len(existing_guide_steps)} step(s).")
    with st.expander("View current steps"):
        for s in existing_guide_steps:
            st.markdown(f"- **{s['title']}** — {s['detail']}")

dso_guide_pdf = st.file_uploader("Guide PDF", type=["pdf"], key="_dso_guide_pdf")
if dso_guide_pdf is not None and st.session_state.get("_dso_last_guide_name") != dso_guide_pdf.name:
    if dso_guide_pdf.size > MAX_PDF_UPLOAD_MB * 1024 * 1024:
        st.session_state["_dso_extracted_steps"] = None
        st.error(f"That PDF is too large (max {MAX_PDF_UPLOAD_MB}MB). Try a smaller file.")
    else:
        with st.spinner("Reading the guide..."):
            try:
                st.session_state["_dso_extracted_steps"] = extract_steps_from_pdf(dso_guide_pdf)
            except PdfExtractionError as e:
                st.session_state["_dso_extracted_steps"] = None
                st.error(str(e))
    st.session_state["_dso_last_guide_name"] = dso_guide_pdf.name

_dso_extracted = st.session_state.get("_dso_extracted_steps")
if _dso_extracted:
    st.caption("Found these steps — uncheck any that shouldn't apply to every student:")
    _selected_guide_steps = []
    for step in _dso_extracted:
        page_note = f", per page {step['page_hint']}" if step.get("page_hint") else ""
        checked = st.checkbox(
            step["title"], value=True, key=f"_dso_guide_step_{step['id']}",
            help=f"{step['detail']}{page_note}",
        )
        if checked:
            _selected_guide_steps.append(step)
    if st.button("Publish to all students", type="primary") and _selected_guide_steps:
        db.set_college_guide_steps(college_id, _selected_guide_steps)
        st.success(f"Published {len(_selected_guide_steps)} step(s) to every student at your college.")
        st.session_state["_dso_extracted_steps"] = None
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

def _csv_formula_safe(value):
    """Prefix values that Excel/Sheets would interpret as a formula (e.g. a
    student setting their display name to '=HYPERLINK(...)') with a leading
    apostrophe so they're treated as inert text when the DSO opens the CSV."""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@"):
        return "'" + text
    return text


_csv_buf = io.StringIO()
_writer = csv.DictWriter(
    _csv_buf,
    fieldnames=["user_id", "name", "email", "visa_type", "origin_country", "current_step_key",
                "current_step_status", "flagged", "updated_at"],
)
_writer.writeheader()
_writer.writerows(
    {k: _csv_formula_safe(v) for k, v in row.items()} for row in filtered
)
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

# --- Graduation: anonymize + delete --------------------------------------
st.markdown("### Graduate an entire class")
st.caption(
    "Graduates every student whose graduation year matches — same anonymize-then-delete "
    "as below, applied to the whole cohort at once. Students who never entered a "
    "graduation year (accounts from before this field existed) aren't included here; "
    "graduate them individually below instead."
)
_grad_years = sorted({r["graduation_year"] for r in roster if r.get("graduation_year")})
if _grad_years:
    gy1, gy2 = st.columns([2, 1])
    with gy1:
        bulk_grad_year = st.selectbox("Graduation year", _grad_years, key="_bulk_grad_year")
    _matching = sum(1 for r in roster if r.get("graduation_year") == bulk_grad_year)
    st.caption(f"{_matching} student(s) have graduation year {bulk_grad_year}.")
    confirm_bulk_grad = st.checkbox(
        f"I understand this permanently deletes all {_matching} matching accounts after "
        "archiving anonymized stats.",
        key="_bulk_grad_confirm",
    )
    if st.button("Graduate this class", disabled=not confirm_bulk_grad):
        graduated_count = db.bulk_graduate_by_year(college_id, bulk_grad_year)
        st.success(f"Graduated {graduated_count} student(s) with graduation year {bulk_grad_year}.")
        st.rerun()
else:
    st.caption("No students have a graduation year on file yet.")

st.markdown("### Mark a student graduated")
st.caption(
    "For one-off cases (e.g. an account from before graduation year was collected) — "
    "records this student's anonymized cohort stats (visa type, origin country, final "
    "step reached, whether they had flagged circumstances — no name, email, or account "
    "id) for your school to learn from, then permanently deletes their individual "
    "account. This can't be undone."
)
grad_student = st.selectbox(
    "Student", list(name_by_id), format_func=lambda uid: name_by_id[uid], key="_grad_student"
)
confirm_grad = st.checkbox(
    "I understand this permanently deletes this student's account after archiving anonymized stats.",
    key="_grad_confirm",
)
if st.button("Mark graduated & anonymize", disabled=not confirm_grad):
    if db.graduate_and_anonymize(grad_student, college_id):
        st.success(f"Archived anonymized stats for {name_by_id[grad_student]} and deleted their account.")
        st.rerun()
    else:
        st.error("Couldn't complete this — the student may already be gone.")

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

# --- Announcements & events -----------------------------------------------
st.markdown("### Post an announcement or event")
st.caption(
    "Students see these on their timeline. Check the box below to post it as a dated "
    "event (an info session, a Q&A) instead of a plain announcement — events show "
    "separately, soonest first."
)
body = st.text_area("Message", placeholder="e.g. Reminder: SEVIS fee is due before your interview.")
is_event = st.checkbox("This is an event (has a date/time)")
event_at_iso = None
if is_event:
    ec1, ec2 = st.columns(2)
    with ec1:
        event_date = st.date_input("Event date", value=datetime.date.today())
    with ec2:
        event_time = st.time_input("Event time", value=datetime.time(12, 0))
    event_at_iso = datetime.datetime.combine(event_date, event_time).isoformat()
if st.button("Post") and body.strip():
    db.post_announcement(college_id, user["id"], body.strip(), event_at=event_at_iso)
    st.success("Posted.")
    st.rerun()

for a in db.list_announcements(college_id, limit=5):
    when = f" · event: {a['event_at'][:16].replace('T', ' ')}" if a.get("event_at") else ""
    st.markdown(f"- **{a['created_at'][:10]}**{when} — {a['body']}")

# --- Custom reminders --------------------------------------------------
st.markdown("### Post a reminder for students")
st.caption(
    "For anything specific your school needs students to do by a date — reporting "
    "enrolled courses, an OPT check-in, a program-extension deadline. Shows as an "
    "in-account banner as the due date approaches, same as the built-in visa/passport "
    "expiration reminders. In-account only — no email/SMS yet."
)
_reminder_templates = {
    "Custom...": ("", ""),
    "Report your enrolled courses": (
        "Report your enrolled courses",
        "Confirm your current course load with your DSO so your SEVIS enrollment record stays accurate.",
    ),
    "OPT unemployment limit check-in": (
        "OPT unemployment limit check-in",
        "F-1 OPT allows a maximum of 90 days of unemployment during your initial 12-month OPT period (150 days total if you have a STEM extension). Report your employment status to your DSO.",
    ),
    "STEM OPT extension filing window": (
        "STEM OPT extension filing window",
        "STEM OPT extensions must be filed before your current OPT authorization expires — start the I-983 Training Plan process with your DSO now.",
    ),
    "Program extension request": (
        "Program extension request",
        "If you won't complete your program by your I-20 end date, request a program extension from your DSO before that date passes.",
    ),
    "Get a travel signature before departing": (
        "Get a travel signature on your I-20",
        "Your I-20 needs a current travel signature from your DSO before any international travel — it's valid for 1 year (6 months while on OPT).",
    ),
}
_template_choice = st.selectbox("Start from a template (optional)", list(_reminder_templates))
_tmpl_title, _tmpl_detail = _reminder_templates[_template_choice]
rc1, rc2 = st.columns(2)
with rc1:
    reminder_title = st.text_input("Title", value=_tmpl_title, key="_reminder_title")
with rc2:
    reminder_due = st.date_input("Due date", value=datetime.date.today(), key="_reminder_due")
reminder_detail = st.text_area("Detail", value=_tmpl_detail, key="_reminder_detail")
if st.button("Post reminder") and reminder_title.strip() and reminder_detail.strip():
    db.create_custom_reminder(college_id, user["id"], reminder_title.strip(), reminder_detail.strip(), reminder_due.isoformat())
    st.success("Posted.")
    st.rerun()

_existing_reminders = db.list_custom_reminders(college_id)
if _existing_reminders:
    st.caption("Active reminders:")
    for r in _existing_reminders:
        rcol1, rcol2 = st.columns([5, 1])
        with rcol1:
            st.markdown(f"- **{r['title']}** — due {r['due_date']}  \n  {r['detail']}")
        with rcol2:
            if st.button("Remove", key=f"_rm_reminder_{r['id']}"):
                db.delete_custom_reminder(r["id"], college_id)
                st.rerun()
