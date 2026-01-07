"""
arXiv search tool for scientific papers.
"""

import logging
import arxiv
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import SecretStr
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from config import settings

logger = logging.getLogger(__name__)

# Initialize lightweight LLM for query transformation
OPENAI_API_KEY = SecretStr(settings.openai_api_key) if settings.openai_api_key else None
query_llm = ChatOpenAI(model="gpt-4o-nano", temperature=0, api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def transform_query_to_arxiv(natural_query: str) -> str:
    """
    Transform a natural language query into an optimized arXiv search query.
    Uses a lightweight LLM to extract key terms and apply logical operators.
    
    Args:
        natural_query: Natural language query from the user
        
    Returns:
        Optimized arXiv search query string
    """
    if not query_llm:
        # Fallback: extract key terms from natural query
        logger.warning("No LLM available for query transformation, using fallback")

        # Simple fallback: remove question words and quotes
        cleaned = natural_query
        for word in ["summarize", "the", "what", "is", "are", "how", "why", "when", "where", "paper"]:
            cleaned = cleaned.replace(word, "").replace(word.capitalize(), "")
        return cleaned.strip()
    
    system_prompt = """You are an arXiv search query optimizer. Convert natural language queries into effective arXiv search queries.

arXiv query syntax:
- ti:"term" - search in title
- abs:term - search in abstract
- au:author - search by author
- cat:category - search by category (e.g., cs.AI, cs.CL)
- all:term - search all fields
- AND, OR, ANDNOT - logical operators

Examples:
- "Summarize the original transformers paper (2017)" → ti:"attention is all you need" OR (abs:transformer AND submittedDate:[2017 TO 2018])
- "Papers about BERT" → ti:BERT OR abs:BERT
- "Recent work on reinforcement learning" → abs:"reinforcement learning"
- "GPT-3 papers" → ti:GPT-3 OR abs:GPT-3

Return ONLY the optimized arXiv query, nothing else."""
    
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=natural_query)
        ]
        response = query_llm.invoke(messages)
        optimized_query = response.content.strip()
        logger.info("Query transformed: %r -> %r", natural_query, optimized_query)
        return optimized_query
    except Exception as e:
        logger.error("Query transformation failed: %s. Using original query.", e)
        return natural_query


async def search_arxiv(query: str, limit: int = 5) -> list[dict]:
    """
    Search arXiv for scientific papers.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of paper results with title, authors, abstract, and URL
    """
    logger.info("arXiv search start: query=%r limit=%d", query, limit)

    try:
        # Transform natural language query to optimized arXiv query
        search_query = transform_query_to_arxiv(query)
        search = arxiv.Search(
            query=search_query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance
        )

        # Use the Client for searching
        client = arxiv.Client()
        
        # Execute the search
        results_iter = client.results(search)
        
        results = []
        for result in results_iter:
            results.append({
                "title": result.title,
                "authors": ", ".join([author.name for author in result.authors]),
                "abstract": result.summary,
                "url": result.entry_id,
                "source": "arXiv"
            })

        logger.info("arXiv search done: results=%d", len(results))
        if not results:
            logger.warning("arXiv returned no results for query=%r", query)
        else:
            sample = ", ".join(r.get("title", "") for r in results[:3])
            logger.debug("arXiv top titles: %s", sample)

        return results

    except Exception as e:
        logger.exception("arXiv search error for query=%r: %s", query, e)
        return []


def search_arxiv_sync(query: str, limit: int = 3) -> list[dict]:
    """
    Synchronous version of arXiv search (for LangChain tool compatibility).
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of paper results with title, authors, abstract, and URL
    """
    logger.info("arXiv sync search start: query=%r limit=%d", query, limit)

    try:
        # Transform natural language query to optimized arXiv query
        search_query = transform_query_to_arxiv(query)
        search = arxiv.Search(
            query=search_query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance
        )

        # Use the Client for searching
        client = arxiv.Client()
        
        # Execute the search
        results_iter = client.results(search)
        
        results = []
        for result in results_iter:
            results.append({
                "title": result.title,
                "authors": ", ".join([author.name for author in result.authors]),
                "abstract": result.summary,
                "url": result.entry_id,
                "source": "arXiv"
            })

        logger.info("arXiv sync search done: results=%d", len(results))
        if not results:
            logger.warning("arXiv sync returned no results for query=%r", query)
        else:
            sample = ", ".join(r.get("title", "") for r in results[:3])
            logger.debug("arXiv sync top titles: %s", sample)

        return results

    except Exception as e:
        logger.exception("arXiv sync search error for query=%r: %s", query, e)
        return []
