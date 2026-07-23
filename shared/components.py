"""
Shared UI components used across multiple pages.
"""

import html

import streamlit as st


_REMINDER_STYLE = {
    "urgent": ("#fff5f5", "#feb2b2", "#c53030", "ti-alert-triangle"),
    "warning": ("#fffbeb", "#f6e05e", "#975a16", "ti-clock-exclamation"),
    "notice": ("var(--surface-2)", "var(--border)", "var(--text-secondary)", "ti-bell"),
}


def render_reminders_banner(reminders: list):
    """Render in-account expiration reminders (see shared/reminders.py).

    Computed fresh from stored dates on every page load — nothing is
    scheduled or emailed; there's no SMTP configured yet, so this is the
    only place these surface."""
    if not reminders:
        return
    cards = []
    for r in reminders:
        bg, border, text, icon = _REMINDER_STYLE.get(r["urgency"], _REMINDER_STYLE["notice"])
        # Built-in reminders (shared/reminders.py's compute_reminders) are safe,
        # system-generated text, but custom_reminders are free text a DSO typed in
        # (pages/20_DSO_Dashboard.py) and rendered here for every student at the
        # college — escape unconditionally rather than trusting the caller to only
        # ever pass the built-in kind.
        title = html.escape(str(r["title"]))
        detail = html.escape(str(r["detail"]))
        cards.append(
            f'<div style="background:{bg};border:0.5px solid {border};border-left:3px solid {border};'
            f'border-radius:12px;padding:10px 14px;margin-bottom:8px;display:flex;gap:10px;align-items:flex-start">'
            f'<i class="ti {icon}" style="font-size:16px;color:{text};margin-top:2px"></i>'
            f'<div><p style="font-weight:500;font-size:13px;color:{text};margin:0 0 2px">{title}</p>'
            f'<p style="font-size:12px;color:{text};margin:0">{detail}</p></div></div>'
        )
    st.markdown(
        f'<div style="max-width:1200px;margin:0 auto 12px;padding:0 1rem">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_disclaimer():
    """Render the persistent disclaimer banner.

    Lists every agency Vera's retrieval index actually pulls from (see
    ingest.py's SOURCE_URLS) — this used to say "USCIS, State Department, SSA"
    only, silently leaving out SEVP, IRS, and embassy-sourced content even
    though answers can cite any of them.
    """
    return """
    <div class="disclaimer-banner">
        <strong>Disclaimer:</strong> This tool provides factual information from official US government sources
        (USCIS, the State Department, SEVP/Study in the States, the SSA, the IRS, and US embassy/consulate
        websites). It does not provide legal advice. For legal advice about your specific situation, consult a
        licensed immigration attorney.
    </div>
    """


_VISA_TYPE_NAMES = {
    "f-1": "F-1", "h-1b": "H-1B", "other": "another visa type",
}


def render_profile_banner(page_visa_type: str = None):
    """A small personalized greeting for the older static info pages.

    Shows the user's name if Vera knows it, and — if the page's visa type
    differs from the one the user told Vera they're pursuing — a soft note
    pointing them to the right one, without hiding this page's content
    (it's still a valid reference page for anyone reading it).
    """
    from shared.vera_state import get_vera_state

    profile = get_vera_state().get("profile", {})
    name = html.escape((profile.get("name") or "").strip())
    visa_type = profile.get("visa_type") or ""

    if not name and not visa_type:
        return

    greeting = f"Hi {name}, " if name else ""
    note = ""
    if page_visa_type and visa_type and visa_type != page_visa_type and visa_type in _VISA_TYPE_NAMES:
        note = f"you told Vera you're pursuing an {_VISA_TYPE_NAMES[visa_type]} — this page covers {_VISA_TYPE_NAMES.get(page_visa_type, page_visa_type.upper())} instead, but the general process is similar."
    elif greeting:
        note = "here's what applies to you."

    if not greeting and not note:
        return

    st.markdown(
        f"""
        <div style="max-width:1200px;margin:0 auto;padding:0 1rem">
            <div style="background:var(--bg-accent);border:0.5px solid var(--border-accent);
                        border-radius:var(--radius);padding:10px 14px;margin-bottom:1rem;
                        font-size:13px;color:var(--text-accent)">
                {greeting}{note}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    """Render the site footer."""
    return """
    <div class="site-footer">
        <p><strong>US Student Visa Information Resource</strong></p>
        <p style="font-size:1.05rem;font-weight:600;color:#fff5f5;background:rgba(197,48,48,0.25);
                  border:1px solid rgba(254,178,178,0.5);border-radius:8px;padding:0.75rem 1rem;
                  max-width:640px;margin:0.75rem auto">
            This tool does not provide legal advice. For legal advice about your specific situation,
            consult a licensed immigration attorney.
        </p>
        <p>
            This tool provides factual information from official US government sources.
        </p>
        <p>
            Sources: <a href="https://www.uscis.gov" target="_blank">uscis.gov</a> |
            <a href="https://travel.state.gov" target="_blank">travel.state.gov</a> |
            <a href="https://www.ssa.gov" target="_blank">ssa.gov</a>
        </p>
    </div>
    """


def render_section(title):
    """Render a section title."""
    return f'<p class="section-title">{title}</p>'


def render_card(title, content_html, link_text=None, link_href="#"):
    """Render a visa info card."""
    link_html = f'<a href="{link_href}" class="card-link">{link_text}</a>' if link_text else ""
    # Strip leading/trailing whitespace to prevent Streamlit rendering raw text
    return (
        f'<div class="content-card">'
        f'<h3>{title}</h3>'
        f'{content_html}'
        f'{link_html}'
        f'</div>'
    ).strip()


def render_source_citations(sources):
    """Render source citations as a formatted list."""
    if not sources:
        return ""

    items = []
    for s in sources:
        url = s.get("url", "#")
        title = s.get("title", "Official Source")
        section = s.get("section", "")
        section_str = f" | {section}" if section else ""
        items.append(f'<li><a href="{url}" target="_blank">{title}</a>{section_str}</li>')

    return f"""
    <div class="source-citation">
        <strong>Sources:</strong>
        <ul style="margin:0.5rem 0 0; padding-left:1.25rem;">
            {''.join(items)}
        </ul>
    </div>
    """


_VISA_TYPE_PAGES = {
    "f-1": "pages/01_F-1_Student_Visa.py",
    "h-1b": "pages/16_Other_Visa_Coming_Soon.py",
    "other": "pages/16_Other_Visa_Coming_Soon.py",
}

HAMBURGER_CSS = """
<style>
    /* A small fixed icon in the corner — same technique as the floating chat
       bubble below (div.st-key-vera_floating_chat), just the opposite corner
       and the smaller 32px size the old inline header button used. Being
       fixed rather than sticky-in-a-header-bar means it never occupies its
       own row of page height; the page content starts right at the top. */
    div.st-key-vera_hamburger_corner {
        position: fixed;
        top: 1.5rem;
        left: 1.5rem;
        z-index: 9999;
    }
    div.st-key-vera_hamburger_corner button {
        width: 40px !important; height: 40px !important; padding: 0 !important;
        border-radius: 50% !important; border: 0.5px solid var(--border) !important;
        background: #ffffff !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12) !important;
    }
    /* The brand wordmark is no longer part of a persistent header — it's
       normal in-flow page content now (scrolls away like anything else),
       just given a little breathing room since the fixed hamburger sits
       on top of the page's natural top-left corner. */
    div.st-key-vera_brand_row {
        padding: 4px 0 12px 60px;
    }
    .st-key-vera_brand_link p {
        font-size: 20px !important;
        font-weight: 700 !important;
        color: var(--text-accent) !important;
    }
    .vera-brand-logo img {
        height: 36px;
        display: block;
    }
    .vera-brand-logo {
        display: inline-block;
        line-height: 0;
    }
</style>
"""


@st.fragment(run_every="30s")
def _render_unread_badge(user: dict):
    """A small "N new messages" line under the Timeline/DSO Dashboard link —
    the "alert like Insta" ask: visible without first opening any thread.
    Self-refreshing on a 30s timer (same st.fragment(run_every=...) technique
    as shared/auth.py's OTP cooldown) since Streamlit has no push/websocket
    hook available to app code to react to a new message immediately.
    """
    from shared import db

    if not user:
        return
    if user.get("role") == "dso":
        counterparts = [
            {"id": r["user_id"], "name": r.get("name") or r.get("email")}
            for r in db.list_students(user["college_id"])
        ]
    else:
        counterparts = db.get_dso_users(user["college_id"])
    if not counterparts:
        return
    total_unread = sum(db.get_unread_count(user["id"], c["id"]) for c in counterparts)
    if total_unread:
        st.caption(f"🔴 {total_unread} new message{'s' if total_unread != 1 else ''}")


def render_hamburger_menu(visa_type: str = "f-1"):
    """Render the corner hamburger menu: Your Timeline, Messages, Guide, Home,
    Forms, Info, Help, Settings, Privacy — plus the Vera brand wordmark as
    normal (non-fixed) page content right below it.

    The menu button itself is fixed to the top-left corner (mirrors
    render_floating_chat's bottom-right bubble) rather than living in a
    sticky header bar, so it never occupies a permanent row of page height.
    """
    from shared.branding import get_logo_data_uri
    from shared import auth, config

    st.markdown(HAMBURGER_CSS, unsafe_allow_html=True)

    with st.container(key="vera_hamburger_corner"):
        with st.popover("☰"):
            st.page_link("pages/04_Ask_a_Question.py", label="Your Timeline", icon=":material/timeline:")
            st.page_link("app.py", label="Home", icon=":material/home:")
            # Same top tier as Timeline/Home (above the divider), but only
            # for a signed-in DSO — students should never see this link,
            # and it's the only way back to the dashboard from any other
            # page once a DSO has navigated away from it.
            _user = auth.get_current_user() if config.is_supabase_configured() else None
            if _user and _user.get("role") == "dso":
                st.page_link(
                    "pages/20_DSO_Dashboard.py", label="DSO Dashboard",
                    icon=":material/admin_panel_settings:",
                )
                _render_unread_badge(_user)  # dashboard's own Messages tab
            else:
                st.page_link("pages/19_Messages.py", label="Messages", icon=":material/mail:")
                if config.is_supabase_configured() and _user:
                    _render_unread_badge(_user)
            st.page_link("pages/12_School_Guide_Upload.py", label="Guide", icon=":material/menu_book:")
            st.divider()
            st.page_link(
                _VISA_TYPE_PAGES.get(visa_type, _VISA_TYPE_PAGES["f-1"]),
                label="Forms",
                icon=":material/description:",
            )
            st.page_link("pages/06_About.py", label="Info", icon=":material/info:")
            st.page_link(
                "pages/17_Interview_Prep.py",
                label="Interview prep",
                icon=":material/record_voice_over:",
            )
            st.page_link(
                "pages/18_Document_Checklist.py",
                label="Document checklist",
                icon=":material/checklist:",
            )
            st.page_link(
                "pages/13_Help_Find_a_Lawyer.py",
                label="Help (find a lawyer)",
                icon=":material/balance:",
            )
            st.page_link("pages/15_Settings.py", label="Settings", icon=":material/settings:")
            st.page_link("pages/14_Privacy.py", label="Privacy", icon=":material/shield_lock:")

            if config.is_supabase_configured() and auth.is_logged_in():
                st.divider()
                if st.button("Sign out", icon=":material/logout:", use_container_width=True):
                    auth.logout()
                    st.switch_page("app.py")

    with st.container(key="vera_brand_row"):
        logo = get_logo_data_uri()
        if logo:
            # Plain <a> rather than st.page_link so the mark itself is the link;
            # Streamlit's page_link only accepts a text label.
            st.markdown(
                f'<a class="vera-brand-logo" href="/Ask_a_Question" target="_self">'
                f'<img src="{logo}" alt="VeraVisa"></a>',
                unsafe_allow_html=True,
            )
        else:
            with st.container(key="vera_brand_link"):
                st.page_link("pages/04_Ask_a_Question.py", label="Vera")


FLOATING_CHAT_CSS = """
<style>
    div.st-key-vera_floating_chat {
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 9999;
    }
    div.st-key-vera_floating_chat button {
        width: 56px !important;
        height: 56px !important;
        border-radius: 50% !important;
        background: var(--fill-primary) !important;
        color: var(--on-primary) !important;
        font-size: 22px !important;
        border: none !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25) !important;
        transition: transform 0.15s ease !important;
    }
    div.st-key-vera_floating_chat button:hover {
        transform: translateY(-2px);
    }
    div.st-key-vera_floating_chat [data-testid="stPopoverBody"] {
        width: 320px !important;
        max-width: 90vw !important;
    }
</style>
"""


def render_floating_chat():
    """Render a real, usable Vera chat widget in a floating bottom-right popover,
    accessible from any page without navigating away. Requires shared/theme.py's
    get_vera_css() to already be loaded on the page (for icons + color tokens).

    In hosted mode this is a no-op for anyone not logged in: several pages that
    call this (01_F-1_Student_Visa.py, 05_Post_Visa_Guide.py, 06_About.py,
    17_Interview_Prep.py, 18_Document_Checklist.py) don't gate on auth.require_login()
    themselves, so without this check an anonymous visitor could reach any of
    them directly by URL and get a live, LLM-backed chat with no account and no
    session-spanning rate limit — unbounded anonymous access to a paid API.
    Local mode has no accounts by design, so the widget still shows for everyone
    there, matching original prototype behavior.
    """
    from shared import auth, config
    from shared.chat_panel import render_chat_panel

    if config.is_supabase_configured() and not auth.is_logged_in():
        return

    st.markdown(FLOATING_CHAT_CSS, unsafe_allow_html=True)
    with st.popover("💬", key="vera_floating_chat"):
        render_chat_panel()
