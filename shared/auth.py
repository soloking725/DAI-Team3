"""
Authentication for Vera's hosted (B2B) mode.

Two modes, switched on config.is_supabase_configured():

- Local mode (no Supabase): there is no login. get_current_user() returns a
  synthetic user so the rest of the app behaves exactly like the original
  prototype — session keyed by the ?vid= URL param, persisted to local JSON.

- Hosted mode: email one-time-code login via Supabase Auth. We use the 6-digit
  OTP flow rather than magic links because Streamlit can't read the URL fragment
  a magic link redirects with. On successful verification we look up the pilot
  college by the email's domain, create/update the app-level users + students
  rows, and cache the identity in st.session_state.

Role model for the MVP: 'student' by default; 'dso' if the email is in the
DSO_EMAILS allow-list. No self-serve role changes.

Which college a user belongs to is decided by their email domain at login time
(colleges.email_domain), so more than one college can coexist — useful for
keeping a throwaway test college alongside the real pilot school. Users only ever
see data for the college their domain maps to.
"""

from __future__ import annotations

import logging
import time

import streamlit as st

from shared import config, db

logger = logging.getLogger(__name__)

_OTP_SEND_COOLDOWN_SECONDS = 60
_OTP_MAX_VERIFY_ATTEMPTS = 5

# "Remember me" cookie — see _restore_session_from_cookie() below and
# migrations/007_web_sessions.sql. Chosen as a middle ground: long enough that
# students aren't stuck re-requesting a slow OTP email every couple of days,
# short enough to bound how long a leaked cookie stays useful.
_SESSION_COOKIE_NAME = "session_token"
_SESSION_TTL_DAYS = 7

# How many extra reruns we'll force waiting for the cookie component to
# report ready() before giving up on this browser session. One is usually
# enough, but a slow network/extension can need a couple more — see
# _restore_session_from_cookie().
_COOKIE_READY_MAX_RERUNS = 3

_LOCAL_USER = {
    "id": "local",
    "email": "",
    "name": "",
    "role": "student",
    "college_id": None,
    "mode": "local",
}


def _cookie_manager():
    """A fresh CookieManager for *this* script run.

    The underlying component crashes with a duplicate-element-key error if
    constructed more than once in the same run, so every call site here goes
    through this one function, and no call site should be reachable more than
    once per run — see the guards in get_current_user()/_restore_session_from_cookie().
    """
    from streamlit_cookies_manager import CookieManager
    return CookieManager(prefix="vera_")


def _restore_session_from_cookie() -> tuple[dict | None, bool]:
    """Look up the persisted-login cookie (if any) and restore auth_user from it.

    Returns (user_or_None, definitive). `definitive` is False when the cookie
    component still hasn't finished its browser round-trip — the caller must
    not cache that as "no session" or a slow-loading component would lock the
    user out of cookie restore for the rest of the browser session.

    The cookie component needs a browser round-trip before it's ready to
    read — on the very first render of a brand-new browser session, ready()
    is False. We force a few extra reruns (bounded by
    _COOKIE_READY_MAX_RERUNS) to give it that round-trip; only once we've
    either gotten a real answer or exhausted the retries do we commit to a
    result.
    """
    cookies = _cookie_manager()
    if not cookies.ready():
        retries = st.session_state.get("_cookie_wait_reruns", 0)
        if retries < _COOKIE_READY_MAX_RERUNS:
            st.session_state["_cookie_wait_reruns"] = retries + 1
            st.rerun()
        # Retries exhausted — per the docstring, this now *is* the definitive
        # answer (give up, no session), not an indefinite "try again later".
        # Returning False here (as this used to) meant get_current_user()
        # never set _cookie_restore_done, so every later auth check in the
        # same run — and every run after — re-instantiated CookieManager(),
        # which crashes with StreamlitDuplicateElementKey the moment two auth
        # checks land in one script run (e.g. render_hamburger_menu's
        # is_logged_in() followed by a page's own require_login()).
        return None, True

    token = cookies.get(_SESSION_COOKIE_NAME)
    if not token:
        return None, True

    user_id = db.resolve_web_session(token)
    if not user_id:
        return None, True
    user_row = db.get_user(user_id)
    if not user_row:
        return None, True
    college = db.get_college(user_row["college_id"]) if user_row.get("college_id") else None
    return {
        "id": user_row["id"],
        "email": user_row.get("email", ""),
        "name": user_row.get("name", ""),
        "role": user_row["role"],
        "college_id": user_row.get("college_id"),
        "college_name": (college or {}).get("name", ""),
        "mode": "hosted",
    }, True


def get_current_user() -> dict | None:
    """The authenticated user for this session, or None if login is required.

    In local mode this never returns None — it returns a synthetic student so the
    app runs without accounts, as before.

    In hosted mode, a plain page reload used to sign a student out instantly:
    st.session_state lives on the WebSocket connection, and a reload opens a
    new one. This falls back to the "remember me" cookie, retrying across a
    few reruns (guarded by _cookie_restore_done, which is only set once the
    cookie component has actually reported ready) before giving up and asking
    for a fresh login.
    """
    if not config.is_supabase_configured():
        return dict(_LOCAL_USER)

    user = st.session_state.get("auth_user")
    if user is not None:
        return user
    if st.session_state.get("_cookie_restore_done"):
        return None

    user, definitive = _restore_session_from_cookie()
    if definitive:
        st.session_state["_cookie_restore_done"] = True
    if user is not None:
        st.session_state["auth_user"] = user
    return user


def is_logged_in() -> bool:
    return get_current_user() is not None


def require_role(role: str) -> dict:
    """Guard for role-restricted pages. Stops the script if the check fails.

    Call at the top of a page body, e.g. `user = require_role("dso")`.
    """
    user = get_current_user()
    if user is None:
        st.warning("Please log in to continue.")
        st.stop()
    if user.get("role") != role:
        st.error("You don't have access to this page.")
        st.stop()
    return user


def require_login(title: str = "Sign in to Vera") -> dict:
    """Gate a page behind login. Returns the user; stops the script if not logged in.

    In local mode this is a no-op (returns the synthetic local student), so the
    prototype keeps working with no accounts. In hosted mode an anonymous visitor
    gets the login form instead of the page body.
    """
    user = get_current_user()
    if user is None:
        render_login(title)
        st.stop()
    return user


def logout() -> None:
    user = st.session_state.get("auth_user")
    if user and user.get("id"):
        # Revoke server-side first — this is the actual security boundary,
        # not whether the browser cookie itself gets cleared below. Revokes
        # every "remember me" session for this user, not just this browser's
        # (e.g. a second tab, or a since-stolen cookie), since there's no
        # single-session-scoped identifier available at this point.
        db.delete_web_sessions_for_user(user["id"])

    try:
        cookies = _cookie_manager()
        if cookies.ready() and cookies.get(_SESSION_COOKIE_NAME):
            del cookies[_SESSION_COOKIE_NAME]
            cookies.save()
    except Exception as e:
        logger.warning("Failed to clear session cookie on logout: %s", e)

    for key in ("auth_user", "vera", "_vera_loaded_key", "chat_history",
                "conversation_history", "request_timestamps", "_otp_email"):
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Login flow (hosted mode only)
# ---------------------------------------------------------------------------
def _resolve_role(email: str) -> str:
    return "dso" if email.lower() in config.DSO_EMAILS else "student"


def _finalize_login(session_user) -> dict | None:
    """After Supabase verifies the OTP, wire up the app-level user record.

    Returns the cached user dict, or None if the email domain isn't the pilot
    college's (caller shows "not authorized").
    """
    email = (session_user.email or "").lower()
    domain = email.split("@")[-1] if "@" in email else ""
    college = db.get_college_by_domain(domain)
    if college is None:
        return None

    role = _resolve_role(email)
    name = (session_user.user_metadata or {}).get("full_name", "") if getattr(
        session_user, "user_metadata", None
    ) else ""
    db.upsert_user(session_user.id, email, college["id"], role, name)
    if role == "student":
        db.ensure_student(session_user.id, college["id"])
    db.write_audit(session_user.id, "login")

    user = {
        "id": session_user.id,
        "email": email,
        "name": name,
        "role": role,
        "college_id": college["id"],
        "college_name": college.get("name", ""),
        "mode": "hosted",
    }
    st.session_state["auth_user"] = user

    # Best-effort: sets the "remember me" cookie so a reload doesn't force a
    # fresh OTP wait. Never worth failing the login itself over — a student
    # who's just waited minutes for a code shouldn't see an error here.
    try:
        token = db.create_web_session(session_user.id, _SESSION_TTL_DAYS)
        if token:
            cookies = _cookie_manager()
            if cookies.ready():
                cookies[_SESSION_COOKIE_NAME] = token
                cookies.save()
    except Exception as e:
        logger.warning("Failed to set session cookie after login: %s", e)
        st.toast("Couldn't save your login for next time — you may need to sign in again after refreshing.", icon="⚠️")

    return user


def _perform_send_code(email: str, client) -> None:
    """The actual OTP send, run only after the button has already been
    re-rendered as disabled (see _render_send_code_button) so a fast second
    click can't slip in and trigger a duplicate email."""
    try:
        client.auth.sign_in_with_otp({"email": email})
        st.session_state["_otp_email"] = email
        st.session_state["_otp_attempts"] = 0
        st.success("Code sent. Check your email.")
        st.warning("Delivery can take 2-3 minutes — please wait before requesting a new code.")
    except Exception as e:
        # The optimistic cooldown started in _render_send_code_button was for
        # a send that didn't actually happen — give the cooldown back so the
        # user isn't stuck waiting 60s to retry a failed request.
        st.session_state["_otp_sent_at"] = st.session_state.pop("_otp_prev_sent_at", 0.0)
        st.error(f"Couldn't send a code: {e}")
    finally:
        st.session_state.pop("_otp_pending_send", None)
        st.session_state.pop("_otp_prev_sent_at", None)


@st.fragment(run_every="1s")
def _render_send_code_button(email: str, client) -> None:
    """The 'Send code' / 'Resend in Xs' button, isolated in its own fragment
    so the cooldown countdown ticks down on its own every second instead of
    only updating on the next full-page rerun.

    Clicking starts the 60s cooldown and disables the button *before* the OTP
    request is made (via a fragment-scoped rerun), rather than after it
    completes — otherwise a double-click (or the 1s auto-refresh) lands while
    the request is still in flight and can fire a second, duplicate send.
    """
    pending_email = st.session_state.get("_otp_pending_send")
    if pending_email:
        st.button("Sending…", use_container_width=True, disabled=True)
        _perform_send_code(pending_email, client)
        return

    last_sent = st.session_state.get("_otp_sent_at", 0.0)
    cooldown_left = _OTP_SEND_COOLDOWN_SECONDS - (time.monotonic() - last_sent)
    if cooldown_left > 0:
        st.button(f"Resend in {int(cooldown_left) + 1}s", use_container_width=True, disabled=True)
    elif st.button("Send code", use_container_width=True):
        domain = email.split("@")[-1] if "@" in email else ""
        if "@" not in email:
            st.error("Enter a valid email address.")
        elif config.ALLOWED_EMAIL_DOMAINS and domain not in config.ALLOWED_EMAIL_DOMAINS:
            st.error("Not authorized for this pilot. Use your school email.")
        else:
            st.session_state["_otp_prev_sent_at"] = last_sent
            st.session_state["_otp_sent_at"] = time.monotonic()
            st.session_state["_otp_pending_send"] = email
            st.rerun(scope="fragment")


def render_login(title: str = "Sign in to Vera") -> None:
    """Render the email-OTP login form. No-op in local mode."""
    if not config.is_supabase_configured():
        return

    client = db.get_auth_client()
    st.markdown(f"### {title}")
    st.caption("Use your school email. We'll send you a 6-digit code.")
    st.info("Email delivery currently takes about 2-3 minutes — please wait for it before trying again.")

    email = st.text_input("School email", key="_otp_email_input").strip().lower()

    col1, _ = st.columns(2)
    with col1:
        _render_send_code_button(email, client)

    sent_to = st.session_state.get("_otp_email")
    if sent_to:
        attempts = st.session_state.get("_otp_attempts", 0)
        if attempts >= _OTP_MAX_VERIFY_ATTEMPTS:
            st.error("Too many incorrect attempts. Request a new code to try again.")
            return
        # A plain st.button next to a text_input doesn't respond to Enter — only
        # a real st.form's submit button does, so wrap code entry + verify here.
        with st.form("_otp_verify_form"):
            code = st.text_input(f"Code sent to {sent_to}", key="_otp_code").strip()
            verify_clicked = st.form_submit_button("Verify", use_container_width=True)
        if verify_clicked:
            try:
                res = client.auth.verify_otp(
                    {"email": sent_to, "token": code, "type": "email"}
                )
                if res.user is None:
                    st.session_state["_otp_attempts"] = attempts + 1
                    st.error("Invalid or expired code.")
                    return
                user = _finalize_login(res.user)
                if user is None:
                    st.error("Not authorized for this pilot.")
                    return
                st.session_state.pop("_otp_attempts", None)
                st.session_state.pop("_otp_sent_at", None)
                st.rerun()
            except Exception as e:
                st.session_state["_otp_attempts"] = attempts + 1
                st.error(f"Verification failed: {e}")
