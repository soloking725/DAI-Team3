"""
Chatbot module for RAG-powered visa question answering.

Uses the same Qwen API (via OpenAI-compatible client) as Hermes Agent.
Reads QWEN_API_KEY and QWEN_BASE_URL from .env file.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# -------------------------------------------------------
# API configuration (same as Hermes)
# -------------------------------------------------------
# Hermes Agent uses LiteLLM proxy at http://litellm.colby.edu:4000/v1
# This app reads the same key and base URL from .env
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "http://litellm.colby.edu:4000/v1")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-3.6-27b")

# -------------------------------------------------------
# System prompt (student visa focused)
# -------------------------------------------------------
SYSTEM_PROMPT = """You are a factual information assistant about US student visa categories (F-1, J-1, M-1)
and the application process.

RULES - follow these strictly:
1. Provide factual information ONLY from the provided context documents.
2. Every factual claim must be attributed to a specific source. Cite the source URL.
3. NEVER interpret immigration law for the user.
4. NEVER recommend what action the user should take.
5. NEVER tell the user whether they are eligible for a visa or what their chances are.
6. NEVER use phrases like "you should file", "I recommend", "you are eligible", "your case qualifies".
7. If the provided context does not contain information to answer the question, say "I do not have information about this from official government sources."
8. Use neutral, factual language. Write in third person.
9. If the user asks for legal advice, respond: "This tool provides factual information from official government sources only. For legal advice about your specific situation, please consult a licensed immigration attorney."
10. Format answers clearly with headings and bullet points where appropriate.
11. Focus on F-1, J-1, and M-1 student visa categories.
12. Do not show your reasoning, thinking process, or chain of thought. Provide only the final answer to the user's question.

The following context from official US government sources is available to answer the user's question."""


def check_api_configured() -> bool:
    """Check if the Qwen API key and base URL are configured."""
    return bool(QWEN_API_KEY and QWEN_API_KEY != "your_qwen_api_key_here")


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
    if not check_api_configured():
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

        # Build the full prompt with context
        full_prompt = f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context}\n" if context else SYSTEM_PROMPT

        # Build message history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if history:
            for msg in history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add context to the user message
        if context:
            context_user_msg = f"Here is the official government context for your question:\n\n{context}\n\n---\n\nQuestion: {user_message}"
        else:
            context_user_msg = user_message

        messages.append({"role": "user", "content": context_user_msg})

        response = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )

        content = response.choices[0].message.content if response.choices else ""

        return {
            "response": content,
            "sources": [],
            "error": None,
        }

    except ImportError:
        return {
            "response": "The OpenAI client library is not installed. Run: pip install openai",
            "sources": [],
            "error": "openai package not installed",
        }
    except Exception as e:
        return {
            "response": f"Error calling the API: {str(e)}. Please check your API key and connection.",
            "sources": [],
            "error": str(e),
        }
