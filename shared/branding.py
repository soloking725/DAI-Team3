"""
Brand assets.

The wordmark is optional: if assets/veravisa-logo.png is present it's used as the
brand mark in the header, otherwise we fall back to the "Vera" text link. This
keeps the app working in a fresh checkout that doesn't have the image yet.
"""

import base64
from functools import lru_cache
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_LOGO_CANDIDATES = ("veravisa-logo.png", "veravisa-logo.svg", "logo.png")

_FAVICON_PATH = _ASSETS / "veravisa-favicon.png"
# Passed to st.set_page_config(page_icon=...) on every page. Falls back to an
# emoji if the asset is missing so a fresh checkout still renders.
FAVICON = str(_FAVICON_PATH) if _FAVICON_PATH.exists() else "🛂"


@lru_cache(maxsize=1)
def get_logo_data_uri() -> str:
    """Return the logo as a data: URI, or "" if no logo file is present."""
    for name in _LOGO_CANDIDATES:
        path = _ASSETS / name
        if path.exists():
            mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{encoded}"
    return ""


def has_logo() -> bool:
    return bool(get_logo_data_uri())


@lru_cache(maxsize=1)
def get_favicon_data_uri() -> str:
    """Return the favicon (the compact checkmark mark, no wordmark) as a
    data: URI, or "" if the asset is missing — for reusing it inline in a
    page's own HTML (e.g. app.py's hero icon), not just as the browser tab
    icon via FAVICON/st.set_page_config."""
    if not _FAVICON_PATH.exists():
        return ""
    encoded = base64.b64encode(_FAVICON_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
