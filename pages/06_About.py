"""About page with disclaimer, sources, and limitations."""

import streamlit as st

from shared.components import (
    render_card,
    render_disclaimer,
    render_floating_chat,
    render_footer,
    render_hamburger_menu,
    render_profile_banner,
    render_section,
    render_source_citations,
)
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.vera_state import get_vera_state

st.set_page_config(page_title="About", page_icon=":book:", layout="wide")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu(visa_type=get_vera_state().get("profile", {}).get("visa_type") or "f-1")
st.markdown(render_disclaimer(), unsafe_allow_html=True)
render_profile_banner()

st.markdown("""
<div style="max-width:1200px; margin:0 auto; padding:2rem 1rem 0;">
    <h1 style="font-size:1.75rem; font-weight:700; color:#166534; margin:0 0 0.5rem;">
        About This Tool
    </h1>
    <p style="color:#4a5568; font-size:1rem; margin:0 0 2rem;">
        Information about this US student visa resource, its data sources, and its limitations.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Purpose
# -------------------------------------------------------
st.markdown(render_section("Purpose"), unsafe_allow_html=True)

st.markdown(render_card(
    title="What This Tool Does",
    content_html="""
    <p>This tool provides factual, sourced information about US student visa categories (F-1, J-1, M-1) and post-arrival requirements. It is designed to help international students understand the visa application process, required documents, fees, and procedures based on official US government sources.</p>
    <p>The tool uses Retrieval-Augmented Generation (RAG) to answer questions by retrieving relevant information from a database of official government content. Every answer includes clickable source links to the original government pages.</p>
    """,
), unsafe_allow_html=True)

# -------------------------------------------------------
# Official Sources
# -------------------------------------------------------
st.markdown(render_section("Official Sources"), unsafe_allow_html=True)

st.markdown(render_card(
    title="Data Sources",
    content_html="""
    <p>All information in this tool is retrieved from official US government websites:</p>
    <ul>
        <li><strong>US Citizenship and Immigration Services (USCIS)</strong> - Visa categories, application procedures, processing times</li>
        <li><strong>US Department of State</strong> - Visa interview requirements, refusal grounds, travel information</li>
        <li><strong>Student and Exchange Visitor Program (SEVP)</strong> - Student status requirements, school certification</li>
        <li><strong>Social Security Administration (SSA)</strong> - SSN application requirements for immigrants and nonimmigrants</li>
        <li><strong>Internal Revenue Service (IRS)</strong> - Tax obligations for nonresident aliens</li>
    </ul>
    """,
), unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://www.uscis.gov",
        "title": "US Citizenship and Immigration Services",
        "agency": "USCIS",
        "section": "Main Website",
    },
    {
        "url": "https://travel.state.gov",
        "title": "US Department of State - Travel Documents",
        "agency": "State Department",
        "section": "Visa Information",
    },
    {
        "url": "https://studyinthestates.dhs.gov",
        "title": "Student and Exchange Visitor Program",
        "agency": "SEVP",
        "section": "Student Resources",
    },
    {
        "url": "https://www.ssa.gov",
        "title": "Social Security Administration",
        "agency": "SSA",
        "section": "SSN Information",
    },
    {
        "url": "https://www.irs.gov",
        "title": "Internal Revenue Service",
        "agency": "IRS",
        "section": "Tax Information",
    },
]), unsafe_allow_html=True)

# -------------------------------------------------------
# Limitations
# -------------------------------------------------------
st.markdown(render_section("Limitations"), unsafe_allow_html=True)

st.markdown(render_card(
    title="What This Tool Does Not Do",
    content_html="""
    <ul>
        <li><strong>Not legal advice</strong> - This tool provides factual information from official sources. It does not provide legal advice or represent you in immigration proceedings.</li>
        <li><strong>Not eligibility assessment</strong> - This tool cannot determine your eligibility for a visa or predict the outcome of your application.</li>
        <li><strong>Not personalized guidance</strong> - This tool does not provide strategic recommendations or tailor advice to your specific situation.</li>
        <li><strong>Not a substitute for official sources</strong> - Always verify information on the original government websites, as policies and fees may change.</li>
        <li><strong>Not for non-US visas</strong> - This tool only covers US student visa categories and does not provide information about other countries' visa programs.</li>
    </ul>
    """,
), unsafe_allow_html=True)

# -------------------------------------------------------
# Legal Disclaimer
# -------------------------------------------------------
st.markdown(render_section("Legal Disclaimer"), unsafe_allow_html=True)

st.markdown(render_card(
    title="Consult a Licensed Immigration Attorney",
    content_html="""
    <p>This tool is provided for informational purposes only. The information contained herein does not constitute legal advice and should not be relied upon as such. Immigration laws and regulations change frequently, and the information provided may become outdated.</p>
    <p style="margin-top:1rem;">For legal advice about your specific immigration situation, consult a licensed immigration attorney. You can find qualified immigration attorneys through:</p>
    <ul>
        <li><strong>American Immigration Lawyers Association (AILA)</strong> - Find an attorney near you</li>
        <li><strong>State bar associations</strong> - Verify attorney credentials and licensing</li>
    </ul>
    """,
    link_text="AILA Attorney Finder",
    link_href="https://www.aila.org/find-an-attorney",
), unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)

# Floating chat button
render_floating_chat()
