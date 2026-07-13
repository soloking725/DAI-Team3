"""
Renders the Vera visa timeline: a connected-dot progress list with a
rotated stamp badge for completed steps, an accent outline on the
current step, and grayed-out styling for upcoming ones.
"""

import streamlit as st

from shared.vera_state import mark_step_status

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


def _first_incomplete_index(steps):
    for i, step in enumerate(steps):
        if step["status"] != "complete":
            return i
    return None


def render_timeline(steps: list, allow_complete: bool = True):
    """Render the timeline. If allow_complete, shows a button to mark the current step done."""
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
                f'<span class="{badge_class}">{_STATUS_LABEL[display_status]}</span></div>'
                f'<p class="vera-step-detail">{step["detail"]}</p></div></div>'
            )
            st.markdown(row_html, unsafe_allow_html=True)

            if allow_complete and is_current:
                if st.button("Mark complete", key=f"complete_{step['id']}"):
                    mark_step_status(step["id"], "complete")
                    st.rerun()
