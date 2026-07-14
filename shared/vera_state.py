"""
Vera session-state schema and helpers.

st.session_state.vera is the single in-memory source of truth for the
current run; shared/persistence.py mirrors it to disk so it survives a
page refresh.
"""

import streamlit as st

from shared.persistence import get_or_create_session_id, load_session, save_session

DEFAULT_VERA_STATE = {
    "trip_details": {
        "origin": "",
        "destination": "",
        "school": "",
    },
    "profile": {
        "name": "",
        "visa_type": "",    # "f-1" | "j-1" | "m-1" | "h-1b" | "other"
    },
    "extenuating_circumstances": {
        "categories": [],   # subset of shared.circumstances.CIRCUMSTANCE_CATEGORIES ids
        "notes": "",
    },
    "timeline": [],     # list of step dicts (see shared/timeline_data.py)
}


def init_vera_state():
    """Hydrate st.session_state.vera from disk (once per session) if not already loaded."""
    if "vera" in st.session_state:
        return
    vid = get_or_create_session_id()
    persisted = load_session(vid)
    state = dict(DEFAULT_VERA_STATE)
    state.update(persisted)
    # Backfill keys added after some sessions were already persisted to disk.
    state.setdefault("profile", dict(DEFAULT_VERA_STATE["profile"]))
    state.setdefault("extenuating_circumstances", dict(DEFAULT_VERA_STATE["extenuating_circumstances"]))
    st.session_state.vera = state


def get_vera_state() -> dict:
    """Return the current Vera state, initializing it if needed."""
    init_vera_state()
    return st.session_state.vera


def persist_vera_state():
    """Write the current Vera state to disk."""
    vid = get_or_create_session_id()
    save_session(vid, st.session_state.vera)


def set_trip_details(origin: str, destination: str, school: str):
    state = get_vera_state()
    state["trip_details"] = {"origin": origin, "destination": destination, "school": school}
    persist_vera_state()


def set_profile(name: str, visa_type: str):
    state = get_vera_state()
    state["profile"] = {"name": name, "visa_type": visa_type}
    persist_vera_state()


def set_extenuating_circumstances(categories: list, notes: str):
    state = get_vera_state()
    state["extenuating_circumstances"] = {"categories": categories, "notes": notes}
    persist_vera_state()


def set_timeline(steps: list):
    state = get_vera_state()
    state["timeline"] = steps
    persist_vera_state()


def add_timeline_steps(steps: list):
    """Append extra steps (e.g. from a school guide PDF) without duplicating by id."""
    state = get_vera_state()
    existing_ids = {s["id"] for s in state["timeline"]}
    for step in steps:
        if step["id"] not in existing_ids:
            state["timeline"].append(step)
    persist_vera_state()


def mark_step_status(step_id: str, status: str):
    state = get_vera_state()
    for step in state["timeline"]:
        if step["id"] == step_id:
            step["status"] = status
            break
    persist_vera_state()


def build_user_context_block(state: dict = None) -> str:
    """A short, factual line about who's asking, prepended to the system prompt
    so chat/enrichment responses are personalized without changing the rules
    they must follow. Never includes anything that isn't already in state —
    this describes the user, it doesn't instruct the model to do anything new.
    """
    state = state or get_vera_state()
    profile = state.get("profile", {})
    trip = state.get("trip_details", {})
    circumstances = state.get("extenuating_circumstances", {})

    parts = []
    if profile.get("name"):
        parts.append(f"The user's name is {profile['name']}.")
    if profile.get("visa_type"):
        parts.append(f"They are pursuing a {profile['visa_type'].upper()} visa.")
    if trip.get("origin"):
        parts.append(f"They are traveling from {trip['origin']}.")
    if trip.get("destination"):
        parts.append(f"They are traveling to {trip['destination']}.")
    if circumstances.get("categories"):
        from shared.circumstances import CIRCUMSTANCE_LABELS
        labels = [CIRCUMSTANCE_LABELS.get(c, c) for c in circumstances["categories"]]
        parts.append(
            "They have flagged the following extenuating circumstances: "
            + "; ".join(labels)
            + ". Do not speculate about how these affect their case — only share"
            " factual information from the provided context, same as any other question."
        )
    if circumstances.get("notes"):
        parts.append(f"Additional notes from the user: {circumstances['notes']}")

    if not parts:
        return ""
    return "USER CONTEXT (for personalization only, does not change the rules above): " + " ".join(parts)
