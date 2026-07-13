"""
Builds a user's visa timeline from the canonical step templates, with
optional constrained LLM enrichment of each step's detail text.

The LLM is never allowed to add, remove, or reorder steps — only to
rewrite a step's descriptive detail, and only when retrieval is
confident. See shared/timeline_data.py for the source of truth.
"""

import logging
import re

from shared.timeline_data import TIMELINE_TEMPLATES, DEFAULT_VISA_TYPE
from shared.retrieval import retrieve_context
from shared.safeguards import check_confidence, filter_output, strip_thinking
from shared.chatbot import call_qwen_api

logger = logging.getLogger(__name__)

_US_DESTINATION_ALIASES = {"united states", "usa", "us", "u.s.", "u.s.a."}

ENRICHMENT_INSTRUCTION = (
    "Using ONLY the context provided below, write one short factual sentence "
    "(max 25 words) describing this specific visa timeline step: \"{title}\". "
    "Do not suggest what the user should do, do not invent dates or deadlines, "
    "and do not mention eligibility or chances of approval. "
    "If the context does not clearly describe this step, respond with exactly: NOT_ENOUGH_CONTEXT"
)


def infer_visa_type(trip_details: dict) -> str:
    """Pick a visa type template. Only US destinations are supported; default to F-1 otherwise."""
    destination = (trip_details.get("destination") or "").strip().lower()
    if destination and destination not in _US_DESTINATION_ALIASES:
        logger.info("Destination '%s' not recognized as the US; defaulting to F-1 template.", destination)
    return DEFAULT_VISA_TYPE


def build_timeline(trip_details: dict) -> list:
    """Return a fresh list of step dicts (status='upcoming') for the trip's visa type. No LLM calls — instant."""
    visa_type = infer_visa_type(trip_details)
    template = TIMELINE_TEMPLATES[visa_type]
    return [
        {
            "id": step["id"],
            "title": step["title"],
            "icon": step["icon"],
            "detail": step["default_detail"],
            "category": step["category"],
            "status": "upcoming",
            "enriched": False,
        }
        for step in template
    ]


def _first_incomplete(steps):
    for step in steps:
        if step["status"] != "complete":
            return step
    return None


def enrich_current_step(steps: list, visa_type: str = DEFAULT_VISA_TYPE) -> bool:
    """
    Enrich only the current (first incomplete) step, and only once — subsequent
    calls are a no-op until that step is marked complete and a new one becomes
    current. Keeps LLM usage to at most one call per page load instead of one
    per step. Returns True if a step was (re)written, so the caller knows to persist.
    """
    step = _first_incomplete(steps)
    if step is None or step.get("enriched"):
        return False
    step["detail"] = enrich_step_detail(step, visa_type)
    step["enriched"] = True
    return True


def enrich_step_detail(step: dict, visa_type: str = DEFAULT_VISA_TYPE) -> str:
    """
    Attempt a constrained, retrieval-grounded rewrite of a step's detail text.

    Falls back to the step's existing (template default) detail whenever
    retrieval confidence is low, the API isn't configured, or the model
    signals it doesn't have enough grounding — never fabricates.
    """
    fallback = step["detail"]

    retrieval = retrieve_context(step["title"], visa_type=visa_type)
    if not retrieval.get("found") or not check_confidence(retrieval.get("distances", [])):
        return fallback

    instruction = ENRICHMENT_INSTRUCTION.format(title=step["title"])
    result = call_qwen_api(instruction, retrieval["context"])
    if result.get("error"):
        return fallback

    response = strip_thinking(result.get("response", "")).strip()
    if not response or "NOT_ENOUGH_CONTEXT" in response.upper():
        return fallback

    filtered, warnings = filter_output(response)
    if warnings:
        # Output tripped an advice-pattern safeguard; stay with the safe default.
        return fallback

    return _strip_inline_citation(filtered)


def _strip_inline_citation(text: str) -> str:
    """Drop a trailing "[Source: ...]" bracket the model sometimes adds despite
    only being asked for a plain sentence — the timeline card isn't a citation UI."""
    return re.sub(r"\s*\[Source:.*?\]\s*$", "", text, flags=re.IGNORECASE).strip()
