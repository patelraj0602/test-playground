# Go Web Scraper

A simple web scraper built in Go using the [Colly](https://github.com/gocolly/colly) library.

## Features

- Scrape page title
- Extract all links from a page
- Extract headers (h1, h2, h3)
- Output as plain text or JSON

## Installation

```bash
go mod tidy
```

## Usage

### Basic usage
```bash
go run main.go -url https://example.com
```

### JSON output
```bash
go run main.go -url https://example.com -json
```

### Build and run
```bash
go build -o scraper
./scraper -url https://example.com
```

## Example Output

```
=== Scrape Results ===
URL: https://example.com
Title: Example Domain

--- Headers ---
- Example Domain

--- Links ---
- https://www.iana.org/domains/example
```

## JSON Output Example

```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "links": ["https://www.iana.org/domains/example"],
  "headers": ["Example Domain"]
}
```
