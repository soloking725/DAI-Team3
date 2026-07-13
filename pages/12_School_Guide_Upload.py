"""
Upload the school's visa guide PDF; Vera extracts any extra required
steps and folds them into the timeline.
Page: 12_School_Guide_Upload.py
"""
import streamlit as st

from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared.vera_state import get_vera_state, add_timeline_steps
from shared.pdf_guide import extract_steps_from_pdf, PdfExtractionError

st.set_page_config(page_title="Add your school's visa guide - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu()

state = get_vera_state()

st.markdown(
    """
    <div style="max-width:460px;margin:1.5rem auto 0;text-align:center">
      <h1 style="margin:0 0 6px">Add your school's visa guide</h1>
      <p style="font-size:14px;color:var(--text-secondary);margin:0">
        Upload the PDF your international office sent you, Vera will fold any extra
        steps into your timeline.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 2, 1])
with center:
    uploaded_pdf = st.file_uploader("School visa guide PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded_pdf is not None and st.session_state.get("_last_guide_name") != uploaded_pdf.name:
        with st.spinner("Reading your school's guide..."):
            try:
                extracted = extract_steps_from_pdf(uploaded_pdf)
                st.session_state["extracted_guide_steps"] = extracted
                st.session_state["_last_guide_name"] = uploaded_pdf.name
            except PdfExtractionError as e:
                st.session_state["extracted_guide_steps"] = None
                st.session_state["_last_guide_name"] = uploaded_pdf.name
                st.error(str(e))

    extracted_steps = st.session_state.get("extracted_guide_steps")

    if extracted_steps:
        st.markdown(
            f"""
            <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                        padding:12px 14px;margin:18px 0">
                <div style="display:flex;align-items:center;gap:10px">
                    <div style="width:32px;height:32px;border-radius:var(--radius);background:var(--bg-accent);
                                display:flex;align-items:center;justify-content:center">
                        <i class="ti ti-file-text" style="color:var(--text-accent)"></i>
                    </div>
                    <div style="flex:1">
                        <p style="font-size:14px;margin:0">{uploaded_pdf.name}</p>
                        <p style="font-size:12px;color:var(--text-muted);margin:0">Read by Vera</p>
                    </div>
                    <i class="ti ti-check" style="color:var(--text-success)"></i>
                </div>
            </div>
            <p style="font-size:13px;color:var(--text-secondary);margin:0 0 10px">
                Vera found these extra steps in your guide
            </p>
            """,
            unsafe_allow_html=True,
        )

        selected_steps = []
        for step in extracted_steps:
            page_note = f", per page {step['page_hint']}" if step.get("page_hint") else ""
            checked = st.checkbox(
                f"{step['title']}",
                value=True,
                key=f"guide_step_{step['id']}",
                help=f"{step['detail']}{page_note}",
            )
            st.markdown(
                f"<p style='font-size:12px;color:var(--text-muted);margin:-8px 0 10px 28px'>{step['detail']}{page_note}</p>",
                unsafe_allow_html=True,
            )
            if checked:
                selected_steps.append(step)

        if st.button("Add to my timeline", use_container_width=True, type="primary"):
            add_timeline_steps(selected_steps)
            st.switch_page("pages/04_Ask_a_Question.py")
    else:
        st.button("Add to my timeline", use_container_width=True, type="primary", disabled=True)
        if st.button("Skip for now", use_container_width=True):
            st.switch_page("pages/04_Ask_a_Question.py")
