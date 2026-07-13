"""
Compact chat widget for the Vera timeline screen — a narrow sidebar-style
panel (header, scrollable messages, input) as opposed to the full-width
chat experience. Reuses the same RAG + safeguard pipeline as the original
Ask a Question page.
"""

import time

import streamlit as st

from shared.retrieval import retrieve_context
from shared.safeguards import (
    classify_input,
    filter_output,
    check_confidence,
    LEGAL_ADVICE_REFUSAL,
    strip_thinking,
    has_visa_keyword,
    extract_visa_type,
)
from shared.chatbot import call_qwen_api
from shared.config import MAX_INPUT_LENGTH, RATE_LIMIT_SECONDS, RATE_LIMIT_MAX_REQUESTS

PANEL_CSS = """
<style>
    .vera-chat-header {
        display:flex; align-items:center; gap:10px;
        padding:14px 16px; border-bottom:0.5px solid var(--border);
        background:var(--surface-2); border-radius:12px 12px 0 0;
    }
    .vera-chat-avatar {
        width:32px; height:32px; border-radius:50%; background:var(--bg-accent);
        display:flex; align-items:center; justify-content:center; flex-shrink:0;
    }
    .vera-chat-avatar i { font-size:17px; color:var(--text-accent); }
    .vera-chat-title { font-weight:500; font-size:14px; margin:0; }
    .vera-chat-subtitle { font-size:12px; color:var(--text-muted); margin:0; }
    .vera-chat-msg {
        border-radius:12px; padding:8px 12px; font-size:13px; max-width:88%;
        margin-bottom:10px;
    }
    .vera-chat-msg-assistant { background:var(--surface-1); }
    .vera-chat-msg-user { background:var(--bg-accent); color:var(--text-accent); margin-left:auto; }
    .vera-chat-warning {
        background:#fffbeb; border:1px solid #f6e05e; border-left:3px solid #d69e2e;
        padding:6px 8px; margin-top:4px; font-size:11px; color:#975a16; border-radius:6px;
    }
</style>
"""


def _init_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "request_timestamps" not in st.session_state:
        st.session_state.request_timestamps = []


def _process_pending_question():
    if not (st.session_state.get("is_processing") and "pending_question" in st.session_state):
        return

    question = st.session_state.pop("pending_question")
    with st.spinner("Searching official sources..."):
        visa_type = extract_visa_type(question)
        retrieval = retrieve_context(query=question, top_k=5, visa_type=visa_type, distance_threshold=1.2)
        context = retrieval.get("context", "")
        sources = retrieval.get("sources", [])
        distances = retrieval.get("distances", [])
        is_confident = check_confidence(distances)

        if not is_confident and has_visa_keyword(question):
            broader = retrieve_context(query=question, top_k=8, visa_type=None, distance_threshold=1.3)
            if check_confidence(broader.get("distances", [])):
                is_confident = True
                context = broader.get("context", "")
                sources = broader.get("sources", [])

        st.session_state.chat_history.append({"role": "user", "content": question})

        if is_confident:
            api_result = call_qwen_api(
                user_message=question,
                context=context,
                history=st.session_state.conversation_history[-10:],
            )
            cleaned = strip_thinking(api_result["response"])
            filtered_text, warnings = filter_output(cleaned)
            st.session_state.chat_history.append({
                "role": "assistant", "content": filtered_text, "warnings": warnings, "sources": sources,
            })
            st.session_state.conversation_history.append({"role": "user", "content": question})
            st.session_state.conversation_history.append({"role": "assistant", "content": filtered_text})
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I do not have information about this from official government sources. Try rephrasing, or consult a licensed immigration attorney for your specific situation.",
                "warnings": ["Low confidence: no relevant official sources found."],
                "sources": [],
            })

    st.session_state.is_processing = False
    st.rerun(scope="fragment")


@st.fragment
def render_chat_panel():
    """Render the compact Vera chat widget. Call once per page.

    Wrapped in @st.fragment so that asking a question only reruns this
    panel (with its own spinner) instead of the entire page — the rest of
    the app (timeline, menu, etc.) stays interactive while Vera answers.
    """
    _init_state()
    _process_pending_question()

    st.markdown(PANEL_CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="vera-chat-header">
            <div class="vera-chat-avatar"><i class="ti ti-message-circle-2"></i></div>
            <div>
                <p class="vera-chat-title">Vera</p>
                <p class="vera-chat-subtitle">Visa assistant</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(height=340, border=True):
        if st.session_state.get("is_processing"):
            st.markdown('<div class="vera-chat-msg vera-chat-msg-assistant">Thinking…</div>', unsafe_allow_html=True)

        if not st.session_state.chat_history:
            st.markdown(
                '<div class="vera-chat-msg vera-chat-msg-assistant">'
                "Hi, I'm here to walk you through your visa timeline. Ask me anything along the way."
                "</div>",
                unsafe_allow_html=True,
            )

        for msg in st.session_state.chat_history:
            css_class = "vera-chat-msg-user" if msg["role"] == "user" else "vera-chat-msg-assistant"
            warning_html = "".join(f'<div class="vera-chat-warning">{w}</div>' for w in msg.get("warnings", []))
            st.markdown(
                f'<div class="vera-chat-msg {css_class}">{msg["content"]}{warning_html}</div>',
                unsafe_allow_html=True,
            )

    with st.form("vera_chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask about your next step",
            placeholder="Ask about your next step",
            key="vera_chat_input",
            label_visibility="collapsed",
            max_chars=MAX_INPUT_LENGTH,
        )
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted and user_input and user_input.strip():
        question = user_input.strip()

        now = time.time()
        st.session_state.request_timestamps = [
            ts for ts in st.session_state.request_timestamps if now - ts < RATE_LIMIT_SECONDS
        ]
        if len(st.session_state.request_timestamps) >= RATE_LIMIT_MAX_REQUESTS:
            st.session_state.chat_history.append({"role": "user", "content": question})
            wait_time = int(RATE_LIMIT_SECONDS - (now - st.session_state.request_timestamps[0]))
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "You've reached the rate limit. Please wait before asking another question.",
                "warnings": [f"Rate limit: max {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_SECONDS:.0f}s. Wait {wait_time}s."],
            })
            st.rerun(scope="fragment")

        st.session_state.request_timestamps.append(now)

        is_legal, flagged = classify_input(question)
        if is_legal:
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": LEGAL_ADVICE_REFUSAL,
                "warnings": [f"Question detected as seeking legal advice. Flagged: {', '.join(flagged)}"],
            })
            st.session_state.conversation_history.append({"role": "user", "content": question})
            st.rerun(scope="fragment")
        else:
            st.session_state.is_processing = True
            st.session_state.pending_question = question
            st.rerun(scope="fragment")
