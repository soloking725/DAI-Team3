"""
Vera design tokens: Tabler Icons + CSS custom properties.

Maps the mockups' var(--x) design tokens onto the VeraVisa brand purple
(#8b72b0, sampled from assets/veravisa-logo.png), with green kept only for
"complete"/success states so brand and status never read as the same signal.

Contrast note: the raw brand purple only hits 4.09:1 against white, which fails
WCAG AA for normal text — so --fill-primary uses a darker step (#7c5fa8, 5.17:1)
for anything with white text on it, and --text-accent is darker still (8.21:1 on
white). Keep that split if you adjust these.
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
        --border-accent: #b9a6d4;

        --text-secondary: #4a5568;
        --text-muted: #718096;

        /* Brand purple */
        --brand: #8b72b0;
        --bg-accent: #f5f2fa;
        --text-accent: #5b4380;

        /* Green stays reserved for completed/success states only */
        --bg-success: #dcfce7;
        --text-success: #15803d;

        --fill-primary: #7c5fa8;
        --on-primary: #ffffff;
    }

    .ti {
        line-height: 1;
        vertical-align: middle;
    }

    /* Built for laptop/desktop widths — Streamlit's own responsive rules
       stack columns into a single vertical list below a certain container
       width. That's right for phones, but keep chat+timeline side-by-side
       for anything wider than a genuine phone viewport. Scoped to the
       chat+timeline row specifically (.st-key-vera_main_row) — this used to
       be a blanket rule on every div[data-testid="stHorizontalBlock"] in the
       app, which forced *every* st.columns() call anywhere (the header, the
       DSO dashboard's filter row, etc.) into equal-width columns regardless
       of the ratio it was actually given. */
    @media (min-width: 700px) {
        .st-key-vera_main_row div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }
        .st-key-vera_main_row div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
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
