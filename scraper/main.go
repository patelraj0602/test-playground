package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"strings"

	"github.com/gocolly/colly/v2"
)

type ScrapedData struct {
	URL     string   `json:"url"`
	Title   string   `json:"title"`
	Links   []string `json:"links"`
	Headers []string `json:"headers"`
}

func main() {
	url := flag.String("url", "", "URL to scrape")
	outputJSON := flag.Bool("json", false, "Output results as JSON")
	flag.Parse()

	if *url == "" {
		log.Fatal("Please provide a URL using -url flag")
	}

	data := scrape(*url)

	if *outputJSON {
		jsonOutput, err := json.MarshalIndent(data, "", "  ")
		if err != nil {
			log.Fatal("Error marshaling JSON:", err)
		}
		fmt.Println(string(jsonOutput))
	} else {
		printResults(data)
	}
}

func scrape(url string) ScrapedData {
	data := ScrapedData{
		URL:     url,
		Links:   []string{},
		Headers: []string{},
	}

	c := colly.NewCollector(
		colly.MaxDepth(1),
	)

	c.OnHTML("title", func(e *colly.HTMLElement) {
		data.Title = strings.TrimSpace(e.Text)
	})

	c.OnHTML("a[href]", func(e *colly.HTMLElement) {
		link := e.Attr("href")
		if link != "" && !strings.HasPrefix(link, "#") {
			data.Links = append(data.Links, link)
		}
	})

	c.OnHTML("h1, h2, h3", func(e *colly.HTMLElement) {
		text := strings.TrimSpace(e.Text)
		if text != "" {
			data.Headers = append(data.Headers, text)
		}
	})

	c.OnRequest(func(r *colly.Request) {
		log.Println("Visiting:", r.URL.String())
	})

	c.OnError(func(r *colly.Response, err error) {
		log.Println("Error:", err)
	})

	err := c.Visit(url)
	if err != nil {
		log.Println("Failed to visit URL:", err)
	}

	return data
}

func printResults(data ScrapedData) {
	fmt.Println("=== Scrape Results ===")
	fmt.Println("URL:", data.URL)
	fmt.Println("Title:", data.Title)

	fmt.Println("\n--- Headers ---")
	for i, h := range data.Headers {
		if i >= 10 {
			fmt.Printf("... and %d more\n", len(data.Headers)-10)
			break
		}
		fmt.Println("-", h)
	}

	fmt.Println("\n--- Links ---")
	for i, link := range data.Links {
		if i >= 10 {
			fmt.Printf("... and %d more\n", len(data.Links)-10)
			break
		}
		fmt.Println("-", link)
	}
}
