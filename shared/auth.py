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

import time

import streamlit as st

from shared import config, db

_OTP_SEND_COOLDOWN_SECONDS = 60
_OTP_MAX_VERIFY_ATTEMPTS = 5

_LOCAL_USER = {
    "id": "local",
    "email": "",
    "name": "",
    "role": "student",
    "college_id": None,
    "mode": "local",
}


def get_current_user() -> dict | None:
    """The authenticated user for this session, or None if login is required.

    In local mode this never returns None — it returns a synthetic student so the
    app runs without accounts, as before.
    """
    if not config.is_supabase_configured():
        return dict(_LOCAL_USER)
    return st.session_state.get("auth_user")


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
    return user


def render_login(title: str = "Sign in to Vera") -> None:
    """Render the email-OTP login form. No-op in local mode."""
    if not config.is_supabase_configured():
        return

    client = db.get_auth_client()
    st.markdown(f"### {title}")
    st.caption("Use your school email. We'll send you a 6-digit code.")
    st.info("Email delivery currently takes about 2-3 minutes — please wait for it before trying again.")

    email = st.text_input("School email", key="_otp_email_input").strip().lower()

    col1, col2 = st.columns(2)
    with col1:
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
                try:
                    client.auth.sign_in_with_otp({"email": email})
                    st.session_state["_otp_email"] = email
                    st.session_state["_otp_sent_at"] = time.monotonic()
                    st.session_state["_otp_attempts"] = 0
                    st.success("Code sent. Check your email.")
                    st.warning("Delivery can take 2-3 minutes — please wait before requesting a new code.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't send a code: {e}")

    sent_to = st.session_state.get("_otp_email")
    if sent_to:
        attempts = st.session_state.get("_otp_attempts", 0)
        if attempts >= _OTP_MAX_VERIFY_ATTEMPTS:
            st.error("Too many incorrect attempts. Request a new code to try again.")
            return
        code = st.text_input(f"Code sent to {sent_to}", key="_otp_code").strip()
        with col2:
            if st.button("Verify", use_container_width=True):
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
