"""
Ask a Question - RAG chatbot interface.
Page: 01_Ask_a_Question.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_chat_placeholder

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="Ask a Question - US Visa Information Resource",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)

# -------------------------------------------------------
# Navigation
# -------------------------------------------------------
st.markdown(render_nav_bar(), unsafe_allow_html=True)
st.markdown(render_disclaimer(), unsafe_allow_html=True)

# -------------------------------------------------------
# Main content
# -------------------------------------------------------
st.markdown("""
<div style="max-width:800px; margin:0 auto; padding:2rem 1rem;">
    <h2 style="color:#1a365d; margin-bottom:0.5rem;">Ask a Visa Question</h2>
    <p style="color:#4a5568; line-height:1.6;">
        Enter your question about US visas. Answers are retrieved from official government sources
        (USCIS, State Department) and include source citations.
    </p>
</div>
""", unsafe_allow_html=True)

# Visa type selector
st.markdown("""
<div style="max-width:800px; margin:0 auto; padding:0 1rem;">
    <label style="font-weight:600; color:#1a365d;">Visa Type (optional)</label>
</div>
""", unsafe_allow_html=True)

visa_type = st.selectbox(
    "Select a visa category to narrow results",
    options=["All categories", "H-1B", "I-129", "I-485", "F-1", "B-1/B-2"],
    index=0,
    key="visa_selector",
    label_visibility="collapsed",
)

# Chat area placeholder
render_chat_placeholder()

st.markdown(render_chat_placeholder(), unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
