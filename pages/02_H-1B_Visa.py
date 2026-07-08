"""
H-1B Visa - Dedicated information page.
Page: 02_H-1B_Visa.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_chat_placeholder, render_card

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="H-1B Visa - US Visa Information Resource",
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
# Page header
# -------------------------------------------------------
st.markdown("""
<div style="max-width:900px; margin:0 auto; padding:2rem 1rem 1rem;">
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">H-1B Visa</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        Temporary work visa for specialty occupations requiring a bachelor's degree or higher.
        Covers IT, engineering, finance, and other professional fields.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Content sections
# -------------------------------------------------------
content_max = '<div style="max-width:900px; margin:0 auto; padding:0 1rem;">'

# Overview
content_max += render_card(
    "Overview",
    """
    <p>The H-1B visa allows U.S. employers to employ foreign workers in specialty occupations
    on a temporary basis. A specialty occupation requires theoretical and practical application
    of a body of highly specialized knowledge and at least a bachelor's degree in the specific
    specialty.</p>
    <p>The annual cap for new H-1B petitions is 65,000 regular cap visas plus 20,000 advanced
    degree exemption visas.</p>
    """,
)

# Required documents
content_max += render_card(
    "Documents Needed",
    """
    <ul>
        <li>Form I-129, Petition for a Nonimmigrant Worker</li>
        <li>Form I-907, Petition for Classification of Nonimmigrant Worker as H-1B1</li>
        <li>Supporting documents from the employer (offer letter, job description)</li>
        <li>Evidence of the beneficiary's qualifications (degrees, transcripts, work experience letters)</li>
        <li>Prevailing wage determination from the Department of Labor</li>
        <li>LMF (Labor Condition Application) attestation</li>
    </ul>
    """,
)

# Fees
content_max += render_card(
    "Fees",
    """
    <ul>
        <li>Base filing fee (Form I-129)</li>
        <li>ACWIA training fee (amount depends on employer size)</li>
        <li>Public Law 114-113 additional fee for H-1B petitioners</li>
        <li> fraud prevention and detection fee</li>
        <li>Optional premium processing fee for faster adjudication</li>
    </ul>
    <p>Current fee amounts are published in the USCIS Fee Index and may change. Check the latest fees at uscis.gov.</p>
    """,
)

# Process
content_max += render_card(
    "Application Process",
    """
    <ol>
        <li>Employer obtains a prevailing wage determination from the Department of Labor.</li>
        <li>Employer files a Labor Condition Application (LCA) with the Department of Labor.</li>
        <li>Employer files Form I-129 with USCIS, along with supporting documents and fees.</li>
        <li>USCIS reviews the petition. May request additional evidence (RFE).</li>
        <li>If approved, the beneficiary applies for an H-1B visa stamp at a US consulate (if outside the US) or changes status (if inside the US).</li>
    </ol>
    """,
)

# Common refusal reasons
content_max += render_card(
    "Common Refusal Reasons",
    """
    <ul>
        <li>The position does not qualify as a specialty occupation</li>
        <li>The beneficiary does not meet the educational requirements</li>
        <li>Employer-employee relationship not established</li>
        <li>The petition was selected in the lottery but found deficient during review</li>
        <li>Failure to pay required fees or submit a valid LCA</li>
    </ul>
    """,
)

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

# -------------------------------------------------------
# Chat for follow-up
# -------------------------------------------------------
st.markdown('<div style="max-width:900px; margin:0 auto; padding:1.5rem 1rem;">', unsafe_allow_html=True)
st.markdown('<h3 style="color:#1a365d;">Have a specific H-1B question?</h3>', unsafe_allow_html=True)
st.markdown(render_chat_placeholder(), unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
