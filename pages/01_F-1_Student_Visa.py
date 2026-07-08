"""F-1 Student Visa information page."""

import streamlit as st

from shared.components import (
    render_card,
    render_disclaimer,
    render_floating_chat,
    render_footer,
    render_nav_bar,
    render_section,
    render_source_citations,
)
from shared.styles import get_global_css

st.set_page_config(page_title="F-1 Student Visa", page_icon=":book:", layout="wide")
st.markdown(get_global_css(), unsafe_allow_html=True)

render_nav_bar()
st.markdown(render_disclaimer(), unsafe_allow_html=True)

st.markdown("""
<div style="max-width:1200px; margin:0 auto; padding:2rem 1rem 0;">
    <h1 style="font-size:1.75rem; font-weight:700; color:#1a365d; margin:0 0 0.5rem;">
        F-1 Student Visa
    </h1>
    <p style="color:#4a5568; font-size:1rem; margin:0 0 2rem;">
        Academic student visa for international students pursuing studies at accredited US institutions.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Overview
# -------------------------------------------------------
st.markdown(render_section("Overview"), unsafe_allow_html=True)

st.markdown(render_card(
    title="What is the F-1 Visa?",
    content_html="""
    <p>The F-1 visa is a nonimmigrant visa for academic students seeking admission to a US academic institution or language training program certified by the Student and Exchange Visitor Program (SEVP).</p>
    <p>Key requirements include:</p>
    <ul>
        <li>Acceptance into a SEVP-certified school</li>
        <li>Ability to pay for the first year of study without unauthorized employment</li>
        <li>Maintenance of a valid F-1 status while in the US</li>
        <li>A foreign residence that you have no intention of abandoning</li>
    </ul>
    """,
    link_text="SEVP School Search",
    link_href="https://studyinthestates.dhs.gov/school-search",
), unsafe_allow_html=True)

# -------------------------------------------------------
# Required Documents
# -------------------------------------------------------
st.markdown(render_section("Required Documents"), unsafe_allow_html=True)

doc_col1, doc_col2 = st.columns(2)

with doc_col1:
    st.markdown(render_card(
        title="Core Documents",
        content_html="""
        <ul>
            <li><strong>Form I-20</strong> - Certificate of Eligibility issued by your SEVP-certified school</li>
            <li><strong>Valid passport</strong> - Must be valid for at least six months beyond your intended period of stay</li>
            <li><strong>Form DS-160</strong> - Online nonimmigrant visa application confirmation page</li>
            <li><strong>SEVIS I-901 fee receipt</strong> - Proof of payment for the SEVIS fee (currently $350)</li>
            <li><strong>Visa application fee receipt</strong> - MRV fee payment (currently $185 for F-1)</li>
            <li><strong>Photograph</strong> - 2x2 inches, taken within the last six months, white background</li>
        </ul>
        """,
    ), unsafe_allow_html=True)

with doc_col2:
    st.markdown(render_card(
        title="Supporting Documents",
        content_html="""
        <ul>
            <li><strong>Academic transcripts</strong> - From previous schools attended</li>
            <li><strong>Standardized test scores</strong> - TOEFL, IELTS, SAT, GRE, GMAT, etc.</li>
            <li><strong>Financial evidence</strong> - Bank statements, sponsorship letters, award letters showing ability to cover costs</li>
            <li><strong>Admission letter</strong> - From the US school confirming enrollment</li>
            <li><strong>Resume or CV</strong> - Especially for graduate students</li>
            <li><strong>Statement of purpose</strong> - Explaining your study plans and goals</li>
        </ul>
        """,
    ), unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
        "title": "Apply for a Student Visa - travel.state.gov",
        "agency": "State Department",
        "section": "Required Documents",
    },
]), unsafe_allow_html=True)

# -------------------------------------------------------
# Fees
# -------------------------------------------------------
st.markdown(render_section("Fee Schedule"), unsafe_allow_html=True)

st.markdown("""
<div class="content-card">
    <h3>Current Fees for F-1 Visa</h3>
    <table style="width:100%; border-collapse:collapse; margin-top:1rem;">
        <thead>
            <tr style="border-bottom:2px solid #e2e8f0;">
                <th style="text-align:left; padding:0.5rem; color:#1a365d; font-size:0.9rem;">Fee</th>
                <th style="text-align:left; padding:0.5rem; color:#1a365d; font-size:0.9rem;">Amount</th>
                <th style="text-align:left; padding:0.5rem; color:#1a365d; font-size:0.9rem;">Notes</th>
            </tr>
        </thead>
        <tbody>
            <tr style="border-bottom:1px solid #e2e8f0;">
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Visa Application Fee (MRV)</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">$185</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Nonrefundable consular processing fee</td>
            </tr>
            <tr style="border-bottom:1px solid #e2e8f0;">
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">SEVIS I-901 Fee</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">$350</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Paid to the Department of Homeland Security</td>
            </tr>
            <tr>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Reciprocity Fee</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Varies</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Some countries require an additional fee. Check your country on the State Department website.</td>
            </tr>
        </tbody>
    </table>
    <p style="font-size:0.85rem; color:#718096; margin-top:1rem;">
        Fees are current as of 2025. Visit the State Department and SEVIS websites for the most up-to-date information.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Application Process
# -------------------------------------------------------
st.markdown(render_section("Application Process"), unsafe_allow_html=True)

st.markdown("""
<div class="content-card">
    <h3>Step-by-Step Process</h3>
    <ol style="padding-left:1.5rem; margin:0.5rem 0;">
        <li style="margin-bottom:0.75rem;"><strong>Get your Form I-20</strong> - Your SEVP-certified school issues this after you accept an offer of admission and provide financial documents.</li>
        <li style="margin-bottom:0.75rem;"><strong>Pay the SEVIS I-901 fee</strong> - Pay the $350 SEVIS fee online at.fm jfs.swIFT.gov and keep the receipt.</li>
        <li style="margin-bottom:0.75rem;"><strong>Complete the DS-160</strong> - Fill out the online nonimmigrant visa application at ceac.state.gov and print the confirmation page.</li>
        <li style="margin-bottom:0.75rem;"><strong>Pay the visa application fee</strong> - Pay the $185 MRV fee and keep the receipt. Some countries also require a reciprocity fee.</li>
        <li style="margin-bottom:0.75rem;"><strong>Schedule your interview</strong> - Book a visa interview appointment at the nearest US embassy or consulate. Appointment wait times vary by location.</li>
        <li style="margin-bottom:0.75rem;"><strong>Prepare for the interview</strong> - Gather all required documents and supporting evidence of ties to your home country.</li>
        <li><strong>Attend the visa interview</strong> - Bring your passport, Form I-20, DS-160 confirmation, fee receipts, and supporting documents to your scheduled interview.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
        "title": "Apply for a Student Visa - travel.state.gov",
        "agency": "State Department",
        "section": "Application Steps",
    },
]), unsafe_allow_html=True)

# -------------------------------------------------------
# Processing Times
# -------------------------------------------------------
st.markdown(render_section("Processing Times"), unsafe_allow_html=True)

st.markdown("""
<div class="content-card">
    <h3>Visa Processing Timeline</h3>
    <p>F-1 visa processing times vary by US embassy or consulate location. The timeline typically includes:</p>
    <ul>
        <li><strong>Administrative processing:</strong> 2-10 weeks after interview in most cases</li>
        <li><strong>Appointment wait times:</strong> Varies by country, from a few days to several months</li>
        <li><strong>Peak seasons:</strong> Spring (March-May) and early fall see higher demand</li>
    </ul>
    <p style="margin-top:1rem;">Check current processing times and appointment availability at the embassy or consulate where you will apply. You can also view USCIS processing times for related I-20 transfers and extensions.</p>
</div>
""", unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://egov.uscis.gov/processing-times/",
        "title": "USCIS Processing Times",
        "agency": "USCIS",
        "section": "Processing Times",
    },
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/international-traveler.html",
        "title": "International Traveler - travel.state.gov",
        "agency": "State Department",
        "section": "Visa Wait Times",
    },
]), unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)

# Floating chat button
render_floating_chat()
