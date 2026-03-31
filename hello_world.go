// Package main implements a simple Hello World CLI in Go.
//
// This is a direct port of hello_world.py, preserving all behaviour:
//   - Default greeting: "Hello, World!"
//   - Custom name via --name flag
//   - Validation: name must be a non-empty, non-whitespace string
//   - Exit code 0 on success, 1 on error
//
// Usage:
//
//	go run hello_world.go
//	go run hello_world.go --name Alice
//	go run hello_world.go --name ""
package main

import (
	"errors"
	"flag"
	"fmt"
	"os"
	"strings"
)

// generateGreeting returns a personalised greeting string.
//
// It trims surrounding whitespace from name before embedding it.
// An empty or whitespace-only name is rejected with an error.
//
// Parameters:
//
//	name - the name to greet; defaults to "World" when the caller
//	       passes an empty string after trimming is accounted for
//	       by the CLI layer.
//
// Returns:
//
//	A greeting string of the form "Hello, <name>!" and a nil error
//	on success, or an empty string and a non-nil error when name is
//	invalid.
//
// Example:
//
//	greeting, err := generateGreeting("Alice")
//	// greeting == "Hello, Alice!", err == nil
func generateGreeting(name string) (string, error) {
	trimmed := strings.TrimSpace(name)
	if trimmed == "" {
		return "", errors.New("name must be a non-empty string")
	}
	return fmt.Sprintf("Hello, %s!", trimmed), nil
}

// printGreeting writes a personalised greeting to stdout.
//
// It is a thin wrapper around generateGreeting that prints the result
// rather than returning it — useful as a top-level helper.
//
// Parameters:
//
//	name - the name to greet.
//
// Returns:
//
//	An error if name is invalid (empty / whitespace-only), nil otherwise.
func printGreeting(name string) error {
	greeting, err := generateGreeting(name)
	if err != nil {
		return err
	}
	fmt.Println(greeting)
	return nil
}

// createArgumentParser configures and returns a *flag.FlagSet for the CLI.
//
// The returned FlagSet has a single string flag:
//
//	--name   Name to greet (default: "World")
//
// Parameters:
//
//	none
//
// Returns:
//
//	A configured *flag.FlagSet and a pointer to the parsed name value.
func createArgumentParser() (*flag.FlagSet, *string) {
	fs := flag.NewFlagSet("hello-world", flag.ContinueOnError)
	name := fs.String("name", "World", "Name to greet (default: World)")
	return fs, name
}

// runCLI is the entry point for the hello-world CLI.
//
// It parses the supplied argument slice (analogous to sys.argv[1:] in
// Python), prints a greeting, and returns an exit code.
//
// Parameters:
//
//	args - slice of CLI arguments to parse, e.g. os.Args[1:].
//
// Returns:
//
//	0 on success, 1 on any error (invalid flag or empty name).
//
// Example:
//
//	code := runCLI([]string{"--name", "World"})
//	// prints: Hello, World!
//	// code == 0
func runCLI(args []string) int {
	parser, name := createArgumentParser()

	if err := parser.Parse(args); err != nil {
		// flag.ContinueOnError already wrote the error to stderr.
		return 1
	}

	if err := printGreeting(*name); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		return 1
	}

	return 0
}

func main() {
	os.Exit(runCLI(os.Args[1:]))
}
