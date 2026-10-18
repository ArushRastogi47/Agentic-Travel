from __future__ import annotations

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from app.logging_config import logger


import os

def get_llm(temperature: float = 0.3):
    """
    Return configured LLM instance.
    Defaults to Google Gemini if GEMINI_API_KEY is present or LLM_PROVIDER is 'gemini'.
    Falls back to Ollama if configured or if Gemini key is missing.
    """
    api_key = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "") or GEMINI_API_KEY
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()
    gemini_model = os.getenv("GEMINI_MODEL", "") or GEMINI_MODEL or "gemini-2.5-flash"

    if provider == "gemini" or bool(api_key):
        if not api_key:
            logger.warning(
                "[LLM] GEMINI_API_KEY is not configured in .env! "
                "Attempting fallback to local Ollama or heuristics."
            )
            try:
                from langchain_ollama import ChatOllama
                return ChatOllama(
                    model=OLLAMA_MODEL,
                    base_url=OLLAMA_BASE_URL,
                    temperature=temperature,
                )
            except Exception:
                raise ValueError(
                    "GEMINI_API_KEY is not set. Please add GEMINI_API_KEY to your .env file."
                )

        from langchain_google_genai import ChatGoogleGenerativeAI

        logger.info(f"[LLM] Initialising Gemini API: model={gemini_model}")
        return ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=api_key,
            temperature=temperature,
            max_retries=2,
        )

    # Default / Ollama path
    from langchain_ollama import ChatOllama

    logger.info(
        f"[LLM] Initialising Ollama: model={OLLAMA_MODEL} base_url={OLLAMA_BASE_URL}"
    )
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
    )

