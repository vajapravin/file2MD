"""Unit tests for URL validation, SSRF protection, and web content fetching."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from fastapi import HTTPException

from file2md.services.url_fetcher import (
    extract_page_title,
    fetch_url_content,
    validate_url_safety,
)


def test_validate_url_safety_rejects_empty_or_non_http() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_url_safety("")
    assert exc.value.status_code == 400
    assert "empty" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        validate_url_safety("ftp://example.com/file.txt")
    assert exc.value.status_code == 400
    assert "Unsupported URL scheme" in exc.value.detail

    with pytest.raises(HTTPException) as exc:
        validate_url_safety("file:///etc/passwd")
    assert exc.value.status_code == 400


@pytest.mark.parametrize(
    "forbidden_host,resolved_ip",
    [
        ("localhost", "127.0.0.1"),
        ("127.0.0.1", "127.0.0.1"),
        ("10.0.0.5", "10.0.0.5"),
        ("192.168.1.100", "192.168.1.100"),
        ("172.16.0.1", "172.16.0.1"),
        ("169.254.169.254", "169.254.169.254"),
        ("internal.corp", "10.10.10.10"),
    ],
)
def test_validate_url_safety_blocks_ssrf(forbidden_host: str, resolved_ip: str) -> None:
    with patch(
        "socket.getaddrinfo",
        return_value=[(None, None, None, None, (resolved_ip, 80))],
    ):
        with pytest.raises(HTTPException) as exc:
            validate_url_safety(f"http://{forbidden_host}/api")
        assert exc.value.status_code == 400
        detail = exc.value.detail
        assert "Access to private or local network addresses is prohibited" in detail


def test_validate_url_safety_accepts_public_domain() -> None:
    with patch(
        "socket.getaddrinfo",
        return_value=[(None, None, None, None, ("93.184.216.34", 443))],
    ):
        url = "https://example.com/docs"
        assert validate_url_safety(url) == url


def test_extract_page_title() -> None:
    html = (
        "<html><head><title>Clean Architecture Guide</title></head>"
        "<body>...</body></html>"
    )
    assert extract_page_title(html, "fallback") == "Clean Architecture Guide.html"

    empty_title = "<html><head><title>   </title></head></html>"
    assert extract_page_title(empty_title, "my_slug") == "my_slug.html"


@pytest.mark.asyncio
async def test_fetch_url_content_success() -> None:
    mock_html = (
        "<!DOCTYPE html><html><head><title>My Article</title></head>"
        "<body><h1>Heading</h1><p>Paragraph content.</p></body></html>"
    )
    mock_response = httpx.Response(
        status_code=200,
        text=mock_html,
        headers={"content-type": "text/html; charset=utf-8"},
        request=httpx.Request("GET", "https://example.com/article"),
    )

    with (
        patch(
            "file2md.services.url_fetcher.validate_url_safety",
            side_effect=lambda u: u,
        ),
        patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.return_value = mock_response

        html_text, filename = await fetch_url_content("https://example.com/article")
        assert "<h1>Heading</h1>" in html_text
        assert filename == "My Article.html"


@pytest.mark.asyncio
async def test_fetch_url_content_follows_redirects() -> None:
    redirect_response = httpx.Response(
        status_code=301,
        headers={"location": "https://example.com/target"},
        request=httpx.Request("GET", "https://example.com/source"),
    )
    final_response = httpx.Response(
        status_code=200,
        text=(
            "<html><head><title>Redirect Target</title></head>"
            "<body>Target</body></html>"
        ),
        request=httpx.Request("GET", "https://example.com/target"),
    )

    with (
        patch(
            "file2md.services.url_fetcher.validate_url_safety",
            side_effect=lambda u: u,
        ),
        patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.side_effect = [redirect_response, final_response]

        html_text, filename = await fetch_url_content("https://example.com/source")
        assert "Target" in html_text
        assert filename == "Redirect Target.html"
        assert mock_get.call_count == 2
