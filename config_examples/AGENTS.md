# ~/.config/opencode/AGENTS.md

## Working agreements

### Python environment and dependencies

* Use **uv** as the standard Python package manager and environment tool.
* Manage Python versions and virtual environments exclusively with `uv python` and `uv venv`.
* Add, update, and remove dependencies using `uv add` and `uv remove`. Do not use `pip`, `pip-tools`, or `poetry`.
* Lock dependencies with `uv lock` and commit the resulting lockfile to version control.
* Prefer reproducible, isolated environments for all applications, scripts, and experiments.
* Ask for explicit confirmation before introducing new production dependencies.

### Testing and quality

* Run `pytest` after any change to Python application code.
* Do not consider work complete until tests pass or failures are explicitly acknowledged.

### Code generation and review

* When generating or reviewing Python code, use **Context7** to reference current Python and library documentation, syntax, and best practices.
* When generating or reviewing frontend code, use **Context7** to reference current frontend framework and library documentation, syntax, and best practices.

### Tooling support

* Use **claude-skills** tools to discover relevant skills when asked to perform specialized or unfamiliar tasks.
* Follow progressive disclosure to keep context small and responses fast:
  * Start with `find_helpful_skills` for any domain-specific task; use a detailed `task_description`.
  * Only use `list_skills` for inventory/debugging or to verify configuration; avoid it for task queries.
  * Use `read_skill_document` after selecting a skill to pull specific scripts/references/assets; list documents first when unsure.
* Prefer `top_k=5-10` to capture all relevant skills; use fewer only when you want the single best match.
* Avoid requesting large or unnecessary documents, and only request base64 image content when you truly need it.
