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
    #TODO : Use LLM for better classification
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
    wiki_results: list[dict] = []
    arxiv_results: list[dict] = []
    
    # Always search Wikipedia for context
    wiki_results = await search_wikipedia(question, limit=2)
    search_results.extend(wiki_results)
    
    # Search arXiv if paper-related
    strategy = state.get("search_strategy", "general")
    if strategy == "papers":
        arxiv_results = await search_arxiv(question, limit=2)
        search_results.extend(arxiv_results)
    
    state["wiki_results"] = wiki_results
    state["arxiv_results"] = arxiv_results
    state["search_results"] = search_results
    return state


async def generate_answer(state: AgentState) -> AgentState:
    """
    Generate final answer with citations from search results.
    """
    question = state.get("question", "")
    wiki_results = state.get("wiki_results", [])
    arxiv_results = state.get("arxiv_results", [])

    if not wiki_results and not arxiv_results:
        state["final_answer"] = (
            "I couldn't find reliable sources for this question. "
            "Please try rephrasing or asking a different question."
        )
        return state

    def _trim(text: str, limit: int = 500) -> str:
        return text[:limit] + "..." if len(text) > limit else text

    context_lines: list[str] = []

    for idx, result in enumerate(wiki_results, 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        snippet = result.get("extract") or result.get("snippet", "")
        context_lines.append(
            f"[W{idx}] {title} :: {_trim(snippet)} (Source: {url})"
        )

    for idx, result in enumerate(arxiv_results, 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "")
        authors = result.get("authors", "Unknown authors")
        abstract = _trim(result.get("abstract", ""))
        context_lines.append(
            f"[A{idx}] {title} :: Authors: {authors}. Abstract: {abstract} (Source: {url})"
        )

    context_block = "\n".join(context_lines) if context_lines else "No external context provided."

    history_messages = state.get("messages", [])
    history_text_lines = []
    for msg in history_messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant" if isinstance(msg, AIMessage) else "system"
        history_text_lines.append(f"{role}: {msg.content}")
    history_block = "\n".join(history_text_lines) if history_text_lines else "None provided."

    user_prompt = f"""
User question:
{question}

Conversation history (for future memory):
{history_block}

Available context:
{context_block}

Instructions:
- Synthesize a clear, concise answer using the provided sources.
- Cite each claim with the source identifiers (e.g., [W1], [A2]).
- Add a short References section listing the cited IDs with their URLs.
- If information is missing, say so explicitly and suggest a follow-up question.
"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *history_messages,
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await llm.ainvoke(messages)
        state["final_answer"] = response.content if hasattr(response, "content") else str(response)
    except Exception:
        state["final_answer"] = (
            "I ran into an issue generating the answer. Please try again or adjust the question."
        )

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
        "wiki_results": [],
        "arxiv_results": [],
        "search_results": [],
        "final_answer": ""
    }
    
    result = await agent.ainvoke(initial_state)
    return result.get("final_answer", "No answer generated")
