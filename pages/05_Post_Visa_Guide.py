"""Post-Arrival Guide for international students."""

import streamlit as st
from shared.branding import FAVICON

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

st.set_page_config(page_title="Post-Arrival Guide", page_icon=FAVICON, layout="wide")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu(visa_type=get_vera_state().get("profile", {}).get("visa_type") or "f-1")
st.markdown(render_disclaimer(), unsafe_allow_html=True)
render_profile_banner()

st.markdown("""
<div style="max-width:1200px; margin:0 auto; padding:2rem 1rem 0;">
    <h1 style="font-size:1.75rem; font-weight:700; color:#5b4380; margin:0 0 0.5rem;">
        Post-Arrival Guide for International Students
    </h1>
    <p style="color:#4a5568; font-size:1rem; margin:0 0 2rem;">
        Essential steps to complete after arriving in the US on a student visa.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Reporting Requirements
# -------------------------------------------------------
st.markdown(render_section("Reporting Requirements"), unsafe_allow_html=True)

st.markdown(render_card(
    title="Arrival Reporting",
    content_html="""
    <p>After arriving in the US, you must report your arrival to your designated school official (DSO) or responsible officer (RO). Your school will update your SEVIS record with your arrival information.</p>
    <p>Key reporting requirements include:</p>
    <ul>
        <li>Report arrival to your DSO within the first week of arriving in the US</li>
        <li>Verify your address and contact information are correct in SEVIS</li>
        <li>Register for classes and maintain full-time enrollment status</li>
        <li>Report any changes to your address, phone number, or email within 10 days</li>
        <li>Report any changes to your major, degree program, or completion date</li>
    </ul>
    """,
    link_text="SEVP Student Reporting Requirements",
    link_href="https://studyinthestates.dhs.gov/f-students",
), unsafe_allow_html=True)

# -------------------------------------------------------
# Social Security Number
# -------------------------------------------------------
st.markdown(render_section("Applying for a Social Security Number"), unsafe_allow_html=True)

st.markdown(render_card(
    title="Social Security Administration (SSA)",
    content_html="""
    <p>If you have an on-campus job offer or off-campus employment authorization, you may apply for a Social Security Number (SSN). You must apply in person at a local SSA office.</p>
    <p>Required documents include:</p>
    <ul>
        <li>Valid passport with current US visa</li>
        <li>Form I-20 or DS-2019</li>
        <li>Form I-94 arrival record</li>
        <li>Job offer letter from employer showing on-campus employment or work authorization</li>
        <li>Proof of US address (lease agreement, utility bill, or bank statement)</li>
        <li>Two additional documents from the SSA acceptable documents list</li>
    </ul>
    <p style="margin-top:1rem;">Note: You cannot apply for an SSN immediately upon arrival. Wait at least one week after arriving and only after receiving a job offer or work authorization.</p>
    """,
    link_text="SSA - Apply for an SSN",
    link_href="https://www.ssa.gov/foreign/immigrant/apply.html",
), unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://www.ssa.gov/foreign/immigrant/apply.html",
        "title": "Apply for an SSN - SSA",
        "agency": "SSA",
        "section": "SSN Application",
    },
]), unsafe_allow_html=True)

# -------------------------------------------------------
# Bank Account
# -------------------------------------------------------
st.markdown(render_section("Opening a Bank Account"), unsafe_allow_html=True)

st.markdown(render_card(
    title="US Bank Account",
    content_html="""
    <p>Opening a US bank account is highly recommended for managing your finances while studying in the US. Most banks require the following documents:</p>
    <ul>
        <li>Valid passport with US visa</li>
        <li>Form I-20 or DS-2019</li>
        <li>Form I-94 arrival record</li>
        <li>Proof of US address</li>
        <li>Initial deposit (amount varies by bank)</li>
    </ul>
    <p style="margin-top:1rem;">Many universities have partnerships with specific banks that offer student accounts with no minimum balance or monthly fees. Check with your school's international student office for recommendations.</p>
    """,
), unsafe_allow_html=True)

# -------------------------------------------------------
# State ID and Driver's License
# -------------------------------------------------------
st.markdown(render_section("State ID and Driver's License"), unsafe_allow_html=True)

st.markdown(render_card(
    title="Department of Motor Vehicles (DMV)",
    content_html="""
    <p>You can apply for a state ID card or driver's license at your local Department of Motor Vehicles (DMV). Requirements vary by state but typically include:</p>
    <ul>
        <li>Valid passport with US visa</li>
        <li>Form I-20 or DS-2019</li>
        <li>Form I-94 arrival record</li>
        <li>Proof of US address (two documents required in most states)</li>
        <li>SSN or ITIN (if you have one)</li>
        <li>Passport-style photograph</li>
        <li>Completion of written and driving tests (for driver's license)</li>
    </ul>
    <p style="margin-top:1rem;">Note: Some states allow you to apply for a state ID without an SSN, but most require an SSN or ITIN for a driver's license. Check your state DMV website for specific requirements.</p>
    """,
    link_text="USCIS - International Students and Academics",
    link_href="https://www.uscis.gov/international-students-academics",
), unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://www.uscis.gov/international-students-academics",
        "title": "International Students and Academics - USCIS",
        "agency": "USCIS",
        "section": "State ID Requirements",
    },
]), unsafe_allow_html=True)

# -------------------------------------------------------
# Tax Obligations
# -------------------------------------------------------
st.markdown(render_section("Tax Obligations"), unsafe_allow_html=True)

st.markdown(render_card(
    title="Internal Revenue Service (IRS)",
    content_html="""
    <p>International students on F-1 and J-1 visas are considered nonresident aliens for tax purposes during their first five years in the US. You must file tax returns if you:</p>
    <ul>
        <li>Received any income from US sources (on-campus work, assistantships, internships)</li>
        <li>Received a scholarship, fellowship, or grant</li>
        <li>Have US-source investment income (interest, dividends)</li>
    </ul>
    <p style="margin-top:1rem;">Required forms include:</p>
    <ul>
        <li><strong>Form 1040-NR</strong> - US Nonresident Alien Income Tax Return</li>
        <li><strong>Form 8843</strong> - Explanation for Individual Unable to Meet the Substantial Presence Test</li>
        <li><strong>W-7</strong> - Application for IRS Individual Taxpayer Identification Number (ITIN)</li>
    </ul>
    <p style="margin-top:1rem;">Many universities offer free tax preparation services for international students during tax season. Check with your school's international student office.</p>
    """,
    link_text="IRS - Nonresident Alien Tax Information",
    link_href="https://www.irs.gov/individuals/international-taxes/nonresident-alien-individuals",
), unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://www.irs.gov/individuals/international-taxes/nonresident-alien-individuals",
        "title": "Nonresident Alien Individuals - IRS",
        "agency": "IRS",
        "section": "Tax Filing Requirements",
    },
]), unsafe_allow_html=True)

# -------------------------------------------------------
# Footer
# -------------------------------------------------------
st.markdown(render_footer(), unsafe_allow_html=True)

# Floating chat button
render_floating_chat()
