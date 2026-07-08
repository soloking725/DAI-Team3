"""
US Visa Information Resource
Landing page - app.py
"""
import streamlit as st

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="US Visa Information Resource",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------
# Global CSS - override Streamlit defaults completely
# -------------------------------------------------------
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    /* Reset default Streamlit styles */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Body typography */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: #f8f9fa;
        color: #1a202c;
    }

    /* Top navigation styling */
    .stDeployButton { display: none; }

    /* Custom navigation bar */
    .top-nav {
        background-color: #1a365d;
        padding: 1rem 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 3px solid #2b6cb0;
    }

    .top-nav-brand {
        color: white;
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0;
    }

    .top-nav-desc {
        color: #cbd5e0;
        font-size: 0.85rem;
        margin: 0;
    }

    /* Disclaimer banner */
    .disclaimer-banner {
        background-color: #fffbeb;
        border: 1px solid #f6e05e;
        border-left: 4px solid #d69e2e;
        padding: 0.875rem 1.25rem;
        margin: 1.5rem auto;
        max-width: 1200px;
        font-size: 0.875rem;
        color: #744210;
    }

    .disclaimer-banner strong {
        color: #975a16;
    }

    /* Hero section */
    .hero {
        text-align: center;
        padding: 3rem 1rem 2rem;
        max-width: 800px;
        margin: 0 auto;
    }

    .hero h1 {
        font-size: 2.25rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.75rem;
        letter-spacing: -0.02em;
    }

    .hero p {
        font-size: 1.1rem;
        color: #4a5568;
        line-height: 1.6;
        max-width: 650px;
        margin: 0 auto 2rem;
    }

    /* Search box */
    .search-container {
        max-width: 600px;
        margin: 0 auto 2.5rem;
        display: flex;
        gap: 0;
    }

    .search-container input {
        flex: 1;
        padding: 0.875rem 1rem;
        font-size: 1rem;
        border: 2px solid #cbd5e0;
        border-right: none;
        border-radius: 6px 0 0 6px;
        outline: none;
        font-family: inherit;
    }

    .search-container input:focus {
        border-color: #2b6cb0;
    }

    .search-container button {
        padding: 0.875rem 1.5rem;
        background-color: #2b6cb0;
        color: white;
        border: 2px solid #2b6cb0;
        border-radius: 0 6px 6px 0;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        font-family: inherit;
    }

    .search-container button:hover {
        background-color: #2c5282;
        border-color: #2c5282;
    }

    /* Visa type cards grid */
    .visa-cards-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.25rem;
        max-width: 1200px;
        margin: 0 auto 3rem;
        padding: 0 1rem;
    }

    .visa-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1.5rem;
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .visa-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #cbd5e0;
    }

    .visa-card h3 {
        font-size: 1.125rem;
        font-weight: 600;
        color: #1a365d;
        margin: 0 0 0.5rem;
    }

    .visa-card p {
        font-size: 0.9rem;
        color: #4a5568;
        line-height: 1.5;
        margin: 0 0 1rem;
    }

    .visa-card .card-link {
        font-size: 0.875rem;
        color: #2b6cb0;
        text-decoration: none;
        font-weight: 600;
    }

    .visa-card .card-link:hover {
        text-decoration: underline;
    }

    /* Section title */
    .section-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a365d;
        margin: 2.5rem 0 1.5rem;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Features section */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        max-width: 1200px;
        margin: 0 auto 3rem;
        padding: 0 1rem;
    }

    .feature-item {
        text-align: center;
        padding: 1.25rem;
    }

    .feature-item h4 {
        font-size: 1rem;
        font-weight: 600;
        color: #1a365d;
        margin: 0 0 0.5rem;
    }

    .feature-item p {
        font-size: 0.85rem;
        color: #718096;
        line-height: 1.5;
        margin: 0;
    }

    /* Footer */
    .site-footer {
        background-color: #1a365d;
        color: #a0aec0;
        text-align: center;
        padding: 2rem 1rem;
        margin-top: 3rem;
        font-size: 0.85rem;
        line-height: 1.6;
    }

    .site-footer a {
        color: #90cdf4;
    }

    .site-footer strong {
        color: #cbd5e0;
    }

    /* Override Streamlit markdown */
    p {
        color: #1a202c;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Top navigation bar
# -------------------------------------------------------
st.markdown("""
<div class="top-nav">
    <div>
        <p class="top-nav-brand">US Visa Information Resource</p>
        <p class="top-nav-desc">Official government information on US visa categories and processes</p>
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Disclaimer banner
# -------------------------------------------------------
st.markdown("""
<div class="disclaimer-banner">
    <strong>Disclaimer:</strong> This tool provides factual information from official US government sources
    (USCIS, State Department, SSA). It does not provide legal advice. For legal advice about your specific
    situation, consult a licensed immigration attorney.
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Hero section
# -------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>Find Information About US Visas</h1>
    <p>Access official guidance on visa categories, required documents, fees, application
    processes, and post-approval steps. All information is sourced from federal government websites.</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Search prompt
# -------------------------------------------------------
st.markdown("""
<div class="search-container">
    <input type="text" placeholder="What visa question do you have? (e.g., What documents do I need for an H-1B?)" disabled />
    <button disabled>Search</button>
</div>
""", unsafe_allow_html=True)

st.markdown('<p style="text-align:center; color:#718096; font-size:0.85rem; margin-top:-1.5rem; margin-bottom:1rem;">Chat feature coming soon. Browse visa types below.</p>', unsafe_allow_html=True)

# -------------------------------------------------------
# Visa type cards
# -------------------------------------------------------
st.markdown('<p class="section-title">Visa Categories</p>', unsafe_allow_html=True)

st.markdown("""
<div class="visa-cards-grid">
    <div class="visa-card">
        <h3>H-1B Visa</h3>
        <p>Temporary work visa for specialty occupations requiring a bachelor's degree or higher.
        Covers IT, engineering, finance, and other professional fields.</p>
        <a href="#" class="card-link">View H-1B guide</a>
    </div>
    <div class="visa-card">
        <h3>I-129 Petition</h3>
        <p>Nonimmigrant Worker Petition filed by employers to bring temporary or permanent workers
        to the United States. Required for H-1B, L-1, O-1, and other categories.</p>
        <a href="#" class="card-link">View I-129 guide</a>
    </div>
    <div class="visa-card">
        <h3>I-485 Application</h3>
        <p>Application to Register Permanent Residence or Adjust Status. Filed by individuals
        already in the US who wish to become lawful permanent residents.</p>
        <a href="#" class="card-link">View I-485 guide</a>
    </div>
    <div class="visa-card">
        <h3>F-1 Student Visa</h3>
        <p>Nonimmigrant visa for academic students enrolled in US academic institutions or language
        training programs.</p>
        <a href="#" class="card-link">Coming soon</a>
    </div>
    <div class="visa-card">
        <h3>B-1/B-2 Visitor Visa</h3>
        <p>Temporary visa for business (B-1) or tourism (B-2) visitors. Covers vacation, medical
        treatment, and business meetings.</p>
        <a href="#" class="card-link">Coming soon</a>
    </div>
    <div class="visa-card">
        <h3>Post-Visa Guide</h3>
        <p>What to do after your visa is approved: applying for a Social Security Number,
        opening a bank account, obtaining a state ID or driver's license.</p>
        <a href="#" class="card-link">View post-visa guide</a>
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
        <p>Complete document checklists for each visa type, sourced from USCIS form instructions.</p>
    </div>
    <div class="feature-item">
        <h4>Fee Schedules</h4>
        <p>Current application fees and payment requirements from official government sources.</p>
    </div>
    <div class="feature-item">
        <h4>Step-by-Step Process</h4>
        <p>Detailed application procedures from filing to interview to decision.</p>
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
st.markdown("""
<div class="site-footer">
    <p><strong>US Visa Information Resource</strong></p>
    <p>
        This tool provides factual information from official US government sources.
        It does not provide legal advice. For legal advice about your specific situation,
        consult a licensed immigration attorney.
    </p>
    <p>
        Sources: <a href="https://www.uscis.gov" target="_blank">uscis.gov</a> |
        <a href="https://travel.state.gov" target="_blank">travel.state.gov</a> |
        <a href="https://www.ssa.gov" target="_blank">ssa.gov</a>
    </p>
</div>
""", unsafe_allow_html=True)
