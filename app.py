"""
US Student Visa Information Resource
Landing page - app.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_floating_chat

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="US Student Visa Information Resource",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------
# Global CSS - override Streamlit defaults completely
# -------------------------------------------------------
st.markdown(get_global_css(), unsafe_allow_html=True)

# -------------------------------------------------------
# Top navigation bar
# -------------------------------------------------------
render_nav_bar()

# -------------------------------------------------------
# Disclaimer banner
# -------------------------------------------------------
st.markdown(render_disclaimer(), unsafe_allow_html=True)

# -------------------------------------------------------
# Hero section with search
# -------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>Find Information About US Student Visas</h1>
    <p>Access official guidance on F-1, J-1, and M-1 student visa categories, required documents,
    fees, application processes, and post-arrival steps. All information is sourced from federal government websites.</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Quick search widget
# -------------------------------------------------------
st.markdown("""
<style>
    .search-widget {
        max-width: 650px;
        margin: -1rem auto 2rem;
        padding: 0 1rem;
    }
</style>
<div class="search-widget">
</div>
""", unsafe_allow_html=True)

# Initialize session state for search query passing
if "chat_query" not in st.session_state:
    st.session_state.chat_query = ""

search_col1, search_col2 = st.columns([5, 1])
with search_col1:
    search_input = st.text_input(
        "Ask a visa question",
        placeholder='e.g., What documents do I need for an F-1 visa interview?',
        key="landing_search",
        label_visibility="collapsed",
    )
with search_col2:
    search_btn = st.button("🔍 Search", type="primary", use_container_width=True)

if search_btn and search_input.strip():
    st.session_state.chat_query = search_input.strip()
    st.switch_page("pages/04_Ask_a_Question.py")

# Also handle Enter key submission
if st.session_state.get("chat_query") and st.session_state.get("from_landing"):
    st.switch_page("pages/04_Ask_a_Question.py")

# -------------------------------------------------------
# Student visa type cards
# -------------------------------------------------------
st.markdown('<p class="section-title">Student Visa Categories</p>', unsafe_allow_html=True)

# Visa cards with working navigation (entire card clickable)
col1, col2, col3 = st.columns(3)

with col1:
    st.page_link(
        "pages/01_F-1_Student_Visa.py",
        label="**F-1 Student Visa**\n\nAcademic student visa for individuals enrolled in accredited US academic institutions or language training programs. The most common visa for international students pursuing degrees.\n\n→ View F-1 guide",
        icon="🎓",
    )

with col2:
    st.page_link(
        "pages/02_J-1_Exchange_Visitor.py",
        label="**J-1 Exchange Visitor**\n\nExchange visitor visa for students participating in government-approved exchange programs, including university programs, research assistantships, and summer work travel.\n\n→ View J-1 guide",
        icon="🌍",
    )

with col3:
    st.page_link(
        "pages/03_M-1_Vocational_Visa.py",
        label="**M-1 Vocational Student**\n\nVocational student visa for individuals enrolled in vocational or technical programs that are primarily practical or technical rather than academic in nature.\n\n→ View M-1 guide",
        icon="🔧",
    )

# -------------------------------------------------------
# Quick start section
# -------------------------------------------------------
st.markdown('<p class="section-title">Getting Started</p>', unsafe_allow_html=True)

st.markdown("""
<div class="quick-start-grid">
    <div class="quick-start-card">
        <h4>1. Select Your Visa Type</h4>
        <p>Use the cards above to learn about each student visa category, required documents, fees, and application steps.</p>
    </div>
    <div class="quick-start-card">
        <h4>2. Ask a Question</h4>
        <p>Have a specific question? Use our chat feature to get factual answers sourced from official government pages.</p>
    </div>
    <div class="quick-start-card">
        <h4>3. Check Processing Times</h4>
        <p>View current visa processing and appointment wait times directly on each visa page.</p>
    </div>
    <div class="quick-start-card">
        <h4>4. Post-Arrival Guide</h4>
        <p>Learn what to do after arriving in the US: SSN application, bank accounts, state IDs, and school registration.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Features / what the tool does
# -------------------------------------------------------
st.markdown('<p class="section-title">What This Tool Provides</p>', unsafe_allow_html=True)

st.markdown("""
<div class="features-grid">
    <div class="feature-item">
        <h4>Required Documents</h4>
        <p>Complete document checklists for each student visa type, sourced from State Department and USCIS.</p>
    </div>
    <div class="feature-item">
        <h4>Fee Schedules</h4>
        <p>Current visa application fees, SEVIS fees, and payment requirements from official sources.</p>
    </div>
    <div class="feature-item">
        <h4>Step-by-Step Process</h4>
        <p>Detailed application procedures from DS-160 filing to consulate interview to decision.</p>
    </div>
    <div class="feature-item">
        <h4>Processing Times</h4>
        <p>Live data on current processing times and appointment wait times.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Sources section
# -------------------------------------------------------
st.markdown('<p class="section-title">Official Sources</p>', unsafe_allow_html=True)

st.markdown("""
<div style="max-width:800px; margin:0 auto 3rem; padding:0 1rem; text-align:center;">
    <p style="color:#4a5568; line-height:1.8;">
        All information in this tool is retrieved from official US government websites:
        <strong>USCIS</strong> (uscis.gov),
        <strong>State Department</strong> (travel.state.gov),
        <strong>Social Security Administration</strong> (ssa.gov), and
        <strong>Internal Revenue Service</strong> (irs.gov).
    </p>
    <p style="color:#4a5568; line-height:1.8;">
        Every answer includes clickable source links to the original government page.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
render_floating_chat()
st.markdown(render_footer(), unsafe_allow_html=True)
