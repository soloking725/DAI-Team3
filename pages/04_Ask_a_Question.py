"""
Ask a Question - RAG chatbot interface.
Page: 04_Ask_a_Question.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_floating_chat
from shared.retrieval import retrieve_context
from shared.safeguards import classify_input, filter_output, check_confidence, LEGAL_ADVICE_REFUSAL
from shared.chatbot import call_qwen_api, check_api_configured

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
# Custom chat CSS
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
</style>
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

# Handle search query from landing page
if st.session_state.get("chat_query") and not st.session_state.chat_history:
    # Auto-submit the query from the landing page
    question = st.session_state.chat_query
    st.session_state.chat_query = ""  # Clear it so it doesn't re-submit

    # Layer 2: Input classification
    is_legal, flagged = classify_input(question)

    if is_legal:
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
        # Retrieve context
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

        # Layer 4: Confidence gate
        if not check_confidence(distances):
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
        else:
            # Call Qwen API
            with st.spinner("Searching official sources..."):
                api_result = call_qwen_api(
                    user_message=question,
                    context=context,
                    history=st.session_state.conversation_history[-10:],
                )

                # Layer 3: Output filtering
                response_text = api_result["response"]
                filtered_text, warnings = filter_output(response_text)

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
                st.rerun()

# -------------------------------------------------------
# Chat history display
# -------------------------------------------------------
st.markdown('<div class="chat-history">', unsafe_allow_html=True)

for msg in st.session_state.chat_history:
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
                sources_html = f"""
                <div style="margin-top:0.75rem; padding:0.5rem 0.75rem; background:#edf2f7; border-radius:4px; font-size:0.825rem;">
                    <strong>Sources:</strong>
                    <ul style="margin:0.25rem 0 0; padding-left:1.25rem; color:#4a5568;">
                        {source_items}
                    </ul>
                </div>
                """

        st.markdown(f'<div class="chat-message assistant-message">{msg["content"]}{sources_html}{warning_html}</div>', unsafe_allow_html=True)

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
    placeholder="e.g., What documents do I need for an F-1 visa interview?",
    key="chat_input",
    label_visibility="collapsed",
)

col1, col2 = st.columns([1, 5])
with col1:
    send_button = st.button("Send", type="primary", use_container_width=True)

with col2:
    clear_button = st.button("Clear Chat", use_container_width=True)

if clear_button:
    st.session_state.chat_history = []
    st.session_state.conversation_history = []
    st.rerun()

if send_button and user_input.strip():
    question = user_input.strip()

    # Layer 2: Input classification: detect legal advice requests
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
        with st.spinner("Generating answer..."):
            api_result = call_qwen_api(
                user_message=question,
                context=context,
                history=st.session_state.conversation_history[-10:],  # Last 10 messages
            )

        # Layer 3: Output filtering: scan for advice patterns, append warnings
        response_text = api_result["response"]
        filtered_text, warnings = filter_output(response_text)

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

        # Clear input and rerun
        st.session_state.chat_input = ""
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
