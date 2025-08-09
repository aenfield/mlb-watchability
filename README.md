# MLB Watchability

This project has two goals:

- To help me understand at a glance which MLB game(s) are most interesting on a given day, based on the 'watchability' appeal of the teams and starting pitchers. I'm inspired by [Carson Cistulli's NERD scores](https://blogs.fangraphs.com/introducing-team-nerd/) work at FanGraphs.
- Be a test bed for me to actually use and learn from detailed experience about agentic coding AI tools - I'm using Claude Code - by building and maintaining a non-trivial project. Based on an initial few weeks of on-and-off experimentation, I'm amazed and impressed by how easy and different it is to build and ship software using a tool like Claude Code.

As of early August 2025, every day, code automatically:

- pulls the day's schedule and team and pitcher stats from external sources;
- generates team, pitcher, and game NERD scores;
- uses the OpenAI API or Claude via Anthropic's API to generate a readable summary of each game that incorporates the NERD stats and the latest from the web;
- authors a blog post by creating a Markdown file; and
- publishes the post to my blog at [andrewenfield.com](https://andrewenfield.com).

## Development

### Run tests

- **Normal tests only**: `uv run pytest` (default - excludes costly tests)
- **Costly tests only**: `uv run pytest -m costly`
- **All tests**: `uv run pytest -m ""`
- **Explicitly normal tests**: `uv run pytest -m "not costly"`

### Other development commands

- **Lint code**: `uv run ruff check`
- **Format code**: `uv run black .`
- **Check types**: `uv run mypy .`
- **Install dependencies**: `uv sync`
- `./run_all_checks.sh` runs normal tests, lints, formats, and checks types
- `./run_all_checks.sh --include-costly` runs all tests, lints, formats, and checks types

### Other commands

- **Run the CLI tool to generate a Markdown file for a day**: `uv run mlbw-markdown`

For more information, see the stuff in the specs/ directory, in CLAUDE.md, and in todo.md.
