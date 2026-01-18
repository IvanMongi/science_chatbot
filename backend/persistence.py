"""
Conversation persistence layer using LangGraph MemorySaver.
Manages thread metadata and checkpoints for conversation memory.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Optional
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

# Database setup for thread metadata
DATABASE_PATH = "./conversations.db"
_memory_saver = None


def _get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Initialize database tables if they don't exist."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Create thread metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_threads (
            thread_id TEXT PRIMARY KEY,
            title TEXT NOT NULL DEFAULT 'Untitled',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            message_count INTEGER DEFAULT 0,
            preview TEXT
        )
    """)
    
    conn.commit()
    conn.close()


# Initialize database on module import
_init_db()


def get_checkpointer():
    """
    Get the LangGraph MemorySaver checkpointer.
    This stores conversation state in memory for the current session.
    Note: For production, consider using SqliteSaver from langgraph-checkpoint-sqlite package.
    """
    global _memory_saver
    if _memory_saver is None:
        _memory_saver = MemorySaver()
    return _memory_saver


def create_thread(thread_id: str, title: str = "Untitled", preview: str = "") -> dict:
    """Create a new conversation thread metadata."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO conversation_threads 
            (thread_id, title, created_at, updated_at, message_count, preview)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (thread_id, title, now, now, preview[:100] if preview else ""))
        
        conn.commit()
        logger.info(f"Created thread: {thread_id}")
        
        return {
            "thread_id": thread_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "preview": preview[:100] if preview else ""
        }
    finally:
        conn.close()


def get_thread(thread_id: str) -> Optional[dict]:
    """Get thread metadata by ID."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT thread_id, title, created_at, updated_at, message_count, preview
            FROM conversation_threads
            WHERE thread_id = ?
        """, (thread_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def list_threads(limit: int = 50, offset: int = 0) -> list[dict]:
    """List all conversation threads (newest first)."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT thread_id, title, created_at, updated_at, message_count, preview
            FROM conversation_threads
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def delete_thread(thread_id: str) -> bool:
    """Delete a thread and its metadata."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete from metadata
        cursor.execute("""
            DELETE FROM conversation_threads
            WHERE thread_id = ?
        """, (thread_id,))
        
        conn.commit()
        logger.info(f"Deleted thread: {thread_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting thread {thread_id}: {e}")
        return False
    finally:
        conn.close()


def update_thread_metadata(thread_id: str, message_count: int = None, preview: str = None) -> Optional[dict]:
    """Update thread metadata after new message."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if thread exists
        cursor.execute("SELECT * FROM conversation_threads WHERE thread_id = ?", (thread_id,))
        if not cursor.fetchone():
            return None
        
        now = datetime.utcnow().isoformat()
        
        # Build update query dynamically
        updates = ["updated_at = ?"]
        params = [now]
        
        if message_count is not None:
            updates.append("message_count = ?")
            params.append(message_count)
        
        if preview is not None:
            updates.append("preview = ?")
            params.append(preview[:100])
        
        params.append(thread_id)
        
        query = f"UPDATE conversation_threads SET {', '.join(updates)} WHERE thread_id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        # Return updated thread
        return get_thread(thread_id)
    finally:
        conn.close()
