"""
Safeguards module - prevents the tool from giving legal advice.

5-layer protection:
1. System prompt guardrails (passed to LLM)
2. Input classification (detects legal advice questions)
3. Output filtering (scans responses for advice patterns)
4. Confidence gating (refuses to answer without sufficient context)
5. Persistent disclaimers (always visible in UI)
"""

import logging
import re

from shared.config import (
    CONFIDENCE_THRESHOLD,
    LEGAL_ADVICE_REFUSAL,
    LEGAL_MATCH_THRESHOLD,
)

# Visa type keywords for fallback activation
VISA_KEYWORDS = ["f-1", "j-1", "m-1", "f1", "j1", "m1", "student visa", "exchange visa"]

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Layer 2: Input classification
# -------------------------------------------------------

# Patterns that indicate the user is asking for legal advice
LEGAL_ADVICE_PATTERNS = [
    "should i",
    "should i file",
    "what should i do",
    "what are my chances",
    "am i eligible",
    "am i qualified",
    "can i get away with",
    "will i be approved",
    "will my application be",
    "what are my options",
    "i need help with my case",
    "my lawyer",
    "help me with",
    "what do you think i should",
    "is it worth applying",
    "can i apply for",
    "will i get",
    "how can i increase my chances",
    "my situation is",
    "i was denied",
    "i got rejected",
    "i have been",
    "which visa should i",
    "can i switch from",
    "will i be deported",
    "can i stay in the us",
    "is my visa valid",
]


def classify_input(user_query):
    """
    Classify a user query to detect if it asks for legal advice.

    Returns:
        tuple: (is_legal_advice: bool, flagged_patterns: list[str])
    """
    query_lower = user_query.lower()
    flagged = []

    for pattern in LEGAL_ADVICE_PATTERNS:
        if pattern in query_lower:
            flagged.append(pattern)

    is_legal = len(flagged) >= 2  # Require 2+ matches to avoid false positives

    return is_legal, flagged


# -------------------------------------------------------
# Layer 3: Output filtering
# -------------------------------------------------------

# Patterns in LLM output that suggest legal advice is being given.
# Regexes with word boundaries so we don't match benign factual mentions
# like "you can file Form I-20 with your school" (a plain filing-instruction
# sentence, not advice) or "your case" inside phrasing like "your case is
# different from most people's" — these fired as false positives before.
ADVICE_OUTPUT_PATTERNS = [
    (r"\byou should\b", "Note: The above suggestion should be verified with an immigration attorney."),
    (r"\byou are eligible\b", "Note: Eligibility determinations require a licensed immigration attorney."),
    (r"\byou qualify for\b", "Note: Qualification determinations require a licensed immigration attorney."),
    (r"\bi recommend\b", "Note: This tool does not provide recommendations. Consult an immigration attorney."),
    (r"\byour case\b", "Note: This tool cannot evaluate individual cases. Consult an immigration attorney."),
    (r"\byou would need to\b", "Note: Individual requirements should be verified with an immigration attorney."),
    (r"\bi suggest\b", "Note: This tool does not provide suggestions. Consult an immigration attorney."),
    (r"\byou must file\b", "Note: Legal obligations should be verified with an immigration attorney."),
]


def filter_output(response_text, existing_warnings=None):
    """
    Scan LLM response for patterns suggesting legal advice.
    Append warnings where found.

    Args:
        response_text: the LLM response text to scan
        existing_warnings: warnings already shown elsewhere in the current
            response (e.g. from other steps rendered in the same view), so
            the same disclaimer note isn't appended repeatedly. Pass a
            shared list/set across calls within one render to dedupe.

    Returns:
        tuple: (filtered_text: str, warnings: list[str])
    """
    already_shown = set(existing_warnings or [])
    warnings = []
    filtered = response_text

    for pattern, warning in ADVICE_OUTPUT_PATTERNS:
        if re.search(pattern, response_text, flags=re.IGNORECASE):
            warnings.append(warning)
            if warning not in already_shown:
                filtered = filtered + "\n\n" + warning
                already_shown.add(warning)

    return filtered, list(dict.fromkeys(warnings))


# -------------------------------------------------------
# Layer 4: Confidence gating
# -------------------------------------------------------


def check_confidence(distances):
    """
    Check if retrieval results have sufficient confidence.

    Args:
        distances: list of cosine distances from ChromaDB query

    Returns:
        bool: True if confident enough to generate an answer
    """
    if not distances:
        return False

    best_distance = min(distances)
    return best_distance < CONFIDENCE_THRESHOLD


# -------------------------------------------------------
# Layer 5: Chain-of-thought stripping + Visa keyword detection
# -------------------------------------------------------

MISSING_MARKER_FALLBACK = (
    "I wasn't able to put together a clean answer to that. "
    "Please try rephrasing your question, or consult a licensed immigration attorney for your specific situation."
)


def strip_thinking(response_text):
    """
    Strip chain-of-thought reasoning from LLM responses.

    Fails closed: the system prompt requires a literal "FINAL ANSWER:"
    marker separating private reasoning from the visible response, and
    responses that omit it are supposed to be discarded. If that marker
    is missing, we do NOT fall back to returning the raw text (which
    would leak arbitrarily-shaped reasoning to the user) — we return a
    generic fallback message instead. The labeled-block regexes below are
    a secondary cleanup for reasoning that leaks *after* the marker, not
    the primary safety mechanism.

    Args:
        response_text: raw LLM response

    Returns:
        str: cleaned response, or a generic fallback if no FINAL ANSWER:
        marker was found (reasoning could not be safely separated out).
    """
    # Primary mechanism: split on the LAST occurrence of the marker in case
    # the reasoning itself mentions the marker name while planning to use it.
    marker_matches = list(re.finditer(r'FINAL ANSWER:\s*\n?', response_text, flags=re.IGNORECASE))
    if not marker_matches:
        logger.warning("No FINAL ANSWER: marker found in LLM response — discarding raw output")
        return MISSING_MARKER_FALLBACK

    cleaned = response_text[marker_matches[-1].end():]

    # Strip <think>...</think> tags (some models use XML-style thinking tags)
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)

    # Strip labeled thinking blocks that are clearly meta-reasoning.
    # Only matches sections explicitly labeled as thinking/analysis.
    # Uses conservative pattern: label + colon, then content until next
    # double-newline section. Does NOT match normal conversational language.
    labeled_thinking = [
        r'(?:^|\n\n)Thinking Process:\s*\n.*?(?=\n\n[A-Z]|\Z)',
        r'(?:^|\n\n)Chain of Thought:\s*\n.*?(?=\n\n[A-Z]|\Z)',
        r'(?:^|\n\n)Self-Correction:\s*\n.*?(?=\n\n[A-Z]|\Z)',
        r'(?:^|\n\n)Check Against Rules:\s*\n.*?(?=\n\n[A-Z]|\Z)',
        r'(?:^|\n\n)Internal Reasoning:\s*\n.*?(?=\n\n[A-Z]|\Z)',
    ]

    for pattern in labeled_thinking:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Clean up extra blank lines and leading/trailing whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()

    if not cleaned:
        logger.warning("Response was empty after stripping content following FINAL ANSWER: marker")
        return MISSING_MARKER_FALLBACK

    if cleaned != response_text:
        logger.info("Stripped chain-of-thought content from LLM response")

    return cleaned


def has_visa_keyword(text):
    """
    Detect if text contains visa type keywords.
    Enables fallback activation when semantic retrieval fails.

    Args:
        text: user query text

    Returns:
        bool: True if any visa keyword is found
    """
    if not text:
        return False
    text_lower = text.lower()
    for kw in VISA_KEYWORDS:
        if kw in text_lower:
            return True
    return False


def extract_visa_type(text):
    """
    Extract visa type from user query text.
    Returns canonical visa type for targeted retrieval.

    Args:
        text: user query text

    Returns:
        str: canonical visa type ('f-1', 'j-1', 'm-1') or None
    """
    if not text:
        return None
    text_lower = text.lower()
    # Check for explicit visa type mentions
    if 'f-1' in text_lower or 'f1' in text_lower:
        return 'f-1'
    if 'j-1' in text_lower or 'j1' in text_lower:
        return 'j-1'
    if 'm-1' in text_lower or 'm1' in text_lower:
        return 'm-1'
    return None
