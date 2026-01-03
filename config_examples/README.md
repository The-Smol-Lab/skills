# Config examples

This directory provides sample configuration files for the Claude Skills MCP server and agent behavior.

## Files

- `AGENTS.md`: Sample agent working agreements for OpenCode/Claude Code, including Context7 usage, claude-skills workflow, testing, and Python environment conventions.
- `config.json`: Baseline config that points at this repo's curated and experimental skill sources with conservative defaults.
- `config_extreme.json`: Expanded config that aggregates multiple public skill sources (plus an optional local path) to maximize available skills; higher default `top_k` for broader search.
