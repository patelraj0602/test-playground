"""Python web scraper package.

This package provides :class:`~scraper.python.scraper.Scraper` for extracting
structured data from web pages, and a :mod:`~scraper.python.cli` module that
exposes the ``pyscraper`` command-line tool.

Quick start::

    from scraper.python import Scraper

    with Scraper() as s:
        data = s.scrape("https://example.com")
        print(data.title)
        print(data.to_json())
"""

from .scraper import DEFAULT_MAX_ITEMS, DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, ScrapedData, Scraper

__all__ = [
    "Scraper",
    "ScrapedData",
    "DEFAULT_TIMEOUT",
    "DEFAULT_USER_AGENT",
    "DEFAULT_MAX_ITEMS",
]

__version__ = "1.0.0"
