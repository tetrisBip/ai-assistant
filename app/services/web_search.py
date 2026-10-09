# app/services/web_search.py
"""
Поиск в интернете. Провайдер выбирается в .env (SEARCH_PROVIDER):
  * tavily      — Tavily API (рекомендуется, заточен под LLM)
  * brave       — Brave Search API
  * duckduckgo  — ddgs, без ключа (нестабильно)

Автодополнение года: если запрос про "свежее" и в нём нет текущего года —
подставляем текущий год. Лечит проблему, когда LLM тянет годы
из своих тренировочных данных.
"""
import httpx

from app.config import settings
from app.utils.logger import log
from app.utils.time_utils import now


FRESH_KEYWORDS = (
    "release", "выйдет", "выход", "новый", "новая", "новое", "новые",
    "latest", "upcoming", "recent", "soon", "скоро", "анонс",
    "announce", "news", "новости", "последн",
)


def _augment_with_year(query: str) -> str:
    """
    Если запрос про свежее и в нём нет текущего года — добавляем год.
    Возвращает изменённый (или исходный) запрос.
    """
    current_year = str(now().year)
    if current_year in query:
        return query
    lower = query.lower()
    if any(kw in lower for kw in FRESH_KEYWORDS):
        new_q = f"{query} {current_year}"
        log.info(f"web_search: augmented query → {new_q!r}")
        return new_q
    return query


def search(query: str, max_results: int = 5) -> list[dict]:
    """
    Возвращает [{"title":..., "url":..., "snippet":...}, ...]
    Возможно, первый элемент — краткий ответ (Tavily).
    Синхронная — вызывается через asyncio.to_thread.
    """
    query = _augment_with_year(query)

    provider = (settings.search_provider or "tavily").lower()

    if provider == "tavily" and settings.tavily_api_key:
        return _search_tavily(query, max_results)

    if provider == "brave" and settings.brave_api_key:
        return _search_brave(query, max_results)

    log.warning(f"provider '{provider}' not configured, falling back to ddg")
    return _search_ddg(query, max_results)


def _search_tavily(query: str, max_results: int) -> list[dict]:
    proxy = settings.llm_proxy or None
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic",
        "include_answer": True,
        "include_raw_content": False,
    }

    try:
        with httpx.Client(proxy=proxy, timeout=30) as client:
            r = client.post("https://api.tavily.com/search", json=payload)
        if r.status_code != 200:
            log.warning(f"tavily HTTP {r.status_code}: {r.text[:200]}")
            return []
        data = r.json()
    except Exception as e:
        log.warning(f"tavily search failed: {e}")
        return []

    out: list[dict] = []

    answer = data.get("answer")
    if answer:
        out.append({
            "title": "Краткий ответ",
            "url": "",
            "snippet": answer,
        })

    for x in data.get("results", []):
        out.append({
            "title": x.get("title", ""),
            "url": x.get("url", ""),
            "snippet": (x.get("content", "") or "")[:500],
        })

    return out


def _search_brave(query: str, max_results: int) -> list[dict]:
    proxy = settings.llm_proxy or None
    try:
        with httpx.Client(proxy=proxy, timeout=20) as client:
            r = client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": min(max_results, 20)},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": settings.brave_api_key,
                },
            )
        if r.status_code != 200:
            log.warning(f"brave HTTP {r.status_code}: {r.text[:200]}")
            return []
        data = r.json()
    except Exception as e:
        log.warning(f"brave search failed: {e}")
        return []

    return [
        {
            "title": x.get("title", ""),
            "url": x.get("url", ""),
            "snippet": x.get("description", ""),
        }
        for x in data.get("web", {}).get("results", [])
    ]


def _search_ddg(query: str, max_results: int) -> list[dict]:
    try:
        from ddgs import DDGS
    except ImportError:
        log.warning("ddgs not installed")
        return []

    proxy = settings.llm_proxy or None
    try:
        with DDGS(proxy=proxy, timeout=20) as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        log.warning(f"ddg search failed: {e}")
        return []

    return [
        {
            "title": r.get("title", ""),
            "url": r.get("href", "") or r.get("url", ""),
            "snippet": r.get("body", "") or r.get("snippet", ""),
        }
        for r in results
    ]


def format_results(results: list[dict]) -> str:
    if not results:
        return "(ничего не найдено)"
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        block = f"{i}. {title}"
        if url:
            block += f"\n   {url}"
        if snippet:
            block += f"\n   {snippet}"
        lines.append(block)
    return "\n\n".join(lines)