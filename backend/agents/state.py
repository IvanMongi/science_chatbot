"""
State definition for the science agent graph.
"""

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """State of the science agent."""
    
    messages: Annotated[Sequence[BaseMessage], add_messages]
    """The conversation messages."""
    
    question: str
    """The original user question."""
    
    search_results: list[dict]
    """Search results from tools."""
    
    final_answer: str
    """The formatted final answer with citations."""
