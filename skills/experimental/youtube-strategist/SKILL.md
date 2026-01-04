---
name: youtube-strategist
description: >
  YouTube content strategy partner for data-driven planning. Use when you need
  to research video ideas, analyze competing videos or channels, validate trends,
  extract transcript insights, or produce a structured YouTube strategy. Triggers
  on requests like "plan a YouTube video about X", "analyze competitors for Y",
  "find what performs for Z", or "is this topic trending on YouTube".
---

# YouTube Strategist

Turn user ideas into data-backed YouTube strategies using keyword research,
competitor analysis, transcript insights, and trend validation.

## Quick start

1. Run `scripts/setup_check.py` to create a local `.venv` and verify tools.
2. Confirm the MCP server is available: `opencode mcp list` should show
   `youtube_transcript` connected.
3. Use `./run.sh <script.py>` or `uv run <script.py>` to execute scripts.
4. Ask for the user's idea(s), target audience, and goals.
5. Use `scripts/youtube_search.py` to gather top videos per keyword.
6. Use `scripts/trends_analyzer.py` to validate trend momentum.
7. Use MCP transcripts for top competitors and summarize with
   `scripts/transcript_analyzer.py`.
8. Produce a structured strategy report, then iterate conversationally.

## Core workflow

1. **Idea intake**
   - Extract keywords and clarify the target audience, format, and outcomes.
   - Ask for competitor channels if the user has them.

2. **Trend validation (Google Trends / YouTube)**
   - Use `scripts/trends_analyzer.py` with `gprop="youtube"`.
   - Look for rising interest and related queries.

3. **Market research (YouTube search)**
   - Use `scripts/youtube_search.py` to collect 10-20 top videos.
   - Capture view counts, publish dates, and titles.

4. **Competitor deep-dive**
   - Pull transcripts for top performers using the MCP server.
   - Use `scripts/transcript_analyzer.py` to extract hooks and topics.

5. **Strategy output**
   - Provide: opportunity analysis, angles, title options, hooks, and outline.
   - Deliver a structured report plus conversational iteration.

## Scripts

- `scripts/setup_check.py`
  - Create `.venv` with `uv venv` when available.
  - Install `yt-dlp` and `pytrends` into the venv.
  - Ensure MCP server for transcripts is configured.

- `run.sh`
  - Wrapper that runs `uv run` for a script in this directory.

- `scripts/youtube_search.py`
  - Search YouTube by keyword and return structured metadata.

- `scripts/video_metadata.py`
  - Fetch detailed metadata for specific video URLs or IDs.

- `scripts/trends_analyzer.py`
  - Query Google Trends for YouTube searches and related queries.

- `scripts/transcript_analyzer.py`
  - Summarize transcripts, extract hooks, and surface topics.

## References

- `references/strategy-frameworks.md`
  - Content patterns, hooks, and differentiation ideas.

- `references/analysis-templates.md`
  - Report templates and structured tables.

- `references/prompt-templates.md`
  - Refinement prompts for titles, hooks, and positioning.

## Output guidance

- Always include a data-backed summary of why a topic is viable or risky.
- Provide 3-5 angles and 5-10 title options.
- If data is weak, suggest pivots rather than forcing the original idea.
