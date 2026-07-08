"""
I-485 Application - Dedicated information page.
Page: 04_I-485_Application.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_chat_placeholder, render_card

st.set_page_config(
    page_title="I-485 Application - US Visa Information Resource",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(render_nav_bar(), unsafe_allow_html=True)
st.markdown(render_disclaimer(), unsafe_allow_html=True)

st.markdown("""
<div style="max-width:900px; margin:0 auto; padding:2rem 1rem 1rem;">
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">I-485 Application</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        Application to Register Permanent Residence or Adjust Status. Filed by individuals
        already in the US who wish to become lawful permanent residents.
    </p>
</div>
""", unsafe_allow_html=True)

content_max = '<div style="max-width:900px; margin:0 auto; padding:0 1rem;">'

content_max += render_card(
    "Overview",
    """
    <p>Form I-485, Application to Register Permanent Residence or Adjust Status, is used by
    eligible immigrants to apply for a green card while they are physically present in the United States.
    Eligibility depends on the basis of the application, such as family sponsorship, employment,
    asylum, or other categories.</p>
    """,
)

content_max += render_card(
    "Documents Needed",
    """
    <ul>
        <li>Form I-485 (complete and signed)</li>
        <li>Two passport-style photographs</li>
        <li>Form I-693, Report of Medical Examination and Vaccination Record</li>
        <li>Copy of approved petition (I-130, I-140, etc.) or evidence of eligibility</li>
        <li>Copy of Form I-94 (arrival/departure record)</li>
        <li>Form I-864, Affidavit of Support (if applicable)</li>
        <li>Financial documents demonstrating ability to support yourself</li>
        <li>Police clearance certificates (if required)</li>
    </ul>
    """,
)

content_max += render_card(
    "Fees",
    """
    <p>The I-485 filing fee includes the application fee and biometrics fee. Current amounts are
    published in the USCIS Fee Index. Fee waivers may be available for certain applicants who
    demonstrate financial hardship. Check uscis.gov for current fees and waiver eligibility.</p>
    """,
)

content_max += render_card(
    "Application Process",
    """
    <ol>
        <li>Determine eligibility based on an approved petition or other basis.</li>
        <li>Prepare Form I-485 and gather supporting documents.</li>
        <li>Complete a medical examination with a USCIS-approved doctor.</li>
        <li>File the application with USCIS (by mail or online) with fees.</li>
        <li>Attend a biometrics appointment for fingerprinting and background check.</li>
        <li>Attend an in-person interview at a USCIS office (if required).</li>
        <li>Receive a decision. If approved, the green card is mailed to the applicant.</li>
    </ol>
    """,
)

content_max += render_card(
    "Common Refusal Reasons",
    """
    <ul>
        <li>Ineligible under the applicable category</li>
        <li>Failure to maintain lawful status (where required)</li>
        <li>Incomplete application or missing documents</li>
        <li>Criminal history or grounds of inadmissibility</li>
        <li>Failure to attend the scheduled interview</li>
    </ul>
    """,
)

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

st.markdown('<div style="max-width:900px; margin:0 auto; padding:1.5rem 1rem;">', unsafe_allow_html=True)
st.markdown('<h3 style="color:#1a365d;">Have a specific I-485 question?</h3>', unsafe_allow_html=True)
st.markdown(render_chat_placeholder(), unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(render_footer(), unsafe_allow_html=True)
