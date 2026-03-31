"""Hello World module.

A simple introductory Python module that demonstrates best practices
including type hints, Google-style docstrings, error handling, and a
CLI entry point.

Example:
    Run directly::

        $ python hello_world.py
        Hello, World!

    Run with a custom name::

        $ python hello_world.py --name Alice
        Hello, Alice!
"""

import argparse
import sys


def greet(name: str = "World") -> str:
    """Return a personalised greeting string.

    Args:
        name: The name to greet. Defaults to ``"World"``.

    Returns:
        A greeting string in the form ``"Hello, <name>!"``.

    Raises:
        ValueError: If *name* is an empty string.

    Example:
        >>> greet()
        'Hello, World!'
        >>> greet("Alice")
        'Hello, Alice!'
    """
    if not name or not name.strip():
        raise ValueError("name must be a non-empty string")
    return f"Hello, {name.strip()}!"


def say_hello(name: str = "World") -> None:
    """Print a personalised greeting to stdout.

    This is a thin wrapper around :func:`greet` that prints the result
    rather than returning it — useful as a top-level helper.

    Args:
        name: The name to greet. Defaults to ``"World"``.

    Example:
        >>> say_hello()
        Hello, World!
        >>> say_hello("Bob")
        Hello, Bob!
    """
    print(greet(name))


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        A configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        description="Print a friendly Hello World greeting."
    )
    parser.add_argument(
        "--name",
        default="World",
        help="Name to greet (default: %(default)s)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the hello-world CLI.

    Parses command-line arguments and prints a greeting.

    Args:
        argv: Argument list to parse. Defaults to ``sys.argv[1:]`` when
            ``None``.

    Returns:
        Exit code: ``0`` on success, ``1`` on error.

    Example:
        >>> main(["--name", "World"])
        Hello, World!
        0
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        say_hello(args.name)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
