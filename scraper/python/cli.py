"""Command-line interface for the Python web scraper.

This module provides a ``scrape`` entry point that mirrors the CLI flags of the
companion Go implementation while adding Python-specific options such as
verbose logging, output file redirection, and image/meta extraction toggles.

Usage::

    python -m scraper.python.cli -url https://example.com
    python -m scraper.python.cli -url https://example.com -json
    python -m scraper.python.cli -url https://example.com -json -output results.json

Or, after installation via pip::

    pyscraper -url https://example.com
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .scraper import DEFAULT_MAX_ITEMS, DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, Scraper


def _build_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser for the CLI.

    Returns:
        A configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        prog="pyscraper",
        description=(
            "Python web scraper — extract title, headers, links, images, "
            "and meta tags from a URL."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pyscraper -url https://example.com
  pyscraper -url https://example.com -json
  pyscraper -url https://example.com -json -output out.json
  pyscraper -url https://example.com --max-links 50 --verbose
        """,
    )

    # ---------- required ----------
    parser.add_argument(
        "-url",
        required=True,
        metavar="URL",
        help="Fully-qualified URL to scrape (http or https).",
    )

    # ---------- output format ----------
    output_group = parser.add_argument_group("output options")
    output_group.add_argument(
        "-json",
        action="store_true",
        dest="json",
        default=False,
        help="Print results as indented JSON (default: human-readable text).",
    )
    output_group.add_argument(
        "-output",
        metavar="FILE",
        dest="output",
        default=None,
        help=(
            "Write output to FILE instead of stdout. "
            "The file is UTF-8 encoded and created/overwritten."
        ),
    )

    # ---------- scraper behaviour ----------
    scraper_group = parser.add_argument_group("scraper options")
    scraper_group.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        metavar="SECONDS",
        help=f"HTTP request timeout in seconds (default: {DEFAULT_TIMEOUT}).",
    )
    scraper_group.add_argument(
        "--user-agent",
        default=DEFAULT_USER_AGENT,
        metavar="UA",
        help="User-Agent header to send with requests.",
    )
    scraper_group.add_argument(
        "--max-links",
        type=int,
        default=DEFAULT_MAX_ITEMS,
        metavar="N",
        help=(
            f"Maximum number of links to include in output "
            f"(0 = unlimited, default: {DEFAULT_MAX_ITEMS})."
        ),
    )
    scraper_group.add_argument(
        "--max-headers",
        type=int,
        default=DEFAULT_MAX_ITEMS,
        metavar="N",
        help=(
            f"Maximum number of header elements to include "
            f"(0 = unlimited, default: {DEFAULT_MAX_ITEMS})."
        ),
    )
    scraper_group.add_argument(
        "--max-images",
        type=int,
        default=DEFAULT_MAX_ITEMS,
        metavar="N",
        help=(
            f"Maximum number of image URLs to include "
            f"(0 = unlimited, default: {DEFAULT_MAX_ITEMS})."
        ),
    )
    scraper_group.add_argument(
        "--no-verify-ssl",
        action="store_false",
        dest="verify_ssl",
        default=True,
        help="Disable TLS certificate verification (not recommended).",
    )

    # ---------- diagnostics ----------
    diag_group = parser.add_argument_group("diagnostic options")
    diag_group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose logging to stderr.",
    )

    return parser


def _configure_logging(verbose: bool) -> None:
    """Configure root logger based on verbosity flag.

    Args:
        verbose: When ``True`` sets the log level to DEBUG; otherwise Warning.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``pyscraper`` CLI command.

    Parses *argv* (defaults to ``sys.argv[1:]``), runs the scraper, and writes
    the output either to stdout or to the file specified by ``-output``.

    Args:
        argv: Argument list to parse.  ``None`` means use ``sys.argv[1:]``.

    Returns:
        Exit code: ``0`` on success, ``1`` on scrape error or I/O failure.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    _configure_logging(args.verbose)

    scraper = Scraper(
        timeout=args.timeout,
        user_agent=args.user_agent,
        max_links=args.max_links,
        max_headers=args.max_headers,
        max_images=args.max_images,
        verify_ssl=args.verify_ssl,
    )

    try:
        data = scraper.scrape(args.url)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        scraper.close()

    # Build output string
    if args.json:
        output_text = data.to_json()
    else:
        output_text = str(data)

    # Write to file or stdout
    if args.output:
        try:
            path = Path(args.output)
            path.write_text(output_text, encoding="utf-8")
            print(f"Output written to {path}", file=sys.stderr)
        except OSError as exc:
            print(f"Error writing to '{args.output}': {exc}", file=sys.stderr)
            return 1
    else:
        print(output_text)

    # Signal failure if the scrape itself reported an error
    return 1 if data.error else 0


if __name__ == "__main__":
    sys.exit(main())
