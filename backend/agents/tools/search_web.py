from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

from agents.state import AgentState


def search_web(state: AgentState) -> AgentState:
    """
    Perform web search using external tools.
    """
    question = state.get("question", "")
    search_results = []
    
    # Always search Wikipedia for context
    wiki_results = await search_wikipedia(question, limit=2)
    search_results.extend(wiki_results)
    
    # Search arXiv if paper-related
    strategy = state.get("search_strategy", "general")
    if strategy == "papers":
        arxiv_results = await search_arxiv(question, limit=2)
        search_results.extend(arxiv_results)
    
    state["search_results"] = search_results
    return state