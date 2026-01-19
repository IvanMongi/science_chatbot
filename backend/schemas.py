"""Pydantic request/response schemas for API endpoints."""

from typing import Optional
from pydantic import BaseModel


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
