"""
About & Disclaimer - Information about the tool.
Page: 06_About.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_card, render_floating_chat

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="About - US Student Visa Information Resource",
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
# Page header
# -------------------------------------------------------
st.markdown("""
<div style="max-width:900px; margin:0 auto; padding:2rem 1rem 1rem;">
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">About This Tool</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        The US Student Visa Information Resource provides factual information about F-1, J-1, and M-1
        student visa categories and application processes, retrieved from official government sources.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Content sections
# -------------------------------------------------------
content_max = '<div style="max-width:900px; margin:0 auto; padding:0 1rem;">'

content_max += render_card(
    "What This Tool Does",
    """
    <p>This tool allows users to access factual information about US student visa categories (F-1, J-1, M-1)
    and receive answers sourced from official US government websites. It uses Retrieval-Augmented Generation
    (RAG) to retrieve information from ingested government documents and cite sources.</p>
    <p>The tool covers student visa categories including F-1 (academic students), J-1 (exchange visitors),
    and M-1 (vocational students). It provides information on required documents, fees, application processes,
    processing times, common refusal reasons, and post-arrival steps.</p>
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
        <li>Diagnose which visa type is best for your specific situation</li>
        <li>Provide information on non-student visa categories (H-1B, L-1, family-based visas, etc.)</li>
    </ul>
    """,
)

content_max += render_card(
    "Official Sources",
    """
    <p>All information in this tool comes from the following official US government websites:</p>
    <ul>
        <li><a href="https://www.uscis.gov" target="_blank">US Citizenship and Immigration Services (USCIS)</a> - Form instructions, fee schedules, OPT/CPT guidelines</li>
        <li><a href="https://travel.state.gov" target="_blank">US Department of State</a> - Visa application process, interview preparation, refusal grounds, DS-160</li>
        <li><a href="https://studyinthestates.dhs.gov" target="_blank">SEVP - Student and Exchange Visitor Program</a> - F-1 and M-1 regulations, school certification</li>
        <li><a href="https://exchanges.state.gov" target="_blank">J Exchange Visitor Program</a> - J-1 exchange visitor regulations and program requirements</li>
        <li><a href="https://www.ssa.gov" target="_blank">Social Security Administration (SSA)</a> - SSN application for international students</li>
        <li><a href="https://www.irs.gov" target="_blank">Internal Revenue Service (IRS)</a> - Tax obligations for nonresident aliens</li>
    </ul>
    """,
)

content_max += render_card(
    "Chatbot and RAG Pipeline",
    """
    <p>The Ask a Question page uses Retrieval-Augmented Generation (RAG) to answer student visa questions:</p>
    <ul>
        <li><strong>Embeddings:</strong> sentence-transformers/all-MiniLM-L6-v2 (free, local)</li>
        <li><strong>Vector database:</strong> ChromaDB for semantic search over ingested government documents</li>
        <li><strong>Chunking:</strong> 600-character chunks with 100-character overlap for precise legal text retrieval</li>
        <li><strong>Generation:</strong> Qwen API (OpenAI-compatible client) with strict system prompts</li>
        <li><strong>Citation:</strong> Every answer includes clickable source links to the original government page</li>
    </ul>
    """,
)

content_max += render_card(
    "Safeguards",
    """
    <p>This tool includes multiple safeguards to prevent it from providing legal advice:</p>
    <ul>
        <li>Strict system prompts instruct the AI to provide only factual information from official sources</li>
        <li>Input classification detects questions asking for legal advice and routes them to a disclaimer</li>
        <li>Output filtering scans AI responses for patterns suggesting legal advice and appends warnings</li>
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
        <li>Your university's international student office (may maintain a list of recommended attorneys)</li>
    </ul>
    """,
)

content_max += render_card(
    "Limitations",
    """
    <p>This tool has the following limitations:</p>
    <ul>
        <li>Information is sourced from government websites and may not reflect the most recent policy changes at the time of use.</li>
        <li>Visa processing times and appointment availability vary by embassy and consulate and change frequently.</li>
        <li>US immigration law and regulations change periodically. Always verify information with official sources.</li>
        <li>The chatbot may not have answers for highly specific or unusual questions.</li>
        <li>This tool does not provide information about visas for countries outside the United States.</li>
    </ul>
    """,
)

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
