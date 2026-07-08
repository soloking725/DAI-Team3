"""
Shared UI components used across multiple pages.
"""


def render_nav_bar(title="US Visa Information Resource", subtitle="Official government information on US visa categories and processes"):
    """Render the top navigation bar."""
    return f"""
    <div class="top-nav">
        <div>
            <p class="top-nav-brand">{title}</p>
            <p class="top-nav-desc">{subtitle}</p>
        </div>
    </div>
    """


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
        <p><strong>US Visa Information Resource</strong></p>
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
            Chat feature will be available here. Configure your Qwen API key in .env to enable it.
        </p>
    </div>
    """
