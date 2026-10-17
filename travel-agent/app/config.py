"""
Application configuration — loaded from environment variables / .env file.
All settings have zero-cost defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Load .env from project root ────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# ── LLM ────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

# ── Application ────────────────────────────────────────────────────────
DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# ── Database ───────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{_PROJECT_ROOT / 'data' / 'travel_agent.db'}",
)

# ── Providers (base URLs — all optional) ──────────────────────────────
OPEN_METEO_BASE_URL: str = os.getenv(
    "OPEN_METEO_BASE_URL", "https://api.open-meteo.com"
)
