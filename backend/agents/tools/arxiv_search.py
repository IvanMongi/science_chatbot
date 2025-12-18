"""
arXiv search tool for scientific papers.
"""

import httpx
import xml.etree.ElementTree as ET
from typing import Optional


async def search_arxiv(query: str, limit: int = 3) -> list[dict]:
    """
    Search arXiv for scientific papers.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        List of paper results with title, authors, abstract, and URL
    """
    base_url = "http://export.arxiv.org/api/query"
    
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params, timeout=15.0)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            results = []
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                id_elem = entry.find("atom:id", ns)
                
                # Get authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)
                
                if title_elem is not None and title_elem.text:
                    results.append({
                        "title": title_elem.text.strip(),
                        "authors": ", ".join(authors) if authors else "Unknown",
                        "abstract": summary_elem.text.strip() if summary_elem is not None and summary_elem.text else "",
                        "url": id_elem.text.strip() if id_elem is not None and id_elem.text else "",
                        "source": "arXiv"
                    })
            
            return results
            
    except Exception as e:
        print(f"arXiv search error: {e}")
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
    import httpx
    
    base_url = "http://export.arxiv.org/api/query"
    
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    try:
        with httpx.Client() as client:
            response = client.get(base_url, params=params, timeout=15.0)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            results = []
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                summary_elem = entry.find("atom:summary", ns)
                id_elem = entry.find("atom:id", ns)
                
                # Get authors
                authors = []
                for author in entry.findall("atom:author", ns):
                    name_elem = author.find("atom:name", ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text)
                
                if title_elem is not None and title_elem.text:
                    results.append({
                        "title": title_elem.text.strip(),
                        "authors": ", ".join(authors) if authors else "Unknown",
                        "abstract": summary_elem.text.strip() if summary_elem is not None and summary_elem.text else "",
                        "url": id_elem.text.strip() if id_elem is not None and id_elem.text else "",
                        "source": "arXiv"
                    })
            
            return results
            
    except Exception as e:
        print(f"arXiv search error: {e}")
        return []
