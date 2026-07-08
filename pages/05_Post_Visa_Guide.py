"""
Post-Arrival Guide for US Student Visa Holders.
Page: 05_Post_Visa_Guide.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_card, render_source_citations, render_floating_chat

# -------------------------------------------------------
# Page config
# -------------------------------------------------------
st.set_page_config(
    page_title="Post-Arrival Guide - US Student Visa Information Resource",
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
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">Post-Arrival Guide for Students</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        Steps to take after arriving in the US on a student visa: reporting to your school,
        applying for a Social Security Number, opening a bank account, obtaining a state ID,
        and understanding your tax obligations.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Content sections
# -------------------------------------------------------
content_max = '<div style="max-width:900px; margin:0 auto; padding:0 1rem;">'

# Reporting to school
content_max += render_card(
    "Report to Your School (SEVP/DSO Reporting)",
    """
    <p>Upon arrival in the US, F-1 and M-1 students must report to their Designated School Official (DSO)
    to activate their SEVIS record. J-1 students must report to their program sponsor or Responsible
    Officer (RO).</p>
    <ul>
        <li>F-1/M-1: Report to your DSO within the first week of arriving, or by the date specified in your I-20. The DSO will update SEVIS with your arrival information and address.</li>
        <li>J-1: Report to your program sponsor or RO within 30 days of arrival to verify your SEVIS record and address.</li>
        <li>Keep your address updated with your DSO/RO at all times. You must report address changes within 10 days.</li>
        <li>Carry your I-20 (or DS-2019) and passport at all times as proof of status.</li>
    </ul>
    """,
)

# Social Security Number
content_max += render_card(
    "Social Security Number (SSN)",
    """
    <p>F-1 students with on-campus work authorization, CPT, or OPT approval can apply for an SSN
    through the Social Security Administration. J-1 students with work authorization may also apply.</p>
    <ul>
        <li>Complete Form SS-5, Application for a Social Security Card</li>
        <li>Bring your passport, visa, I-94 arrival record, and I-20 (or DS-2019)</li>
        <li>F-1 students: bring a job offer letter from the university or an approved EAD (for CPT/OPT)</li>
        <li>Visit a local Social Security Administration office in person</li>
        <li>SSN cards are typically mailed within 7-14 business days</li>
        <li>M-1 students are generally not eligible for an SSN during their program</li>
    </ul>
    <div class="source-citation">
        Source: <a href="https://www.ssa.gov" target="_blank">ssa.gov</a>
    </div>
    """,
)

# Opening a bank account
content_max += render_card(
    "Opening a Bank Account",
    """
    <p>Requirements vary by bank. Generally you will need:</p>
    <ul>
        <li>Valid passport with US student visa</li>
        <li>I-20 or DS-2019 form</li>
        <li>I-94 arrival record</li>
        <li>SSN or ITIN (some banks accept an alternative such as your I-20 and passport)</li>
        <li>Proof of address (utility bill, lease agreement, or school acceptance letter with US address)</li>
        <li>Initial deposit (varies by bank)</li>
    </ul>
    <p>Some banks have specific programs for international students. Contact individual banks for their requirements.
    Consider banks with branches near your campus for convenience.</p>
    """,
)

# State ID / Driver's License
content_max += render_card(
    "State ID or Driver's License",
    """
    <p>Each state has its own requirements for issuing IDs and driver's licenses to student visa holders.
    Generally you will need:</p>
    <ul>
        <li>Valid visa and I-94 record</li>
        <li>I-20 or DS-2019 form as proof of student status</li>
        <li>Proof of state residency (utility bill, lease, bank statement, school enrollment verification)</li>
        <li>SSN or proof of SSN application</li>
        <li>Passport</li>
        <li>Pass the written test and vision test (for driver's license)</li>
        <li>Pay the state fee</li>
    </ul>
    <p>Contact your state's DMV for specific requirements. Some states accept an I-20 as proof of residency.</p>
    """,
)

# Tax obligations
content_max += render_card(
    "Tax Obligations for International Students",
    """
    <p>Student visa holders are generally required to file federal and state tax returns, even if no US income was earned.</p>
    <ul>
        <li>File Form 1040-NR (Nonresident Alien Individual US Income Tax Return) for most nonresident students. After 5 calendar years, the substantial presence test may classify you as a resident alien for tax purposes, in which case you file Form 1040.</li>
        <li>Report all US-source income including on-campus wages, research/teaching assistantships, and scholarships (portion that is not tuition).</li>
        <li>Use your SSN or apply for an ITIN (Individual Taxpayer Identification Number) via Form W-7 if you do not have an SSN and have a filing obligation.</li>
        <li>File state tax returns where applicable.</li>
        <li>Treaty benefits: If your country has a tax treaty with the US, you may be eligible for exemptions or reductions. File Form 1040-NR with treaty claims as appropriate.</li>
        <li>Deadlines: Federal and state tax returns are generally due by April 15 of the following year.</li>
    </ul>
    <div class="source-citation">
        Source: <a href="https://www.irs.gov/individuals/international-taxes/nonresident-alien-individuals" target="_blank">irs.gov - Nonresident Alien Tax Information</a>
    </div>
    """,
)

# Health insurance
content_max += render_card(
    "Health Insurance",
    """
    <p>Many US universities require international students to carry health insurance. Options include:</p>
    <ul>
        <li>University-sponsored health insurance plan (often mandatory for the first year)</li>
        <li>Private health insurance plans meeting university requirements</li>
        <li>Some J-1 exchange programs include health insurance as part of the program</li>
    </ul>
    <p>Check with your university's international student office for minimum coverage requirements. The Affordable
    Care Act requires all individuals in the US to have minimum essential health coverage, though nonresident
    aliens may qualify for a transitional relief exemption.</p>
    """,
)

# Important notes
content_max += render_card(
    "Important Notes",
    """
    <p>Requirements and procedures vary by state and by visa type. Always verify requirements
    with the relevant state and federal agencies and your school's international student office.
    This information is for general guidance only and does not constitute legal advice.</p>
    <p>Key documents to keep organized:</p>
    <ul>
        <li>Passport with valid visa</li>
        <li>I-20 (F-1/M-1) or DS-2019 (J-1) with latest DSO/RO signature</li>
        <li>I-94 arrival record (available online at i94.cbp.dhs.gov)</li>
        <li>SSN card (if applicable)</li>
        <li>Financial documents and scholarship letters</li>
        <li>State ID or driver's license</li>
    </ul>
    """,
)

# Sources
content_max += render_source_citations([
    {"title": "Social Security Administration - SSN for Immigrants", "url": "https://www.ssa.gov/foreign/immigrant/apply.html"},
    {"title": "IRS - Nonresident Alien Tax Information", "url": "https://www.irs.gov/individuals/international-taxes/nonresident-alien-individuals"},
    {"title": "USCIS - International Students", "url": "https://www.uscis.gov/international-students-academics"},
    {"title": "CBP - I-94 Arrival/Departure Record", "url": "https://i94.cbp.dhs.gov"},
])

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)
