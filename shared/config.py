"""
Centralized configuration for the US Student Visa Information Resource.

All tunable constants live here. Environment variables override defaults
where applicable (loaded from .env via python-dotenv).

Security: Never commit .env files containing real credentials.
See .env.example for the required variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level above shared/)
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

# -------------------------------------------------------
# API Configuration
# -------------------------------------------------------
QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL: str = os.getenv("QWEN_BASE_URL", "http://litellm.colby.edu:4000/v1")
QWEN_MODEL: str = os.getenv("QWEN_MODEL", "qwen-3.6-27b")
QWEN_MAX_TOKENS: int = int(os.getenv("QWEN_MAX_TOKENS", "2048"))
QWEN_TEMPERATURE: float = float(os.getenv("QWEN_TEMPERATURE", "0.3"))


def is_api_configured() -> bool:
    """Return True if the Qwen API key is set to a real value."""
    return bool(QWEN_API_KEY and QWEN_API_KEY not in ("", "your_qwen_api_key_here"))


# -------------------------------------------------------
# Supabase / accounts (B2B MVP)
# -------------------------------------------------------
# When these are unset, the app runs in "local mode": no login, session state is
# keyed by the ?vid= URL param and persisted to local/vera_sessions/*.json (the
# original prototype behavior). When they're set, the app runs in "hosted mode":
# email-OTP login, a real Postgres backend, and a DSO dashboard. Nothing else in
# the app needs to know which mode it's in — shared/persistence.py and
# shared/auth.py switch on is_supabase_configured() behind stable signatures.
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
# Service key is used server-side only (Streamlit is trusted middleware that does
# its own role checks in shared/auth.py). Never expose it to the browser.
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

# Email domains allowed to request a login code, comma-separated. This is only a
# cheap pre-check so we don't email codes to arbitrary addresses — the
# authoritative check is the colleges.email_domain lookup at verification time,
# which also decides *which* college the user is enrolled in. Leave blank to skip
# the pre-check entirely and rely on that lookup alone.
ALLOWED_EMAIL_DOMAINS: list[str] = [
    d.strip().lower().lstrip("@")
    for d in os.getenv("ALLOWED_EMAIL_DOMAINS", "").split(",")
    if d.strip()
]

# Comma-separated allow-list of emails granted the 'dso' role on first login.
DSO_EMAILS: list[str] = [
    e.strip().lower() for e in os.getenv("DSO_EMAILS", "").split(",") if e.strip()
]


def is_supabase_configured() -> bool:
    """True when the hosted (accounts + Postgres) backend is fully wired up."""
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_SERVICE_KEY)


# -------------------------------------------------------
# Embedding & ChromaDB Configuration
# -------------------------------------------------------
EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
CHROMA_PATH: str = str(_project_root / "chroma_db")
COLLECTION_NAME: str = "student_visa_documents"

# Chunking parameters
CHUNK_SIZE: int = 800
CHUNK_OVERLAP: int = 150

# Retrieval parameters
DEFAULT_TOP_K: int = 5
DISTANCE_THRESHOLD: float = 1.2      # Max cosine distance to accept a chunk
CONFIDENCE_THRESHOLD: float = 1.0    # Below this distance to consider "confident"


# -------------------------------------------------------
# Safeguard Configuration
# -------------------------------------------------------
# Require at least this many keyword matches to classify as legal advice
LEGAL_MATCH_THRESHOLD: int = 2

# Standard refusal text for legal advice requests
LEGAL_ADVICE_REFUSAL: str = (
    "This tool provides factual information from official US government sources only. "
    "It cannot provide legal advice or evaluate individual cases. "
    "For legal advice about your specific situation, please consult a licensed immigration attorney. "
    "You can find attorneys through the American Immigration Lawyers Association at "
    "https://www.aila.org/find-an-attorney."
)

# URL to AILA attorney finder (referenced in UI)
AILA_ATTORNEY_FINDER: str = "https://www.aila.org/find-an-attorney"


# -------------------------------------------------------
# Input / Output Limits (Security)
# -------------------------------------------------------
MAX_INPUT_LENGTH: int = 1000        # Max characters for a single chat query
RATE_LIMIT_SECONDS: float = 60.0    # Window: seconds for rate limit counting
RATE_LIMIT_MAX_REQUESTS: int = 5    # Max queries per window
MIN_SECONDS_BETWEEN_QUERIES: float = 2.0   # Rate limit: seconds between sends


# -------------------------------------------------------
# Conversation Memory
# -------------------------------------------------------
CONVERSATION_HISTORY_LENGTH: int = 10  # Messages kept for LLM context


# -------------------------------------------------------
# System Prompt (RAG chatbot)
# -------------------------------------------------------
SYSTEM_PROMPT: str = """You are Vera, a warm and knowledgeable Visa Travel Agent who helps international
students navigate the US student visa process (F-1, J-1, M-1). You're friendly, encouraging, and speak
plainly like a helpful travel agent — but everything you say must stay strictly factual and sourced.

RULES - follow these strictly:
1. Provide factual information ONLY from the provided context documents.
2. Every factual claim must be attributed to a specific source. Cite the source URL.
3. NEVER interpret immigration law for the user.
4. NEVER recommend what action the user should take.
5. NEVER tell the user whether they are eligible for a visa or what their chances are.
6. NEVER use phrases like "you should file", "I recommend", "you are eligible", "your case qualifies".
7. If the provided context does not contain information to answer the question, say "I do not have information about this from official government sources."
8. Use neutral, factual language for the substance of the answer — a friendly tone is fine, but don't editorialize about the user's chances or situation.
9. If the user asks for legal advice, respond: "This tool provides factual information from official government sources only. For legal advice about your specific situation, please consult a licensed immigration attorney."
10. Format answers clearly with headings and bullet points where appropriate.
11. Focus on F-1, J-1, and M-1 student visa categories.

THINKING - how to reason without showing it:
Before answering, think step by step about the rules above, whether the context actually
supports an answer, and how to phrase it. Keep this reasoning brief — a few short lines.

Then output the exact literal line:
FINAL ANSWER:
on its own, with nothing else on that line. Everything after that line is what the user
sees: no preamble, no "here's my thinking", no restating the rules, no meta-commentary
about the process — just the answer itself, formatted for the user.

This FINAL ANSWER: marker is REQUIRED in every single response, with no exceptions, even
for very short answers where thinking feels unnecessary. Responses that omit it are
discarded and never shown to the user, so always include it.

The following context from official US government sources is available to answer the user's question."""
