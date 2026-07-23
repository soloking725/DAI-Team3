"""
Shared DSO<->student inbox UI: a recency-sorted conversation list with unread
badges, plus a bounded/scrollable thread + length-limited composer.

Used by both pages/20_DSO_Dashboard.py and pages/04_Ask_a_Question.py so
neither duplicates the old pattern (a bare st.selectbox you had to already
know the answer to before any message became visible, and an unbounded
st.markdown loop with no scroll container or length limit — see the removed
inline blocks this replaces).
"""

import html

import streamlit as st

from shared import db

MESSAGING_CSS = """
<style>
    .vera-msg-name { font-size:14px; margin:0; }
    .vera-msg-name-unread { font-weight:700; }
    .vera-msg-preview { font-size:12px; color:var(--text-secondary); margin:0;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .vera-msg-dot { display:inline-block; width:8px; height:8px; border-radius:50%;
        background:#e53e3e; margin-right:6px; }
</style>
"""


def _preview(body: str, length: int = 60) -> str:
    body = (body or "").strip().replace("\n", " ")
    if len(body) > length:
        return body[:length].rstrip() + "…"
    return body or "Say hello…"


def render_inbox(
    *,
    college_id: str,
    current_user_id: str,
    counterparts: list[dict],
    state_key: str,
    thread_height: int = 380,
) -> None:
    """Render a conversation list + the selected thread + composer.

    counterparts: the caller's already-fetched roster/DSO list, each a dict
    with at least "id" and "name" (or "email" as a fallback label).
    state_key: unique prefix for this call's session_state/widget keys, so
    the DSO and student pages (or multiple inboxes on one page) never collide.
    """
    if not counterparts:
        st.caption("No one to message yet.")
        return

    st.markdown(MESSAGING_CSS, unsafe_allow_html=True)

    conversations = db.list_conversations(college_id, current_user_id, counterparts)

    sel_key = f"_{state_key}_selected_thread"
    if st.session_state.get(sel_key) not in {c["id"] for c in conversations}:
        st.session_state[sel_key] = conversations[0]["id"]

    for conv in conversations:
        row_l, row_r = st.columns([5, 2])
        with row_l:
            name_class = "vera-msg-name-unread" if conv["unread_count"] else ""
            dot = '<span class="vera-msg-dot"></span>' if conv["unread_count"] else ""
            st.markdown(
                f'<p class="vera-msg-name {name_class}">{dot}{html.escape(conv["name"])}</p>'
                f'<p class="vera-msg-preview">{html.escape(_preview(conv["last_message"]))}</p>',
                unsafe_allow_html=True,
            )
        with row_r:
            label = f"Open ({conv['unread_count']})" if conv["unread_count"] else "Open"
            is_selected = st.session_state[sel_key] == conv["id"]
            if st.button(
                label, key=f"_{state_key}_open_{conv['id']}",
                use_container_width=True, type="primary" if is_selected else "secondary",
            ):
                st.session_state[sel_key] = conv["id"]
                st.rerun()

    st.divider()

    selected = next(c for c in conversations if c["id"] == st.session_state[sel_key])
    st.markdown(f"**{html.escape(selected['name'])}**")

    # Clears the unread badge for this thread the moment it's opened — see
    # migrations/013_messaging_inbox.sql / db.mark_thread_read.
    db.mark_thread_read(current_user_id, selected["id"], college_id)

    with st.container(height=thread_height, border=True):
        thread = db.list_thread(college_id, current_user_id, selected["id"])
        if not thread:
            st.caption("No messages yet — say hello.")
        for m in thread:
            who = "You" if m["sender_id"] == current_user_id else selected["name"]
            when = m["created_at"][:16].replace("T", " ")
            st.markdown(f"**{html.escape(who)}** · {when}  \n{html.escape(m['body'])}")

    compose_key = f"_{state_key}_compose_{selected['id']}"
    body = st.text_area(
        "Message", key=compose_key, max_chars=db.MAX_MESSAGE_LENGTH,
        placeholder="Write a message…", label_visibility="collapsed",
    )
    st.caption(f"{len(body)}/{db.MAX_MESSAGE_LENGTH}")
    if st.button("Send", key=f"_{state_key}_send_{selected['id']}", disabled=not body.strip()):
        try:
            db.send_message(college_id, current_user_id, selected["id"], body.strip())
        except ValueError as e:
            st.error(str(e))
        else:
            st.rerun()
