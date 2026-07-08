"""
I-129 Petition - Dedicated information page.
Page: 03_I-129_Petition.py
"""
import streamlit as st
from shared.styles import get_global_css
from shared.components import render_nav_bar, render_disclaimer, render_footer, render_chat_placeholder, render_card

st.set_page_config(
    page_title="I-129 Petition - US Visa Information Resource",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(render_nav_bar(), unsafe_allow_html=True)
st.markdown(render_disclaimer(), unsafe_allow_html=True)

st.markdown("""
<div style="max-width:900px; margin:0 auto; padding:2rem 1rem 1rem;">
    <h1 style="color:#1a365d; margin-bottom:0.5rem;">I-129 Petition</h1>
    <p style="color:#4a5568; font-size:1.05rem; line-height:1.6;">
        Nonimmigrant Worker Petition filed by employers to bring temporary or permanent workers
        to the United States. Required for H-1B, L-1, O-1, TN, and other categories.
    </p>
</div>
""", unsafe_allow_html=True)

content_max = '<div style="max-width:900px; margin:0 auto; padding:0 1rem;">'

content_max += render_card(
    "Overview",
    """
    <p>Form I-129, Petition for a Nonimmigrant Worker, is used by employers to request USCIS
    to approve a petition for a foreign worker in one of the following categories: H-1B, H-1B1,
    H-2A, H-2B, H-3, L-1, O-1, O-2, PN, Q-1, R-1, TD, or an extension of stay or change of status.</p>
    """,
)

content_max += render_card(
    "Documents Needed",
    """
    <ul>
        <li>Form I-129 (complete and signed)</li>
        <li>Supplement forms specific to the visa category (e.g., H-1B supplement)</li>
        <li>Evidence of the employer's ability to pay the required wage</li>
        <li>Supporting documentation for the beneficiary's qualifications</li>
        <li>Applicable filing fees</li>
        <li>Category-specific documents (LCA for H-1B, intracompany transfer docs for L-1, etc.)</li>
    </ul>
    """,
)

content_max += render_card(
    "Fees",
    """
    <p>Fees depend on the visa category and employer size. The base I-129 filing fee applies to
    all petitions. Additional fees may include ACWIA training fees, fraud prevention fees,
    and public law fees. Check the current USCIS Fee Index for amounts.</p>
    """,
)

content_max += render_card(
    "Application Process",
    """
    <ol>
        <li>Employer prepares and completes Form I-129 with the appropriate supplement.</li>
        <li>Employer gathers supporting documentation.</li>
        <li>Employer pays required fees.</li>
        <li>Employer files the petition with USCIS (by mail or online).</li>
        <li>USCIS reviews and may request additional evidence.</li>
        <li>If approved, the beneficiary may apply for a visa or change of status.</li>
    </ol>
    """,
)

content_max += render_card(
    "Common Refusal Reasons",
    """
    <ul>
        <li>Insufficient evidence that the position qualifies for the requested category</li>
        <li>Beneficiary does not meet required qualifications</li>
        <li>Missing or incomplete supporting documentation</li>
        <li>Failure to pay required fees</li>
        <li>Invalid or expired LCA (for H-category petitions)</li>
    </ul>
    """,
)

content_max += '</div>'
st.markdown(content_max, unsafe_allow_html=True)

st.markdown('<div style="max-width:900px; margin:0 auto; padding:1.5rem 1rem;">', unsafe_allow_html=True)
st.markdown('<h3 style="color:#1a365d;">Have a specific I-129 question?</h3>', unsafe_allow_html=True)
st.markdown(render_chat_placeholder(), unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown(render_footer(), unsafe_allow_html=True)
