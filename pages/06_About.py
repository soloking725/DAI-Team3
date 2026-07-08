"""
About & Disclaimer - Information about the tool.
Page: 06_About.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_card

st.set_page_config(
    page_title="About - US Visa Information Resource",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(render_nav_bar(), unsafe_allow_html=True)
st.markdown(render_disclaimer(), unsafe_allow_html=True)

st.markdown("""
<div style="max-width:900px; margin:0 auto; padding:2rem 1rem 1rem;">
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">About This Tool</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        The US Visa Information Resource provides factual information about US visa categories
        and application processes, retrieved from official government sources.
    </p>
</div>
""", unsafe_allow_html=True)

content_max = '<div style="max-width:900px; margin:0 auto; padding:0 1rem;">'

content_max += render_card(
    "What This Tool Does",
    """
    <p>This tool allows users to ask questions about US visa categories and receive factual
    answers sourced from official US government websites. It uses Retrieval-Augmented Generation
    (RAG) to retrieve information from ingested government documents and cite sources.</p>
    <p>The tool covers visa categories including H-1B, I-129, I-485, F-1, and B-1/B-2.
    It provides information on required documents, fees, application processes, processing times,
    and post-visa steps.</p>
    """,
)

content_max += render_card(
    "What This Tool Does Not Do",
    """
    <ul>
        <li>Provide legal advice</li>
        <li>Evaluate individual cases or situations</li>
        <li>Guarantee approval or predict outcomes</li>
        <li>Replace consultation with a licensed immigration attorney</li>
        <li>Accept or review personal application documents</li>
    </ul>
    """,
)

content_max += render_card(
    "Official Sources",
    """
    <p>All information in this tool comes from the following official US government websites:</p>
    <ul>
        <li><a href="https://www.uscis.gov" target="_blank">US Citizenship and Immigration Services (USCIS)</a> - Visa categories, form instructions, fee schedules, processing guidelines</li>
        <li><a href="https://travel.state.gov" target="_blank">US Department of State</a> - Visa bulletin, interview preparation, refusal grounds</li>
        <li><a href="https://www.ssa.gov" target="_blank">Social Security Administration (SSA)</a> - SSN application for new immigrants</li>
        <li><a href="https://www.irs.gov" target="_blank">Internal Revenue Service (IRS)</a> - Tax obligations for visa holders</li>
    </ul>
    """,
)

content_max += render_card(
    "Safeguards",
    """
    <p>This tool includes multiple safeguards to prevent it from providing legal advice:</p>
    <ul>
        <li>Strict system prompts instruct the AI to provide only factual information</li>
        <li>Input classification detects questions asking for legal advice and routes them to a disclaimer</li>
        <li>Output filtering scans responses for patterns suggesting legal advice</li>
        <li>Confidence gating prevents the tool from answering questions without sufficient source material</li>
        <li>Persistent disclaimers are visible on every page</li>
    </ul>
    """,
)

content_max += render_card(
    "Finding an Immigration Attorney",
    """
    <p>For legal advice about your specific immigration situation, consult a licensed immigration
    attorney. You can find qualified attorneys through:</p>
    <ul>
        <li>American Immigration Lawyers Association: <a href="https://www.aila.org/find-an-attorney" target="_blank">aila.org/find-an-attorney</a></li>
        <li>Your state bar association's lawyer referral service</li>
        <li>Legal aid organizations that offer immigration services</li>
    </ul>
    """,
)

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

st.markdown(render_footer(), unsafe_allow_html=True)
