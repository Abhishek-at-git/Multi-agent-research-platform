"""Database persistence layer for Multi-Agent Research Assistant.

Provides SQLite storage for generated reports, query logs, citations,
and system audit history.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import get_settings

logger = logging.getLogger("research_assistant.db")


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open connection to the SQLite database and ensure schema is initialized."""
    path = db_path or get_settings().database_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize database tables and indexes."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    language TEXT DEFAULT 'English',
                    model_used TEXT,
                    summary TEXT,
                    report_markdown TEXT NOT NULL,
                    pdf_path TEXT,
                    sources_count INTEGER DEFAULT 0,
                    word_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id INTEGER,
                    query TEXT NOT NULL,
                    results_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
                )
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_topic ON reports(topic)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at)")
        logger.info(f"Database schema initialized at: {db_path or get_settings().database_path}")
    finally:
        conn.close()


def save_report(
    topic: str,
    report_markdown: str,
    language: str = "English",
    model_used: Optional[str] = None,
    summary: Optional[str] = None,
    pdf_path: Optional[str] = None,
    sources_count: int = 0,
    db_path: Optional[Path] = None,
) -> int:
    """Save a newly completed research report into the SQLite database.

    Args:
        topic: The research subject.
        report_markdown: The full Markdown text of the report.
        language: Language of the report.
        model_used: Gemini model used.
        summary: Short executive summary snippet.
        pdf_path: Path to exported PDF if generated.
        sources_count: Number of sources cited.
        db_path: Optional custom DB path.

    Returns:
        int: The inserted report ID.
    """
    init_db(db_path)
    conn = get_db_connection(db_path)

    # Calculate word count
    word_count = len(report_markdown.split())

    # Extract short summary if not passed
    if not summary:
        lines = [line.strip() for line in report_markdown.splitlines() if line.strip() and not line.startswith("#")]
        summary = " ".join(lines[:3])[:350] + ("..." if len(lines) > 3 else "")

    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO reports (
                    topic, language, model_used, summary, report_markdown,
                    pdf_path, sources_count, word_count, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed')
                """,
                (
                    topic,
                    language,
                    model_used or get_settings().gemini_model,
                    summary,
                    report_markdown,
                    pdf_path,
                    sources_count,
                    word_count,
                ),
            )
            report_id = cursor.lastrowid
            logger.info(f"Saved report #{report_id} for topic '{topic}' to database.")
            return report_id
    finally:
        conn.close()


def list_reports(limit: int = 50, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Retrieve list of saved reports ordered by creation time descending."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            SELECT id, topic, language, model_used, summary, pdf_path,
                   sources_count, word_count, status, created_at
            FROM reports
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_report(report_id: int, db_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Retrieve a single report by ID, including its full markdown."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_report(report_id: int, db_path: Optional[Path] = None) -> bool:
    """Delete a report by ID."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        with conn:
            cursor = conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


def get_db_stats(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Get aggregated statistics about saved reports."""
    init_db(db_path)
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_reports,
                COALESCE(SUM(word_count), 0) as total_words,
                COALESCE(SUM(sources_count), 0) as total_sources,
                COUNT(DISTINCT language) as total_languages
            FROM reports
        """)
        row = cursor.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()
