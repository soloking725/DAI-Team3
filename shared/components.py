"""
Shared UI components used across multiple pages.
"""

import html

import streamlit as st


def render_disclaimer():
    """Render the persistent disclaimer banner."""
    return """
    <div class="disclaimer-banner">
        <strong>Disclaimer:</strong> This tool provides factual information from official US government sources
        (USCIS, State Department, SSA). It does not provide legal advice. For legal advice about your specific
        situation, consult a licensed immigration attorney.
    </div>
    """


_VISA_TYPE_NAMES = {
    "f-1": "F-1", "j-1": "J-1", "m-1": "M-1", "h-1b": "H-1B", "other": "another visa type",
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
        <p>
            This tool provides factual information from official US government sources.
            It does not provide legal advice. For legal advice about your specific situation,
            consult a licensed immigration attorney.
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
    "j-1": "pages/02_J-1_Exchange_Visitor.py",
    "m-1": "pages/03_M-1_Vocational_Visa.py",
    "h-1b": "pages/16_Other_Visa_Coming_Soon.py",
    "other": "pages/16_Other_Visa_Coming_Soon.py",
}

HAMBURGER_CSS = """
<style>
    /* The header is a real bar pinned to the top of the viewport, not a couple of
       controls floating in the middle of the centered 1200px column. The ::before
       pseudo-element paints a full-bleed background/border across the whole window
       width while the controls themselves stay aligned with the page content. */
    div.st-key-vera_header {
        position: sticky;
        top: 0;
        z-index: 998;
        padding: 10px 0 8px;
        margin-bottom: 4px;
    }
    div.st-key-vera_header::before {
        content: "";
        position: absolute;
        top: 0; bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100vw;
        background: #ffffff;
        border-bottom: 0.5px solid var(--border);
        z-index: -1;
    }
    /* Nav bars shouldn't stack, unlike the main chat+timeline columns which
       intentionally go vertical on phones — the hamburger icon and small
       logo easily fit one row at any width, so force nowrap unconditionally
       rather than only above the tablet breakpoint. */
    div.st-key-vera_header div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    div.st-key-vera_header div[data-testid="stColumn"] {
        width: auto !important;
        min-width: 0 !important;
    }
    div.st-key-vera_header div[data-testid="stPopover"] button {
        width:32px !important; height:32px !important; padding:0 !important;
        border-radius:var(--radius) !important; border:0.5px solid var(--border) !important;
    }
    .st-key-vera_brand_link p {
        font-size: 22px !important;
        font-weight: 700 !important;
        color: var(--text-accent) !important;
    }
    /* Three-zone app-bar layout: hamburger | centered logo | matching empty
       spacer. The spacer column mirrors the hamburger column's width so the
       middle column's centered content lands on the true midpoint of the
       bar, not just the midpoint of the leftover space — this holds at any
       viewport width since Streamlit's columns are already percentage
       based, no hardcoded pixel math needed. text-align (not flex
       justify-content) does the centering: Streamlit's own wrapper divs
       inside the column stretch to 100% width, so a flex justify-content
       on the column has nothing narrower than itself to center — but the
       logo is display:inline-block, so text-align on any block ancestor
       still centers it correctly. */
    div.st-key-vera_header [data-testid="stColumn"]:has(.vera-brand-logo),
    div.st-key-vera_header [data-testid="stColumn"]:has(.st-key-vera_brand_link) {
        text-align: center;
    }
    /* Streamlit wraps inline markdown content (our logo <a>) in a <p> that
       carries its own text-align: left, which wins over the inherited
       center above — override it explicitly. */
    div.st-key-vera_header [data-testid="stColumn"]:has(.vera-brand-logo) p {
        text-align: center;
    }
    .vera-brand-logo img {
        height: 30px;
        display: block;
    }
    .vera-brand-logo {
        display: inline-block;
        line-height: 0;
    }
</style>
"""


def render_hamburger_menu(visa_type: str = "f-1"):
    """Render the top-left hamburger menu: Your Timeline, Home, Forms, Info, Help, Settings, Privacy.

    "Vera" itself is a clickable brand link back to the timeline, so there's
    always a way back to the chat+timeline screen from anywhere on the site.
    """
    from shared.branding import get_logo_data_uri

    st.markdown(HAMBURGER_CSS, unsafe_allow_html=True)

    with st.container(key="vera_header"):
        col1, col2, col3 = st.columns([1, 10, 1], vertical_alignment="center")
        with col1:
            with st.popover("☰"):
                st.page_link("pages/04_Ask_a_Question.py", label="Your Timeline", icon=":material/timeline:")
                st.page_link("app.py", label="Home", icon=":material/home:")
                st.divider()
                st.page_link(
                    _VISA_TYPE_PAGES.get(visa_type, _VISA_TYPE_PAGES["f-1"]),
                    label="Forms",
                    icon=":material/description:",
                )
                st.page_link("pages/06_About.py", label="Info", icon=":material/info:")
                st.page_link(
                    "pages/13_Help_Find_a_Lawyer.py",
                    label="Help (find a lawyer)",
                    icon=":material/balance:",
                )
                st.page_link("pages/15_Settings.py", label="Settings", icon=":material/settings:")
                st.page_link("pages/14_Privacy.py", label="Privacy", icon=":material/shield_lock:")
        with col2:
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
    """
    from shared.chat_panel import render_chat_panel

    st.markdown(FLOATING_CHAT_CSS, unsafe_allow_html=True)
    with st.popover("💬", key="vera_floating_chat"):
        render_chat_panel()
