# test-playground

A collection of web-scraper implementations in multiple languages.

## Implementations

| Language | Directory | Description |
|----------|-----------|-------------|
| Go | [`scraper/`](scraper/) | Original scraper using the Colly library |
| Python | [`scraper/python/`](scraper/python/) | Python scraper using Requests + BeautifulSoup |

## Quick start

### Go

```bash
cd scraper
go mod tidy
go run main.go -url https://example.com
go run main.go -url https://example.com -json
```

### Python

```bash
cd scraper/python
pip install -r requirements.txt
python -m scraper.python.cli -url https://example.com
python -m scraper.python.cli -url https://example.com -json
```

See each sub-directory for a full README with all available options.
