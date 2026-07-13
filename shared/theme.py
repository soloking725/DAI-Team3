"""
Vera design tokens: Tabler Icons + CSS custom properties.

Maps the mockups' var(--x) design tokens onto a light-green brand accent,
with a distinct (deeper-tint) green reserved for "complete" success states
so the two don't visually collide, and 12px-rounded surfaces.
"""

VERA_CSS = """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3.44.0/dist/tabler-icons.min.css" />
<style>
    :root {
        --radius: 8px;

        --surface-1: #f8f9fa;
        --surface-2: #ffffff;

        --border: #e2e8f0;
        --border-strong: #cbd5e0;
        --border-accent: #4ade80;

        --text-secondary: #4a5568;
        --text-muted: #718096;

        --bg-accent: #f0fdf4;
        --text-accent: #166534;

        --bg-success: #dcfce7;
        --text-success: #15803d;

        --fill-primary: #16a34a;
        --on-primary: #ffffff;
    }

    .ti {
        line-height: 1;
        vertical-align: middle;
    }

    /* Built for laptop/desktop widths — Streamlit's own responsive rules
       stack columns into a single vertical list below a certain container
       width. That's right for phones, but keep chat+timeline side-by-side
       for anything wider than a genuine phone viewport. */
    @media (min-width: 700px) {
        div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            width: auto !important;
            flex: 1 1 0 !important;
            min-width: 0 !important;
        }
    }
</style>
"""


def get_vera_css():
    """Return the Vera design-token CSS + icon font, to be injected once per page."""
    return VERA_CSS
