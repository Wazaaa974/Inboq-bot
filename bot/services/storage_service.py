"""SQLite persistence layer for conversations, leads, and stats.

# TODO: monter un volume Railway sur /data pour que inboq.db survive aux déploiements.
# Sans volume, le fichier est recréé à chaque redémarrage Railway.
"""

import json
import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# TODO: monter un volume Railway sur /data
DB_PATH = Path("/data/inboq.db")


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Call once at startup."""
    with _get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                user_id    INTEGER PRIMARY KEY,
                history    TEXT NOT NULL,
                state      TEXT NOT NULL DEFAULT 'new',
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS leads (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                name      TEXT,
                username  TEXT,
                summary   TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stats (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        # Idempotent migration: add state column to existing DBs
        try:
            conn.execute("ALTER TABLE conversations ADD COLUMN state TEXT NOT NULL DEFAULT 'new'")
        except sqlite3.OperationalError:
            pass  # column already exists


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

def get_history(user_id: int) -> list[dict]:
    """Return conversation history for a user, or [] if none."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT history FROM conversations WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return []
    return json.loads(row["history"])


def save_history(user_id: int, history: list[dict]) -> None:
    """Upsert conversation history for a user."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO conversations (user_id, history, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET history = excluded.history,
                                               updated_at = excluded.updated_at
            """,
            (user_id, json.dumps(history), now),
        )


def count_active_conversations() -> int:
    """Number of users with at least one conversation message."""
    with _get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM conversations").fetchone()
    return row["n"] if row else 0


def get_state(user_id: int) -> str:
    """Return the conversation state for a user ('new' if no row exists)."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT state FROM conversations WHERE user_id = ?", (user_id,)
        ).fetchone()
    return row["state"] if row else "new"


def set_state(user_id: int, state: str) -> None:
    """Upsert the conversation state for a user."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO conversations (user_id, history, state, updated_at)
            VALUES (?, '[]', ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET state = excluded.state,
                                               updated_at = excluded.updated_at
            """,
            (user_id, state, now),
        )


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def save_lead(
    user_id: int,
    name: str,
    username: str | None,
    summary: str,
    timestamp: str,
) -> None:
    """Insert a new qualified lead."""
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO leads (user_id, name, username, summary, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, username, summary, timestamp),
        )


def count_leads() -> int:
    with _get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS n FROM leads").fetchone()
    return row["n"] if row else 0


def get_recent_leads(limit: int = 5) -> list[dict]:
    """Return the most recent leads, newest first."""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def get_stats() -> dict[str, str]:
    """Return all stats as a plain dict."""
    with _get_conn() as conn:
        rows = conn.execute("SELECT key, value FROM stats").fetchall()
    return {r["key"]: r["value"] for r in rows}


def increment_stat(key: str, by: int = 1) -> None:
    """Atomically increment an integer stat counter."""
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO stats (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = CAST(CAST(value AS INTEGER) + ? AS TEXT)
            """,
            (key, str(by), by),
        )


def get_stat(key: str, default: int = 0) -> int:
    """Return a single integer stat."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM stats WHERE key = ?", (key,)
        ).fetchone()
    return int(row["value"]) if row else default


def set_stat(key: str, value: str) -> None:
    """Upsert a stat value."""
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO stats (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
