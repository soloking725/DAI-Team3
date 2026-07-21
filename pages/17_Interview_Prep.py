"""
Visa interview preparation — factual, sourced prep material, kept separate
from the main chat so students have one place to review it without having
to ask Vera the same questions repeatedly. Same no-legal-advice contract as
the rest of the app (see shared/config.py's SYSTEM_PROMPT and
shared/components.render_disclaimer).
Page: 17_Interview_Prep.py
"""
import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu, render_disclaimer, render_floating_chat
from shared.vera_state import get_vera_state
from shared.retrieval import retrieve_context
from shared.safeguards import check_confidence

st.set_page_config(page_icon=FAVICON, page_title="Interview prep - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

visa_type = get_vera_state().get("profile", {}).get("visa_type") or "f-1"
render_hamburger_menu(visa_type=visa_type)
st.markdown(render_disclaimer(), unsafe_allow_html=True)

st.markdown(
    """
    <div style="max-width:700px;margin:1.5rem auto 0">
      <h1 style="margin:0 0 6px">Visa interview prep</h1>
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6;margin:0 0 18px">
        This covers what consular officers typically focus on and what to bring — factual
        preparation, not legal advice, and not a guarantee of what will be asked in your
        specific interview. For questions about your individual case, consult a licensed
        immigration attorney.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

_, center, _ = st.columns([1, 6, 1])
with center:
    st.markdown("#### What the interview covers")
    st.markdown(
        """
        <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                    padding:16px 18px;margin-bottom:14px">
          <p style="font-size:13px;color:var(--text-secondary);line-height:1.7;margin:0">
            Consular officers use the interview to assess whether you qualify for the visa,
            focusing on a few consistent areas rather than a fixed script:
          </p>
          <ul style="font-size:13px;color:var(--text-secondary);line-height:1.7;margin:8px 0 0">
            <li><strong>Study plans</strong> — why you chose your specific school and program</li>
            <li><strong>Funding</strong> — how tuition and living costs will be paid, and by whom</li>
            <li><strong>Ties to your home country</strong> — family, career plans, or property that
                support your intent to return after your program</li>
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### What to bring")
    st.markdown(
        """
        <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                    padding:16px 18px;margin-bottom:14px">
          <ul style="font-size:13px;color:var(--text-secondary);line-height:1.7;margin:0">
            <li>Valid passport</li>
            <li>Form I-20 (signed)</li>
            <li>DS-160 confirmation page</li>
            <li>SEVIS I-901 fee receipt</li>
            <li>Financial documents (bank statements, sponsor affidavit, scholarship letter)</li>
          </ul>
          <p style="font-size:13px;color:var(--text-secondary);line-height:1.7;margin:8px 0 0">
            Be ready to speak specifically about the contents of these documents — the exact
            program length, or the source of sponsorship funds — rather than only in general terms.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Practice topics")
    retrieval = retrieve_context(
        "visa interview preparation topics and common questions", top_k=4,
        visa_type=visa_type, category="interview_prep", distance_threshold=1.2,
    )
    if retrieval.get("found") and check_confidence(retrieval.get("distances", [])):
        sources = retrieval.get("sources", [])
        source_lines = "".join(
            f'<li><a href="{s.get("url", "#")}" target="_blank">{s.get("title", "Official source")}</a></li>'
            for s in sources
        )
        st.markdown(
            f"""
            <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                        padding:16px 18px;margin-bottom:14px">
              <p style="font-size:13px;color:var(--text-secondary);line-height:1.7;margin:0 0 8px">
                Ask Vera in the chat about your specific study plans, funding, or ties to home —
                the chat is grounded in the same official sources below and will point you to what
                each covers.
              </p>
              <ul style="font-size:13px;margin:0">{source_lines}</ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                        padding:16px 18px;margin-bottom:14px">
              <p style="font-size:13px;color:var(--text-secondary);line-height:1.7;margin:0">
                Vera doesn't have specific interview-prep guidance indexed right now — check
                travel.state.gov or EducationUSA, or ask Vera in the chat.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### Interviews are short")
    st.markdown(
        """
        <p style="font-size:13px;color:var(--text-secondary);line-height:1.7">
          Interviews are typically a few minutes, and officers decide based on the interview and
          documentation provided that day. There's no fixed list of guaranteed questions — focus
          on being able to explain your own plans and documents accurately and specifically.
        </p>
        """,
        unsafe_allow_html=True,
    )

render_floating_chat()
