"""
Global CSS styles that override Streamlit defaults completely.
Apply on every page to maintain a consistent, non-Streamlit look.
"""

GLOBAL_CSS = """
<style>
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* Body background: prevents flash on navigation */
    body {
        background-color: #f8f9fa !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #f8f9fa;
    }

    /* Layout reset */
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* Typography */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: #f8f9fa;
        color: #1a202c;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #5b4380;
    }

    p, span, label {
        color: #4a5568;
    }

    /* Top navigation bar */
    .top-nav {
        background-color: #1a365d;
        border-bottom: 1px solid #2b6cb0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .top-nav-inner {
        max-width: 1200px;
        margin: 0 auto;
        padding: 0.75rem 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 2rem;
        flex-wrap: wrap;
    }

    .top-nav-brand-col {
        display: flex;
        flex-direction: column;
        min-width: 250px;
    }

    .top-nav-brand {
        color: white;
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        margin: 0;
        line-height: 1.3;
    }

    .top-nav-desc {
        color: #90cdf4;
        font-size: 0.78rem;
        margin: 0.15rem 0 0;
        line-height: 1.4;
    }

    .top-nav-links {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        flex-wrap: wrap;
    }

    .nav-link {
        color: #cbd5e0 !important;
        text-decoration: none !important;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.4rem 0.85rem;
        border-radius: 4px;
        transition: all 0.15s ease;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        white-space: nowrap;
    }

    .nav-link:hover {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.1);
    }

    /* Style st.page_link buttons in nav to look like text links */
    .top-nav .stPageLink {
        color: #cbd5e0 !important;
        text-decoration: none !important;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.4rem 0.85rem;
        border-radius: 4px;
        transition: all 0.15s ease;
        background: none !important;
        border: none !important;
        box-shadow: none !important;
    }

    .top-nav .stPageLink:hover {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
    }

    .top-nav .stPageLink p {
        color: inherit !important;
        font-size: 0.85rem;
    }

    .top-nav .stPageLink[aria-current="page"] {
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.15) !important;
    }

    /* Disclaimer banner */
    .disclaimer-banner {
        background-color: #fffbeb;
        border: 1px solid #f6e05e;
        border-left: 4px solid #d69e2e;
        padding: 0.875rem 1.25rem;
        margin: 1.5rem auto;
        max-width: 1200px;
        font-size: 0.875rem;
        color: #744210;
    }

    .disclaimer-banner strong {
        color: #975a16;
    }

    /* Visa card */
    .visa-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        transition: box-shadow 0.2s ease;
    }

    .visa-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }

    .visa-card h3 {
        font-size: 1.125rem;
        font-weight: 600;
        color: #5b4380;
        margin: 0 0 0.5rem;
    }

    .visa-card p {
        font-size: 0.9rem;
        color: #4a5568;
        line-height: 1.5;
        margin: 0;
    }

    /* Section title */
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #5b4380;
        margin: 2.5rem 0 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }

    /* Content card (info blocks) */
    .content-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.25rem;
    }

    .content-card h3 {
        font-size: 1.125rem;
        font-weight: 600;
        color: #5b4380;
        margin: 0 0 0.75rem;
    }

    .content-card p, .content-card li {
        font-size: 0.925rem;
        color: #4a5568;
        line-height: 1.7;
    }

    .content-card ul {
        padding-left: 1.25rem;
        margin: 0;
    }

    /* Source citation box */
    .source-citation {
        background: #edf2f7;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 0.75rem 1rem;
        margin-top: 1rem;
        font-size: 0.85rem;
        color: #4a5568;
    }

    .source-citation a {
        color: #7c5fa8;
    }

    /* Chat area */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 2rem 1rem;
    }

    /* Coming soon badge */
    .coming-soon {
        background: #edf2f7;
        color: #718096;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        font-size: 0.875rem;
        text-align: center;
        border: 1px dashed #cbd5e0;
    }

    /* Footer */
    .site-footer {
        background-color: #1a365d;
        color: #a0aec0;
        text-align: center;
        padding: 2rem 1rem;
        margin-top: 3rem;
        font-size: 0.85rem;
        line-height: 1.6;
    }

    .site-footer a {
        color: #90cdf4;
    }

    .site-footer strong {
        color: #cbd5e0;
    }

    /* Override Streamlit default elements */
    .stExpander {
        border: 1px solid #e2e8f0 !important;
        border-radius: 4px !important;
    }

    .stButton > button {
        border-radius: 4px !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Streamlit chat overrides */
    .stChatMessage {
        border-left: 3px solid #7c5fa8 !important;
    }

    /* Landing page hero section */
    .hero {
        text-align: center;
        padding: 3rem 1rem 2rem;
        max-width: 800px;
        margin: 0 auto;
    }

    .hero h1 {
        font-size: 2.25rem;
        font-weight: 700;
        color: #5b4380;
        margin-bottom: 0.75rem;
        letter-spacing: -0.02em;
    }

    .hero p {
        font-size: 1.1rem;
        color: #4a5568;
        line-height: 1.6;
        max-width: 650px;
        margin: 0 auto 2rem;
    }

    /* Visa type cards grid */
    .visa-cards-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.25rem;
        max-width: 1200px;
        margin: 0 auto 3rem;
        padding: 0 1rem;
    }

    .visa-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }

    .visa-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-color: #cbd5e0;
    }

    .visa-card h3 {
        font-size: 1.125rem;
        font-weight: 600;
        color: #5b4380;
        margin: 0 0 0.5rem;
    }

    .visa-card p {
        font-size: 0.9rem;
        color: #4a5568;
        line-height: 1.5;
        margin: 0 0 1rem;
    }

    .visa-card .card-link {
        font-size: 0.875rem;
        color: #7c5fa8;
        text-decoration: none;
        font-weight: 600;
    }

    .visa-card .card-link:hover {
        text-decoration: underline;
    }

    /* Section title */
    .section-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 600;
        color: #5b4380;
        margin: 2.5rem 0 1.5rem;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Features section */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        max-width: 1200px;
        margin: 0 auto 3rem;
        padding: 0 1rem;
    }

    .feature-item {
        text-align: center;
        padding: 1.25rem;
    }

    .feature-item h4 {
        font-size: 1rem;
        font-weight: 600;
        color: #5b4380;
        margin: 0 0 0.5rem;
    }

    .feature-item p {
        font-size: 0.85rem;
        color: #718096;
        line-height: 1.5;
        margin: 0;
    }

    /* Quick start section */
    .quick-start-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.25rem;
        max-width: 900px;
        margin: 0 auto 3rem;
        padding: 0 1rem;
    }

    .quick-start-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
    }

    .quick-start-card h4 {
        font-size: 1rem;
        font-weight: 600;
        color: #5b4380;
        margin: 0 0 0.5rem;
    }

    .quick-start-card p {
        font-size: 0.875rem;
        color: #4a5568;
        line-height: 1.5;
        margin: 0;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .visa-cards-grid {
            grid-template-columns: 1fr;
        }
        .features-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .quick-start-grid {
            grid-template-columns: 1fr;
        }
        .hero h1 {
            font-size: 1.75rem;
        }
        .top-nav {
            flex-direction: column;
            align-items: flex-start;
        }
        .top-nav-links {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }
    }
</style>
"""


def get_global_css():
    """Return the global CSS string to be injected on every page."""
    return GLOBAL_CSS
