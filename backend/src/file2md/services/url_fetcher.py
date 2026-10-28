"""Secure URL fetching service with SSRF protection and content extraction."""

import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from fastapi import HTTPException, status

from file2md.config import get_settings
from file2md.services.validators import sanitize_filename

logger = structlog.get_logger()

# Maximum allowed download size for web pages (10 MB)
MAX_URL_CONTENT_BYTES: int = 10 * 1024 * 1024
MAX_REDIRECT_HOPS: int = 5
REQUEST_TIMEOUT_SECONDS: float = 15.0


def validate_url_safety(url_str: str) -> str:
    """Validate URL protocol and ensure destination does not resolve to local IPs."""
    if not url_str or not url_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL parameter cannot be empty.",
        )

    parsed = urlparse(url_str.strip())
    if parsed.scheme.lower() not in {"http", "https"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported URL scheme '{parsed.scheme}'. "
                "Only HTTP and HTTPS are allowed."
            ),
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL: Missing hostname.",
        )

    # Resolve hostname to IP addresses and verify they are strictly public
    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve host '{hostname}'.",
        ) from exc

    for entry in addr_info:
        ip_str = entry[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                logger.warning("ssrf_blocked", hostname=hostname, ip=ip_str)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Access to private or local network addresses is prohibited."
                    ),
                )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid IP address resolved for host '{hostname}'.",
            ) from exc

    return url_str.strip()


def extract_page_title(html: str, fallback: str) -> str:
    """Extract <title> content from HTML or fallback to URL slug."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        title = match.group(1).strip()
        title = re.sub(r"\s+", " ", title)
        if title:
            return sanitize_filename(f"{title}.html")
    return sanitize_filename(f"{fallback}.html")


async def fetch_url_content(target_url: str) -> tuple[str, str]:
    """Safely fetch HTML content from verified URL with continuous SSRF checks.

    Returns:
        tuple of (html_text, suggested_filename)
    """
    settings = get_settings()
    max_bytes = min(settings.max_upload_size_bytes, MAX_URL_CONTENT_BYTES)

    current_url = validate_url_safety(target_url)
    headers = {
        "User-Agent": "file2MD-Converter/1.0 (+https://file2md.vajapravin.me)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=False,
    ) as client:
        redirects = 0
        while redirects <= MAX_REDIRECT_HOPS:
            try:
                response = await client.get(current_url, headers=headers)
            except httpx.TimeoutException as exc:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"Request to '{current_url}' timed out.",
                ) from exc
            except httpx.RequestError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to fetch content from URL: {exc}",
                ) from exc

            # Handle redirects safely
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    break
                current_url = validate_url_safety(urljoin(current_url, location))
                redirects += 1
                continue

            # Non-redirect response: check HTTP status
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Target URL returned HTTP status {response.status_code}: "
                        f"{response.reason_phrase}"
                    ),
                )

            # Check content length
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) > max_bytes:
                max_mb = max_bytes // (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Web page size exceeds maximum limit of {max_mb} MB.",
                )

            body_bytes = response.content
            if len(body_bytes) > max_bytes:
                max_mb = max_bytes // (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Web page size exceeds maximum limit of {max_mb} MB.",
                )

            if not body_bytes:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Fetched URL returned empty content.",
                )

            html_text = response.text
            parsed = urlparse(current_url)
            fallback_slug = parsed.hostname or "webpage"
            if parsed.path and parsed.path.strip("/"):
                path_slug = parsed.path.strip("/").replace("/", "_")
                fallback_slug = f"{fallback_slug}_{path_slug}"

            suggested_name = extract_page_title(html_text, fallback_slug)
            return html_text, suggested_name

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many redirects encountered while fetching URL.",
        )
