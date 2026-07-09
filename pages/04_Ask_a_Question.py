"""
Ask a Question - RAG chatbot interface.
Page: 04_Ask_a_Question.py
"""
import time
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer
from shared.retrieval import retrieve_context
from shared.safeguards import classify_input, filter_output, check_confidence, LEGAL_ADVICE_REFUSAL, strip_thinking, has_visa_keyword, extract_visa_type
from shared.chatbot import call_qwen_api
from shared.config import MAX_INPUT_LENGTH, RATE_LIMIT_SECONDS, RATE_LIMIT_MAX_REQUESTS

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="Ask a Question - US Student Visa Information Resource",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)

# -------------------------------------------------------
# Navigation
# -------------------------------------------------------
render_nav_bar()
st.markdown(render_disclaimer(), unsafe_allow_html=True)

# -------------------------------------------------------
# Custom chat CSS + JavaScript
# -------------------------------------------------------
st.markdown("""
<style>
    .chat-message {
        padding: 1rem 1.25rem;
        border-radius: 6px;
        margin-bottom: 0.75rem;
        max-width: 85%;
    }
    .user-message {
        background-color: #ebf4ff;
        border: 1px solid #bee3f8;
        margin-left: auto;
        color: #1a365d;
    }
    .assistant-message {
        background-color: white;
        border: 1px solid #e2e8f0;
        color: #1a202c;
    }
    .chat-input-area {
        max-width: 800px;
        margin: 0 auto;
        padding: 1rem;
        position: sticky;
        bottom: 0;
        background: #f8f9fa;
        border-top: 1px solid #e2e8f0;
    }
    .chat-history {
        max-width: 800px;
        margin: 0 auto;
        padding: 1.5rem 1rem 2rem;
        min-height: 400px;
    }
    .confidence-low {
        background: #fffbeb;
        border: 1px solid #f6e05e;
        border-left: 4px solid #d69e2e;
        padding: 0.5rem 0.75rem;
        margin-top: 0.5rem;
        font-size: 0.8rem;
        color: #975a16;
        border-radius: 4px;
    }
    .typing-indicator {
        display: inline-block;
        padding: 1rem 1.25rem;
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        margin-bottom: 0.75rem;
    }
    .typing-indicator span {
        height: 8px;
        width: 8px;
        background-color: #a0aec0;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        animation: typing 1.4s infinite ease-in-out both;
    }
    .typing-indicator span:nth-child(1) { animation-delay: 0s; }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
        40% { transform: scale(1); opacity: 1; }
    }
    .copy-btn {
        background: #edf2f7;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        color: #4a5568;
        cursor: pointer;
        margin-top: 0.5rem;
    }
    .copy-btn:hover {
        background: #e2e8f0;
    }
    .rate-limited {
        background: #fff5f5;
        border: 1px solid #feb2b2;
        border-left: 4px solid #e53e3e;
        padding: 0.5rem 0.75rem;
        margin-top: 0.5rem;
        font-size: 0.8rem;
        color: #9b2c2c;
        border-radius: 4px;
    }
    /* Prevent flash during st.rerun() — keep background consistent */
    .stApp, .stViewController, [data-testid="stAppViewContainer"], body {
        background-color: #f8f9fa !important;
        transition: none !important;
    }
    /* Keep chat input area pinned so it never jumps or disappears */
    .chat-input-area {
        position: sticky !important;
        bottom: 0 !important;
        z-index: 100 !important;
    }
    /* Smooth typing indicator so it doesn't cause layout shift */
    .typing-indicator {
        min-height: 3.5rem;
    }
</style>
<script>
(function() {
    setTimeout(function() {
        var inputs = document.querySelectorAll('input[type="text"]');
        var buttons = Array.from(document.querySelectorAll('button'));
        var chatInput = inputs[inputs.length - 1];
        var sendBtn = buttons.find(function(b) { return b.textContent.includes('Send'); });
        if (chatInput && sendBtn) {
            chatInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendBtn.click();
                }
            });
        }
        // Copy helper for assistant responses
        window.copyText = function(elId, btn) {
            var el = document.getElementById(elId);
            if (el) {
                navigator.clipboard.writeText(el.innerText).then(function() {
                    btn.textContent = 'Copied!';
                    setTimeout(function() { btn.textContent = 'Copy'; }, 1500);
                });
            }
        };
    }, 300);
})();
</script>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Main content
# -------------------------------------------------------
st.markdown("""
<div style="max-width:800px; margin:0 auto; padding:1.5rem 1rem 0.5rem;">
    <h2 style="color:#1a365d; margin-bottom:0.5rem;">Ask a Visa Question</h2>
    <p style="color:#4a5568; line-height:1.6;">
        Enter your question about US student visas (F-1, J-1, M-1). Answers are retrieved from official
        government sources (USCIS, State Department) and include source citations.
    </p>
</div>
""", unsafe_allow_html=True)

# Visa type selector
st.markdown("""
<div style="max-width:800px; margin:0 auto; padding:0 1rem 1rem;">
    <label style="font-weight:600; color:#1a365d;">Visa Type (optional)</label>
</div>
""", unsafe_allow_html=True)

visa_type = st.selectbox(
    "Select a visa category to narrow results",
    options=["All categories", "F-1", "J-1", "M-1"],
    index=0,
    key="visa_selector",
    label_visibility="collapsed",
)

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Initialize rate limiting state
if "request_timestamps" not in st.session_state:
    st.session_state.request_timestamps = []

# Handle search query from landing page - prefill input instead of auto-submitting
landing_query = st.session_state.pop("chat_query", "")

# -------------------------------------------------------
# Process pending question (runs on the second rerun after typing indicator shows)
# -------------------------------------------------------
if st.session_state.get("is_processing") and "pending_question" in st.session_state:
    question = st.session_state.pop("pending_question")
    with st.spinner("Searching official sources and generating answer..."):
        # Auto-detect visa type from query if user hasn't selected one
        query_visa_type = extract_visa_type(question)
        visatype_filter = None if visa_type == "All categories" else visa_type
        # Override with detected visa type if user hasn't explicitly selected one
        if visatype_filter is None and query_visa_type:
            visatype_filter = query_visa_type

        retrieval_result = retrieve_context(
            query=question,
            top_k=5,
            visa_type=visatype_filter,
            distance_threshold=1.2,
        )

        context = retrieval_result.get("context", "")
        sources = retrieval_result.get("sources", [])
        distances = retrieval_result.get("distances", [])

        is_confident = check_confidence(distances)

        # Keyword fallback: if confidence is low but query has visa keywords, try broader search
        if not is_confident and has_visa_keyword(question):
            broader = retrieve_context(
                query=question,
                top_k=8,
                visa_type=None,  # Search all categories
                distance_threshold=1.3,
            )
            if check_confidence(broader.get("distances", [])):
                is_confident = True
                context = broader.get("context", "")
                sources = broader.get("sources", [])
                distances = broader.get("distances", [])

        if is_confident:
            api_result = call_qwen_api(
                user_message=question,
                context=context,
                history=st.session_state.conversation_history[-10:],
            )
            response_text = api_result["response"]
            # Strip chain-of-thought before filtering for advice
            cleaned_text = strip_thinking(response_text)
            filtered_text, warnings = filter_output(cleaned_text)

            st.session_state.chat_history.append({
                "role": "user",
                "content": question,
            })
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": filtered_text,
                "warnings": warnings,
                "sources": sources,
            })
            st.session_state.conversation_history.append({"role": "user", "content": question})
            st.session_state.conversation_history.append({"role": "assistant", "content": filtered_text})
        else:
            st.session_state.chat_history.append({
                "role": "user",
                "content": question,
            })
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I do not have information about this from official government sources. Please try rephrasing your question or consult a licensed immigration attorney for advice on your specific situation.",
                "warnings": ["Low confidence: no relevant official sources found."],
                "sources": [],
            })

    st.session_state.is_processing = False
    st.rerun()

# -------------------------------------------------------
# Chat history display
# -------------------------------------------------------
st.markdown('<div class="chat-history">', unsafe_allow_html=True)

# Show typing indicator if actively processing (do NOT stop rendering — input must stay visible)
if st.session_state.get("is_processing"):
    st.markdown('<div class="typing-indicator"><span></span><span></span><span></span></div>', unsafe_allow_html=True)

for idx, msg in enumerate(st.session_state.chat_history):
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-message user-message">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        # Assistant message with optional warning
        warning_html = ""
        if msg.get("warnings"):
            for w in msg["warnings"]:
                warning_html += f'<div class="confidence-low">{w}</div>'

        sources_html = ""
        if msg.get("sources"):
            source_items = ""
            seen = set()
            for s in msg["sources"]:
                url = s.get("url", "#")
                if url not in seen:
                    source_items += f'<li><a href="{url}" target="_blank">{s.get("title", "Source")}</a></li>'
                    seen.add(url)
            if source_items:
                # Collapsible accordion for sources
                sources_html = f"""
                <details style="margin-top:0.75rem; padding:0.5rem 0.75rem; background:#edf2f7; border-radius:4px; font-size:0.825rem;">
                    <summary style="cursor:pointer; font-weight:600; color:#2d3748;">Sources ({len(msg['sources'])})</summary>
                    <ul style="margin:0.25rem 0 0; padding-left:1.25rem; color:#4a5568;">
                        {source_items}
                    </ul>
                </details>
                """

        # Copy button using JavaScript
        copy_id = f"resp-{idx}"
        st.markdown(
            f'<div class="chat-message assistant-message" id="{copy_id}">{msg["content"]}{sources_html}{warning_html}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'''<button class="copy-btn" onclick="copyText('{copy_id}', this)">Copy</button>''',
            unsafe_allow_html=True,
        )

# Empty state
if not st.session_state.chat_history:
    st.markdown("""
    <div style="text-align:center; padding:3rem 1rem; color:#718096;">
        <p style="font-size:1rem; margin-bottom:0.5rem;">No questions yet.</p>
        <p style="font-size:0.875rem;">Type a question below to get started. Try asking about F-1 visa requirements, fees, or application steps.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# Chat input
# -------------------------------------------------------
st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)

user_input = st.text_input(
    "Your question",
    value=landing_query,
    placeholder="e.g., What documents do I need for an F-1 visa interview?",
    key="chat_input",
    label_visibility="collapsed",
    max_chars=MAX_INPUT_LENGTH,
)

col1, col2, col3 = st.columns([1, 5, 1])
with col1:
    send_button = st.button("Send", type="primary", use_container_width=True)

with col2:
    clear_button = st.button("Clear Chat", use_container_width=True)

with col3:
    st.markdown(
        '<span style="font-size:0.75rem; color:#718096; display:flex; align-items:center;">'
        '<span style="color:#e53e3e; margin-right:0.25rem;">*</span> Not legal advice</span>',
        unsafe_allow_html=True,
    )

if clear_button:
    st.session_state.chat_history = []
    st.session_state.conversation_history = []
    st.session_state.request_timestamps = []
    st.rerun()

if send_button and user_input:
    question = user_input.strip()
    if not question:
        st.rerun()

    # -------------------------------------------------------
    # 2.1: Input validation
    # -------------------------------------------------------
    if len(question) > MAX_INPUT_LENGTH:
        st.session_state.chat_history.append({
            "role": "user",
            "content": question[:100] + "...",
        })
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Your question is too long. Please keep questions under 1,000 characters.",
            "warnings": [],
            "sources": [],
        })
        st.rerun()

    # -------------------------------------------------------
    # 2.2: Rate limiting (per-session)
    # -------------------------------------------------------
    now = time.time()
    # Clean old timestamps
    st.session_state.request_timestamps = [
        ts for ts in st.session_state.request_timestamps
        if now - ts < RATE_LIMIT_SECONDS
    ]

    if len(st.session_state.request_timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        st.session_state.chat_history.append({
            "role": "user",
            "content": question,
        })
        wait_time = int(RATE_LIMIT_SECONDS - (now - st.session_state.request_timestamps[0]))
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "You have reached the rate limit. Please wait before asking another question.",
            "warnings": [f"Rate limit: max {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_SECONDS}s. Wait {wait_time}s."],
            "sources": [],
        })
        st.rerun()

    # Record this request
    st.session_state.request_timestamps.append(now)

    # -------------------------------------------------------
    # Layer 2: Input classification: detect legal advice requests
    # -------------------------------------------------------
    is_legal, flagged = classify_input(question)

    if is_legal:
        # BLOCK: Return refusal, do NOT proceed to retrieval or API call
        st.session_state.chat_history.append({
            "role": "user",
            "content": question,
        })
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": LEGAL_ADVICE_REFUSAL,
            "warnings": [f"Question detected as seeking legal advice. Flagged patterns: {', '.join(flagged)}"],
            "sources": [],
        })
        st.session_state.conversation_history.append({"role": "user", "content": question})
        st.rerun()
    else:
        # Show typing indicator, then process on next run
        st.session_state.is_processing = True
        st.session_state.pending_question = question
        st.rerun()

        # Retrieve context from ChromaDB
        visatype_filter = None if visa_type == "All categories" else visa_type
        retrieval_result = retrieve_context(
            query=question,
            top_k=5,
            visa_type=visatype_filter,
            distance_threshold=1.2,
        )

        context = retrieval_result.get("context", "")
        sources = retrieval_result.get("sources", [])
        distances = retrieval_result.get("distances", [])

        # Layer 4: Confidence gate: refuse if no relevant sources found
        if not check_confidence(distances):
            st.session_state.is_processing = False
            st.session_state.chat_history.append({
                "role": "user",
                "content": question,
            })
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "I do not have information about this from official government sources. Please try rephrasing your question or consult a licensed immigration attorney for advice on your specific situation.",
                "warnings": ["Low confidence: no relevant official sources found."],
                "sources": [],
            })
            st.rerun()

        # Call Qwen API with retrieved context
        api_result = call_qwen_api(
            user_message=question,
            context=context,
            history=st.session_state.conversation_history[-10:],  # Last 10 messages
        )

        # Layer 3: Output filtering: scan for advice patterns, append warnings
        response_text = api_result["response"]
        filtered_text, warnings = filter_output(response_text)

        # Clear processing flag
        st.session_state.is_processing = False

        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": question,
        })

        # Add assistant response to history
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": filtered_text,
            "warnings": warnings,
            "sources": sources,
        })

        # Update conversation history for context
        st.session_state.conversation_history.append({"role": "user", "content": question})
        st.session_state.conversation_history.append({"role": "assistant", "content": filtered_text})

        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
