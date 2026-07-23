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

  "Stay logged in across a reload" is carried primarily via a ?st= URL query
  param (an opaque, revocable, TTL-bound token — see migrations/007_web_sessions.sql),
  not a cookie. A browser cookie is still attempted as a secondary, best-effort
  fallback, but query params are the one thing Streamlit reliably round-trips
  on every rerun; cookies set via a custom-component iframe are a widely-reported
  source of "doesn't survive F5" bugs on Streamlit Community Cloud specifically
  (the whole app runs inside the platform's own wrapper iframe) across every
  cookie-manager package in the ecosystem, not something specific to this app.

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

# Caps total OTP sends per email *domain* in a rolling window — the
# session-local cooldown above resets for free in a new tab/incognito
# window, so it does nothing against a script working through many
# different (often nonexistent) usernames at one allowed domain. This is
# the actual backstop; see migrations/014_otp_rate_limits.sql. Sized to
# comfortably clear a real pilot college's first-day signup rush (a few
# hundred students within an hour) while still bounding a flood.
_OTP_DOMAIN_MAX_SENDS = 100
_OTP_DOMAIN_WINDOW_SECONDS = 3600

# "Remember me" session TTL, shared by both persistence mechanisms below —
# the primary ?st= query param (_restore_session_from_query_param) and the
# secondary best-effort cookie (_restore_session_from_cookie). See
# migrations/007_web_sessions.sql. Chosen as a middle ground: long enough
# that students aren't stuck re-requesting a slow OTP email every couple of
# days, short enough to bound how long a leaked token stays useful.
_SESSION_COOKIE_NAME = "session_token"
_SESSION_TTL_DAYS = 7

# How many extra reruns we'll force waiting for the cookie component to
# report ready() before giving up on this browser session. This has to cover
# a full browser round-trip on the *first* mount of the component (load its
# iframe, execute its JS bundle, call back) — on a cold Streamlit Cloud
# instance that alone can burn through a handful of quick reruns, and giving
# up too early here is exactly what made a plain page reload silently log
# students out (see the retries-exhausted branch below: once this budget is
# spent we commit to "no session" for the rest of the browser session).
_COOKIE_READY_MAX_RERUNS = 10

_LOCAL_USER = {
    "id": "local",
    "email": "",
    "name": "",
    "role": "student",
    "college_id": None,
    "mode": "local",
}


_SESSION_QUERY_PARAM = "st"


def _user_from_web_session(token: str) -> dict | None:
    """Shared lookup for both the query-param and cookie restore paths —
    resolves an opaque "remember me" token (migrations/007_web_sessions.sql)
    to the user it belongs to, or None if it's missing/expired/revoked."""
    if not token:
        return None
    user_id = db.resolve_web_session(token)
    if not user_id:
        return None
    user_row = db.get_user(user_id)
    if not user_row:
        return None
    college = db.get_college(user_row["college_id"]) if user_row.get("college_id") else None
    return {
        "id": user_row["id"],
        "email": user_row.get("email", ""),
        "name": user_row.get("name", ""),
        "role": user_row["role"],
        "college_id": user_row.get("college_id"),
        "college_name": (college or {}).get("name", ""),
        "mode": "hosted",
    }


def _restore_session_from_query_param() -> dict | None:
    """The primary "stay logged in across a reload" mechanism — a
    revocable, opaque session token carried in the URL's ?st= param.

    This exists because the cookie path below (streamlit_cookies_manager)
    is unreliable specifically on Streamlit Community Cloud: the whole app
    is itself served inside the platform's own wrapper iframe, so the
    cookie component's bridge from its own component-iframe up to
    "the app" (not the true top-level page) plus Streamlit's own
    component-value caching adds up to a widely-reported class of bugs
    across every cookie-manager package in the Streamlit ecosystem, not
    something specific to a coding mistake here (see the streamlit-cookies-
    manager and streamlit-authenticator issue trackers). Query params don't
    go through any of that — they're just part of the URL Streamlit already
    round-trips on every rerun, which is exactly why local mode's ?vid=
    session id has always survived reloads reliably while this cookie never
    did. Same trust model as the cookie it replaces as primary: an opaque,
    revocable token (never the raw Supabase JWT), same TTL, same server-side
    revocation on logout — just carried somewhere Streamlit actually
    guarantees round-trips.
    """
    token = st.query_params.get(_SESSION_QUERY_PARAM)
    return _user_from_web_session(token) if token else None


def _cookie_manager():
    """A fresh CookieManager for *this* script run.

    The underlying component crashes with a duplicate-element-key error if
    constructed more than once in the same run, so every call site here goes
    through this one function, and no call site should be reachable more than
    once per run — see the guards in get_current_user()/_restore_session_from_cookie().
    """
    from streamlit_cookies_manager import CookieManager
    return CookieManager(prefix="vera_")


def _restore_session_from_cookie() -> tuple[dict | None, bool, str]:
    """Look up the persisted-login cookie (if any) and restore auth_user from it.

    Returns (user_or_None, definitive, token). `token` is returned alongside
    the user so the caller can promote it into the ?st= query param (the
    primary mechanism — see _restore_session_from_query_param) once the
    cookie has successfully produced one, so the *next* load doesn't need
    the cookie at all. `definitive` is False when the cookie
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
        return None, True, ""

    token = cookies.get(_SESSION_COOKIE_NAME) or ""
    return _user_from_web_session(token), True, token


def get_current_user() -> dict | None:
    """The authenticated user for this session, or None if login is required.

    In local mode this never returns None — it returns a synthetic student so the
    app runs without accounts, as before.

    In hosted mode, a plain page reload used to sign a student out instantly:
    st.session_state lives on the WebSocket connection, and a reload opens a
    new one. The ?st= query param (see _restore_session_from_query_param) is
    the primary fix for that — checked first since it's synchronous and
    doesn't need any browser round-trip. The cookie is only consulted as a
    secondary, best-effort path (e.g. a bookmarked/shared URL that's lost its
    query string) — see _restore_session_from_cookie's docstring for why it
    can't be the primary mechanism on its own.
    """
    if not config.is_supabase_configured():
        return dict(_LOCAL_USER)

    user = st.session_state.get("auth_user")
    if user is not None:
        return user

    user = _restore_session_from_query_param()
    if user is not None:
        st.session_state["auth_user"] = user
        st.session_state["_cookie_restore_done"] = True
        return user

    if st.session_state.get("_cookie_restore_done"):
        return None

    user, definitive, token = _restore_session_from_cookie()
    if definitive:
        st.session_state["_cookie_restore_done"] = True
    if user is not None:
        st.session_state["auth_user"] = user
        # Promote to the query param too — once the cookie has produced a
        # user, subsequent reruns (and the very next page load) should be
        # able to use the fast, reliable path instead of doing this again.
        if token:
            st.query_params[_SESSION_QUERY_PARAM] = token
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
        # not whether the browser cookie/query param themselves get cleared
        # below. Revokes every "remember me" session for this user, not just
        # this browser's (e.g. a second tab, or a since-stolen token), since
        # there's no single-session-scoped identifier available at this point.
        db.delete_web_sessions_for_user(user["id"])

    st.query_params.pop(_SESSION_QUERY_PARAM, None)

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

    # "Remember me" so a reload doesn't force a fresh OTP wait. The query
    # param is the primary mechanism (reliable — see
    # _restore_session_from_query_param's docstring) and is set
    # unconditionally; the cookie is attempted too, best-effort, purely as a
    # fallback for a URL that loses its query string (e.g. a bookmark saved
    # without it). Neither is worth failing the login itself over — a
    # student who's just waited minutes for a code shouldn't see an error.
    try:
        token = db.create_web_session(session_user.id, _SESSION_TTL_DAYS)
        if token:
            st.query_params[_SESSION_QUERY_PARAM] = token
            try:
                cookies = _cookie_manager()
                if cookies.ready():
                    cookies[_SESSION_COOKIE_NAME] = token
                    cookies.save()
            except Exception as e:
                logger.warning("Failed to set session cookie after login (query param still works): %s", e)
    except Exception as e:
        logger.warning("Failed to create a persisted login session: %s", e)
        st.toast("Couldn't save your login for next time — you may need to sign in again after refreshing.", icon="⚠️")

    return user


def _perform_send_code(email: str, client) -> None:
    """The actual OTP send, run only after the button has already been
    re-rendered as disabled (see _render_otp_flow) so a fast second click
    can't slip in and trigger a duplicate email."""
    from shared import db

    domain = email.split("@")[-1] if "@" in email else ""
    allowed, _wait_seconds = db.check_and_increment_otp_domain_rate_limit(
        domain, _OTP_DOMAIN_MAX_SENDS, _OTP_DOMAIN_WINDOW_SECONDS
    )
    if not allowed:
        # Deliberately vague — no exact counts/thresholds, so this doesn't
        # help an attacker calibrate around the limit.
        st.session_state["_otp_sent_at"] = st.session_state.pop("_otp_prev_sent_at", 0.0)
        st.session_state["_otp_flash"] = (
            "error",
            "Too many login attempts for this school right now. Please try again later.",
        )
        st.session_state.pop("_otp_pending_send", None)
        st.session_state.pop("_otp_prev_sent_at", None)
        return
    try:
        client.auth.sign_in_with_otp({"email": email})
        st.session_state["_otp_email"] = email
        st.session_state["_otp_attempts"] = 0
        st.session_state["_otp_flash"] = (
            "success",
            "Code sent. Check your email — delivery can take 2-3 minutes.",
        )
    except Exception as e:
        # The optimistic cooldown started by the Send code button was for a
        # send that didn't actually happen — give the cooldown back so the
        # user isn't stuck waiting 60s to retry a failed request.
        st.session_state["_otp_sent_at"] = st.session_state.pop("_otp_prev_sent_at", 0.0)
        st.session_state["_otp_flash"] = ("error", f"Couldn't send a code: {e}")
    finally:
        st.session_state.pop("_otp_pending_send", None)
        st.session_state.pop("_otp_prev_sent_at", None)


@st.fragment(run_every="1s")
def _render_otp_flow(email: str, client) -> None:
    """Send/resend button, code entry, and Verify all live in *one* fragment
    (run_every="1s" so the cooldown countdown ticks on its own) so every step
    of this flow only ever needs a fragment-scoped rerun.

    This used to be split: the button in its own fragment, the code-entry
    form in the outer, non-fragment page body. Making the code box appear
    after sending meant escaping the button's fragment with an unscoped
    st.rerun() to force the outer body to re-run — and that cross-boundary
    escape could leave a stale copy of the form rendered outside the
    fragment instead of cleanly replacing it (two Verify buttons stacked).
    Keeping the whole flow in one fragment means a plain
    st.rerun(scope="fragment") is enough at every step; only a *successful*
    login still escapes with a full st.rerun(), since that's a one-time
    transition to a whole different page, not a repeatable action.
    """
    pending_email = st.session_state.get("_otp_pending_send")
    col1, _ = st.columns(2)
    if pending_email:
        with col1:
            st.button("Sending…", use_container_width=True, disabled=True)
        _perform_send_code(pending_email, client)
        st.rerun(scope="fragment")

    _flash = st.session_state.pop("_otp_flash", None)
    if _flash:
        _kind, _message = _flash
        getattr(st, _kind)(_message)

    last_sent = st.session_state.get("_otp_sent_at", 0.0)
    cooldown_left = _OTP_SEND_COOLDOWN_SECONDS - (time.monotonic() - last_sent)
    with col1:
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
                # Login success changes the whole page (post-login content,
                # the hamburger menu's sign-out option, etc.), not just this
                # fragment's own subtree — this is the one step that still
                # needs to escape to a full rerun.
                st.rerun()
            except Exception as e:
                st.session_state["_otp_attempts"] = attempts + 1
                st.error(f"Verification failed: {e}")


def render_login(title: str = "Sign in to Vera") -> None:
    """Render the email-OTP login form. No-op in local mode."""
    if not config.is_supabase_configured():
        return

    client = db.get_auth_client()
    st.markdown(f"### {title}")
    st.caption("Use your school email. We'll send you a 6-digit code.")
    st.info("Email delivery currently takes about 2-3 minutes — please wait for it before trying again.")

    email = st.text_input("School email", key="_otp_email_input").strip().lower()

    _render_otp_flow(email, client)
