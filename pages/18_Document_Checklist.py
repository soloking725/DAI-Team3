"""
Required-documents checklist, organized by stage. A literal, checkable
checklist — items persist to vera_state.document_checklist (per-account in
hosted mode, per ?vid= session locally) so a student's progress survives a
page refresh, same pattern as the visa timeline's step statuses.
Page: 18_Document_Checklist.py
"""
import streamlit as st

from shared.branding import FAVICON
from shared.components import (
    render_disclaimer,
    render_floating_chat,
    render_footer,
    render_hamburger_menu,
    render_profile_banner,
    render_section,
)
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.vera_state import get_vera_state, set_checklist_item

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
        Everything you're likely to need, grouped by when you'll need it. Check items off as you gather them.
    </p>
</div>
""", unsafe_allow_html=True)

# (section title, [(card title, [(item id, item text)], optional link) ...])
CHECKLIST = [
    ("Before your I-20 is issued", [
        ("School application & admission", [
            ("admission_letter", "Acceptance/admission letter from your school"),
            ("funding_proof", "Proof of funding for at least your first year (bank statements, scholarship letter, or sponsor affidavit)"),
            ("passport_valid", "Passport valid for the duration of your intended studies (or per your embassy's specific rule)"),
        ], None),
    ]),
    ("Before the DS-160 and interview", [
        ("Application paperwork", [
            ("i20_signed", "Form I-20, signed by you and your school"),
            ("sevis_receipt", "SEVIS I-901 fee payment receipt"),
            ("photo", "Passport-style photo meeting the State Department's photo requirements"),
            ("ds160_confirmation", "DS-160 confirmation page (printed) once submitted"),
            ("interview_confirmation", "Visa interview appointment confirmation"),
        ], None),
        ("Financial documents", [
            ("bank_statements", "Personal or parental bank statements"),
            ("scholarship_letter", "Scholarship or assistantship award letter, if applicable"),
            ("i134", "Affidavit of Support (Form I-134), if a sponsor other than you is funding your program"),
            ("sponsor_proof", "Proof of the sponsor's income or assets"),
            ("translations", "Certified translations of any documents not in English (check your specific post's requirement)"),
        ], None),
    ]),
    ("At the interview", [
        ("Bring with you", [
            ("valid_passport", "Valid passport"),
            ("i20_signed_interview", "Form I-20 (signed)"),
            ("ds160_confirmation_interview", "DS-160 confirmation page"),
            ("sevis_receipt_interview", "SEVIS I-901 fee receipt"),
            ("appointment_letter", "Visa appointment confirmation letter"),
            ("financial_docs_interview", "Financial documents (see above)"),
            ("prior_passports", "Previous passports, if you have prior US visas or travel history"),
        ], None),
    ]),
    ("After arrival in the US", [
        ("Keep on hand", [
            ("passport_i94", "Passport with visa and admission (I-94) record"),
            ("i20_endorsed", "Form I-20, endorsed by your DSO"),
            ("address_proof", "Proof of a US address (lease, utility bill, or bank statement) — needed for SSN, bank account, and state ID applications"),
            ("work_auth_letter", "Job offer or work-authorization letter, if applying for a Social Security Number"),
        ], ("See the Post-Arrival Guide for what each of these is used for.", "Post-Arrival Guide", "/Post_Visa_Guide")),
    ]),
]

checklist_state = get_vera_state()["document_checklist"]

_total_items = sum(len(items) for _, cards in CHECKLIST for _, items, _ in cards)
_checked_items = sum(1 for v in checklist_state.values() if v)
st.progress(
    min(_checked_items / _total_items, 1.0) if _total_items else 0,
    text=f"{_checked_items} of {_total_items} checked off",
)

for section_title, cards in CHECKLIST:
    st.markdown(render_section(section_title), unsafe_allow_html=True)
    for card_title, items, link in cards:
        with st.container(border=True):
            st.markdown(f"**{card_title}**")
            for item_id, item_text in items:
                checked = st.checkbox(
                    item_text,
                    value=bool(checklist_state.get(item_id, False)),
                    key=f"_checklist_{item_id}",
                )
                if checked != bool(checklist_state.get(item_id, False)):
                    set_checklist_item(item_id, checked)
            if link:
                note, link_text, link_href = link
                st.caption(f"{note} [{link_text}]({link_href})")

st.markdown(render_footer(), unsafe_allow_html=True)
render_floating_chat()
