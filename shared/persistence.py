"""
Local-file persistence for the Vera flow.

There's no user-account system, so progress is keyed by a session id
carried in the URL (?vid=...) rather than a login. This lets state
survive a browser refresh without adding auth.
"""

import json
import logging
import uuid
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

_project_root = Path(__file__).resolve().parent.parent
SESSIONS_DIR = _project_root / "local" / "vera_sessions"


def get_or_create_session_id() -> str:
    """Return the vid from the URL query params, creating and persisting one if absent."""
    vid = st.query_params.get("vid")
    if vid:
        return vid
    vid = uuid.uuid4().hex
    st.query_params["vid"] = vid
    return vid


def load_session(vid: str) -> dict:
    """Load persisted Vera state for a session id. Returns {} if none exists yet."""
    path = SESSIONS_DIR / f"{vid}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load Vera session %s: %s", vid, e)
        return {}


def save_session(vid: str, data: dict) -> None:
    """Persist Vera state for a session id."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{vid}.json"
    path.write_text(json.dumps(data, indent=2))


def delete_session(vid: str) -> None:
    """Remove a session's persisted state, if any."""
    path = SESSIONS_DIR / f"{vid}.json"
    path.unlink(missing_ok=True)
