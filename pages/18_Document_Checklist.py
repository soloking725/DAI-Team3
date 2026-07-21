"""
Required-documents checklist, organized by stage. Static factual content
(same render_card pattern as the older info pages) rather than something
the student has to ask the chatbot for one item at a time.
Page: 18_Document_Checklist.py
"""
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
)
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.vera_state import get_vera_state

st.set_page_config(page_icon=FAVICON, page_title="Document checklist - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu(visa_type=get_vera_state().get("profile", {}).get("visa_type") or "f-1")
st.markdown(render_disclaimer(), unsafe_allow_html=True)
render_profile_banner()

st.markdown("""
<div style="max-width:1200px; margin:0 auto; padding:2rem 1rem 0;">
    <h1 style="font-size:1.75rem; font-weight:700; color:#5b4380; margin:0 0 0.5rem;">
        Document Checklist
    </h1>
    <p style="color:#4a5568; font-size:1rem; margin:0 0 2rem;">
        Everything you're likely to need, grouped by when you'll need it.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown(render_section("Before your I-20 is issued"), unsafe_allow_html=True)
st.markdown(render_card(
    title="School application & admission",
    content_html="""
    <ul>
        <li>Acceptance/admission letter from your school</li>
        <li>Proof of funding for at least your first year (bank statements, scholarship letter, or sponsor affidavit)</li>
        <li>Passport valid for the duration of your intended studies (or per your embassy's specific rule)</li>
    </ul>
    """,
), unsafe_allow_html=True)

st.markdown(render_section("Before the DS-160 and interview"), unsafe_allow_html=True)
st.markdown(render_card(
    title="Application paperwork",
    content_html="""
    <ul>
        <li>Form I-20, signed by you and your school</li>
        <li>SEVIS I-901 fee payment receipt</li>
        <li>Passport-style photo meeting the State Department's photo requirements</li>
        <li>DS-160 confirmation page (printed) once submitted</li>
        <li>Visa interview appointment confirmation</li>
    </ul>
    """,
), unsafe_allow_html=True)

st.markdown(render_card(
    title="Financial documents",
    content_html="""
    <ul>
        <li>Personal or parental bank statements</li>
        <li>Scholarship or assistantship award letter, if applicable</li>
        <li>Affidavit of Support (Form I-134), if a sponsor other than you is funding your program</li>
        <li>Proof of the sponsor's income or assets</li>
        <li>Certified translations of any documents not in English (check your specific post's requirement)</li>
    </ul>
    """,
), unsafe_allow_html=True)

st.markdown(render_section("At the interview"), unsafe_allow_html=True)
st.markdown(render_card(
    title="Bring with you",
    content_html="""
    <ul>
        <li>Valid passport</li>
        <li>Form I-20 (signed)</li>
        <li>DS-160 confirmation page</li>
        <li>SEVIS I-901 fee receipt</li>
        <li>Visa appointment confirmation letter</li>
        <li>Financial documents (see above)</li>
        <li>Previous passports, if you have prior US visas or travel history</li>
    </ul>
    """,
), unsafe_allow_html=True)

st.markdown(render_section("After arrival in the US"), unsafe_allow_html=True)
st.markdown(render_card(
    title="Keep on hand",
    content_html="""
    <ul>
        <li>Passport with visa and admission (I-94) record</li>
        <li>Form I-20, endorsed by your DSO</li>
        <li>Proof of a US address (lease, utility bill, or bank statement) — needed for SSN, bank account, and state ID applications</li>
        <li>Job offer or work-authorization letter, if applying for a Social Security Number</li>
    </ul>
    <p style="margin-top:1rem;">See the Post-Arrival Guide for what each of these is used for.</p>
    """,
    link_text="Post-Arrival Guide",
    link_href="/Post_Visa_Guide",
), unsafe_allow_html=True)

st.markdown(render_footer(), unsafe_allow_html=True)
render_floating_chat()
