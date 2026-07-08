"""
J-1 Exchange Visitor Visa - Dedicated information page.
Page: 02_J-1_Exchange_Visitor.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_card, render_source_citations, render_floating_chat
from shared.components import render_coming_soon, render_chat_placeholder

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="J-1 Exchange Visitor - US Student Visa Information Resource",
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
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">J-1 Exchange Visitor Visa</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        The J-1 visa is for individuals approved to participate in work and study-based exchange visitor
        programs in the US. It covers students, scholars, trainees, teachers, and researchers.
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
    <p>The J-1 exchange visitor visa is designed for participants in programs approved by the US
    Department of State. It promotes cultural exchange through work and study-based activities. J-1
    students are sponsored by designated exchange visitor programs that issue the DS-2019 form.</p>
    <p>J-1 categories relevant to students include:</p>
    <ul>
        <li><strong>Student:</strong> Enrolled in academic study programs (similar to F-1 but under the exchange visitor framework).</li>
        <li><strong>Research Scholar:</strong> Researchers and postdoctoral scholars.</li>
        <li><strong>Summer Work Travel:</strong> Short-term employment during summer vacation for enrolled students.</li>
        <li><strong>Trainee:</strong> Recent graduates seeking supervised training in their field.</li>
    </ul>
    """,
)

# Required documents
content_max += render_card(
    "Documents Needed for Visa Application",
    """
    <ul>
        <li>Form DS-2019, Certificate of Eligibility for Exchange Visitor Status (issued by the exchange program sponsor)</li>
        <li>Valid passport (must be valid for at least 6 months beyond intended period of stay)</li>
        <li>Form DS-160 confirmation page (Online Nonimmigrant Visa Application)</li>
        <li>Visa application fee receipt</li>
        <li>SEVIS fee (I-901) payment receipt</li>
        <li>Photograph meeting US visa requirements (2x2 inches, white background)</li>
        <li>Financial evidence demonstrating ability to cover all expenses as stated on DS-2019</li>
        <li>Program invitation letter or evidence of acceptance</li>
        <li>Academic and professional documents supporting the exchange program</li>
    </ul>
    """,
)

# Fees
content_max += render_card(
    "Fees",
    """
    <ul>
        <li><strong>MRV Visa Application Fee:</strong> $185 (non-refundable, paid before interview appointment)</li>
        <li><strong>SEVIS I-901 Fee:</strong> $220 for J-1 students (varies by program category; paid at fmjfee.gov)</li>
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
        <li>Apply to and accept placement in a US Department of State-approved exchange visitor program.</li>
        <li>Receive Form DS-2019 from the exchange program sponsor.</li>
        <li>Pay the SEVIS I-901 fee online at fmjfee.gov.</li>
        <li>Complete the online DS-160 visa application at ceac.state.gov.</li>
        <li>Pay the MRV visa application fee.</li>
        <li>Schedule a visa interview appointment at the nearest US embassy or consulate.</li>
        <li>Attend the visa interview with required documents (DS-2019, passport, DS-160 confirmation, fee receipts, financial evidence).</li>
        <li>If approved, receive the visa stamp in passport.</li>
        <li>Enter the US within 30 days of the program start date on the DS-2019.</li>
    </ol>
    """,
)

# Two-year home residency requirement
content_max += render_card(
    "Two-Year Home Country Physical Presence Requirement",
    """
    <p>Some J-1 exchange visitors are subject to the two-year home country physical presence requirement
    under INA Section 212(e). This means they must return to their home country for two years before
    being eligible for certain US immigrant visas or changing status to H-1B.</p>
    <p>This requirement typically applies if:</p>
    <ul>
        <li>The exchange visitor's government or an externally funded program provided a grant, scholarship, or funding.</li>
        <li>The field of study or research is on the US Department of State's Exchange Visitor Skills List for their country.</li>
        <li>The exchange visitor is coming to the US for graduate medical training or research.</li>
    </ul>
    """,
)

# Common refusal reasons
content_max += render_card(
    "Common Refusal Reasons",
    """
    <ul>
        <li>Failure to demonstrate strong ties to home country (immigrant intent under INA Section 214(b))</li>
        <li>Failure to meet the requirements of the specific exchange visitor category</li>
        <li>Invalid or expired Form DS-2019</li>
        <li>Inadequate financial support for the program duration</li>
        <li>Previous violations of US immigration law</li>
        <li>Subject to two-year home residency requirement without a waiver</li>
        <li>Insufficient English proficiency for the program</li>
    </ul>
    """,
)

# Processing times
content_max += render_card(
    "Processing Times",
    """
    <p>Visa processing times vary by US embassy or consulate and by season. J-1 applications may require
    additional administrative processing. Check current appointment availability and processing estimates
    at travel.state.gov for your specific location.</p>
    """ + render_coming_soon("Live processing times data") + """
    """,
)

# Sources
content_max += render_source_citations([
    {"title": "US Department of State - J-1 Exchange Visitor Program", "url": "https://travel.state.gov/content/travel/en/us-visas/study/exchange-visitor.html"},
    {"title": "Department of State - Exchange Visitor Program", "url": "https://exchanges.state.gov"},
    {"title": "USCIS - J Exchange Visitor", "url": "https://www.uscis.gov/j-exchange-visitor"},
])

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

# -------------------------------------------------------
# Chat for follow-up
# -------------------------------------------------------
st.markdown('<div style="max-width:900px; margin:0 auto; padding:1.5rem 1rem;">', unsafe_allow_html=True)
st.markdown('<h3 style="color:#1a365d;">Have a specific J-1 question?</h3>', unsafe_allow_html=True)
st.markdown(render_chat_placeholder(), unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
