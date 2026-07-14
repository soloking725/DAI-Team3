"""
Chatbot module for RAG-powered visa question answering.

Uses the Qwen API via an OpenAI-compatible client.
Reads credentials from .env file (loaded via shared.config).
"""

import logging
from typing import Optional

from shared.config import (
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
    QWEN_MAX_TOKENS,
    QWEN_TEMPERATURE,
    SYSTEM_PROMPT,
    is_api_configured,
)

logger = logging.getLogger(__name__)


def call_qwen_api(user_message: str, context: str, history: Optional[list] = None) -> dict:
    """
    Call the Qwen API via OpenAI-compatible client to generate a response.

    Args:
        user_message: The user's question.
        context: Retrieved context from RAG (ChromaDB).
        history: Optional conversation history for context.

    Returns:
        dict with 'response', 'sources', 'error' keys.
    """
    if not is_api_configured():
        logger.warning("Qwen API not configured (missing QWEN_API_KEY)")
        return {
            "response": (
                "Chat is not yet configured. Add your Qwen API key to the .env file "
                "as QWEN_API_KEY and optionally set QWEN_BASE_URL (default: "
                "http://litellm.colby.edu:4000/v1) to enable chat."
            ),
            "sources": [],
            "error": "API not configured",
        }

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=QWEN_API_KEY,
            base_url=QWEN_BASE_URL,
        )

        # Build message history — personalize with a factual user-context line
        # when running inside a Streamlit session (falls back silently otherwise,
        # e.g. if called from a script with no st.session_state).
        system_content = SYSTEM_PROMPT
        try:
            from shared.vera_state import build_user_context_block
            user_context = build_user_context_block()
            if user_context:
                system_content = f"{SYSTEM_PROMPT}\n\n{user_context}"
        except Exception:
            logger.debug("No Vera session context available; using base system prompt.")

        messages = [{"role": "system", "content": system_content}]

        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add context to the user message
        if context:
            context_user_msg = (
                f"Here is the official government context for your question:\n\n"
                f"{context}\n\n---\n\nQuestion: {user_message}"
            )
        else:
            context_user_msg = user_message

        messages.append({"role": "user", "content": context_user_msg})

        logger.info(
            "Calling Qwen API (model=%s, tokens=%d) for query: %s",
            QWEN_MODEL,
            QWEN_MAX_TOKENS,
            user_message[:60],
        )

        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=messages,
            temperature=QWEN_TEMPERATURE,
            max_tokens=QWEN_MAX_TOKENS,
        )

        content = response.choices[0].message.content if response.choices else ""
        content = content or ""  # Guard against None

        logger.info("Qwen API responded successfully (%d chars)", len(content))

        return {
            "response": content,
            "sources": [],
            "error": None,
        }

    except ImportError:
        logger.error("openai package not installed")
        return {
            "response": "The OpenAI client library is not installed. Run: pip install openai",
            "sources": [],
            "error": "openai package not installed",
        }
    except Exception as e:
        logger.error("Qwen API call failed: %s", e, exc_info=True)
        return {
            "response": f"Error calling the API: {str(e)}. Please check your API key and connection.",
            "sources": [],
            "error": str(e),
        }
