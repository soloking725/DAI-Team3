"""
Builds a user's visa timeline from the canonical step templates, with
optional constrained LLM enrichment of each step's detail text.

The LLM is never allowed to add, remove, or reorder steps — only to
rewrite a step's descriptive detail, and only when retrieval is
confident. See shared/timeline_data.py for the source of truth.
"""

import json
import logging
import os
import re

from shared.timeline_data import TIMELINE_TEMPLATES, DEFAULT_VISA_TYPE
from shared.retrieval import retrieve_context
from shared.safeguards import check_confidence, filter_output, strip_thinking
from shared.chatbot import call_qwen_api

logger = logging.getLogger(__name__)

_US_DESTINATION_ALIASES = {"united states", "usa", "us", "u.s.", "u.s.a."}

_ENRICHMENT_CACHE_PATH = os.path.join(os.path.dirname(__file__), "timeline_enrichment_cache.json")
_enrichment_cache = None


def _load_enrichment_cache() -> dict:
    """Load the precomputed step-detail cache (see precompute_timeline_enrichment.py),
    once per process. Every entry in TIMELINE_TEMPLATES is the same for every user on
    a given visa type, so this is generated offline instead of via a live LLM call per
    user — that live call used to block the whole page on "Mark complete"."""
    global _enrichment_cache
    if _enrichment_cache is None:
        try:
            with open(_ENRICHMENT_CACHE_PATH) as f:
                _enrichment_cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning("No precomputed timeline enrichment cache found (%s); using template defaults.", e)
            _enrichment_cache = {}
    return _enrichment_cache

ENRICHMENT_INSTRUCTION = (
    "Using ONLY the context provided below, write one short factual sentence "
    "(max 25 words) describing this specific visa timeline step: \"{title}\". "
    "Do not suggest what the user should do, do not invent dates or deadlines, "
    "and do not mention eligibility or chances of approval. "
    "If the context does not clearly describe this step, respond with exactly: NOT_ENOUGH_CONTEXT"
)


def infer_visa_type(trip_details: dict, selected_visa_type: str = "") -> str:
    """Pick a visa type template.

    The visa type the user explicitly chose (Trip Details' profile.visa_type)
    is authoritative when it matches a known template; destination is only
    used as a fallback for sessions that predate that field. Only US
    destinations are supported; default to F-1 otherwise.
    """
    selected = (selected_visa_type or "").strip().lower()
    if selected in TIMELINE_TEMPLATES:
        return selected
    destination = (trip_details.get("destination") or "").strip().lower()
    if destination and destination not in _US_DESTINATION_ALIASES:
        logger.info("Destination '%s' not recognized as the US; defaulting to F-1 template.", destination)
    return DEFAULT_VISA_TYPE


def build_timeline(trip_details: dict, selected_visa_type: str = "") -> list:
    """Return a fresh list of step dicts (status='upcoming') for the trip's visa type.

    Detail text comes from the precomputed enrichment cache when available (see
    precompute_timeline_enrichment.py) — no LLM calls here, instant either way.
    """
    visa_type = infer_visa_type(trip_details, selected_visa_type)
    template = TIMELINE_TEMPLATES[visa_type]
    cached = _load_enrichment_cache().get(visa_type, {})
    return [
        {
            "id": step["id"],
            "title": step["title"],
            "icon": step["icon"],
            "detail": cached.get(step["id"], step["default_detail"]),
            "category": step["category"],
            "form_url": step.get("form_url"),
            "form_name": step.get("form_name"),
            "status": "upcoming",
            "enriched": True,
        }
        for step in template
    ]


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


def enrich_step_with_origin(step: dict, visa_type: str, origin_country: str) -> str:
    """Rewrite an interview-stage step's detail using the student's own origin
    country's embassy/consulate content (see ingest.py's
    ORIGIN_COUNTRY_SOURCE_URLS), instead of the generic per-visa-type default
    every student otherwise gets from the precomputed cache.

    Same constrained/confidence-gated/never-fabricate contract as
    enrich_step_detail() — this is the one live, per-student call the timeline
    makes (at most once, for the current step only), mirroring the existing
    single-call-per-page-load design used for the general enrichment pass.
    """
    fallback = step["detail"]
    if not origin_country:
        return fallback

    retrieval = retrieve_context(step["title"], visa_type=visa_type, origin_country=origin_country)
    if not retrieval.get("found") or not check_confidence(retrieval.get("distances", [])):
        return fallback

    instruction = ENRICHMENT_INSTRUCTION.format(title=step["title"]) + (
        f" Focus specifically on {origin_country}-specific details (embassy/consulate "
        f"location, appointment process) if the context provides them."
    )
    result = call_qwen_api(instruction, retrieval["context"])
    if result.get("error"):
        return fallback

    response = strip_thinking(result.get("response", "")).strip()
    if not response or "NOT_ENOUGH_CONTEXT" in response.upper():
        return fallback

    filtered, warnings = filter_output(response)
    if warnings:
        return fallback

    return _strip_inline_citation(filtered)


def _strip_inline_citation(text: str) -> str:
    """Drop a trailing "[Source: ...]" bracket the model sometimes adds despite
    only being asked for a plain sentence — the timeline card isn't a citation UI."""
    return re.sub(r"\s*\[Source:.*?\]\s*$", "", text, flags=re.IGNORECASE).strip()
