import logging
import urllib.parse

import httpx

logger = logging.getLogger(__name__)

WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary"
WIKIPEDIA_SEARCH_API = "https://en.wikipedia.org/w/api.php"
TIMEOUT = 10.0
# Wikipedia requires a descriptive User-Agent or returns 403
HEADERS = {"User-Agent": "Gardener/1.0 (plant-identification-app)"}


def _base_species(name: str) -> str:
    """Strip taxonomic authority from a scientific name.

    'Pongamia pinnata (L.) Pierre' → 'Pongamia pinnata'
    'Rosa canina L.'               → 'Rosa canina'
    """
    # Everything from the first '(' onward is author citation
    base = name.split("(")[0].strip()
    # Also drop a trailing single-token abbreviation like 'L.' or 'Thunb.'
    parts = base.split()
    if len(parts) > 2 and parts[-1].endswith("."):
        base = " ".join(parts[:-1])
    return base


async def get_summary(species: str, common_name: str | None = None) -> dict | None:
    """Fetch Wikipedia page summary for a species.

    Strategy (stops at the first hit):
    1. Direct title lookup with cleaned name (authority stripped)
    2. Direct title lookup with common name
    3. Wikipedia search API with cleaned name (handles model label quirks)
    4. Wikipedia search API with common name
    Returns None if no article is found.
    """
    base = _base_species(species)
    candidates: list[str] = [base]
    if species.lower() != base.lower():
        candidates.append(species)
    if common_name and common_name.lower() not in {s.lower() for s in candidates}:
        candidates.append(common_name)

    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS) as client:
        for term in candidates:
            result = await _fetch_summary(client, term)
            if result is not None:
                return result

        for term in candidates:
            result = await _search_and_fetch(client, term)
            if result is not None:
                return result

    logger.info("No Wikipedia article found for: %s", species)
    return None


async def _fetch_summary(client: httpx.AsyncClient, title: str) -> dict | None:
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = f"{WIKIPEDIA_API}/{encoded}"
    try:
        response = await client.get(url, follow_redirects=True)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return _extract_fields(data)
    except httpx.HTTPStatusError as exc:
        logger.warning("Wikipedia HTTP error for '%s': %s", title, exc)
        return None
    except httpx.RequestError as exc:
        logger.error("Wikipedia request error for '%s': %s", title, exc)
        return None


async def _search_and_fetch(client: httpx.AsyncClient, query: str) -> dict | None:
    """Use the Wikipedia search API to find the closest article, then fetch its summary."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": 1,
        "srprop": "",
    }
    try:
        response = await client.get(WIKIPEDIA_SEARCH_API, params=params)
        response.raise_for_status()
        results = response.json().get("query", {}).get("search", [])
        if not results:
            return None
        title = results[0]["title"]
        logger.info("Wikipedia search '%s' → '%s'", query, title)
        return await _fetch_summary(client, title)
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        logger.warning("Wikipedia search error for '%s': %s", query, exc)
        return None


def _extract_fields(data: dict) -> dict:
    return {
        "title": data.get("title", ""),
        "description": data.get("description"),
        "extract": data.get("extract"),
        "thumbnail": data.get("thumbnail"),
        "content_urls": data.get("content_urls"),
    }
