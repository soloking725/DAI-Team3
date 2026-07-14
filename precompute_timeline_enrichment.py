"""
Precompute grounded detail text for every canonical timeline step.

shared/timeline.py's enrich_step_detail() only ever depends on a step's
title and visa type — never on anything user-specific — so its output is
identical for every user on the same visa type. Rather than calling the LLM
live per user (which used to block the whole page when marking a step
complete), this script runs it once for every (visa_type, step) combination
in shared/timeline_data.TIMELINE_TEMPLATES and caches the results in
shared/timeline_enrichment_cache.json, which shared/timeline.build_timeline()
reads at runtime.

Re-run this after changing TIMELINE_TEMPLATES or re-running ingest_static.py/
ingest.py with content that could affect these steps.

Usage:
    python precompute_timeline_enrichment.py
"""

import json
import os

from shared.timeline_data import TIMELINE_TEMPLATES
from shared.timeline import enrich_step_detail

CACHE_PATH = os.path.join(os.path.dirname(__file__), "shared", "timeline_enrichment_cache.json")


def main():
    cache = {}
    for visa_type, steps in TIMELINE_TEMPLATES.items():
        print(f"Visa type: {visa_type}")
        cache[visa_type] = {}
        for step in steps:
            print(f"  {step['id']}: {step['title']}")
            # enrich_step_detail expects a dict with "title" and "detail" (its fallback)
            detail = enrich_step_detail({"title": step["title"], "detail": step["default_detail"]}, visa_type)
            cache[visa_type][step["id"]] = detail
            changed = "enriched" if detail != step["default_detail"] else "default (not enriched)"
            print(f"    -> {changed}: {detail}")

    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"\nWrote {CACHE_PATH}")


if __name__ == "__main__":
    main()
