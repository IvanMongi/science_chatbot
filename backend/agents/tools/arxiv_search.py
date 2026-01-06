"""
arXiv search tool for scientific papers.
"""

import logging
import httpx
import xml.etree.ElementTree as ET
from typing import Optional

logger = logging.getLogger(__name__)


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
    
    logger.info("arXiv search start: query=%r limit=%d", query, limit)

    try:
        async with httpx.AsyncClient() as client:
            logger.debug("arXiv request: url=%s params=%s", base_url, params)
            response = await client.get(base_url, params=params, timeout=15.0)
            logger.debug("arXiv response status: %s bytes=%d", response.status_code, len(response.content or b""))
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entries = root.findall("atom:entry", ns)
            results = []
            for entry in entries:
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

            logger.info("arXiv search done: entries=%d results=%d", len(entries), len(results))
            if not results:
                logger.warning("arXiv returned no results for query=%r", query)
            else:
                sample = ", ".join(r.get("title", "") for r in results[:3])
                logger.debug("arXiv top titles: %s", sample)

            return results

    except httpx.HTTPError as http_err:
        logger.exception("arXiv HTTP error for query=%r: %s", query, http_err)
        return []
    except ET.ParseError as parse_err:
        logger.exception("arXiv XML parse error for query=%r: %s", query, parse_err)
        return []
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
    base_url = "http://export.arxiv.org/api/query"
    
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": limit,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    logger.info("arXiv sync search start: query=%r limit=%d", query, limit)

    try:
        with httpx.Client() as client:
            logger.debug("arXiv sync request: url=%s params=%s", base_url, params)
            response = client.get(base_url, params=params, timeout=15.0)
            logger.debug("arXiv sync response status: %s bytes=%d", response.status_code, len(response.content or b""))
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entries = root.findall("atom:entry", ns)
            results = []
            for entry in entries:
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

            logger.info("arXiv sync search done: entries=%d results=%d", len(entries), len(results))
            if not results:
                logger.warning("arXiv sync returned no results for query=%r", query)
            else:
                sample = ", ".join(r.get("title", "") for r in results[:3])
                logger.debug("arXiv sync top titles: %s", sample)

            return results

    except httpx.HTTPError as http_err:
        logger.exception("arXiv sync HTTP error for query=%r: %s", query, http_err)
        return []
    except ET.ParseError as parse_err:
        logger.exception("arXiv sync XML parse error for query=%r: %s", query, parse_err)
        return []
    except Exception as e:
        logger.exception("arXiv sync search error for query=%r: %s", query, e)
        return []
