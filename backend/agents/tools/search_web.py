import logging

from agents.state import AgentState
from .wikipedia_search import search_wikipedia
from .arxiv_search import search_arxiv


logger = logging.getLogger(__name__)


async def search_web(state: AgentState) -> AgentState:
    """
    Perform web search using Wikipedia and arXiv tools.
    """
    question = state.get("question", "")
    strategy = state.get("search_strategy", "general")
    logger.info("search_web start: strategy=%s question=%r", strategy, question)

    search_results = []

    # Always search Wikipedia for context
    wiki_results = await search_wikipedia(question, limit=2)
    logger.info("search_web: wikipedia results=%d", len(wiki_results))
    search_results.extend(wiki_results)

    # Search arXiv if paper-related
    if strategy == "papers":
        arxiv_results = await search_arxiv(question, limit=2)
        logger.info("search_web: arxiv results=%d", len(arxiv_results))
        search_results.extend(arxiv_results)

    logger.info("search_web done: total results=%d", len(search_results))
    if not search_results:
        logger.warning("search_web: no results combined for question=%r", question)

    state["search_results"] = search_results
    return state