"""
LangGraph agent definition for scientific information retrieval.
"""
import json
import logging
from typing import Any, Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from IPython.display import Image, display
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from pydantic import SecretStr

from .state import AgentState
from .tools.wikipedia_search import search_wikipedia
from .tools.arxiv_search import search_arxiv
from .prompts import SYSTEM_PROMPT
from config import settings
from persistence import get_checkpointer

# Set up loggerToolMessage
logger = logging.getLogger(__name__)

# Define constants
OPENAI_API_KEY = SecretStr(settings.openai_api_key) if settings.openai_api_key else None


@tool
async def search_tool(question: str) -> dict:
    """
    Execute searches and return results based on the question.
    Determines search strategy and retrieves relevant information from Wikipedia and arXiv.
    
    Args:
        question: The user's scientific question
        
    Returns:
        Dictionary containing wiki_results and arxiv_results
    """
    # Classify: Determine search strategy
    #TODO: improve classification with a small model or keyword matching
    needs_papers = any(keyword in question.lower() for keyword in [
        "paper", "study", "research", "publication", "arxiv", "recent"
    ])
    search_strategy = "papers" if needs_papers else "general"
    
    # Search: Execute searches based on strategy
    wiki_results: list[dict] = []
    arxiv_results: list[dict] = []
    
    # Always search Wikipedia for context
    wiki_results = await search_wikipedia(question, limit=2)
    
    # Search arXiv if paper-related
    if search_strategy == "papers":
        arxiv_results = await search_arxiv(question, limit=2)
    
    return {
        "wiki_results": wiki_results,
        "arxiv_results": arxiv_results,
    }

# Register tools
tools = [search_tool]

# Define the llm instance
llm = ChatOpenAI(model="gpt-4.1-nano", temperature=1, api_key=OPENAI_API_KEY)

# Create LLM with tools
llm_with_tools = llm.bind_tools(tools)


def create_science_agent():
    """
    Create the LangGraph agent for scientific information retrieval.
    
    Returns:
        Compiled StateGraph ready for execution with persistence
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("generate", generate_answer)
    workflow.add_node("tools", ToolNode(tools))
    
    # Define the flow
    workflow.add_edge(START, "generate")
    workflow.add_conditional_edges(
        "generate",
        tools_condition
    )
    workflow.add_edge("tools", "generate")
    
    # Compile the graph with persistence
    checkpointer = get_checkpointer()
    agent = workflow.compile(checkpointer=checkpointer)

    # Show
    display(Image(agent.get_graph(xray=True).draw_mermaid_png()))

    return agent

    return agent


async def generate_answer(state: AgentState):
    """
    Generate final answer with citations from search results.
    Can either generate a direct answer or call the search_tool.
    """

    wiki_results = state.get("wiki_results", [])
    arxiv_results = state.get("arxiv_results", [])
    
    logger.info(f"[GENERATE] Starting generation. Wiki results: {len(wiki_results)}, arXiv results: {len(arxiv_results)}")

    messages = [
        SystemMessage(content=SYSTEM_PROMPT), 
        *state["messages"]
    ]

    return {"messages": [llm_with_tools.invoke(messages)]}


# For testing/development
async def run_agent(question: str) -> Any:
    """
    Helper function to run the agent with a question.
    
    Args:
        question: The user's scientific question
        
    Returns:
        The final answer with citations
    """
    logger.info(f"[RUN_AGENT] Starting agent with question: {question[:50]}...")
    agent = create_science_agent()
    
    initial_state: AgentState = {
        "messages": [HumanMessage(content=question)]
    }
    
    result = await agent.ainvoke(initial_state, {"recursion_limit": 5})
    logger.info(f"[RUN_AGENT] Agent completed. Answer:\n")
    for m in result['messages']:
        m.pretty_print()

    return result['messages'][-1].content
