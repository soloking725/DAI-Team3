"""
Shared UI components used across multiple pages.
"""

import streamlit as st


def render_nav_bar(title="US Student Visa Information Resource", subtitle="Official government information on US student visa categories and processes"):
    """Render the top navigation bar with working page links using Streamlit native navigation."""
    # Brand
    st.markdown(f"""
    <div class="top-nav">
        <div class="top-nav-inner">
            <div class="top-nav-brand-col">
                <p class="top-nav-brand">{title}</p>
                <p class="top-nav-desc">{subtitle}</p>
            </div>
            <div class="top-nav-links">
                <a href="/" class="nav-link">Home</a>
                <a href="/01_F-1_Student_Visa" class="nav-link">F-1</a>
                <a href="/02_J-1_Exchange_Visitor" class="nav-link">J-1</a>
                <a href="/03_M-1_Vocational_Visa" class="nav-link">M-1</a>
                <a href="/04_Ask_a_Question" class="nav-link">Ask a Question</a>
                <a href="/05_Post_Visa_Guide" class="nav-link">Post-Arrival</a>
                <a href="/06_About" class="nav-link">About</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_disclaimer():
    """Render the persistent disclaimer banner."""
    return """
    <div class="disclaimer-banner">
        <strong>Disclaimer:</strong> This tool provides factual information from official US government sources
        (USCIS, State Department, SSA). It does not provide legal advice. For legal advice about your specific
        situation, consult a licensed immigration attorney.
    </div>
    """


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
    return f"""
    <div class="content-card">
        <h3>{title}</h3>
        {content_html}
        {link_html}
    </div>
    """


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


def render_coming_soon(feature_name):
    """Render a 'coming soon' placeholder."""
    return f'<div class="coming-soon">{feature_name} - Coming soon</div>'


def render_chat_placeholder():
    """Render a placeholder for the chat feature."""
    return """
    <div style="background:white; border:1px solid #e2e8f0; border-radius:6px; padding:2rem; text-align:center; margin-top:1.5rem;">
        <p style="color:#718096; font-size:0.95rem; margin:0;">
            Chat feature available on the Ask a Question page. Configure your Qwen API key in .env to enable it.
        </p>
    </div>
    """


def render_floating_chat():
    """Render a floating chat button in the bottom-right corner accessible from any page.

    Uses a Streamlit page_link styled with CSS to look like a floating button.
    Place this at the bottom of each page.
    """
    st.markdown("""
    <style>
        .floating-chat-container {
            position: fixed;
            bottom: 1.5rem;
            right: 1.5rem;
            z-index: 9999;
        }
        .floating-chat-container > div {
            background: #1a365d !important;
            border-radius: 50px !important;
            box-shadow: 0 4px 16px rgba(26, 54, 93, 0.4) !important;
            transition: all 0.2s ease !important;
            padding: 0.6rem 1.25rem !important;
            border: none !important;
        }
        .floating-chat-container > div:hover {
            background: #2b6cb0 !important;
            box-shadow: 0 6px 20px rgba(26, 54, 93, 0.5) !important;
            transform: translateY(-1px);
        }
        .floating-chat-container p {
            color: white !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            margin: 0 !important;
            font-family: 'Inter', sans-serif !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # The actual clickable navigation uses Streamlit native page_link
    st.markdown('<div class="floating-chat-container">', unsafe_allow_html=True)
    st.page_link("pages/04_Ask_a_Question.py", label="Ask a Question")
    st.markdown('</div>', unsafe_allow_html=True)
