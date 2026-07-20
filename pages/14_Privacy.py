"""
Privacy: what Vera stores and where, in both local and hosted mode.
Page: 14_Privacy.py
"""
import streamlit as st

from shared.branding import FAVICON
from shared.styles import get_global_css
from shared.theme import get_vera_css
from shared.components import render_hamburger_menu
from shared.vera_state import get_vera_state
from shared import config

st.set_page_config(page_icon=FAVICON, page_title="Privacy - Vera", layout="wide", initial_sidebar_state="collapsed")
st.markdown(get_global_css(), unsafe_allow_html=True)
st.markdown(get_vera_css(), unsafe_allow_html=True)

render_hamburger_menu(visa_type=get_vera_state().get("profile", {}).get("visa_type") or "f-1")

hosted = config.is_supabase_configured()

if hosted:
    intro = (
        "Vera is running in hosted mode for your school: you sign in with your school "
        "email (a one-time code, no password), and your data is stored in a private "
        "database rather than only in your browser session. Here's what's actually "
        "stored, and who can see it."
    )
    trip_details_block = """
      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:16px">
        <p style="font-weight:500;margin:0 0 6px">Your account and trip details</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0">
          Your school email, name, visa type, country of origin, destination, school, any
          extenuating circumstances you flag (e.g. a prior denial, SEVIS issue, or hardship —
          plus any notes you add), and your timeline progress are stored in your school's
          database, keyed to your account. Your school's Designated School Official (DSO)
          can see this information — that's who administers your visa paperwork — but only
          for students at your own school. Signing in with a different school email would
          not give you access to another school's students.
        </p>
      </div>
    """
    messages_block = """
      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:12px">
        <p style="font-weight:500;margin:0 0 6px">Messages and announcements</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0">
          Direct messages between you and your DSO, and school-wide announcements your DSO
          posts, are stored in the same database and visible to both of you (announcements
          are visible to everyone at your school). We also keep a basic audit log of actions
          like logins, roster views, and step overrides, so there's a record of who accessed
          or changed what.
        </p>
      </div>
    """
    session_note = (
        "Signing out clears your session on this device; your account data stays in your "
        "school's database until you or your DSO deletes it."
    )
else:
    intro = "Vera doesn't use accounts or logins right now. Here's what's actually stored, and where."
    trip_details_block = """
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
    """
    messages_block = ""
    session_note = "Use Settings to reset your progress and start a fresh, unlinked session."

st.markdown(
    f"""
    <div style="max-width:600px;margin:1.5rem auto 0">
      <h1 style="margin:0 0 12px">Privacy</h1>
      <p style="font-size:14px;color:var(--text-secondary);line-height:1.6">{intro}</p>

      {trip_details_block}

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

      {messages_block}

      <div style="background:var(--surface-2);border:0.5px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-top:12px">
        <p style="font-weight:500;margin:0 0 6px">What Vera doesn't do</p>
        <p style="font-size:13px;color:var(--text-secondary);margin:0">
          No third-party ad trackers, no data resale, no ID documents (like your I-20) collected or
          stored. Vera does not provide legal advice — see the disclaimer shown throughout the site.
        </p>
      </div>

      <p style="font-size:13px;color:var(--text-secondary);line-height:1.6;margin-top:16px">{session_note}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
