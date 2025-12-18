"""
Wikipedia search tool for the science agent.
"""

import httpx
from typing import Optional


async def search_wikipedia(query: str, limit: int = 3) -> list[dict]:
    """
    Search Wikipedia for scientific information.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of search results with title, snippet, and URL
    """
    base_url = "https://en.wikipedia.org/w/api.php"
    
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
        "srprop": "snippet|titlesnippet",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                    "url": f"https://en.wikipedia.org/wiki/{item.get('title', '').replace(' ', '_')}",
                    "source": "Wikipedia"
                })
            
            return results
            
    except Exception as e:
        print(f"Wikipedia search error: {e}")
        return []


def search_wikipedia_sync(query: str, limit: int = 3) -> list[dict]:
    """
    Synchronous version of Wikipedia search (for LangChain tool compatibility).
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of search results with title, snippet, and URL
    """
    import httpx
    
    base_url = "https://en.wikipedia.org/w/api.php"
    
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
        "srprop": "snippet|titlesnippet",
    }
    
    try:
        with httpx.Client() as client:
            response = client.get(base_url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", ""),
                    "url": f"https://en.wikipedia.org/wiki/{item.get('title', '').replace(' ', '_')}",
                    "source": "Wikipedia"
                })
            
            return results
            
    except Exception as e:
        print(f"Wikipedia search error: {e}")
        return []
