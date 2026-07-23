"""
Persistence for the Vera flow — backend-pluggable behind stable signatures.

Two backends, chosen at runtime by config.is_supabase_configured():

- Local mode (default / prototype): no accounts. State is keyed by a session id
  carried in the URL (?vid=...) and mirrored to local/vera_sessions/<vid>.json so
  it survives a browser refresh without auth.

- Hosted mode: state is keyed by the authenticated user's id and stored in
  Postgres via shared/db.py. The ?vid= param is unused.

Callers (shared/vera_state.py, pages/15_Settings.py) use get_storage_key() +
load_session/save_session/delete_session and never need to know which backend is
live. get_or_create_session_id() is kept as an alias of get_storage_key() so
existing call sites keep working.
"""

import json
import logging
import re
import time
import uuid
from pathlib import Path

import streamlit as st

from shared import config
from shared import auth

logger = logging.getLogger(__name__)

_project_root = Path(__file__).resolve().parent.parent
SESSIONS_DIR = _project_root / "local" / "vera_sessions"

# Local mode has no accounts, so a session file lives as long as its ?vid= URL
# does — with no expiry, a link leaked once (browser history, a shared screen,
# a pasted URL) would expose that student's trip details and extenuating-
# circumstances notes indefinitely. Bounding the file's lifetime by its last
# save time caps that exposure window without requiring the login this mode
# is deliberately designed not to have.
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60


def _hosted() -> bool:
    return config.is_supabase_configured()


# Every key this module ever mints is uuid.uuid4().hex — exactly 32 lowercase
# hex characters. Anything else arriving via the *client-controlled* ?vid= URL
# param is rejected outright rather than ever reaching a filesystem path.
#
# Without this, load_session/save_session/delete_session build a path as
# `SESSIONS_DIR / f"{key}.json"` straight from that param. A key like
# "../../../../etc/cron.d/x" walks the file operations outside SESSIONS_DIR,
# and — worse — pathlib's `/` operator discards the left operand entirely
# when the right side looks absolute (`Path("/a/b") / "/etc/passwd"` ==
# `Path("/etc/passwd")`), so a value like "/tmp/evil" (URL-encoded as
# "%2Ftmp%2Fevil") would let a client choose an arbitrary absolute path —
# for save_session, an arbitrary-file-write primitive (the JSON blob is
# whatever's in the client's own Vera state), constrained only to paths the
# server process can write to. This closes that off at the one place a raw
# ?vid= value gets turned into a key.
_VALID_KEY_RE = re.compile(r"^[0-9a-f]{32}$")


def _is_valid_key(key: str) -> bool:
    return bool(key) and bool(_VALID_KEY_RE.match(key))


# ---------------------------------------------------------------------------
# Session identity
# ---------------------------------------------------------------------------
def get_storage_key() -> str:
    """The key the current session's state is stored under.

    Hosted: the authenticated user's id, or "" when nobody is logged in — pages
    reachable before login (the welcome screen) still read state, and there's
    nothing to persist for an anonymous visitor. The load/save/delete helpers
    below treat "" as "in-memory only" rather than querying Postgres with a key
    that isn't a uuid.

    Local: a ?vid= URL param, created once per browser.
    """
    if _hosted():
        user = auth.get_current_user()
        return user["id"] if user else ""
    vid = st.query_params.get("vid")
    # A malformed/tampered ?vid= (see _is_valid_key's docstring above) is
    # treated exactly like a missing one — mint a fresh, valid one instead
    # of ever handing an attacker-chosen string to a filesystem path.
    if vid and _is_valid_key(vid):
        return vid
    vid = uuid.uuid4().hex
    st.query_params["vid"] = vid
    return vid


# Back-compat alias — existing call sites import this name.
def get_or_create_session_id() -> str:
    return get_storage_key()


# ---------------------------------------------------------------------------
# Load / save / delete
# ---------------------------------------------------------------------------
def load_session(key: str) -> dict:
    """Load persisted Vera state for a storage key. Returns {} if none exists."""
    if _hosted():
        if not key:  # anonymous visitor — nothing saved for them
            return {}
        from shared import db
        return db.load_state(key)
    if not _is_valid_key(key):
        logger.warning("load_session: rejected malformed key")
        return {}
    path = SESSIONS_DIR / f"{key}.json"
    if not path.exists():
        return {}
    if time.time() - path.stat().st_mtime > SESSION_TTL_SECONDS:
        logger.info("Vera session %s expired (older than TTL); discarding", key)
        path.unlink(missing_ok=True)
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load Vera session %s: %s", key, e)
        return {}


def save_session(key: str, data: dict) -> None:
    """Persist Vera state for a storage key.

    In hosted mode with no logged-in user this is a no-op: state stays in
    st.session_state for the current run and is dropped on refresh. Onboarding is
    gated behind login, so nothing a user cares about is silently lost here.
    """
    if _hosted():
        if not key:
            logger.debug("save_session skipped: no authenticated user")
            return
        from shared import db
        user = auth.get_current_user()
        college_id = user.get("college_id") if user else None
        db.save_state(key, data, college_id=college_id)
        return
    if not _is_valid_key(key):
        logger.warning("save_session: rejected malformed key")
        return
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{key}.json"
    path.write_text(json.dumps(data, indent=2))


def delete_session(key: str) -> None:
    """Remove a session's persisted state, if any."""
    if _hosted():
        if not key:
            return
        from shared import db
        db.delete_state(key)
        return
    if not _is_valid_key(key):
        logger.warning("delete_session: rejected malformed key")
        return
    path = SESSIONS_DIR / f"{key}.json"
    path.unlink(missing_ok=True)
