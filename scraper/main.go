// Package main implements a command-line web scraper that extracts the page
// title, header tags, and hyperlinks from a given URL. Results can be printed
// as human-readable text or as JSON.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"strings"

	"github.com/gocolly/colly/v2"
)

// maxDisplayItems is the maximum number of headers or links shown in the
// plain-text output before the "… and N more" truncation message is printed.
const maxDisplayItems = 10

// ScrapedData holds the data collected from a single page visit.
type ScrapedData struct {
	URL     string   `json:"url"`
	Title   string   `json:"title"`
	Links   []string `json:"links"`
	Headers []string `json:"headers"`
}

// --- Entry point -----------------------------------------------------------

func main() {
	url := flag.String("url", "", "URL to scrape (required)")
	outputJSON := flag.Bool("json", false, "Print results as JSON instead of plain text")
	flag.Parse()

	if *url == "" {
		log.Fatal("error: please provide a URL with the -url flag")
	}

	data, err := scrape(*url)
	if err != nil {
		log.Fatal("error scraping URL:", err)
	}

	if *outputJSON {
		printJSON(data)
	} else {
		printText(data)
	}
}

// --- Scraping --------------------------------------------------------------

// scrape visits the given URL and returns the page title, all non-anchor
// links, and the text content of h1/h2/h3 elements.
//
// It only crawls a single page (MaxDepth = 1) and never follows links to
// other domains.
func scrape(url string) (ScrapedData, error) {
	data := ScrapedData{
		URL:     url,
		Links:   []string{},
		Headers: []string{},
	}

	c := colly.NewCollector(
		colly.MaxDepth(1),
	)

	registerHandlers(c, &data)

	if err := c.Visit(url); err != nil {
		return ScrapedData{}, fmt.Errorf("visiting %q: %w", url, err)
	}

	return data, nil
}

// registerHandlers attaches all colly event handlers to the collector.
// Separating handler registration from scrape() keeps each piece small and
// independently testable.
func registerHandlers(c *colly.Collector, data *ScrapedData) {
	// Capture the page <title>.
	c.OnHTML("title", func(e *colly.HTMLElement) {
		data.Title = strings.TrimSpace(e.Text)
	})

	// Collect every hyperlink that is not a same-page anchor (#…).
	c.OnHTML("a[href]", func(e *colly.HTMLElement) {
		link := e.Attr("href")
		if link != "" && !strings.HasPrefix(link, "#") {
			data.Links = append(data.Links, link)
		}
	})

	// Collect text from the three most-prominent heading levels.
	c.OnHTML("h1, h2, h3", func(e *colly.HTMLElement) {
		if text := strings.TrimSpace(e.Text); text != "" {
			data.Headers = append(data.Headers, text)
		}
	})

	// Log each outgoing request so the user can see progress.
	c.OnRequest(func(r *colly.Request) {
		log.Println("visiting:", r.URL.String())
	})

	// Log HTTP or network errors without aborting the whole run.
	c.OnError(func(_ *colly.Response, err error) {
		log.Println("request error:", err)
	})
}

// --- Output ----------------------------------------------------------------

// printText prints a human-readable summary of the scraped data to stdout.
// Each list section shows at most maxDisplayItems entries, followed by a
// count of any remaining items.
func printText(data ScrapedData) {
	fmt.Println("=== Scrape Results ===")
	fmt.Println("URL:  ", data.URL)
	fmt.Println("Title:", data.Title)

	fmt.Println("\n--- Headers ---")
	printList(data.Headers)

	fmt.Println("\n--- Links ---")
	printList(data.Links)
}

// printList prints up to maxDisplayItems entries from items, then a trailing
// summary line if more entries were truncated.
func printList(items []string) {
	limit := min(len(items), maxDisplayItems)
	for _, item := range items[:limit] {
		fmt.Println(" -", item)
	}

	if remaining := len(items) - limit; remaining > 0 {
		fmt.Printf("  … and %d more\n", remaining)
	}
}

// printJSON serialises data as indented JSON and writes it to stdout.
// The program exits with a fatal error if marshalling fails (which should
// never happen for this struct, but is handled for safety).
func printJSON(data ScrapedData) {
	output, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		log.Fatal("error marshalling JSON:", err)
	}
	fmt.Println(string(output))
}

// --- Helpers ---------------------------------------------------------------

// min returns the smaller of two integers.
// (Replace with the built-in min() once the project upgrades to Go 1.21+.)
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
