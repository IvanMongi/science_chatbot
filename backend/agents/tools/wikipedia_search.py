"""
Wikipedia search helpers for the science agent.

Implements a two-step flow:
1) `wiki_search(query)` to fetch ranked candidate pages (title, pageid, snippet, url).
2) `wiki_get_page(title/pageid)` to fetch canonical title, extract (lead intro), and url.

Thin wrappers `search_wikipedia`/`search_wikipedia_sync` are kept for compatibility.
"""

import html
import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def _clean_snippet(snippet: str) -> str:
    """Strip HTML tags and decode entities from a snippet."""
    text = re.sub(r"<[^>]+>", "", snippet or "")
    return html.unescape(text).strip()


def _wiki_base_url(lang: str = "en") -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"


def _page_url_from_title(title: str) -> str:
    return f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}" if title else ""


async def wiki_search(query: str, limit: int = 5, lang: str = "en") -> list[dict]:
    """
    Search Wikipedia and return ranked candidate pages.

    Each result contains: title, pageid, snippet, url, source.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
        "srprop": "snippet|titlesnippet",
        "utf8": 1,
    }

    logger.info("wiki_search start: query=%r limit=%d", query, limit)

    try:
        async with httpx.AsyncClient() as client:
            logger.debug("wiki_search request: params=%s", params)
            resp = await client.get(
                _wiki_base_url(lang),
                params=params,
                timeout=10.0,
                headers={"User-Agent": "science-chatbot/1.0 (langgraph)"},
            )
            logger.debug("wiki_search response status: %s", resp.status_code)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("query", {}).get("search", [])
        results: list[dict] = []
        for item in items:
            title = item.get("title", "")
            pageid = item.get("pageid")
            results.append({
                "title": title,
                "pageid": pageid,
                "snippet": _clean_snippet(item.get("snippet", "")),
                "url": _page_url_from_title(title),
                "source": "Wikipedia",
            })

        logger.info("wiki_search done: items=%d results=%d", len(items), len(results))
        if results:
            sample = ", ".join(r.get("title", "") for r in results[:3])
            logger.debug("wiki_search top titles: %s", sample)
        else:
            logger.warning("wiki_search returned no results for query=%r", query)

        return results

    except httpx.HTTPError as http_err:
        logger.exception("wiki_search HTTP error for query=%r: %s", query, http_err)
        return []
    except Exception as exc:  # noqa: BLE001
        logger.exception("wiki_search error for query=%r: %s", query, exc)
        return []


async def wiki_get_page(*, title: Optional[str] = None, pageid: Optional[int] = None, lang: str = "en") -> Optional[dict]:
    """
    Fetch the canonical title, lead extract, and url for a page.

    Provide either `pageid` or `title`. Returns None if not found.
    """
    if not title and pageid is None:
        raise ValueError("Provide either title or pageid to wiki_get_page")

    page_param = {"pageids": str(pageid)} if pageid is not None else {"titles": title}
    params = {
        "action": "query",
        "prop": "info|extracts",
        "inprop": "url",
        "exintro": 1,
        "explaintext": 1,
        "redirects": 1,
        "format": "json",
        "utf8": 1,
        **page_param,
    }

    logger.info("wiki_get_page start: title=%r pageid=%s", title, pageid)

    try:
        async with httpx.AsyncClient() as client:
            logger.debug("wiki_get_page request: params=%s", params)
            resp = await client.get(
                _wiki_base_url(lang),
                params=params,
                timeout=10.0,
                headers={"User-Agent": "science-chatbot/1.0 (langgraph)"},
            )
            logger.debug("wiki_get_page response status: %s", resp.status_code)
            resp.raise_for_status()
            data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            logger.warning("wiki_get_page found no pages: title=%r pageid=%s", title, pageid)
            return None

        page = next(iter(pages.values()))
        if not page or int(page.get("pageid", -1)) == -1:
            logger.warning("wiki_get_page returned invalid page: title=%r pageid=%s", title, pageid)
            return None

        resolved_title = page.get("title", title or "")
        page_url = page.get("fullurl") or _page_url_from_title(resolved_title)

        result = {
            "title": resolved_title,
            "pageid": page.get("pageid"),
            "extract": (page.get("extract") or "").strip(),
            "url": page_url,
            "source": "Wikipedia",
        }

        logger.info("wiki_get_page done: title=%r pageid=%s", result["title"], result["pageid"])
        return result

    except httpx.HTTPError as http_err:
        logger.exception("wiki_get_page HTTP error: title=%r pageid=%s err=%s", title, pageid, http_err)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.exception("wiki_get_page error: title=%r pageid=%s err=%s", title, pageid, exc)
        return None


# Compatibility wrappers
async def search_wikipedia(query: str, limit: int = 3, lang: str = "en") -> list[dict]:
    """Backward-compatible alias for wiki_search that also attaches extracts when available."""
    candidates = await wiki_search(query, limit=limit, lang=lang)
    enriched: list[dict] = []
    for candidate in candidates:
        pageid = candidate.get("pageid")
        # Best-effort fetch of the lead extract for top candidates
        details = await wiki_get_page(pageid=pageid, lang=lang) if pageid is not None else None
        enriched.append({
            **candidate,
            "extract": details.get("extract") if details else "",
        })
    return enriched


def wiki_search_sync(query: str, limit: int = 5, lang: str = "en") -> list[dict]:
    """Synchronous version of wiki_search."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
        "srprop": "snippet|titlesnippet",
        "utf8": 1,
    }

    logger.info("wiki_search_sync start: query=%r limit=%d", query, limit)

    try:
        with httpx.Client() as client:
            logger.debug("wiki_search_sync request: params=%s", params)
            resp = client.get(
                _wiki_base_url(lang),
                params=params,
                timeout=10.0,
                headers={"User-Agent": "science-chatbot/1.0 (langgraph)"},
            )
            logger.debug("wiki_search_sync response status: %s", resp.status_code)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("query", {}).get("search", [])
        results: list[dict] = []
        for item in items:
            title = item.get("title", "")
            results.append({
                "title": title,
                "pageid": item.get("pageid"),
                "snippet": _clean_snippet(item.get("snippet", "")),
                "url": _page_url_from_title(title),
                "source": "Wikipedia",
            })

        logger.info("wiki_search_sync done: items=%d results=%d", len(items), len(results))
        return results

    except httpx.HTTPError as http_err:
        logger.exception("wiki_search_sync HTTP error for query=%r: %s", query, http_err)
        return []
    except Exception as exc:  # noqa: BLE001
        logger.exception("wiki_search_sync error for query=%r: %s", query, exc)
        return []


def wiki_get_page_sync(*, title: Optional[str] = None, pageid: Optional[int] = None, lang: str = "en") -> Optional[dict]:
    """Synchronous version of wiki_get_page."""
    if not title and pageid is None:
        raise ValueError("Provide either title or pageid to wiki_get_page_sync")

    page_param = {"pageids": str(pageid)} if pageid is not None else {"titles": title}
    params = {
        "action": "query",
        "prop": "info|extracts",
        "inprop": "url",
        "exintro": 1,
        "explaintext": 1,
        "redirects": 1,
        "format": "json",
        "utf8": 1,
        **page_param,
    }

    logger.info("wiki_get_page_sync start: title=%r pageid=%s", title, pageid)

    try:
        with httpx.Client() as client:
            logger.debug("wiki_get_page_sync request: params=%s", params)
            resp = client.get(
                _wiki_base_url(lang),
                params=params,
                timeout=10.0,
                headers={"User-Agent": "science-chatbot/1.0 (langgraph)"},
            )
            logger.debug("wiki_get_page_sync response status: %s", resp.status_code)
            resp.raise_for_status()
            data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            logger.warning("wiki_get_page_sync found no pages: title=%r pageid=%s", title, pageid)
            return None

        page = next(iter(pages.values()))
        if not page or int(page.get("pageid", -1)) == -1:
            logger.warning("wiki_get_page_sync returned invalid page: title=%r pageid=%s", title, pageid)
            return None

        resolved_title = page.get("title", title or "")
        page_url = page.get("fullurl") or _page_url_from_title(resolved_title)

        return {
            "title": resolved_title,
            "pageid": page.get("pageid"),
            "extract": (page.get("extract") or "").strip(),
            "url": page_url,
            "source": "Wikipedia",
        }

    except httpx.HTTPError as http_err:
        logger.exception("wiki_get_page_sync HTTP error: title=%r pageid=%s err=%s", title, pageid, http_err)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.exception("wiki_get_page_sync error: title=%r pageid=%s err=%s", title, pageid, exc)
        return None


# Deprecated sync alias
def search_wikipedia_sync(query: str, limit: int = 3, lang: str = "en") -> list[dict]:
    """Backward-compatible alias for wiki_search_sync."""
    return wiki_search_sync(query=query, limit=limit, lang=lang)
