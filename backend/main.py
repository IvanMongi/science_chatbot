from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.graph import create_science_agent
from persistence import (
    create_thread, list_threads, delete_thread, get_thread, update_thread_metadata,
    save_messages_to_db, load_messages_from_db, get_messages_for_display, _get_db_connection
)
from langchain_core.messages import HumanMessage
import logging
import uuid
from typing import Optional
from config import settings


logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s: %(message)s")

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Science Chatbot API",
    version="0.2.0",
    description="Scientific information retrieval chatbot with LangGraph agents"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    use_agent: bool = False


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    mode: str


class ThreadUpdateRequest(BaseModel):
    title: str


class ThreadSummary(BaseModel):
    thread_id: str
    title: str
    preview: str
    created_at: str
    updated_at: str
    message_count: int


@app.get("/api/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.2.0"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    Chat endpoint with conversation persistence.
    Creates or continues a thread based on thread_id.
    """
    # Generate or use existing thread_id
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Create thread if new
    if not req.thread_id:
        create_thread(thread_id=thread_id, title="New Conversation", preview=req.message[:50])
    
    try:
        # Load existing messages from database
        existing_messages = load_messages_from_db(thread_id)
        logger.info(f"Loaded {len(existing_messages)} existing messages for thread {thread_id}")
        
        # Add new user message
        new_user_message = HumanMessage(content=req.message)
        all_messages = existing_messages + [new_user_message]
        
        agent = create_science_agent()
        
        # Invoke agent with all messages (existing + new)
        initial_state = {"messages": all_messages}
        result = await agent.ainvoke(initial_state, config)
        
        # Extract final answer
        answer = result['messages'][-1].content
        
        # Save all messages to database (function handles deduplication)
        save_messages_to_db(thread_id, result['messages'])
        
        # Update thread metadata
        update_thread_metadata(
            thread_id=thread_id,
            message_count=len(result['messages']),
            preview=req.message[:50]
        )
        
        return ChatResponse(
            reply=answer,
            thread_id=thread_id,
            mode="agent" if req.use_agent else "echo"
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            reply=f"Error: {str(e)}",
            thread_id=thread_id,
            mode="error"
        )


@app.get("/api/threads")
async def get_threads(limit: int = 50, offset: int = 0) -> dict:
    """List all conversation threads."""
    threads = list_threads(limit=limit, offset=offset)
    return {
        "threads": [
            ThreadSummary(
                thread_id=t.get('thread_id'),
                title=t.get('title'),
                preview=t.get('preview') or "",
                created_at=t.get('created_at'),
                updated_at=t.get('updated_at'),
                message_count=t.get('message_count')
            )
            for t in threads
        ]
    }


@app.delete("/api/threads/{thread_id}")
async def delete_thread_endpoint(thread_id: str) -> dict:
    """Delete a conversation thread."""
    success = delete_thread(thread_id)
    return {"success": success, "thread_id": thread_id}


@app.put("/api/threads/{thread_id}")
async def update_thread_endpoint(thread_id: str, req: ThreadUpdateRequest) -> dict:
    """Update thread title."""
    thread = get_thread(thread_id)
    if not thread:
        return {"error": "Thread not found", "success": False}
    
    # Update only the title
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE conversation_threads
            SET title = ?
            WHERE thread_id = ?
        """, (req.title, thread_id))
        conn.commit()
        logger.info(f"Updated thread {thread_id} title to: {req.title}")
        return {"success": True, "thread_id": thread_id, "title": req.title}
    except Exception as e:
        logger.error(f"Error updating thread {thread_id}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


@app.get("/api/threads/{thread_id}")
async def get_thread_endpoint(thread_id: str) -> dict:
    """Get thread metadata."""
    thread = get_thread(thread_id)
    if not thread:
        return {"error": "Thread not found"}
    return {
        "thread_id": thread.get('thread_id'),
        "title": thread.get('title'),
        "preview": thread.get('preview'),
        "created_at": thread.get('created_at'),
        "updated_at": thread.get('updated_at'),
        "message_count": thread.get('message_count')
    }


@app.get("/api/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str) -> dict:
    """Get all messages for a thread (for frontend display)."""
    # Check if thread exists
    thread = get_thread(thread_id)
    if not thread:
        return {"error": "Thread not found", "messages": []}
    
    messages = get_messages_for_display(thread_id)
    return {
        "thread_id": thread_id,
        "messages": messages
    }


@app.get("/api/agent/status")
async def agent_status() -> dict:
    """Check if agent mode is available."""
    try:
        agent = create_science_agent()
        return {
            "available": True,
            "message": "LangGraph agent is ready"
        }
    except Exception as e:
        return {
            "available": False,
            "message": f"Agent not available: {str(e)}"
        }


# To run: uvicorn main:app --reload --host 0.0.0.0 --port 8000
