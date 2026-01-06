"""
State definition for the science agent graph.
"""

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """State of the science agent.
    Subclass of Messages with additional fields."""
    
    question: str
    """The original user question."""
    
    search_strategy: str
    """Search strategy chosen for the query (e.g., 'papers' or 'general')."""
    
    search_results: list[dict]
    """Search results from tools."""
    
    final_answer: str
    """The formatted final answer with citations."""
