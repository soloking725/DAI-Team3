"""
Renders the Vera visa timeline: a connected-dot progress list with a
rotated stamp badge for completed steps, an accent outline on the
current step, and grayed-out styling for upcoming ones.
"""

import streamlit as st

from shared.vera_state import mark_step_status
from shared.circumstances import CIRCUMSTANCE_LABELS, CIRCUMSTANCE_QUERIES
from shared.retrieval import retrieve_context
from shared.safeguards import check_confidence

CIRCUMSTANCES_CARD_CSS = """
<style>
    .vera-circ-card {
        background:#fffbeb; border:0.5px solid #f6e05e; border-left:3px solid #d69e2e;
        border-radius:12px; padding:12px 14px; margin-bottom:16px;
    }
    .vera-circ-card h4 { margin:0 0 6px; font-size:13px; color:#975a16; }
    .vera-circ-card p { margin:0 0 4px; font-size:12px; color:#7b4b12; line-height:1.5; }
</style>
"""


def render_circumstances_card(categories: list, visa_type: str = "f-1"):
    """Grounded, confidence-gated guidance for any extenuating circumstances the
    user flagged at onboarding. Never fabricates — falls back to a plain
    'see the source pages' pointer when retrieval isn't confident, same
    safeguard pattern as shared/timeline.py's step enrichment."""
    if not categories:
        return

    st.markdown(CIRCUMSTANCES_CARD_CSS, unsafe_allow_html=True)
    for cat_id in categories:
        label = CIRCUMSTANCE_LABELS.get(cat_id, cat_id)
        query = CIRCUMSTANCE_QUERIES.get(cat_id, label)
        retrieval = retrieve_context(query, top_k=3, visa_type=visa_type, distance_threshold=1.2)
        if retrieval.get("found") and check_confidence(retrieval.get("distances", [])):
            sources = retrieval.get("sources", [])
            source_note = f" (see: {sources[0]['title']})" if sources else ""
            body = (
                f"Because you flagged \"{label}\", Vera has relevant official guidance available"
                f"{source_note} — ask Vera about it in the chat for details."
            )
        else:
            body = (
                f"You flagged \"{label}\". Vera doesn't have specific official guidance indexed for this yet — "
                "for anything involving a prior denial, SEVIS issue, or hardship, consider consulting a licensed "
                "immigration attorney."
            )
        st.markdown(
            f"""<div class="vera-circ-card"><h4>{label}</h4><p>{body}</p></div>""",
            unsafe_allow_html=True,
        )

TIMELINE_CSS = """
<style>
    .vera-step-row { display:grid; grid-template-columns:32px 1fr; gap:12px; position:relative; padding-bottom:22px; }
    .vera-step-row:last-child { padding-bottom:0; }
    .vera-step-dot-col { position:relative; display:flex; justify-content:center; }
    .vera-step-line { position:absolute; top:28px; bottom:-22px; width:2px; background:var(--border); }
    .vera-step-dot {
        width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center;
        border:0.5px solid var(--border); background:var(--surface-1);
    }
    .vera-step-dot i { font-size:15px; color:var(--text-muted); }
    .vera-step-dot-complete { background:var(--bg-success); border:none; transform:rotate(-6deg); }
    .vera-step-dot-complete i { color:var(--text-success); }
    .vera-step-dot-current { background:var(--bg-accent); border:none; }
    .vera-step-dot-current i { color:var(--text-accent); }
    .vera-step-card {
        background:var(--surface-2); border:0.5px solid var(--border); border-radius:12px; padding:12px 14px;
    }
    .vera-step-card-current { border:0.5px solid var(--border-accent); }
    .vera-step-card-upcoming .vera-step-title { color:var(--text-muted); }
    .vera-step-title-row { display:flex; justify-content:space-between; align-items:center; gap:8px; }
    .vera-step-title { font-weight:500; font-size:14px; margin:0; }
    .vera-step-badge { font-size:12px; padding:2px 10px; border-radius:var(--radius); white-space:nowrap; }
    .vera-step-badge-complete { background:var(--bg-success); color:var(--text-success); }
    .vera-step-badge-current { background:var(--bg-accent); color:var(--text-accent); }
    .vera-step-badge-upcoming { background:var(--surface-1); color:var(--text-muted); }
    .vera-step-detail { font-size:12px; color:var(--text-muted); margin:4px 0 0; }
</style>
"""

_STATUS_LABEL = {"complete": "Complete", "current": "In progress", "upcoming": "Upcoming"}
_STATUS_ICON = {"complete": "ti-check", "current": None, "upcoming": None}

STEP_DETAILS_CARD_CSS = """
<style>
    .vera-step-details-card {
        background:var(--surface-1); border:0.5px solid var(--border); border-radius:12px;
        padding:10px 14px; margin:-14px 0 18px 44px; font-size:12px; color:var(--text-secondary);
    }
    .vera-step-details-card p { margin:0 0 6px; line-height:1.5; }
    .vera-step-details-card a { color:var(--text-accent); }
</style>
"""


def _first_incomplete_index(steps):
    for i, step in enumerate(steps):
        if step["status"] != "complete":
            return i
    return None


def render_step_details(step: dict, visa_type: str = "f-1"):
    """Grounded, confidence-gated extra content for a timeline step — practice
    interview guidance for interview-category steps, and/or a link to the real
    official form when the step has one. Never fabricates questions or forms;
    falls back to a plain pointer when retrieval isn't confident, same pattern
    as render_circumstances_card."""
    st.markdown(STEP_DETAILS_CARD_CSS, unsafe_allow_html=True)
    parts = []

    if step.get("static_detail_html"):
        parts.append(step["static_detail_html"])

    if step.get("category") == "interview":
        retrieval = retrieve_context(
            "visa interview preparation topics", top_k=3, visa_type=visa_type,
            category="interview_prep", distance_threshold=1.2,
        )
        if retrieval.get("found") and check_confidence(retrieval.get("distances", [])):
            sources = retrieval.get("sources", [])
            source_note = f" (see: {sources[0]['title']})" if sources else ""
            parts.append(
                f"<p><strong>Practice interview prep:</strong> Be ready to discuss your study plans and school "
                f"choice, how you'll fund your studies, and your ties to your home country{source_note} — "
                f"ask Vera in the chat for more detail grounded in official sources.</p>"
            )
        else:
            parts.append(
                "<p><strong>Practice interview prep:</strong> Vera doesn't have specific guidance indexed for "
                "this yet — the State Department's travel.state.gov and your school's international student "
                "office are the best places to check.</p>"
            )

    if step.get("form_url"):
        form_name = step.get("form_name") or "the official form"
        parts.append(f'<p><a href="{step["form_url"]}" target="_blank">Go to {form_name} ↗</a></p>')

    if parts:
        st.markdown(f'<div class="vera-step-details-card">{"".join(parts)}</div>', unsafe_allow_html=True)


@st.fragment
def render_timeline(steps: list, allow_complete: bool = True, visa_type: str = "f-1"):
    """Render the timeline. If allow_complete, shows a button to mark the current step done.

    Wrapped in @st.fragment (fragment-scoped reruns below) so that "Details"
    / "Mark complete" clicks don't trigger a full-page rerun — a full rerun
    here would interrupt the chat panel's own fragment mid-flight (see
    shared/chat_panel.py), abandoning an in-progress answer and leaving
    is_processing stuck True.
    """
    st.markdown(TIMELINE_CSS, unsafe_allow_html=True)

    current_idx = _first_incomplete_index(steps)

    with st.container(height=480, border=False):
        for i, step in enumerate(steps):
            status = step["status"]
            is_current = i == current_idx and status != "complete"
            display_status = "current" if is_current else status
            icon = "ti-check" if status == "complete" else step["icon"]

            dot_class = "vera-step-dot"
            if status == "complete":
                dot_class += " vera-step-dot-complete"
            elif is_current:
                dot_class += " vera-step-dot-current"

            card_class = "vera-step-card"
            if is_current:
                card_class += " vera-step-card-current"
            elif display_status == "upcoming":
                card_class += " vera-step-card-upcoming"

            badge_class = f"vera-step-badge vera-step-badge-{display_status}"
            is_last = i == len(steps) - 1
            line_html = "" if is_last else '<div class="vera-step-line"></div>'

            # Built as one unbroken line: a blank, indented line here would be
            # parsed by CommonMark as an indented code block and escaped verbatim.
            row_html = (
                f'<div class="vera-step-row">'
                f'<div class="vera-step-dot-col">{line_html}'
                f'<div class="{dot_class}"><i class="ti {icon}"></i></div></div>'
                f'<div class="{card_class}"><div class="vera-step-title-row">'
                f'<p class="vera-step-title">{step["title"]}</p>'
                f'<span class="{badge_class}">{_STATUS_LABEL.get(display_status, display_status.title())}</span></div>'
                f'<p class="vera-step-detail">{step["detail"]}</p></div></div>'
            )
            st.markdown(row_html, unsafe_allow_html=True)

            has_details = (
                step.get("category") == "interview"
                or step.get("form_url")
                or step.get("static_detail_html")
            )
            if has_details:
                open_key = f"vera_step_open_{step['id']}"
                is_open = st.session_state.get(open_key, False)
                if st.button("Details" if not is_open else "Hide details", key=f"details_{step['id']}"):
                    st.session_state[open_key] = not is_open
                    st.rerun(scope="fragment")
                if is_open:
                    render_step_details(step, visa_type=visa_type)

            if allow_complete and is_current:
                if st.button("Mark complete", key=f"complete_{step['id']}"):
                    mark_step_status(step["id"], "complete")
                    st.rerun(scope="fragment")
            elif allow_complete and status == "complete":
                if st.button("Undo", key=f"undo_{step['id']}"):
                    mark_step_status(step["id"], "upcoming")
                    st.rerun(scope="fragment")
