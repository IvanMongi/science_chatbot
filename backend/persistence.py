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
    
    # Create messages table for storing individual messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
            content TEXT NOT NULL,
            tool_calls TEXT,
            tool_call_id TEXT,
            created_at TEXT NOT NULL,
            message_index INTEGER NOT NULL,
            FOREIGN KEY (thread_id) REFERENCES conversation_threads(thread_id) ON DELETE CASCADE,
            UNIQUE (thread_id, message_index)
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)")
    
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


def save_messages_to_db(thread_id: str, messages: list) -> None:
    """Save new messages to database for persistence and display."""
    import json
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current max index
        cursor.execute(
            "SELECT MAX(message_index) FROM messages WHERE thread_id = ?",
            (thread_id,)
        )
        result = cursor.fetchone()
        max_index = result[0] if result[0] is not None else -1
        
        # Get existing message count to detect new messages
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE thread_id = ?",
            (thread_id,)
        )
        existing_count = cursor.fetchone()[0]
        
        # Only save messages beyond what's already stored
        new_messages = messages[existing_count:]
        
        for idx, msg in enumerate(new_messages):
            message_index = max_index + idx + 1
            
            # Extract message data
            role = msg.__class__.__name__.replace("Message", "").lower()
            if role == "ai":
                role = "assistant"
            elif role == "human":
                role = "user"
            
            content = msg.content if hasattr(msg, 'content') else ""
            tool_calls_json = None
            tool_call_id = None
            
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                # Serialize tool calls to JSON
                tool_calls_json = json.dumps([{
                    'name': tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None),
                    'args': tc.get('args') if isinstance(tc, dict) else getattr(tc, 'args', {}),
                    'id': tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                } for tc in msg.tool_calls])
            
            if hasattr(msg, 'tool_call_id'):
                tool_call_id = msg.tool_call_id
            
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                INSERT INTO messages (thread_id, role, content, tool_calls, tool_call_id, created_at, message_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (thread_id, role, content, tool_calls_json, tool_call_id, now, message_index))
        
        conn.commit()
        logger.info(f"Saved {len(new_messages)} new messages for thread {thread_id}")
    except Exception as e:
        logger.error(f"Error saving messages for thread {thread_id}: {e}")
        raise
    finally:
        conn.close()


def load_messages_from_db(thread_id: str) -> list:
    """Load conversation history from database."""
    import json
    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT role, content, tool_calls, tool_call_id
            FROM messages
            WHERE thread_id = ?
            ORDER BY message_index
        """, (thread_id,))
        
        db_messages = cursor.fetchall()
        messages = []
        
        for row in db_messages:
            role = row[0]
            content = row[1]
            tool_calls_json = row[2]
            tool_call_id = row[3]
            
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                ai_msg = AIMessage(content=content)
                if tool_calls_json:
                    try:
                        ai_msg.tool_calls = json.loads(tool_calls_json)
                    except:
                        pass
                messages.append(ai_msg)
            elif role == "tool":
                messages.append(ToolMessage(
                    content=content,
                    tool_call_id=tool_call_id or ""
                ))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        
        logger.info(f"Loaded {len(messages)} messages for thread {thread_id}")
        return messages
    except Exception as e:
        logger.error(f"Error loading messages for thread {thread_id}: {e}")
        return []
    finally:
        conn.close()


def get_messages_for_display(thread_id: str) -> list[dict]:
    """Get messages formatted for frontend display (excluding system/tool messages)."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT role, content, created_at
            FROM messages
            WHERE thread_id = ? AND role IN ('user', 'assistant')
            ORDER BY message_index
        """, (thread_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "role": row[0],
                "content": row[1],
                "created_at": row[2]
            })
        
        return messages
    finally:
        conn.close()
