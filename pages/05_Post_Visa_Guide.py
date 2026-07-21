"""Post-Arrival Guide for international students."""

import datetime

import streamlit as st
from shared.branding import FAVICON

from shared.components import (
    render_card,
    render_disclaimer,
    render_floating_chat,
    render_footer,
    render_hamburger_menu,
    render_profile_banner,
    render_reminders_banner,
    render_section,
    render_source_citations,
)
from shared.reminders import compute_reminders
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.vera_state import get_vera_state, set_post_visa_dates

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
# Staying in status: expirations and reportable changes
# -------------------------------------------------------
st.markdown(render_section("Staying in Status: Expirations & Changes"), unsafe_allow_html=True)

st.markdown(render_card(
    title="Visa and Passport Expiration",
    content_html="""
    <p>Your F-1 <strong>status</strong> and your visa <strong>stamp</strong> are not the same thing. Your
    status (how long you can stay and study) is tied to your I-20's program end date plus any authorized
    grace period, not to the visa stamp in your passport — a visa can expire while you remain in valid
    status inside the US, and you would only need a valid visa stamp again to re-enter the country after
    travel abroad.</p>
    <ul>
        <li>Your passport must generally stay valid at least six months beyond any date you plan to travel — check with your embassy or consulate for your country's exact rule, since practices vary.</li>
        <li>If your passport is due to expire, renew it through your home country's embassy or consulate in the US before it lapses.</li>
        <li>If your visa stamp will be expired the next time you plan to re-enter the US, you would need to apply for a new one at a US embassy or consulate before that trip — the DS-160/interview process is the same one used for the original visa.</li>
    </ul>
    """,
    link_text="SEVP - Extending or Maintaining Status",
    link_href="https://studyinthestates.dhs.gov/students",
), unsafe_allow_html=True)

_post_visa = get_vera_state().get("post_visa", {})


def _parse(value):
    try:
        return datetime.date.fromisoformat(value) if value else None
    except ValueError:
        return None


st.markdown(
    """
    <div style="max-width:1200px;margin:0 0 8px;padding:0 1rem">
      <p style="font-size:13px;color:var(--text-secondary);margin:0">
        Enter these once and Vera will remind you here, and on your timeline, as they
        approach — in-account only for now, no email yet.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
_, _pc1, _pc2, _ = st.columns([1, 3, 3, 1])
with _pc1:
    _visa_exp = st.date_input(
        "Visa expiration date", value=_parse(_post_visa.get("visa_expiration")),
        format="YYYY-MM-DD",
    )
with _pc2:
    _passport_exp = st.date_input(
        "Passport expiration date", value=_parse(_post_visa.get("passport_expiration")),
        format="YYYY-MM-DD",
    )
_new_visa_exp = _visa_exp.isoformat() if _visa_exp else ""
_new_passport_exp = _passport_exp.isoformat() if _passport_exp else ""
if (_new_visa_exp, _new_passport_exp) != (
    _post_visa.get("visa_expiration", ""), _post_visa.get("passport_expiration", "")
):
    set_post_visa_dates(_new_visa_exp, _new_passport_exp)
    st.rerun()

render_reminders_banner(compute_reminders(get_vera_state().get("post_visa", {})))

st.markdown(render_card(
    title="Reporting a Major, Course, or Employment Change",
    content_html="""
    <p>Certain changes must be reported to your DSO so your SEVIS record stays accurate — this is a factual
    SEVIS/school-administration requirement, not something you self-file with USCIS:</p>
    <ul>
        <li><strong>Changing your major or degree program</strong> — report it to your DSO, who updates SEVIS; this can affect your I-20's program end date.</li>
        <li><strong>Dropping below full-time enrollment</strong> — must be pre-approved by your DSO except in narrow, documented circumstances (e.g. academic difficulty, medical reasons); reporting after the fact is not sufficient.</li>
        <li><strong>Starting or changing on-campus or authorized off-campus employment (e.g. CPT/OPT)</strong> — must be authorized and recorded by your DSO before you begin, or by USCIS for OPT employment authorization.</li>
        <li><strong>Changing your US address</strong> — report to your DSO within 10 days of the move so SEVIS stays current.</li>
    </ul>
    <p style="margin-top:1rem;">Your school's international student office is the first point of contact for all of these — they submit the actual SEVIS update on your behalf.</p>
    """,
    link_text="SEVP - Reporting Requirements for F-1 Students",
    link_href="https://studyinthestates.dhs.gov/f-students",
), unsafe_allow_html=True)

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
    <p>International students on F-1 visas are considered nonresident aliens for tax purposes during their first five years in the US. You must file tax returns if you:</p>
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
