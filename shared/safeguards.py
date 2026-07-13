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

# Patterns in LLM output that suggest legal advice is being given
ADVICE_OUTPUT_PATTERNS = [
    ("you should", "Note: The above suggestion should be verified with an immigration attorney."),
    ("you are eligible", "Note: Eligibility determinations require a licensed immigration attorney."),
    ("you qualify for", "Note: Qualification determinations require a licensed immigration attorney."),
    ("i recommend", "Note: This tool does not provide recommendations. Consult an immigration attorney."),
    ("your case", "Note: This tool cannot evaluate individual cases. Consult an immigration attorney."),
    ("you would need to", "Note: Individual requirements should be verified with an immigration attorney."),
    ("you can file", "Note: Filing decisions should be made with guidance from an immigration attorney."),
    ("i suggest", "Note: This tool does not provide suggestions. Consult an immigration attorney."),
    ("you must file", "Note: Legal obligations should be verified with an immigration attorney."),
]


def filter_output(response_text):
    """
    Scan LLM response for patterns suggesting legal advice.
    Append warnings where found.

    Returns:
        tuple: (filtered_text: str, warnings: list[str])
    """
    warnings = []
    filtered = response_text

    for pattern, warning in ADVICE_OUTPUT_PATTERNS:
        if pattern.lower() in response_text.lower():
            warnings.append(warning)
            # Append the warning to the response
            if warning not in filtered:
                filtered = filtered + "\n\n" + warning

    return filtered, list(set(warnings))


# -------------------------------------------------------
# Layer 4: Confidence gating
# -------------------------------------------------------

# Cosine distance threshold - above this, retrieval is considered insufficient
CONFIDENCE_THRESHOLD = 1.0


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

def strip_thinking(response_text):
    """
    Strip obvious chain-of-thought containers from LLM responses.
    Conservative approach — only removes clearly-marked thinking blocks
    to avoid stripping legitimate response content.

    Args:
        response_text: raw LLM response

    Returns:
        str: cleaned response with thinking containers removed
    """
    cleaned = response_text

    # 0. Primary mechanism: the system prompt requires a literal "FINAL ANSWER:"
    #    marker line separating private reasoning from the visible response.
    #    This doesn't depend on the model remembering to open/close a tag —
    #    if the marker is present, everything before it (however it's shaped)
    #    is discarded. Split on the LAST occurrence in case the reasoning
    #    itself mentions the marker name while planning to use it.
    marker_matches = list(re.finditer(r'FINAL ANSWER:\s*\n?', cleaned, flags=re.IGNORECASE))
    if marker_matches:
        cleaned = cleaned[marker_matches[-1].end():]

    # 1. Strip <think>...</think> tags (some models use XML-style thinking tags)
    cleaned = re.sub(r'<think>.*?</think>', '', cleaned, flags=re.DOTALL)

    # 2. Strip labeled thinking blocks that are clearly meta-reasoning.
    #    Only matches sections explicitly labeled as thinking/analysis.
    #    Uses conservative pattern: label + colon, then content until next
    #    double-newline section. Does NOT match normal conversational language.
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
