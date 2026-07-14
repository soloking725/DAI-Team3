"""
Privacy: what Vera stores and why.
Page: 14_Privacy.py
"""
import streamlit as st

from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared.vera_state import get_vera_state

st.set_page_config(page_title="Privacy - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu(visa_type=get_vera_state().get("profile", {}).get("visa_type") or "f-1")

st.markdown(
    """
    <div style="max-width:600px;margin:1.5rem auto 0">
      <h1 style="margin:0 0 12px">Privacy</h1>
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6">
        Vera doesn't use accounts or logins. Here's what's actually stored, and where.
      </p>

      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:16px">
        <p style="font-weight:500;margin:0 0 6px">Your trip details and timeline progress</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0">
          Your name, visa type, country of origin, destination, school, any extenuating circumstances
          you flag (e.g. a prior denial, SEVIS issue, or hardship — plus any notes you add), and which
          timeline steps you've marked complete are saved to a file on the server, keyed to a random
          session ID kept in your browser's URL (not a cookie, not an account). Anyone with that exact
          URL could view the same session.
        </p>
      </div>

      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:12px">
        <p style="font-weight:500;margin:0 0 6px">Your school's visa guide PDF</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0">
          When you upload a school guide PDF, its text is sent to Vera's language model provider to pull
          out any required steps. The file itself is not saved to disk — only the extracted steps you
          choose to add to your timeline are kept.
        </p>
      </div>

      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:12px">
        <p style="font-weight:500;margin:0 0 6px">Chat messages</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0">
          Questions you ask Vera are sent to the same language model provider to generate an answer,
          along with the relevant official government context. Chat history lives only in your current
          browser session and isn't saved to disk.
        </p>
      </div>

      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:12px">
        <p style="font-weight:500;margin:0 0 6px">What Vera doesn't do</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0">
          No third-party ad trackers, no data resale, no ID documents (like your I-20) collected or
          stored. Vera does not provide legal advice — see the disclaimer shown throughout the site.
        </p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
