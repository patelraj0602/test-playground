"""Web scraper library for extracting page metadata from URLs.

This module provides a Python implementation of the web scraper, mirroring and
extending the functionality of the companion Go scraper. It extracts titles,
headers, links, images, and meta tags from web pages using BeautifulSoup.

Example:
    Basic usage::

        from scraper import Scraper

        s = Scraper()
        result = s.scrape("https://example.com")
        print(result.title)
        print(result.links)

    With custom options::

        s = Scraper(timeout=10, user_agent="MyBot/1.0", max_links=50)
        result = s.scrape("https://example.com")
        print(result.to_dict())
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Default HTTP request timeout in seconds
DEFAULT_TIMEOUT: int = 10

# Default user-agent sent with every request
DEFAULT_USER_AGENT: str = (
    "Mozilla/5.0 (compatible; PyScraper/1.0; +https://github.com/test-playground)"
)

# Maximum number of links / headers returned when no explicit limit is set
DEFAULT_MAX_ITEMS: int = 200


@dataclass
class ScrapedData:
    """Container for all data extracted from a single web page.

    Attributes:
        url: The URL that was scraped.
        title: The text content of the ``<title>`` element, or an empty string
            if no title was found.
        headers: List of text content from ``<h1>``, ``<h2>``, and ``<h3>``
            elements, in document order.
        links: List of resolved (absolute) href values from ``<a>`` tags,
            excluding fragment-only anchors.
        images: List of resolved ``src`` attribute values from ``<img>`` tags.
        meta: Mapping of ``name`` -> ``content`` for ``<meta>`` elements that
            carry both attributes (e.g. description, keywords, author).
        status_code: HTTP status code returned by the server.
        error: Human-readable error message if the scrape failed, otherwise
            ``None``.
    """

    url: str
    title: str = ""
    headers: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)
    status_code: int = 0
    error: Optional[str] = None

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a plain-dict representation suitable for JSON serialisation.

        Returns:
            A dictionary containing all scraped fields.
        """
        return {
            "url": self.url,
            "title": self.title,
            "headers": self.headers,
            "links": self.links,
            "images": self.images,
            "meta": self.meta,
            "status_code": self.status_code,
            "error": self.error,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialise the scraped data to a JSON string.

        Args:
            indent: Number of spaces used for indentation. Defaults to 2.

        Returns:
            A formatted JSON string.
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def __str__(self) -> str:  # pragma: no cover
        """Return a human-readable summary of the scraped page."""
        lines = [
            "=== Scrape Results ===",
            f"URL:    {self.url}",
            f"Status: {self.status_code}",
            f"Title:  {self.title}",
        ]
        if self.error:
            lines.append(f"Error:  {self.error}")

        lines.append("\n--- Headers ---")
        for h in self.headers[:10]:
            lines.append(f"  - {h}")
        if len(self.headers) > 10:
            lines.append(f"  ... and {len(self.headers) - 10} more")

        lines.append("\n--- Links ---")
        for link in self.links[:10]:
            lines.append(f"  - {link}")
        if len(self.links) > 10:
            lines.append(f"  ... and {len(self.links) - 10} more")

        lines.append("\n--- Images ---")
        for img in self.images[:5]:
            lines.append(f"  - {img}")
        if len(self.images) > 5:
            lines.append(f"  ... and {len(self.images) - 5} more")

        if self.meta:
            lines.append("\n--- Meta Tags ---")
            for name, content in self.meta.items():
                lines.append(f"  {name}: {content}")

        return "\n".join(lines)


class Scraper:
    """HTTP web scraper that extracts structured data from a URL.

    The scraper fetches the page with ``requests`` and parses the HTML with
    ``BeautifulSoup``.  It is intentionally single-page (depth = 1), matching
    the behaviour of the companion Go implementation.

    Args:
        timeout: Seconds to wait for the server to respond. Defaults to
            ``DEFAULT_TIMEOUT`` (10 s).
        user_agent: ``User-Agent`` header value sent with every request.
            Defaults to ``DEFAULT_USER_AGENT``.
        max_links: Maximum number of links to return per page. ``0`` means
            unlimited. Defaults to ``DEFAULT_MAX_ITEMS``.
        max_headers: Maximum number of header elements to return. ``0`` means
            unlimited. Defaults to ``DEFAULT_MAX_ITEMS``.
        max_images: Maximum number of image URLs to return. ``0`` means
            unlimited. Defaults to ``DEFAULT_MAX_ITEMS``.
        verify_ssl: Whether to verify the server's TLS certificate.
            Defaults to ``True``.

    Example:
        ::

            s = Scraper(timeout=5, max_links=20)
            data = s.scrape("https://example.com")
            print(data)
    """

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        max_links: int = DEFAULT_MAX_ITEMS,
        max_headers: int = DEFAULT_MAX_ITEMS,
        max_images: int = DEFAULT_MAX_ITEMS,
        verify_ssl: bool = True,
    ) -> None:
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_links = max_links
        self.max_headers = max_headers
        self.max_images = max_images
        self.verify_ssl = verify_ssl

        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.user_agent})

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(self, url: str) -> ScrapedData:
        """Fetch *url* and extract structured data from the HTML response.

        Only the initial URL is fetched (depth = 1).  Redirects are followed
        automatically by ``requests``.

        Args:
            url: The fully-qualified URL to scrape (must include scheme).

        Returns:
            A :class:`ScrapedData` instance populated with the extracted
            content.  If the request fails the ``error`` field will be set and
            the other fields will contain empty/default values.

        Raises:
            ValueError: If *url* is empty or lacks a valid scheme.

        Example:
            ::

                data = scraper.scrape("https://example.com")
                print(data.title)
        """
        if not url:
            raise ValueError("url must not be empty")

        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"Unsupported URL scheme '{parsed.scheme}'. Use http or https."
            )

        data = ScrapedData(url=url)

        try:
            logger.info("Fetching %s", url)
            response = self._session.get(
                url, timeout=self.timeout, verify=self.verify_ssl
            )
            data.status_code = response.status_code
            response.raise_for_status()
        except requests.exceptions.Timeout:
            data.error = f"Request timed out after {self.timeout}s"
            logger.warning(data.error)
            return data
        except requests.exceptions.SSLError as exc:
            data.error = f"SSL certificate verification failed: {exc}"
            logger.warning(data.error)
            return data
        except requests.exceptions.ConnectionError as exc:
            data.error = f"Connection error: {exc}"
            logger.warning(data.error)
            return data
        except requests.exceptions.HTTPError as exc:
            data.error = f"HTTP error {data.status_code}: {exc}"
            logger.warning(data.error)
            return data
        except requests.exceptions.RequestException as exc:
            data.error = f"Unexpected request error: {exc}"
            logger.warning(data.error)
            return data

        soup = BeautifulSoup(response.text, "html.parser")
        base_url = self._resolve_base_url(soup, url)

        data.title = self._extract_title(soup)
        data.headers = self._extract_headers(soup)
        data.links = self._extract_links(soup, base_url)
        data.images = self._extract_images(soup, base_url)
        data.meta = self._extract_meta(soup)

        logger.info(
            "Scraped %s — title=%r  links=%d  headers=%d",
            url,
            data.title,
            len(data.links),
            len(data.headers),
        )
        return data

    def close(self) -> None:
        """Close the underlying ``requests.Session`` and release connections.

        It is good practice to call this when the :class:`Scraper` is no longer
        needed, or to use the scraper as a context manager instead.
        """
        self._session.close()

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "Scraper":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Private extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_base_url(soup: BeautifulSoup, page_url: str) -> str:
        """Return the effective base URL for resolving relative links.

        Checks for an explicit ``<base href="…">`` element; falls back to
        *page_url*.

        Args:
            soup: Parsed HTML document.
            page_url: URL of the fetched page, used as the fallback base.

        Returns:
            The base URL string.
        """
        base_tag = soup.find("base", href=True)
        if base_tag:
            return base_tag["href"]  # type: ignore[index]
        return page_url

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        """Extract and clean the page ``<title>`` text.

        Args:
            soup: Parsed HTML document.

        Returns:
            Stripped title string, or an empty string if not present.
        """
        tag = soup.find("title")
        return tag.get_text(strip=True) if tag else ""

    def _extract_headers(self, soup: BeautifulSoup) -> list[str]:
        """Extract text from ``<h1>``, ``<h2>``, and ``<h3>`` elements.

        Args:
            soup: Parsed HTML document.

        Returns:
            List of non-empty, stripped header strings, truncated to
            ``self.max_headers`` entries (unlimited when ``max_headers == 0``).
        """
        headers: list[str] = []
        for tag in soup.find_all(["h1", "h2", "h3"]):
            text = tag.get_text(strip=True)
            if text:
                headers.append(text)
            if self.max_headers and len(headers) >= self.max_headers:
                break
        return headers

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract and resolve absolute URLs from ``<a href="…">`` elements.

        Fragment-only hrefs (``#…``) and empty values are skipped.

        Args:
            soup: Parsed HTML document.
            base_url: Base URL used to resolve relative hrefs.

        Returns:
            Deduplicated list of absolute URLs, truncated to
            ``self.max_links`` entries (unlimited when ``max_links == 0``).
        """
        links: list[str] = []
        seen: set[str] = set()

        for tag in soup.find_all("a", href=True):
            href: str = tag["href"].strip()
            if not href or href.startswith("#"):
                continue
            absolute = urljoin(base_url, href)
            if absolute not in seen:
                seen.add(absolute)
                links.append(absolute)
            if self.max_links and len(links) >= self.max_links:
                break
        return links

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract and resolve absolute URLs from ``<img src="…">`` elements.

        Args:
            soup: Parsed HTML document.
            base_url: Base URL used to resolve relative src paths.

        Returns:
            Deduplicated list of absolute image URLs, truncated to
            ``self.max_images`` entries (unlimited when ``max_images == 0``).
        """
        images: list[str] = []
        seen: set[str] = set()

        for tag in soup.find_all("img", src=True):
            src: str = tag["src"].strip()
            if not src:
                continue
            absolute = urljoin(base_url, src)
            if absolute not in seen:
                seen.add(absolute)
                images.append(absolute)
            if self.max_images and len(images) >= self.max_images:
                break
        return images

    @staticmethod
    def _extract_meta(soup: BeautifulSoup) -> dict[str, str]:
        """Extract ``name`` / ``content`` pairs from ``<meta>`` elements.

        Args:
            soup: Parsed HTML document.

        Returns:
            Dictionary mapping lowercase meta-name to content value.
            Standard tags captured include ``description``, ``keywords``,
            ``author``, ``viewport``, and ``robots``, among others.
        """
        meta: dict[str, str] = {}
        for tag in soup.find_all("meta", attrs={"name": True, "content": True}):
            name: str = tag.get("name", "").strip().lower()
            content: str = tag.get("content", "").strip()
            if name and content:
                meta[name] = content
        return meta
