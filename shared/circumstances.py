"""
Canonical extenuating-circumstances categories.

Single source of truth for the onboarding checklist (pages/11), the
timeline warning card (shared/timeline_ui.py), and retrieval queries
(shared/retrieval.py) — so the id used to tag static guidance content
in ingest_static.py always matches what the UI collects.
"""

CIRCUMSTANCE_CATEGORIES = [
    {
        "id": "prior_denial",
        "label": "Prior visa denial (Section 214(b) or other)",
        "query": "visa denied 214(b) refusal reapply",
    },
    {
        "id": "sevis_termination",
        "label": "SEVIS record terminated or at risk",
        "query": "SEVIS record terminated reinstatement",
    },
    {
        "id": "financial_hardship",
        "label": "Financial hardship affecting documents or fees",
        "query": "financial hardship proof of funds sponsor affidavit",
    },
    {
        "id": "medical_family_emergency",
        "label": "Medical or family emergency",
        "query": "medical emergency family emergency travel visa",
    },
    {
        "id": "delayed_documents",
        "label": "Delayed I-20/DS-2019 or other documents",
        "query": "delayed I-20 DS-2019 documents late",
    },
    {
        "id": "other",
        "label": "Something else",
        "query": "extenuating circumstances visa process",
    },
]

CIRCUMSTANCE_LABELS = {c["id"]: c["label"] for c in CIRCUMSTANCE_CATEGORIES}
CIRCUMSTANCE_QUERIES = {c["id"]: c["query"] for c in CIRCUMSTANCE_CATEGORIES}
