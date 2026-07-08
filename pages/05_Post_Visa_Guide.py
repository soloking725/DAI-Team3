"""
Post-Visa Guide - What to do after approval.
Page: 05_Post_Visa_Guide.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_card

st.set_page_config(
    page_title="Post-Visa Guide - US Visa Information Resource",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(render_nav_bar(), unsafe_allow_html=True)
st.markdown(render_disclaimer(), unsafe_allow_html=True)

st.markdown("""
<div style="max-width:900px; margin:0 auto; padding:2rem 1rem 1rem;">
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">Post-Visa Guide</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        Steps to take after your visa is approved: applying for a Social Security Number,
        opening a bank account, obtaining a state ID or driver's license, and more.
    </p>
</div>
""", unsafe_allow_html=True)

content_max = '<div style="max-width:900px; margin:0 auto; padding:0 1rem;">'

content_max += render_card(
    "Social Security Number (SSN)",
    """
    <p>Most visa holders who are authorized to work in the US can apply for an SSN through
    the Social Security Administration.</p>
    <ul>
        <li>Complete Form SS-5, Application for a Social Security Card</li>
        <li>Bring your visa, I-94 record, and employment authorization documents</li>
        <li>Visit a local Social Security Administration office in person</li>
        <li>SSN cards are typically mailed within 2 weeks</li>
    </ul>
    <div class="source-citation">
        Source: <a href="https://www.ssa.gov" target="_blank">ssa.gov</a>
    </div>
    """,
)

content_max += render_card(
    "Opening a Bank Account",
    """
    <p>Requirements vary by bank. Generally you will need:</p>
    <ul>
        <li>Valid passport with US visa</li>
        <li>SSN or ITIN (some banks accept an alternative)</li>
        <li>Proof of address (utility bill, lease agreement)</li>
        <li>I-94 arrival record</li>
        <li>Initial deposit (varies by bank)</li>
    </ul>
    <p>Some banks have specific programs for international customers. Contact individual banks
    for their requirements.</p>
    """,
)

content_max += render_card(
    "State ID or Driver's License",
    """
    <p>Each state has its own requirements for issuing IDs and driver's licenses to visa holders.
    Generally you will need:</p>
    <ul>
        <li>Valid visa and I-94 record</li>
        <li>Proof of state residency (utility bill, lease, bank statement)</li>
        <li>SSN or proof of SSN application</li>
        <li>Passport</li>
        <li>Pass the written test and vision test (for driver's license)</li>
        <li>Pay the state fee</li>
    </ul>
    <p>Contact your state's DMV for specific requirements.</p>
    """,
)

content_max += render_card(
    "Tax Obligations",
    """
    <p>Visa holders with work authorization are generally required to file federal and state tax returns.</p>
    <ul>
        <li>File Form 1040 (or 1040-NR for nonresident aliens) with the IRS</li>
        <li>Determine residency status for tax purposes (substantial presence test)</li>
        <li>Use your SSN or apply for an ITIN if you do not have an SSN</li>
        <li>File state tax returns where applicable</li>
    </ul>
    <div class="source-citation">
        Source: <a href="https://www.irs.gov" target="_blank">irs.gov</a>
    </div>
    """,
)

content_max += render_card(
    "Important Notes",
    """
    <p>Requirements and procedures vary by state and by visa type. Always verify requirements
    with the relevant state and federal agencies. This information is for general guidance only
    and does not constitute legal advice.</p>
    """,
)

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

st.markdown(render_footer(), unsafe_allow_html=True)
