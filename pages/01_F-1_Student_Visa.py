"""
F-1 Student Visa - Dedicated information page.
Page: 01_F-1_Student_Visa.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_card, render_source_citations, render_floating_chat
from shared.components import render_coming_soon, render_chat_placeholder

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="F-1 Student Visa - US Student Visa Information Resource",
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
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">F-1 Student Visa</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        The F-1 visa is for academic students seeking admission to an accredited US academic institution
        or language training program. It is the most common visa for international students pursuing degrees.
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
    <p>The F-1 nonimmigrant visa category allows students to study at a US college, university,
    seminary, conservatory, academic high school, elementary school, or other educational institution,
    including language training programs. It is classified under section 101(a)(15)(F) of the
    Immigration and Nationality Act.</p>
    <p>To qualify, a student must be enrolled in a program that requires full-time study,
    demonstrate proficiency in English or enrollment in English language training, and be able to
    show sufficient funds to cover tuition and living expenses without unauthorized employment.</p>
    """,
)

# Required documents
content_max += render_card(
    "Documents Needed for Visa Application",
    """
    <ul>
        <li>Form I-20, Certificate of Eligibility for Nonimmigrant Student Status (issued by SEVP-approved school)</li>
        <li>Valid passport (must be valid for at least 6 months beyond intended period of stay)</li>
        <li>Form DS-160 confirmation page (Online Nonimmigrant Visa Application)</li>
        <li>Visa application fee receipt</li>
        <li>SEVIS fee (I-901) payment receipt</li>
        <li>Photograph meeting US visa requirements (2x2 inches, white background)</li>
        <li>Financial evidence demonstrating ability to cover tuition and living expenses (bank statements, scholarship letters, sponsor letters)</li>
        <li>Academic transcripts, diplomas, and standardized test scores (TOEFL, IELTS, GRE, SAT)</li>
        <li>Admission letter from the US educational institution</li>
    </ul>
    """,
)

# Fees
content_max += render_card(
    "Fees",
    """
    <ul>
        <li><strong>MRV Visa Application Fee:</strong> $185 (non-refundable, paid before interview appointment)</li>
        <li><strong>SEVIS I-901 Fee:</strong> $350 for F-1 students (paid online at fmjfee.gov before the interview)</li>
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
        <li>Apply to and receive admission from a SEVP-approved US educational institution.</li>
        <li>Receive Form I-20 from the school after accepting admission and providing financial documentation.</li>
        <li>Pay the SEVIS I-901 fee online at fmjfee.gov.</li>
        <li>Complete the online DS-160 visa application at ceac.state.gov.</li>
        <li>Pay the MRV visa application fee.</li>
        <li>Schedule a visa interview appointment at the nearest US embassy or consulate.</li>
        <li>Attend the visa interview with required documents (I-20, passport, DS-160 confirmation, fee receipts, financial evidence).</li>
        <li>If approved, receive the visa stamp in passport. Some applicants may be subject to administrative processing.</li>
        <li>Enter the US within 30 days of the program start date on the I-20.</li>
    </ol>
    """,
)

# Work authorization
content_max += render_card(
    "Work Authorization for F-1 Students",
    """
    <ul>
        <li><strong>On-campus employment:</strong> F-1 students may work on campus up to 20 hours per week during school sessions and full time during breaks. No additional authorization required beyond valid F-1 status.</li>
        <li><strong>CPT (Curricular Practical Training):</strong> Work authorization for off-campus employment directly related to the major field of study. Requires recommendation from the Designated School Official (DSO) before beginning work.</li>
        <li><strong>OPT (Optional Practical Training):</strong> Temporary employment directly related to the student's major area of study. Requires approval from USCIS via Form I-765. Available for up to 12 months after completing studies. STEM degree holders may be eligible for a 24-month extension.</li>
    </ul>
    """,
)

# Common refusal reasons
content_max += render_card(
    "Common Refusal Reasons",
    """
    <ul>
        <li>Failure to demonstrate sufficient financial resources to cover tuition and living expenses</li>
        <li>Failure to establish strong ties to home country (immigrant intent under INA Section 214(b))</li>
        <li>Invalid or expired Form I-20</li>
        <li>Incomplete or inconsistent documentation</li>
        <li>Failure to prove intent to return home after studies are completed</li>
        <li>Previous violations of US immigration law</li>
        <li>Inadequate English proficiency without enrollment in language training</li>
    </ul>
    <p>Refusal under INA Section 214(b) is the most common: the consular officer was not convinced the applicant intends to return to their home country after studies.</p>
    """,
)

# Processing times
content_max += render_card(
    "Processing Times",
    """
    <p>Visa processing times vary by US embassy or consulate and by season. Summer months (May-August)
    typically see higher demand and longer wait times. Check current appointment availability and
    processing estimates at travel.state.gov for your specific location.</p>
    """ + render_coming_soon("Live processing times data") + """
    """,
)

# Sources
content_max += render_source_citations([
    {"title": "US Department of State - F-1 Student Visa", "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html"},
    {"title": "USCIS - International Students", "url": "https://www.uscis.gov/international-students-academics"},
    {"title": "SEVP - Student and Exchange Visitor Program", "url": "https://studyinthestates.dhs.gov"},
])

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

# -------------------------------------------------------
# Chat for follow-up
# -------------------------------------------------------
st.markdown('<div style="max-width:900px; margin:0 auto; padding:1.5rem 1rem;">', unsafe_allow_html=True)
st.markdown('<h3 style="color:#1a365d;">Have a specific F-1 question?</h3>', unsafe_allow_html=True)
st.markdown(render_chat_placeholder(), unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
