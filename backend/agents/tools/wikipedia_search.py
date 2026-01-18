"""
Wikipedia search helpers for the science agent.

Implements a two-step flow:
1) `wiki_search(query)` to fetch ranked candidate pages (title, pageid, snippet, url).
2) `wiki_get_page(title/pageid)` to fetch canonical title, extract (lead intro), and url.
"""

import html
import logging
import re
import asyncio
import time
from typing import Optional

import httpx
from urllib.parse import quote
from config import settings

logger = logging.getLogger(__name__)
# Suppress verbose logs from HTTP clients
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('httpcore').setLevel(logging.ERROR)

def _clean_snippet(snippet: str) -> str:
    """Strip HTML tags and decode entities from a snippet."""
    text = re.sub(r"<[^>]+>", "", snippet or "")
    return html.unescape(text).strip()


def _wiki_base_url(lang: str = "en") -> str:
    return f"https://{lang}.wikipedia.org/w/api.php"


def _page_url_from_title(title: str) -> str:
    return f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}" if title else ""


def _rest_search_url(lang: str = "en") -> str:
    # REST search endpoint (cached interface)
    return f"https://{lang}.wikipedia.org/w/rest.php/v1/search/page"


def _rest_summary_url(title: str, lang: str = "en") -> str:
    # REST summary endpoint for current page content
    return f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'))}"


def _wiki_headers() -> dict:
    ua = settings.wikimedia_user_agent or f"science-chatbot/{settings.api_version} (+local; contact: set WIKIMEDIA_USER_AGENT)"
    return {
        "User-Agent": ua,
        "Accept-Encoding": "gzip",
    }


# Simple global throttle to keep concurrency=1 and RPS below policy
_REQUEST_LOCK = asyncio.Lock()
_LAST_REQUEST_AT = 0.0


async def _throttle():
    global _LAST_REQUEST_AT
    async with _REQUEST_LOCK:
        min_interval = 1.0 / max(settings.wikimedia_rps, 0.1)
        now = time.monotonic()
        wait_for = (_LAST_REQUEST_AT + min_interval) - now
        if wait_for > 0:
            await asyncio.sleep(wait_for)
        _LAST_REQUEST_AT = time.monotonic()


async def _get_with_backoff(client: httpx.AsyncClient, url: str, *, params: dict | None = None, timeout: float = 10.0) -> httpx.Response:
    attempts = 0
    while True:
        attempts += 1
        await _throttle()
        resp = await client.get(url, params=params, timeout=timeout, headers=_wiki_headers())
        # Respect 429 Too Many Requests
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            delay = 1.0
            try:
                if retry_after:
                    delay = max(1.0, float(retry_after))
            except ValueError:
                delay = 2.0
            logger.warning("Received 429 from Wikimedia; sleeping %.1fs then retrying", delay)
            await asyncio.sleep(delay)
            if attempts < 3:
                continue
        # For 403, surface error and stop to avoid hammering
        if resp.status_code == 403:
            logger.error("Wikimedia returned 403 Forbidden. Ensure compliant User-Agent and throttle settings.")
        resp.raise_for_status()
        return resp


async def wiki_search(query: str, limit: int = 5, lang: str = "en") -> list[dict]:
    """
    Search Wikipedia and return ranked candidate pages.

    Each result contains: title, pageid, snippet, url, source.
    """

    try:
        async with httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=1, max_connections=5)) as client:
            # Prefer REST cached search interface
            resp = await _get_with_backoff(client, _rest_search_url(lang), params={"q": query, "limit": max(1, min(limit, 5))})
            data = resp.json()

        items = data.get("pages", [])
        results: list[dict] = []
        for item in items:
            title = item.get("title", "")
            pageid = item.get("id")
            snippet = _clean_snippet(item.get("excerpt", ""))
            results.append({
                "title": title,
                "pageid": pageid,
                "snippet": snippet,
                "url": _page_url_from_title(title),
                "source": "Wikipedia",
            })

        if results:
            sample = ", ".join(r.get("title", "") for r in results[:3])
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

    try:
        async with httpx.AsyncClient(limits=httpx.Limits(max_keepalive_connections=1, max_connections=5)) as client:
            resolved_title = title
            # Prefer REST summary when title is available
            if resolved_title:
                resp = await _get_with_backoff(client, _rest_summary_url(resolved_title, lang))
                data = resp.json()
                page_url = data.get("content_urls", {}).get("desktop", {}).get("page") or _page_url_from_title(resolved_title)
                result = {
                    "title": data.get("title", resolved_title),
                    "pageid": data.get("pageid"),
                    "extract": (data.get("extract") or "").strip(),
                    "url": page_url,
                    "source": "Wikipedia",
                }
                return result
            # Fallback to Action API if only pageid is given
            page_param = {"pageids": str(pageid)}
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
            resp = await _get_with_backoff(client, _wiki_base_url(lang), params=params)
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                logger.warning("wiki_get_page found no pages: title=%r pageid=%s", title, pageid)
                return None
            page = next(iter(pages.values()))
            if not page or int(page.get("pageid", -1)) == -1:
                logger.warning("wiki_get_page returned invalid page: title=%r pageid=%s", title, pageid)
                return None
            resolved_title = page.get("title")
            page_url = page.get("fullurl") or _page_url_from_title(resolved_title or "")
            result = {
                "title": resolved_title,
                "pageid": page.get("pageid"),
                "extract": (page.get("extract") or "").strip(),
                "url": page_url,
                "source": "Wikipedia",
            }
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
        details = await wiki_get_page(title=candidate.get("title"), lang=lang) if candidate.get("title") else (
            await wiki_get_page(pageid=pageid, lang=lang) if pageid is not None else None
        )
        enriched.append({
            **candidate,
            "extract": details.get("extract") if details else "",
        })
    return enriched
