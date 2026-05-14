import logging
import urllib.parse

import httpx

logger = logging.getLogger(__name__)

WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary"
TIMEOUT = 10.0


async def get_summary(species: str, common_name: str | None = None) -> dict | None:
    """Fetch Wikipedia page summary for a species.

    Falls back to common_name if the species page is missing.
    Returns None if no article is found.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        result = await _fetch_summary(client, species)
        if result is not None:
            return result

        if common_name and common_name.lower() != species.lower():
            logger.info("Falling back to common name lookup: %s", common_name)
            result = await _fetch_summary(client, common_name)
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


def _extract_fields(data: dict) -> dict:
    return {
        "title": data.get("title", ""),
        "description": data.get("description"),
        "extract": data.get("extract"),
        "thumbnail": data.get("thumbnail"),
        "content_urls": data.get("content_urls"),
    }
