"""
Persistence — SQLite-based storage for conversations, state, and checkpoints.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.config import DATABASE_URL
from app.logging_config import logger


def _get_db_path() -> str:
    """Extract file path from SQLite URL."""
    url = DATABASE_URL
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "")
    return "./data/travel_agent.db"


def init_database() -> None:
    """Create tables if they don't exist."""
    db_path = _get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_query TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trip_states (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            state_json TEXT NOT NULL,
            checkpoint_type TEXT DEFAULT 'auto',
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE TABLE IF NOT EXISTS human_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            feedback TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );
    """)

    conn.commit()
    conn.close()
    logger.info(f"[Database] Initialised at {db_path}")


def save_conversation(thread_id: str, query: str) -> None:
    """Insert or update a conversation record."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    now = datetime.now().isoformat()
    conn.execute(
        """
        INSERT INTO conversations (id, user_query, status, created_at, updated_at)
        VALUES (?, ?, 'active', ?, ?)
        ON CONFLICT(id) DO UPDATE SET updated_at = ?, user_query = ?
        """,
        (thread_id, query, now, now, now, query),
    )
    conn.commit()
    conn.close()


def save_state(thread_id: str, state: dict, checkpoint_type: str = "auto") -> None:
    """Save a state snapshot."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    now = datetime.now().isoformat()

    # Serialise state (handle non-JSON-serialisable objects)
    state_json = json.dumps(state, default=str)

    conn.execute(
        "INSERT INTO trip_states (conversation_id, state_json, checkpoint_type, created_at) VALUES (?, ?, ?, ?)",
        (thread_id, state_json, checkpoint_type, now),
    )
    conn.commit()
    conn.close()


def save_feedback(thread_id: str, decision: str, feedback: str = "") -> None:
    """Save human feedback."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    now = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO human_feedback (conversation_id, decision, feedback, created_at) VALUES (?, ?, ?, ?)",
        (thread_id, decision, feedback, now),
    )
    conn.commit()
    conn.close()


def get_conversation(thread_id: str) -> dict | None:
    """Retrieve a conversation by thread ID."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM conversations WHERE id = ?", (thread_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_latest_state(thread_id: str) -> dict | None:
    """Retrieve the latest state for a conversation."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT state_json FROM trip_states WHERE conversation_id = ? ORDER BY id DESC LIMIT 1",
        (thread_id,),
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row["state_json"])
    return None


def get_recent_conversations(limit: int = 10) -> list[dict]:
    """Retrieve the most recent conversations."""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

