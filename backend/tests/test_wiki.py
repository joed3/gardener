from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import wiki


@pytest.mark.asyncio
async def test_get_summary_success():
    mock_data = {
        "title": "Monstera deliciosa",
        "description": "Species of flowering plant",
        "extract": "Monstera deliciosa, the Swiss cheese plant...",
        "thumbnail": {"source": "https://example.com/img.jpg", "width": 320, "height": 427},
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Monstera_deliciosa"}},
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        result = await wiki.get_summary("Monstera deliciosa")

    assert result is not None
    assert result["title"] == "Monstera deliciosa"
    assert result["description"] == "Species of flowering plant"
    assert result["extract"] is not None


@pytest.mark.asyncio
async def test_get_summary_404_fallback_to_common_name():
    not_found_response = MagicMock()
    not_found_response.status_code = 404

    found_response = MagicMock()
    found_response.status_code = 200
    found_response.json.return_value = {
        "title": "Swiss Cheese Plant",
        "description": "Popular houseplant",
        "extract": "The Swiss cheese plant is...",
        "thumbnail": None,
        "content_urls": None,
    }
    found_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=[not_found_response, found_response])
        mock_client_class.return_value = mock_client

        result = await wiki.get_summary("Rare species xyz", common_name="Swiss Cheese Plant")

    assert result is not None
    assert result["title"] == "Swiss Cheese Plant"


@pytest.mark.asyncio
async def test_get_summary_all_404_returns_none():
    not_found = MagicMock()
    not_found.status_code = 404

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=not_found)
        mock_client_class.return_value = mock_client

        result = await wiki.get_summary("Unknown plant xyz", common_name="Unknown common")

    assert result is None


def test_extract_fields():
    data = {
        "title": "Rosa canina",
        "description": "Dog rose",
        "extract": "Rosa canina is a...",
        "thumbnail": None,
        "content_urls": None,
        "extra_field": "ignored",
    }
    result = wiki._extract_fields(data)
    assert set(result.keys()) == {"title", "description", "extract", "thumbnail", "content_urls"}
    assert result["title"] == "Rosa canina"
    assert "extra_field" not in result
