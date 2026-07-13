"""J-1 Exchange Visitor information page."""

import streamlit as st

from shared.components import (
    render_card,
    render_disclaimer,
    render_floating_chat,
    render_footer,
    render_hamburger_menu,
    render_section,
    render_source_citations,
)
from shared.styles import get_global_css
from shared.theme import get_vera_css

st.set_page_config(page_title="J-1 Exchange Visitor", page_icon=":book:", layout="wide")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu(visa_type="j-1")
st.markdown(render_disclaimer(), unsafe_allow_html=True)

st.markdown("""
<div style="max-width:1200px; margin:0 auto; padding:2rem 1rem 0;">
    <h1 style="font-size:1.75rem; font-weight:700; color:#166534; margin:0 0 0.5rem;">
        J-1 Exchange Visitor Visa
    </h1>
    <p style="color:#4a5568; font-size:1rem; margin:0 0 2rem;">
        Exchange visitor visa for individuals approved to participate in US government-sponsored exchange programs.
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Overview
# -------------------------------------------------------
st.markdown(render_section("Overview"), unsafe_allow_html=True)

st.markdown(render_card(
    title="What is the J-1 Visa?",
    content_html="""
    <p>The J-1 visa is issued to nonimmigrants approved to participate in work and study-based exchange visitor programs in the US. These programs are designed to promote cultural exchange and mutual understanding between the US and other countries.</p>
    <p>Common J-1 categories for students include:</p>
    <ul>
        <li><strong>University student</strong> - Degree or non-degree students enrolled in a US university, college, or seminary</li>
        <li><strong>Research scholar</strong> - Researchers, professors, or assistants conducting research at US institutions</li>
        <li><strong>Summer work travel</strong> - College students participating in approved summer work and travel programs</li>
        <li><strong>Short-term scholarship</strong> - Individuals coming for short-term exchange, observation, or study</li>
        <li><strong>Professor</strong> - Professors and researchers invited by US higher education institutions</li>
    </ul>
    """,
    link_text="Department of State Exchange Programs",
    link_href="https://exchangeprogram.state.gov",
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
            <li><strong>Form DS-2019</strong> - Certificate of Eligibility issued by your program sponsor</li>
            <li><strong>Valid passport</strong> - Must be valid for at least six months beyond your intended period of stay</li>
            <li><strong>Form DS-160</strong> - Online nonimmigrant visa application confirmation page</li>
            <li><strong>Visa application fee receipt</strong> - MRV fee payment (currently $185 for J-1)</li>
            <li><strong>Photograph</strong> - 2x2 inches, taken within the last six months, white background</li>
            <li><strong>SEVIS I-901 fee receipt</strong> - If required by your program category</li>
        </ul>
        """,
    ), unsafe_allow_html=True)

with doc_col2:
    st.markdown(render_card(
        title="Supporting Documents",
        content_html="""
        <ul>
            <li><strong>Program sponsor letter</strong> - Confirmation of your exchange visitor program placement</li>
            <li><strong>Financial evidence</strong> - Proof of sufficient funds to cover your stay in the US</li>
            <li><strong>Academic transcripts</strong> - From previous educational institutions attended</li>
            <li><strong>CV or resume</strong> - Especially important for research scholars and professors</li>
            <li><strong>Proof of ties to home country</strong> - Evidence of intention to return after program completion</li>
            <li><strong>Health insurance documentation</strong> - J-1 participants must meet State Department health insurance requirements</li>
        </ul>
        """,
    ), unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/exchange-visitor.html",
        "title": "Exchange Visitor Visa - travel.state.gov",
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
    <h3>Current Fees for J-1 Visa</h3>
    <table style="width:100%; border-collapse:collapse; margin-top:1rem;">
        <thead>
            <tr style="border-bottom:2px solid #e2e8f0;">
                <th style="text-align:left; padding:0.5rem; color:#166534; font-size:0.9rem;">Fee</th>
                <th style="text-align:left; padding:0.5rem; color:#166534; font-size:0.9rem;">Amount</th>
                <th style="text-align:left; padding:0.5rem; color:#166534; font-size:0.9rem;">Notes</th>
            </tr>
        </thead>
        <tbody>
            <tr style="border-bottom:1px solid #e2e8f0;">
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Visa Application Fee (MRV)</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">$185</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Nonrefundable consular processing fee</td>
            </tr>
            <tr style="border-bottom:1px solid #e2e8f0;">
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">SEVIS I-901 Fee (if applicable)</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">$220</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Required for some J-1 categories. Check with your sponsor.</td>
            </tr>
            <tr>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Reciprocity Fee</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Varies</td>
                <td style="padding:0.75rem 0.5rem; font-size:0.9rem; color:#4a5568;">Some countries require an additional fee. Check your country on the State Department website.</td>
            </tr>
        </tbody>
    </table>
    <p style="font-size:0.85rem; color:#718096; margin-top:1rem;">
        Fees are current as of 2025. Visit the State Department website for the most up-to-date information.
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
        <li style="margin-bottom:0.75rem;"><strong>Get your Form DS-2019</strong> - Your exchange program sponsor issues this after you are accepted into the program and meet financial requirements.</li>
        <li style="margin-bottom:0.75rem;"><strong>Pay the SEVIS I-901 fee (if required)</strong> - Pay the fee online at fmjfee.gov and keep the receipt. Not all J-1 categories require this fee.</li>
        <li style="margin-bottom:0.75rem;"><strong>Complete the DS-160</strong> - Fill out the online nonimmigrant visa application at ceac.state.gov and print the confirmation page.</li>
        <li style="margin-bottom:0.75rem;"><strong>Pay the visa application fee</strong> - Pay the $185 MRV fee and keep the receipt. Some countries also require a reciprocity fee.</li>
        <li style="margin-bottom:0.75rem;"><strong>Schedule your interview</strong> - Book a visa interview appointment at the nearest US embassy or consulate. Appointment wait times vary by location.</li>
        <li style="margin-bottom:0.75rem;"><strong>Prepare for the interview</strong> - Gather all required documents and supporting evidence of your program and ties to your home country.</li>
        <li><strong>Attend the visa interview</strong> - Bring your passport, Form DS-2019, DS-160 confirmation, fee receipts, and supporting documents to your scheduled interview.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

st.markdown(render_source_citations([
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/exchange-visitor.html",
        "title": "Exchange Visitor Visa - travel.state.gov",
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
    <p>J-1 visa processing times vary by US embassy or consulate location and exchange program category. The timeline typically includes:</p>
    <ul>
        <li><strong>Administrative processing:</strong> 2-10 weeks after interview in most cases</li>
        <li><strong>Appointment wait times:</strong> Varies by country, from a few days to several months</li>
        <li><strong>Summer work travel:</strong> Higher demand during spring months (March-May)</li>
        <li><strong>Research scholars:</strong> May require additional administrative processing</li>
    </ul>
    <p style="margin-top:1rem;">Check current processing times and appointment availability at the embassy or consulate where you will apply.</p>
</div>
""", unsafe_allow_html=True)

st.markdown(render_source_citations([
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
