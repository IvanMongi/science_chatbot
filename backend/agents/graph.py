"""
LangGraph agent definition for scientific information retrieval.
"""

from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from .state import AgentState
from .tools.wikipedia_search import search_wikipedia
from .tools.arxiv_search import search_arxiv
from .prompts import SYSTEM_PROMPT
from config import settings

# Define constants
OPENAI_API_KEY = SecretStr(settings.openai_api_key) if settings.openai_api_key else None

# Define the llm instance
llm = ChatOpenAI(model="gpt-4.1-nano", temperature=1, api_key=OPENAI_API_KEY)

def create_science_agent():
    """
    Create the LangGraph agent for scientific information retrieval.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("classify", classify_question)
    workflow.add_node("search", search_information)
    workflow.add_node("generate", generate_answer)
    
    # Define the flow
    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "search")
    workflow.add_edge("search", "generate")
    workflow.add_edge("generate", END)
    
    # Compile the graph
    return workflow.compile()

# TODO: Enhance with LLM calls for classification and answer generation
async def classify_question(state: AgentState) -> AgentState:
    """
    Classify the user's question and determine search strategy.
    """
    question = state.get("question", "")
    
    # Simple classification logic - can be enhanced with LLM
    needs_papers = any(keyword in question.lower() for keyword in [
        "paper", "study", "research", "publication", "arxiv", "recent"
    ])
    
    state["search_strategy"] = "papers" if needs_papers else "general"
    return state


async def search_information(state: AgentState) -> AgentState:
    """
    Execute searches based on the question.
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


async def generate_answer(state: AgentState) -> AgentState:
    """
    Generate final answer with citations from search results.
    
    This is a simple implementation. In a full version, you would use
    an LLM to synthesize the information intelligently.
    """
    question = state.get("question", "")
    search_results = state.get("search_results", [])
    
    if not search_results:
        state["final_answer"] = "I couldn't find reliable sources for this question. Please try rephrasing or asking a different question."
        return state
    
    # Build answer with citations (simplified version)
    answer_parts = [f"Based on the available sources regarding '{question}':\n"]
    
    for idx, result in enumerate(search_results, 1):
        source = result.get("source", "Unknown")
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        
        if source == "Wikipedia":
            snippet = result.get("snippet", "")
            extract = result.get("extract", "")
            wiki_text = extract or snippet
            answer_parts.append(f"\n{idx}. From Wikipedia - {title}:")
            answer_parts.append(f"   {wiki_text}")
            answer_parts.append(f"   [Source: {title} - {url}]")
            
        elif source == "arXiv":
            authors = result.get("authors", "Unknown authors")
            abstract = result.get("abstract", "")
            # Truncate abstract if too long
            abstract_preview = abstract[:200] + "..." if len(abstract) > 200 else abstract
            answer_parts.append(f"\n{idx}. Paper: {title}")
            answer_parts.append(f"   Authors: {authors}")
            answer_parts.append(f"   {abstract_preview}")
            answer_parts.append(f"   [Source: {title} - {url}]")
    
    answer_parts.append("\n\nNote: This is a prototype. In the full version, an LLM would synthesize this information into a coherent answer.")
    
    state["final_answer"] = "\n".join(answer_parts)
    return state


# For testing/development
async def run_agent(question: str) -> str:
    """
    Helper function to run the agent with a question.
    
    Args:
        question: The user's scientific question
        
    Returns:
        The final answer with citations
    """
    agent = create_science_agent()
    
    initial_state: AgentState = {
        "messages": [HumanMessage(content=question)],
        "question": question,
        "search_strategy": "general",
        "search_results": [],
        "final_answer": ""
    }
    
    result = await agent.ainvoke(initial_state)
    return result.get("final_answer", "No answer generated")
