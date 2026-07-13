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
