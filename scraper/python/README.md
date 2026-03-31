# Python Web Scraper

A Python companion to the [Go scraper](../README.md) that extracts structured
data from web pages.  It uses [Requests](https://requests.readthedocs.io/) for
HTTP and [BeautifulSoup 4](https://www.crummy.com/software/BeautifulSoup/) for
HTML parsing.

## Features

| Feature | Go scraper | Python scraper |
|---------|-----------|----------------|
| Page title | ✅ | ✅ |
| Headers (h1–h3) | ✅ | ✅ |
| Links | ✅ | ✅ |
| Images | ❌ | ✅ |
| Meta tags | ❌ | ✅ |
| JSON output | ✅ | ✅ |
| Output to file | ❌ | ✅ |
| Configurable timeout | ❌ | ✅ |
| Custom User-Agent | ❌ | ✅ |
| Usable as a library | ❌ | ✅ |

## Installation

```bash
# Install dependencies only
pip install -r requirements.txt

# Or install as a package (adds the `pyscraper` command to your PATH)
pip install .
```

Python 3.9 or later is required.

## CLI Usage

The `pyscraper` CLI mirrors the flags of the Go implementation:

```bash
# Human-readable output
pyscraper -url https://example.com

# JSON output
pyscraper -url https://example.com -json

# Write JSON to a file
pyscraper -url https://example.com -json -output results.json

# Limit links and enable verbose logging
pyscraper -url https://example.com --max-links 20 --verbose
```

### All flags

| Flag | Default | Description |
|------|---------|-------------|
| `-url URL` | *(required)* | URL to scrape |
| `-json` | `false` | Output as JSON |
| `-output FILE` | stdout | Write output to a file |
| `--timeout N` | `10` | HTTP timeout in seconds |
| `--user-agent UA` | built-in | Custom User-Agent string |
| `--max-links N` | `200` | Max links returned (0 = unlimited) |
| `--max-headers N` | `200` | Max headers returned (0 = unlimited) |
| `--max-images N` | `200` | Max images returned (0 = unlimited) |
| `--no-verify-ssl` | `false` | Disable TLS verification |
| `--verbose` / `-v` | `false` | Verbose logging to stderr |

### Example output

```
=== Scrape Results ===
URL:    https://example.com
Status: 200
Title:  Example Domain

--- Headers ---
  - Example Domain

--- Links ---
  - https://www.iana.org/domains/example

--- Images ---

--- Meta Tags ---
```

### Example JSON output

```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "headers": ["Example Domain"],
  "links": ["https://www.iana.org/domains/example"],
  "images": [],
  "meta": {},
  "status_code": 200,
  "error": null
}
```

## Library Usage

```python
from scraper.python import Scraper, ScrapedData

# Use as a context manager (recommended — closes the HTTP session automatically)
with Scraper(timeout=5, max_links=50) as s:
    data: ScrapedData = s.scrape("https://example.com")

print(data.title)          # "Example Domain"
print(data.links)          # ["https://www.iana.org/domains/example"]
print(data.headers)        # ["Example Domain"]
print(data.images)         # []
print(data.meta)           # {}
print(data.status_code)    # 200
print(data.error)          # None

# Serialise to JSON string
print(data.to_json())

# Serialise to plain dict (e.g. for further processing)
d = data.to_dict()
```

### Scraper options

```python
from scraper.python import Scraper

s = Scraper(
    timeout=10,             # seconds before request times out
    user_agent="MyBot/1.0", # custom User-Agent header
    max_links=100,          # cap the number of links (0 = no cap)
    max_headers=50,         # cap the number of headers
    max_images=50,          # cap the number of images
    verify_ssl=True,        # set False to skip TLS cert verification
)
```

## Running without installing

```bash
cd /path/to/repo
pip install requests beautifulsoup4 lxml
python -m scraper.python.cli -url https://example.com
```

## Project structure

```
scraper/python/
├── __init__.py       # Package exports
├── scraper.py        # Core Scraper class and ScrapedData dataclass
├── cli.py            # argparse CLI (pyscraper entry point)
├── requirements.txt  # Runtime dependencies
├── pyproject.toml    # PEP 517/518 build metadata
└── README.md         # This file
```
