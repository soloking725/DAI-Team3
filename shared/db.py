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

import logging
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


# ---------------------------------------------------------------------------
# Users (identity + role), created/updated at login by shared/auth.py
# ---------------------------------------------------------------------------
def upsert_user(
    user_id: str, email: str, college_id: str, role: str, name: str = ""
) -> dict:
    """Insert or update the app-level user record for an authenticated identity."""
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
        .select("user_id,visa_type,origin_country,current_step_key,current_step_status,extenuating_flags,updated_at")
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
            }
        )
    return roster


def dso_override_step(actor_id: str, student_user_id: str, step_id: str, status: str) -> None:
    """DSO overrides one timeline step's status on a student's behalf.

    Edits the student's blob in place (timeline lives inside full_state), tags the
    step as DSO-updated, re-saves (which refreshes the denormalized columns), and
    writes an audit row.
    """
    client = get_client()
    if client is None:
        return
    blob = load_state(student_user_id)
    changed = False
    for step in blob.get("timeline", []):
        if step.get("id") == step_id:
            step["status"] = status
            step["updated_by"] = "dso"
            changed = True
            break
    if changed:
        save_state(student_user_id, blob)
        write_audit(actor_id, "edit_step", student_user_id, {"step": step_id, "status": status})


# ---------------------------------------------------------------------------
# Announcements (DSO -> students, pulled on page load)
# ---------------------------------------------------------------------------
def post_announcement(college_id: str, author_id: str, body: str) -> None:
    client = get_client()
    if client is None:
        return
    client.table("announcements").insert(
        {"college_id": college_id, "author_id": author_id, "body": body}
    ).execute()


def list_announcements(college_id: str, limit: int = 10) -> list[dict]:
    client = get_client()
    if client is None:
        return []
    res = (
        client.table("announcements")
        .select("body,created_at")
        .eq("college_id", college_id)
        .order("created_at", desc=True)
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
