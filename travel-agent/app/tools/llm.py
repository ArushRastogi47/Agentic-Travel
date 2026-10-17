"""
LLM tool — thin wrapper around Ollama via langchain-ollama.
Provides a single `get_llm()` function so no module hard-codes the model.
"""

from __future__ import annotations

from langchain_ollama import ChatOllama

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.logging_config import logger


def get_llm(temperature: float = 0.3) -> ChatOllama:
    """Return a ChatOllama instance configured from env vars."""
    logger.info(
        f"Initialising LLM: model={OLLAMA_MODEL}  base_url={OLLAMA_BASE_URL}"
    )
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
    )
