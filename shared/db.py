"""
Supabase data layer for Vera's hosted (B2B) mode.

Everything that touches Postgres goes through this module so queries aren't
scattered across pages. The client is created once per Streamlit process via
@st.cache_resource (Streamlit reruns the whole script on every interaction, so
an uncached client would reconnect constantly).

Design notes:
- Streamlit is trusted middleware here: it authenticates the user in
  shared/auth.py and then talks to Postgres with the *service* key. Row-Level
  Security policies exist in migrations/001_init.sql as defense-in-depth, but the
  authoritative access check for the MVP is that every query below filters by an
  explicit college_id passed down from the authenticated session.
- The student's Vera state is stored two ways in the `students` row: the full
  blob in `full_state` (the app's source of truth, round-trips losslessly), plus
  denormalized columns (visa_type, origin_country, current_step_*) that the DSO
  dashboard can filter/sort in SQL without unpacking JSON. save_state() keeps the
  two in sync; nothing else writes those columns.

If `supabase` isn't installed or isn't configured, is_available() is False and
callers fall back to local-file persistence — the app still runs.
"""

from __future__ import annotations

import datetime
import logging
import secrets
from typing import Any, Optional

import streamlit as st

from shared import config

logger = logging.getLogger(__name__)

try:
    from supabase import Client, create_client
    _SUPABASE_IMPORTABLE = True
except ImportError:  # supabase-py not installed → local mode only
    Client = Any  # type: ignore
    create_client = None  # type: ignore
    _SUPABASE_IMPORTABLE = False


def is_available() -> bool:
    """True when we can actually talk to Postgres (package present + configured)."""
    return _SUPABASE_IMPORTABLE and config.is_supabase_configured()


@st.cache_resource
def get_client() -> Optional["Client"]:
    """Return a process-wide Supabase client, or None in local mode.

    Uses the service key: server-side, trusted, bypasses RLS. Access control is
    enforced by the explicit college_id filters in the query helpers below plus
    the role checks in shared/auth.py — never by trusting the browser.
    """
    if not is_available():
        return None
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


@st.cache_resource
def get_auth_client() -> Optional["Client"]:
    """Separate client, anon key, for the OTP login handshake only.

    Never share this with get_client(): calling .auth.verify_otp() on a
    Supabase client swaps its session onto the logged-in user's JWT, which
    would silently downgrade every later service-key query (via get_client())
    from bypassing RLS to running as that authenticated user, since both are
    cached singletons for the process lifetime.
    """
    if not is_available():
        return None
    return create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)


# ---------------------------------------------------------------------------
# Colleges
# ---------------------------------------------------------------------------
def get_college_by_domain(email_domain: str) -> Optional[dict]:
    """Look up the pilot college row for an email domain (e.g. 'colby.edu')."""
    client = get_client()
    if client is None:
        return None
    res = (
        client.table("colleges")
        .select("*")
        .eq("email_domain", email_domain.lower())
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_college(college_id: str) -> Optional[dict]:
    client = get_client()
    if client is None:
        return None
    res = client.table("colleges").select("*").eq("id", college_id).limit(1).execute()
    return res.data[0] if res.data else None


def set_college_guide_url(college_id: str, guide_pdf_url: str) -> None:
    client = get_client()
    if client is None:
        return
    client.table("colleges").update({"guide_pdf_url": guide_pdf_url}).eq(
        "id", college_id
    ).execute()


def set_college_guide_steps(college_id: str, steps: list) -> None:
    """Store the steps the DSO extracted from the school's guide PDF
    (see shared/pdf_guide.py), once per college. Every student at this
    college inherits these automatically (pages/04_Ask_a_Question.py)
    instead of each uploading and extracting their own copy."""
    client = get_client()
    if client is None:
        return
    client.table("colleges").update({"guide_steps": steps}).eq(
        "id", college_id
    ).execute()


# ---------------------------------------------------------------------------
# Users (identity + role), created/updated at login by shared/auth.py
# ---------------------------------------------------------------------------
def upsert_user(
    user_id: str, email: str, college_id: str, role: str, name: str = ""
) -> dict:
    """Insert or update the app-level user record for an authenticated identity.

    `role` is re-derived from the DSO_EMAILS allow-list on every login (see
    shared/auth.py's _resolve_role) and written here each time, so granting or
    revoking DSO access is a secrets-only change — no DB update needed, and no
    stale role lingering from before an email was added to/removed from the
    allow-list.
    """
    client = get_client()
    if client is None:
        raise RuntimeError("upsert_user called in local mode")
    row = {
        "id": user_id,
        "email": email.lower(),
        "college_id": college_id,
        "role": role,
    }
    if name:
        row["name"] = name
    client.table("users").upsert(row).execute()
    return get_user(user_id)


def get_user(user_id: str) -> Optional[dict]:
    client = get_client()
    if client is None:
        return None
    res = client.table("users").select("*").eq("id", user_id).limit(1).execute()
    return res.data[0] if res.data else None


# ---------------------------------------------------------------------------
# Web sessions ("remember me") — a browser-cookie-held opaque token mapped to
# a user_id here, so a full page reload can restore login without a fresh OTP
# round-trip. The cookie never carries the raw Supabase JWT, only this random
# token, so a leaked cookie can be revoked by deleting/expiring its row here
# without touching the underlying Supabase Auth session.
# ---------------------------------------------------------------------------
def create_web_session(user_id: str, ttl_days: int) -> str:
    """Create a new persisted login token for user_id, valid for ttl_days."""
    client = get_client()
    if client is None:
        return ""
    token = secrets.token_urlsafe(32)
    expires_at = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=ttl_days)
    ).isoformat()
    client.table("web_sessions").insert(
        {"token": token, "user_id": user_id, "expires_at": expires_at}
    ).execute()
    return token


def resolve_web_session(token: str) -> Optional[str]:
    """Return the user_id a still-valid session token belongs to, or None.

    Opportunistically deletes the row if it's expired, instead of waiting on
    a scheduled cleanup job — the same way a lazily-expired cache entry works.
    """
    client = get_client()
    if client is None or not token:
        return None
    res = (
        client.table("web_sessions")
        .select("user_id,expires_at")
        .eq("token", token)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    row = res.data[0]
    expires_at = datetime.datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
    if datetime.datetime.now(datetime.timezone.utc) >= expires_at:
        client.table("web_sessions").delete().eq("token", token).execute()
        return None
    return row["user_id"]


def delete_web_sessions_for_user(user_id: str) -> None:
    """Revoke every persisted login session for a user (sign-out).

    Deletes by user_id rather than the one token the current browser holds,
    so signing out on one device also revokes any other still-valid "remember
    me" cookie for that account (e.g. a second tab or a since-stolen cookie) —
    the actual security boundary is this server-side row, not whether the
    browser also managed to clear its own cookie.
    """
    client = get_client()
    if client is None:
        return
    client.table("web_sessions").delete().eq("user_id", user_id).execute()


# ---------------------------------------------------------------------------
# Student state  (the app's vera-state blob <-> normalized students row)
# ---------------------------------------------------------------------------
def _denormalize(blob: dict) -> dict:
    """Pull the DSO-dashboard-relevant columns out of a vera-state blob."""
    profile = blob.get("profile", {}) or {}
    trip = blob.get("trip_details", {}) or {}
    timeline = blob.get("timeline", []) or []
    # "current step" = first step not yet complete, matching the timeline UI.
    current = next((s for s in timeline if s.get("status") != "complete"), None) or {}
    return {
        "visa_type": profile.get("visa_type") or None,
        "origin_country": trip.get("origin") or None,
        "destination": trip.get("destination") or None,
        "school": trip.get("school") or None,
        "entering_year": trip.get("entering_year") or None,
        "graduation_year": trip.get("graduation_year") or None,
        "current_step_key": current.get("id"),
        "current_step_status": current.get("status"),
        "extenuating_flags": blob.get("extenuating_circumstances", {}) or {},
        "full_state": blob,
    }


def ensure_student(user_id: str, college_id: str) -> None:
    """Make sure a students row exists so the dashboard sees the user immediately."""
    client = get_client()
    if client is None:
        return
    existing = (
        client.table("students").select("user_id").eq("user_id", user_id).limit(1).execute()
    )
    if not existing.data:
        client.table("students").insert(
            {"user_id": user_id, "college_id": college_id, "full_state": {}}
        ).execute()


def load_state(user_id: str) -> dict:
    """Return a student's vera-state blob, or {} if none saved yet."""
    client = get_client()
    if client is None:
        return {}
    res = (
        client.table("students")
        .select("full_state")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if res.data and res.data[0].get("full_state"):
        return res.data[0]["full_state"]
    return {}


def save_state(user_id: str, blob: dict, college_id: Optional[str] = None) -> None:
    """Upsert a student's blob and the denormalized columns derived from it."""
    client = get_client()
    if client is None:
        return
    row = {"user_id": user_id, **_denormalize(blob)}
    if college_id:
        row["college_id"] = college_id
    client.table("students").upsert(row).execute()


def delete_state(user_id: str) -> None:
    """Reset a student's saved progress (keeps the row, clears the state)."""
    client = get_client()
    if client is None:
        return
    client.table("students").update(
        {
            "full_state": {},
            "visa_type": None,
            "origin_country": None,
            "destination": None,
            "school": None,
            "current_step_key": None,
            "current_step_status": None,
            "extenuating_flags": {},
        }
    ).eq("user_id", user_id).execute()


def delete_student_account(user_id: str, college_id: str) -> bool:
    """Permanently remove a student's account and every row referencing them
    (messages, audit log entries, the students row, the users row itself),
    plus their underlying Supabase Auth identity — a full right-to-erasure,
    not just the app-level profile.

    Always available on request — self-service from Settings, or as part of
    graduate_and_anonymize() below — regardless of whether the student's
    school requires them to use Vera. A school mandating use of the tool
    doesn't require Vera to keep the student's data forever; it isn't the
    system of record for SEVIS compliance (that's the DSO's own SEVIS access).

    Scoped to college_id so a caller can only delete a student that actually
    belongs to the acting DSO's (or the student's own) college.
    """
    client = get_client()
    if client is None:
        return False
    row = (
        client.table("users").select("id,college_id,role")
        .eq("id", user_id).limit(1).execute()
    )
    if not row.data or row.data[0]["college_id"] != college_id or row.data[0]["role"] != "student":
        return False
    # messages/audit_logs reference users(id) without ON DELETE CASCADE, so
    # they have to go first or the final users delete would hit a FK violation.
    client.table("messages").delete().or_(
        f"sender_id.eq.{user_id},recipient_id.eq.{user_id}"
    ).execute()
    client.table("audit_logs").delete().eq("actor_id", user_id).execute()
    client.table("students").delete().eq("user_id", user_id).execute()
    client.table("users").delete().eq("id", user_id).execute()
    try:
        client.auth.admin.delete_user(user_id)
    except Exception as e:  # app-level data is already gone; don't undo that over this
        logger.warning("Failed to delete Supabase Auth identity for %s: %s", user_id, e)
    return True


def record_graduation_aggregate(
    college_id: str, visa_type: Optional[str], origin_country: Optional[str],
    final_step_key: Optional[str], had_flagged_circumstances: bool,
) -> None:
    """Insert one anonymous cohort-stats row — no name/email/user_id — see
    migrations/004_graduation_aggregates.sql."""
    client = get_client()
    if client is None:
        return
    client.table("graduation_aggregates").insert({
        "college_id": college_id,
        "visa_type": visa_type,
        "origin_country": origin_country,
        "final_step_key": final_step_key,
        "had_flagged_circumstances": had_flagged_circumstances,
        "cohort_year": datetime.date.today().year,
    }).execute()


def graduate_and_anonymize(user_id: str, college_id: str) -> bool:
    """DSO-triggered: record this student's anonymized aggregate stats, then
    permanently delete their individual account in the same operation — so a
    school keeps pattern-level cohort data to learn from without retaining an
    identifiable record of any one student after they leave."""
    client = get_client()
    if client is None:
        return False
    res = (
        client.table("students")
        .select("visa_type,origin_country,current_step_key,extenuating_flags")
        .eq("user_id", user_id).eq("college_id", college_id).limit(1).execute()
    )
    if not res.data:
        return False
    s = res.data[0]
    record_graduation_aggregate(
        college_id,
        s.get("visa_type"),
        s.get("origin_country"),
        s.get("current_step_key"),
        bool((s.get("extenuating_flags") or {}).get("categories")),
    )
    return delete_student_account(user_id, college_id)


# ---------------------------------------------------------------------------
# DSO dashboard queries
# ---------------------------------------------------------------------------
def list_students(college_id: str) -> list[dict]:
    """Roster for a college: one row per student with name/email + progress."""
    client = get_client()
    if client is None:
        return []
    # Two small queries (users for name/email, students for progress) joined in
    # Python — simpler and plenty fast at pilot scale than a Postgres view.
    users = (
        client.table("users")
        .select("id,name,email")
        .eq("college_id", college_id)
        .eq("role", "student")
        .execute()
    ).data or []
    students = (
        client.table("students")
        .select(
            "user_id,visa_type,origin_country,current_step_key,current_step_status,"
            "extenuating_flags,updated_at,entering_year,graduation_year"
        )
        .eq("college_id", college_id)
        .execute()
    ).data or []
    by_id = {s["user_id"]: s for s in students}
    roster = []
    for u in users:
        s = by_id.get(u["id"], {})
        flags = s.get("extenuating_flags") or {}
        roster.append(
            {
                "user_id": u["id"],
                "name": u.get("name") or "",
                "email": u.get("email") or "",
                "visa_type": s.get("visa_type") or "",
                "origin_country": s.get("origin_country") or "",
                "current_step_key": s.get("current_step_key") or "",
                "current_step_status": s.get("current_step_status") or "",
                "flagged": bool(flags.get("categories")),
                "updated_at": s.get("updated_at") or "",
                "entering_year": s.get("entering_year"),
                "graduation_year": s.get("graduation_year"),
            }
        )
    return roster


def bulk_graduate_by_year(college_id: str, graduation_year: int) -> int:
    """Graduate every student in college_id whose graduation_year matches,
    recording each one's anonymized aggregate stats and deleting their
    account (see graduate_and_anonymize). Returns how many were graduated.

    Students who never got a graduation_year backfilled (see the "one more
    thing" prompt in pages/04_Ask_a_Question.py) aren't matched by this and
    still need the per-student "Mark a student graduated" fallback below.
    """
    client = get_client()
    if client is None:
        return 0
    res = (
        client.table("students")
        .select("user_id")
        .eq("college_id", college_id)
        .eq("graduation_year", graduation_year)
        .execute()
    )
    user_ids = [row["user_id"] for row in (res.data or [])]
    count = 0
    for user_id in user_ids:
        if graduate_and_anonymize(user_id, college_id):
            count += 1
    return count


def dso_override_step(
    actor_id: str, college_id: str, student_user_id: str, step_id: str, status: str
) -> bool:
    """DSO overrides one timeline step's status on a student's behalf.

    college_id scopes this to the acting DSO's own college regardless of which
    caller/UI invokes it — the service-role client bypasses RLS, so this check
    is the actual tenant boundary, not just the roster the UI happens to show.

    Edits the student's blob in place (timeline lives inside full_state), tags the
    step as DSO-updated, re-saves (which refreshes the denormalized columns), and
    writes an audit row. Returns True if a step was actually changed.
    """
    client = get_client()
    if client is None:
        return False
    if status not in ("upcoming", "complete"):
        raise ValueError(f"invalid step status: {status!r}")

    res = (
        client.table("students")
        .select("user_id,full_state")
        .eq("user_id", student_user_id)
        .eq("college_id", college_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        return False

    blob = res.data[0].get("full_state") or {}
    changed = False
    for step in blob.get("timeline", []):
        if step.get("id") == step_id:
            step["status"] = status
            step["updated_by"] = "dso"
            changed = True
            break
    if changed:
        save_state(student_user_id, blob, college_id=college_id)
        write_audit(actor_id, "edit_step", student_user_id, {"step": step_id, "status": status})
    return changed


# ---------------------------------------------------------------------------
# Announcements (DSO -> students, pulled on page load) — either a plain
# undated announcement, or an event (info session, Q&A) tagged with event_at.
# ---------------------------------------------------------------------------
def post_announcement(college_id: str, author_id: str, body: str, event_at: Optional[str] = None) -> None:
    """event_at, if given, is an ISO 8601 timestamp string — makes this an event."""
    client = get_client()
    if client is None:
        return
    row = {"college_id": college_id, "author_id": author_id, "body": body}
    if event_at:
        row["event_at"] = event_at
    client.table("announcements").insert(row).execute()


def list_announcements(college_id: str, limit: int = 10) -> list[dict]:
    """Most recent announcements/events, newest-posted first (see list_upcoming_events
    for events specifically, sorted by when they happen rather than when posted)."""
    client = get_client()
    if client is None:
        return []
    res = (
        client.table("announcements")
        .select("body,event_at,created_at")
        .eq("college_id", college_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def list_upcoming_events(college_id: str, limit: int = 10) -> list[dict]:
    """Announcements tagged with a future event_at (info sessions, Q&As),
    soonest first — a student-facing "what's coming up" list distinct from
    the general reverse-chronological announcement feed."""
    client = get_client()
    if client is None:
        return []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    res = (
        client.table("announcements")
        .select("body,event_at,created_at")
        .eq("college_id", college_id)
        .gte("event_at", now)
        .order("event_at", desc=False)
        .limit(limit)
        .execute()
    )
    return res.data or []


# ---------------------------------------------------------------------------
# Custom reminders — the generic version of the hardcoded visa/passport
# expiration reminders (shared/reminders.py) a DSO can author for anything
# else students need to be nudged about (reporting enrolled courses, OPT
# unemployment-limit tracking, program-extension deadlines, etc). Still
# in-account only — no email/SMS transport exists in this app yet.
# ---------------------------------------------------------------------------
def create_custom_reminder(college_id: str, author_id: str, title: str, detail: str, due_date: str) -> None:
    """due_date is an ISO date string ("YYYY-MM-DD")."""
    client = get_client()
    if client is None:
        return
    client.table("custom_reminders").insert({
        "college_id": college_id, "author_id": author_id,
        "title": title, "detail": detail, "due_date": due_date,
    }).execute()


def list_custom_reminders(college_id: str, limit: int = 50) -> list[dict]:
    client = get_client()
    if client is None:
        return []
    res = (
        client.table("custom_reminders")
        .select("id,title,detail,due_date,created_at")
        .eq("college_id", college_id)
        .order("due_date", desc=False)
        .limit(limit)
        .execute()
    )
    return res.data or []


def delete_custom_reminder(reminder_id: str, college_id: str) -> None:
    client = get_client()
    if client is None:
        return
    client.table("custom_reminders").delete().eq("id", reminder_id).eq("college_id", college_id).execute()


# ---------------------------------------------------------------------------
# Direct messages (DSO <-> student, one thread per pair)
# ---------------------------------------------------------------------------
def get_dso_users(college_id: str) -> list[dict]:
    """DSOs for a college, so a student can pick who to message."""
    client = get_client()
    if client is None:
        return []
    res = (
        client.table("users")
        .select("id,name,email")
        .eq("college_id", college_id)
        .eq("role", "dso")
        .execute()
    )
    return res.data or []


def send_message(college_id: str, sender_id: str, recipient_id: str, body: str) -> None:
    """Insert a message, after verifying both parties actually belong to
    college_id and are a valid dso<->student pair.

    The service-role client bypasses RLS, so nothing else stops a caller bug
    from cross-wiring a message to the wrong college or pairing two students —
    this check is the actual tenant boundary for this table, not just a
    convenience for the UIs that currently only ever pass correctly-scoped IDs.
    """
    client = get_client()
    if client is None:
        return
    parties = (
        client.table("users")
        .select("id,college_id,role")
        .in_("id", [sender_id, recipient_id])
        .execute()
    ).data or []
    by_id = {p["id"]: p for p in parties}
    sender = by_id.get(sender_id)
    recipient = by_id.get(recipient_id)
    if not sender or not recipient:
        raise ValueError("send_message: sender or recipient not found")
    if sender["college_id"] != college_id or recipient["college_id"] != college_id:
        raise ValueError("send_message: sender/recipient must belong to college_id")
    if {sender["role"], recipient["role"]} != {"student", "dso"}:
        raise ValueError("send_message: only dso<->student messages are allowed")
    client.table("messages").insert(
        {
            "college_id": college_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "body": body,
        }
    ).execute()


def list_thread(college_id: str, user_a: str, user_b: str, limit: int = 100) -> list[dict]:
    """Every message between two specific users, oldest first."""
    client = get_client()
    if client is None:
        return []
    res = (
        client.table("messages")
        .select("sender_id,recipient_id,body,created_at")
        .eq("college_id", college_id)
        .or_(
            f"and(sender_id.eq.{user_a},recipient_id.eq.{user_b}),"
            f"and(sender_id.eq.{user_b},recipient_id.eq.{user_a})"
        )
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return res.data or []


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------
def write_audit(actor_id: str, action: str, target_id: Optional[str] = None,
                detail: Optional[dict] = None) -> None:
    client = get_client()
    if client is None:
        return
    try:
        client.table("audit_logs").insert(
            {"actor_id": actor_id, "action": action, "target_id": target_id,
             "detail": detail or {}}
        ).execute()
    except Exception as e:  # audit writes must never break a user action
        logger.warning("audit write failed (%s): %s", action, e)


# ---------------------------------------------------------------------------
# Chat rate limiting (persisted, hosted mode only — see
# migrations/006_chat_rate_limits.sql for why this exists alongside the
# session-only check in shared/chat_panel.py)
# ---------------------------------------------------------------------------
def check_and_increment_chat_rate_limit(
    user_id: str, max_requests: int, window_seconds: float
) -> tuple[bool, int]:
    """Fixed-window rate limit keyed by a durable user_id instead of the
    ephemeral st.session_state used elsewhere, so it survives a new browser
    tab/session. Returns (allowed, seconds_to_wait_if_not_allowed).

    Fixed window, not sliding: simpler, and a user could in theory send up to
    ~2x max_requests straddling a window boundary. Accepted tradeoff for an
    abuse-prevention cost control, not a strict SLA. Also not perfectly
    atomic (read-then-write, no DB-side transaction) — truly concurrent
    requests could slip a couple extra through — but this closes the "new tab
    resets my counter for free" gap the in-memory check can't.
    """
    client = get_client()
    if client is None:
        return True, 0  # local mode: no durable identity to key on

    now = datetime.datetime.now(datetime.timezone.utc)
    res = (
        client.table("chat_rate_limits")
        .select("window_start,request_count")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    row = res.data[0] if res.data else None

    if row is None:
        client.table("chat_rate_limits").insert(
            {"user_id": user_id, "window_start": now.isoformat(), "request_count": 1}
        ).execute()
        return True, 0

    window_start = datetime.datetime.fromisoformat(row["window_start"].replace("Z", "+00:00"))
    elapsed = (now - window_start).total_seconds()

    if elapsed >= window_seconds:
        client.table("chat_rate_limits").update(
            {"window_start": now.isoformat(), "request_count": 1}
        ).eq("user_id", user_id).execute()
        return True, 0

    if row["request_count"] >= max_requests:
        return False, int(window_seconds - elapsed)

    client.table("chat_rate_limits").update(
        {"request_count": row["request_count"] + 1}
    ).eq("user_id", user_id).execute()
    return True, 0
