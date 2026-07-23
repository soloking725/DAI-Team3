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
import uuid
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


def _validate_uuid(value: str, field: str) -> str:
    """Return `value` unchanged if it's a well-formed UUID, else raise ValueError.

    These IDs are always server-side Supabase auth UUIDs, never user input — but
    a few call sites below interpolate them into PostgREST `.or_()` filter
    *strings* (which .eq()/.in_() parameterization doesn't cover). Validating the
    shape here means a future caller that ever passes something attacker-derived
    can't break out of the filter grammar (commas, parentheses, operators). Cheap
    insurance on a latent injection pattern, not a response to a live bug.
    """
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f"{field} is not a valid UUID: {value!r}")


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


def update_user_name(user_id: str, name: str) -> None:
    """Sync a student's display name into the users table.

    The real signup flow is email-OTP only (no name field), so users.name
    starts out blank for every student and is only ever filled in here, once
    they type their name on the trip-details onboarding step (see
    pages/10_Trip_Details.py) — that's what the DSO roster's Name column
    (list_students) reads from.
    """
    client = get_client()
    if client is None:
        return
    client.table("users").update({"name": name}).eq("id", user_id).execute()


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
    post_visa = blob.get("post_visa", {}) or {}
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
        "visa_expiration": post_visa.get("visa_expiration") or None,
        "passport_expiration": post_visa.get("passport_expiration") or None,
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
    user_id = _validate_uuid(user_id, "user_id")  # interpolated into .or_() below
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
    # visa_expiration/passport_expiration (migrations/010) may not be applied
    # yet on a given deployment — fall back to the columns that have always
    # existed rather than hard-erroring the whole roster (and everything
    # after it on the page) until the migration is run.
    _base_select = (
        "user_id,visa_type,origin_country,current_step_key,current_step_status,"
        "extenuating_flags,updated_at,entering_year,graduation_year"
    )
    try:
        students = (
            client.table("students")
            .select(_base_select + ",visa_expiration,passport_expiration")
            .eq("college_id", college_id)
            .execute()
        ).data or []
    except Exception as e:
        if "visa_expiration" not in str(e) and "passport_expiration" not in str(e):
            raise
        logger.warning(
            "students.visa_expiration/passport_expiration not found — "
            "run migrations/010_visa_passport_expiration.sql. Falling back "
            "without those columns for now."
        )
        students = (
            client.table("students")
            .select(_base_select)
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
                "visa_expiration": s.get("visa_expiration") or "",
                "passport_expiration": s.get("passport_expiration") or "",
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
    if len(body) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"post_announcement: body exceeds {MAX_MESSAGE_LENGTH} characters")
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
def create_custom_reminder(
    college_id: str, author_id: str, title: str, detail: str, due_date: str,
    target_visa_type: Optional[str] = None, target_step_key: Optional[str] = None,
) -> None:
    """due_date is an ISO date string ("YYYY-MM-DD").

    target_visa_type/target_step_key are None for "everyone at the college"
    (the original, only behavior) — set either to narrow who sees it, e.g. a
    reminder that only makes sense for students still on a specific step.
    """
    client = get_client()
    if client is None:
        return
    row = {
        "college_id": college_id, "author_id": author_id,
        "title": title, "detail": detail, "due_date": due_date,
        "target_visa_type": target_visa_type, "target_step_key": target_step_key,
    }
    try:
        client.table("custom_reminders").insert(row).execute()
    except Exception as e:
        # target_visa_type/target_step_key (migrations/011) may not be applied
        # yet — post the reminder untargeted (visible to everyone, the
        # pre-migration behavior) rather than losing it outright.
        if "target_visa_type" not in str(e) and "target_step_key" not in str(e):
            raise
        logger.warning(
            "custom_reminders.target_visa_type/target_step_key not found — "
            "run migrations/011_reminder_targeting.sql. Posting untargeted for now."
        )
        row.pop("target_visa_type", None)
        row.pop("target_step_key", None)
        client.table("custom_reminders").insert(row).execute()


def list_custom_reminders(
    college_id: str, limit: int = 50,
    visa_type: Optional[str] = None, step_key: Optional[str] = None,
) -> list[dict]:
    """All reminders for a college when visa_type/step_key are omitted (the DSO
    authoring/management view). Pass a student's own visa_type/step_key to get
    only the reminders that apply to them (a reminder with a null target column
    applies to everyone; a non-null target must match)."""
    client = get_client()
    if client is None:
        return []
    try:
        res = (
            client.table("custom_reminders")
            .select("id,title,detail,due_date,created_at,target_visa_type,target_step_key")
            .eq("college_id", college_id)
            .order("due_date", desc=False)
            .limit(limit)
            .execute()
        )
        rows = res.data or []
    except Exception as e:
        if "target_visa_type" not in str(e) and "target_step_key" not in str(e):
            raise
        logger.warning(
            "custom_reminders.target_visa_type/target_step_key not found — "
            "run migrations/011_reminder_targeting.sql. Treating all reminders as untargeted."
        )
        res = (
            client.table("custom_reminders")
            .select("id,title,detail,due_date,created_at")
            .eq("college_id", college_id)
            .order("due_date", desc=False)
            .limit(limit)
            .execute()
        )
        rows = res.data or []
    if visa_type is None and step_key is None:
        return rows
    return [
        r for r in rows
        if (not r.get("target_visa_type") or r["target_visa_type"] == visa_type)
        and (not r.get("target_step_key") or r["target_step_key"] == step_key)
    ]


def delete_custom_reminder(reminder_id: str, college_id: str) -> None:
    client = get_client()
    if client is None:
        return
    client.table("custom_reminders").delete().eq("id", reminder_id).eq("college_id", college_id).execute()


# ---------------------------------------------------------------------------
# Direct messages (DSO <-> student, one thread per pair)
# ---------------------------------------------------------------------------
# Both messages.body and announcements.body carry the matching check
# constraint added in migrations/013_messaging_inbox.sql — this mirrors it
# client-side so a caller gets a friendly ValueError instead of a raw
# Postgres constraint-violation error.
MAX_MESSAGE_LENGTH = 4000


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
    if len(body) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"send_message: body exceeds {MAX_MESSAGE_LENGTH} characters")
    client.table("messages").insert(
        {
            "college_id": college_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "body": body,
        }
    ).execute()


def list_thread(college_id: str, user_a: str, user_b: str, limit: int = 50) -> list[dict]:
    """The most recent `limit` messages between two specific users, oldest first.

    Fetched newest-first (so LIMIT keeps the *latest* messages, not the
    earliest ones a plain oldest-first-with-limit query would return) and
    reversed back to oldest-first for display.
    """
    client = get_client()
    if client is None:
        return []
    user_a = _validate_uuid(user_a, "user_a")  # interpolated into .or_() below
    user_b = _validate_uuid(user_b, "user_b")
    res = (
        client.table("messages")
        .select("sender_id,recipient_id,body,created_at")
        .eq("college_id", college_id)
        .or_(
            f"and(sender_id.eq.{user_a},recipient_id.eq.{user_b}),"
            f"and(sender_id.eq.{user_b},recipient_id.eq.{user_a})"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return list(reversed(res.data or []))


def mark_thread_read(user_id: str, other_user_id: str, college_id: str) -> None:
    """Record that user_id has seen everything in this thread as of now —
    called when a thread is opened. Upserted rather than inserted since
    there's exactly one row per (user_id, other_user_id) pair."""
    client = get_client()
    if client is None:
        return
    client.table("thread_reads").upsert(
        {
            "user_id": user_id,
            "other_user_id": other_user_id,
            "college_id": college_id,
            "last_read_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        on_conflict="user_id,other_user_id",
    ).execute()


def _last_read_at(client, user_id: str, other_user_id: str) -> Optional[str]:
    res = (
        client.table("thread_reads")
        .select("last_read_at")
        .eq("user_id", user_id)
        .eq("other_user_id", other_user_id)
        .limit(1)
        .execute()
    )
    return res.data[0]["last_read_at"] if res.data else None


def get_unread_count(user_id: str, other_user_id: str) -> int:
    """How many messages other_user_id has sent user_id since user_id last
    opened this thread (or the whole thread, if it's never been opened)."""
    client = get_client()
    if client is None:
        return 0
    last_read = _last_read_at(client, user_id, other_user_id)
    query = (
        client.table("messages")
        .select("id", count="exact")
        .eq("sender_id", other_user_id)
        .eq("recipient_id", user_id)
    )
    if last_read:
        query = query.gt("created_at", last_read)
    return query.execute().count or 0


def list_conversations(college_id: str, user_id: str, counterparts: list[dict]) -> list[dict]:
    """One row per possible counterpart (the DSOs at a student's college, or
    the students on a DSO's roster), each with its last message + unread
    count, sorted most-recent-activity first — the inbox list. Counterparts
    with no messages yet sort last, alphabetically.

    `counterparts` is the caller's already-fetched roster/DSO list (each a
    dict with at least "id" and "name") — this never queries for the set of
    possible counterparts itself, since callers already have it (db.list_students
    / db.get_dso_users) and a college's DSO/student count is small enough that
    one list_thread-shaped query per counterpart is cheap.
    """
    client = get_client()
    if client is None:
        return []
    conversations = []
    for person in counterparts:
        other_id = person["id"]
        thread = list_thread(college_id, user_id, other_id, limit=1)
        last = thread[-1] if thread else None
        conversations.append(
            {
                "id": other_id,
                "name": person.get("name") or person.get("email") or "Unknown",
                "last_message": last["body"] if last else "",
                "last_message_at": last["created_at"] if last else None,
                "unread_count": get_unread_count(user_id, other_id),
            }
        )
    conversations.sort(
        key=lambda c: (c["last_message_at"] is None, c["last_message_at"] and -_to_epoch(c["last_message_at"]), c["name"])
    )
    return conversations


def _to_epoch(iso_ts: str) -> float:
    return datetime.datetime.fromisoformat(iso_ts.replace("Z", "+00:00")).timestamp()


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


def check_and_increment_otp_domain_rate_limit(
    domain: str, max_requests: int, window_seconds: float
) -> tuple[bool, int]:
    """Fixed-window rate limit on OTP sends, keyed by the requested email's
    domain rather than the individual address — see
    migrations/014_otp_rate_limits.sql for why a per-address limit doesn't
    help against someone iterating through many different fake usernames at
    one allowed domain. Same fixed-window shape as
    check_and_increment_chat_rate_limit above; returns (allowed, wait_seconds).
    """
    client = get_client()
    if client is None:
        return True, 0  # local mode: no OTP flow exists at all

    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        res = (
            client.table("otp_send_log")
            .select("window_start,request_count")
            .eq("domain", domain)
            .limit(1)
            .execute()
        )
    except Exception as e:
        # otp_send_log (migrations/014) may not be applied yet on a given
        # deployment. This is the *domain-wide* abuse backstop, not the only
        # OTP defense — shared/auth.py still enforces its own per-session send
        # cooldown and per-code verify-attempt cap. Failing open here (allow
        # the send) means a missing migration degrades this one layer instead
        # of taking down login entirely for every user, which is strictly
        # worse than the abuse case this table guards against.
        if "otp_send_log" not in str(e):
            raise
        logger.warning(
            "otp_send_log table not found — run migrations/014_otp_rate_limits.sql. "
            "Allowing this OTP send without the domain-wide rate limit for now."
        )
        return True, 0
    row = res.data[0] if res.data else None

    if row is None:
        client.table("otp_send_log").insert(
            {"domain": domain, "window_start": now.isoformat(), "request_count": 1}
        ).execute()
        return True, 0

    window_start = datetime.datetime.fromisoformat(row["window_start"].replace("Z", "+00:00"))
    elapsed = (now - window_start).total_seconds()

    if elapsed >= window_seconds:
        client.table("otp_send_log").update(
            {"window_start": now.isoformat(), "request_count": 1}
        ).eq("domain", domain).execute()
        return True, 0

    if row["request_count"] >= max_requests:
        return False, int(window_seconds - elapsed)

    client.table("otp_send_log").update(
        {"request_count": row["request_count"] + 1}
    ).eq("domain", domain).execute()
    return True, 0
