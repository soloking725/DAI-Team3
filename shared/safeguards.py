"""
Safeguards module - prevents the tool from giving legal advice.

5-layer protection:
1. System prompt guardrails (passed to LLM)
2. Input classification (detects legal advice questions)
3. Output filtering (scans responses for advice patterns)
4. Confidence gating (refuses to answer without sufficient context)
5. Persistent disclaimers (always visible in UI)
"""

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

# Standard refusal message for legal advice requests
LEGAL_ADVICE_REFUSAL = (
    "This tool provides factual information from official US government sources only. "
    "It cannot provide legal advice or evaluate individual cases. "
    "For legal advice about your specific situation, please consult a licensed immigration attorney. "
    "You can find attorneys through the American Immigration Lawyers Association at "
    "https://www.aila.org/find-an-attorney."
)


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
