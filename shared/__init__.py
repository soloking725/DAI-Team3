"""
Shared module for US Student Visa Information Resource.
"""
from shared.styles import get_global_css
from shared.safeguards import classify_input, filter_output, check_confidence, LEGAL_ADVICE_REFUSAL
from shared.retrieval import retrieve_context
from shared.chatbot import call_qwen_api, check_api_configured

__all__ = [
    "get_global_css",
    "classify_input",
    "filter_output",
    "check_confidence",
    "LEGAL_ADVICE_REFUSAL",
    "retrieve_context",
    "call_qwen_api",
    "check_api_configured",
]
