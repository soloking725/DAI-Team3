"""
Extracts extra timeline steps from a school-provided visa guide PDF.

Real extraction only: pdfplumber pulls text, the LLM is given a strict
JSON-only prompt asking it to lift out items *explicitly* stated as
required actions/deadlines. Anything that fails to parse or validate is
reported as an error to the caller rather than silently replaced with
made-up steps.
"""

import json
import logging
import re
import uuid

import pdfplumber

from shared.chatbot import call_qwen_api
from shared.safeguards import strip_thinking

logger = logging.getLogger(__name__)

MAX_STEPS = 10
MAX_PDF_CHARS = 12000  # keep prompt size reasonable

EXTRACTION_PROMPT = """You will be given the text of a school's visa guide PDF.

Extract a JSON array of action items that are EXPLICITLY stated in the text as \
something the student must do, submit, or attend. Do not infer, summarize \
opinions, or invent anything not literally present in the text.

Each item must have exactly these fields:
- "title": short imperative phrase (max 12 words)
- "detail": one sentence quoting or closely paraphrasing the requirement, including any stated deadline
- "page_hint": the page number this was found on, if determinable from the text, else null

Respond with ONLY the JSON array, no other text. If there are no explicit \
action items in the text, respond with exactly: []

Guide text:
---
{text}
---"""


class PdfExtractionError(Exception):
    pass


def _extract_text(file) -> str:
    text_parts = []
    with pdfplumber.open(file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"[page {page_num}]\n{page_text}")
    return "\n\n".join(text_parts)


def _parse_json_array(raw: str):
    raw = strip_thinking(raw).strip()

    # Strip a ```json ... ``` fence if the model added one despite instructions.
    fence_match = re.search(r"```(?:json)?\s*(\[.*\])\s*```", raw, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # The model may prepend reasoning text (sometimes containing stray "["/"]"
        # of its own, e.g. "[Output Generation]"). The real array is the last
        # bracketed span since the prompt asks for JSON as the final output.
        start, end = raw.rfind("["), raw.rfind("]")
        if start == -1 or end == -1 or end < start:
            raise
        return json.loads(raw[start:end + 1])


def extract_steps_from_pdf(file) -> list:
    """
    Returns a list of validated step dicts: {id, title, detail, icon, category, status, source, page_hint}.
    Raises PdfExtractionError if the PDF has no usable text or the model
    output can't be parsed/validated — callers should surface this to the
    user and let them retry, not fall back to placeholder content.
    """
    text = _extract_text(file)
    if not text.strip():
        raise PdfExtractionError("Couldn't read any text from that PDF. Try a different file.")

    result = call_qwen_api(
        EXTRACTION_PROMPT.format(text=text[:MAX_PDF_CHARS]),
        context="",
    )
    if result.get("error"):
        raise PdfExtractionError(f"Extraction failed: {result['error']}")

    try:
        items = _parse_json_array(result.get("response", ""))
    except (json.JSONDecodeError, AttributeError) as e:
        raise PdfExtractionError(f"Couldn't understand the model's response: {e}")

    if not isinstance(items, list):
        raise PdfExtractionError("Unexpected response format from extraction.")

    steps = []
    for item in items[:MAX_STEPS]:
        if not isinstance(item, dict):
            continue
        title = (item.get("title") or "").strip()
        if not title:
            continue
        detail = (item.get("detail") or "").strip()
        page_hint = item.get("page_hint")
        steps.append({
            "id": f"guide_{uuid.uuid4().hex[:8]}",
            "title": title,
            "detail": detail or "See your school's guide for details.",
            "icon": "ti-file-text",
            "category": "school_guide",
            "status": "upcoming",
            "source": "school_guide",
            "page_hint": page_hint,
            "enriched": True,  # already has real, source-specific detail — skip generic enrichment
        })

    if not steps:
        raise PdfExtractionError("No explicit action items were found in that PDF.")

    return steps
