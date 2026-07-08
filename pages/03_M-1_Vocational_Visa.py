"""
M-1 Vocational Student Visa - Dedicated information page.
Page: 03_M-1_Vocational_Visa.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_card, render_source_citations, render_floating_chat
from shared.components import render_coming_soon, render_chat_placeholder

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="M-1 Vocational Student - US Student Visa Information Resource",
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
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">M-1 Vocational Student Visa</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        The M-1 visa is for nonimmigrant students pursuing a vocational or technical program
        in the United States that is primarily practical rather than academic in nature.
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
    <p>The M-1 visa is for students enrolled in vocational or technical programs at SEVP-approved
    institutions. Vocational programs include trade school, technical school, mechanical or auto
    repair, culinary arts, cosmetology, and other nonacademic programs. Unlike the F-1 visa,
    which covers academic study, the M-1 visa is specifically for practical or technical training.</p>
    <p>M-1 students are classified under section 101(a)(15)(M) of the Immigration and Nationality Act.</p>
    """,
)

# Key differences from F-1
content_max += render_card(
    "Key Differences from F-1 Visa",
    """
    <ul>
        <li><strong>Program length:</strong> M-1 status is generally limited to 1 year, with possible extensions not exceeding 3 years total. F-1 has no such fixed limit.</li>
        <li><strong>Transfers:</strong> M-1 students may only transfer to another vocational program at the same level or higher. Transferring to a lower-level program requires restarting the program clock.</li>
        <li><strong>Work authorization:</strong> M-1 students are not authorized to work during their program. After completing studies, they may be eligible for practical training on a temporary basis.</li>
        <li><strong>Dependents:</strong> M-2 dependents may attend school but may not engage in employment.</li>
        <li><strong>No OPT:</strong> M-1 students are not eligible for Optional Practical Training (OPT). Only post-completion practical training (up to 1 month per 15 months of study) is available.</li>
    </ul>
    """,
)

# Required documents
content_max += render_card(
    "Documents Needed for Visa Application",
    """
    <ul>
        <li>Form I-20, Certificate of Eligibility for Nonimmigrant Student Status (issued by SEVP-approved vocational school)</li>
        <li>Valid passport (must be valid for at least 6 months beyond intended period of stay)</li>
        <li>Form DS-160 confirmation page (Online Nonimmigrant Visa Application)</li>
        <li>Visa application fee receipt</li>
        <li>SEVIS fee (I-901) payment receipt</li>
        <li>Photograph meeting US visa requirements (2x2 inches, white background)</li>
        <li>Financial evidence demonstrating ability to cover tuition and living expenses</li>
        <li>Admission letter from the vocational school</li>
    </ul>
    """,
)

# Fees
content_max += render_card(
    "Fees",
    """
    <ul>
        <li><strong>MRV Visa Application Fee:</strong> $185 (non-refundable, paid before interview appointment)</li>
        <li><strong>SEVIS I-901 Fee:</strong> $220 for M-1 students (paid online at fmjfee.gov before the interview)</li>
        <li><strong>Reciprocity Fee:</strong> Varies by country; check travel.state.gov for country-specific fees</li>
    </ul>
    <p>Fee amounts are subject to change. Verify current fees at travel.state.gov before applying.</p>
    """,
)

# Application process
content_max += render_card(
    "Application Process",
    """
    <ol>
        <li>Apply to and receive admission from a SEVP-approved vocational or technical school.</li>
        <li>Receive Form I-20 from the school after accepting admission and providing financial documentation.</li>
        <li>Pay the SEVIS I-901 fee online at fmjfee.gov.</li>
        <li>Complete the online DS-160 visa application at ceac.state.gov.</li>
        <li>Pay the MRV visa application fee.</li>
        <li>Schedule a visa interview appointment at the nearest US embassy or consulate.</li>
        <li>Attend the visa interview with required documents.</li>
        <li>If approved, receive the visa stamp in passport. Enter the US within 30 days of the program start date.</li>
    </ol>
    """,
)

# Common refusal reasons
content_max += render_card(
    "Common Refusal Reasons",
    """
    <ul>
        <li>Failure to demonstrate strong ties to home country (immigrant intent under INA Section 214(b))</li>
        <li>Insufficient financial evidence to cover program expenses</li>
        <li>Program does not qualify as vocational or technical in nature</li>
        <li>Invalid or expired Form I-20</li>
        <li>Previous violations of US immigration law</li>
        <li>Incomplete or inconsistent documentation</li>
    </ul>
    """,
)

# Processing times
content_max += render_card(
    "Processing Times",
    """
    <p>Visa processing times vary by US embassy or consulate. Check current appointment availability
    and processing estimates at travel.state.gov for your specific location.</p>
    """ + render_coming_soon("Live processing times data") + """
    """,
)

# Sources
content_max += render_source_citations([
    {"title": "US Department of State - M-1 Vocational Student", "url": "https://travel.state.gov/content/travel/en/us-visas/study/other-study-options/vocational-students.html"},
    {"title": "USCIS - M Vocational Student", "url": "https://www.uscis.gov/m-vocational-student"},
    {"title": "SEVP - Student and Exchange Visitor Program", "url": "https://studyinthestates.dhs.gov"},
])

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

# -------------------------------------------------------
# Chat for follow-up
# -------------------------------------------------------
st.markdown('<div style="max-width:900px; margin:0 auto; padding:1.5rem 1rem;">', unsafe_allow_html=True)
st.markdown('<h3 style="color:#1a365d;">Have a specific M-1 question?</h3>', unsafe_allow_html=True)
st.markdown(render_chat_placeholder(), unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
