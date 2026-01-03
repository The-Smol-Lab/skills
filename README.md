# Skills Catalog
A curated library of reusable "skills" for coding agents. Each skill bundles guidance, references, and optionally scripts so agents can execute domain-specific tasks consistently.

## What’s in this repo
- Curated skills organized by domain under `skills/curated/`
- Experimental skills under `skills/experimental/`
- Each skill includes a `SKILL.md` plus optional `references/`, `scripts/`, and `templates/`

## How to use
1. Pick a skill that matches your task.
2. Read the skill’s `SKILL.md` for scope and usage.
3. Use any referenced docs or scripts to complete the task.

## Using with OpenCode (MCP)
OpenCode can access this repo through the [K-Dense AI claude-skills-mcp](https://github.com/K-Dense-AI/claude-skills-mcp) server, which provides semantic search and progressive disclosure for skills.

1. Clone this repo somewhere on your machine.
2. Add an MCP server to your OpenCode config (`~/.config/opencode/opencode.json` or a per-project `opencode.json`):

```jsonc
{
  "mcp": {
    "claude-skills": {
      "type": "local",
      "command": ["uvx", "claude-skills-mcp", "--config", "~/.claude/skills/config.json"]
    }
  }
}
```
See opencode doc here for mcp official mcp config: [https://opencode.ai/docs/mcp-servers/](https://opencode.ai/docs/mcp-servers/)

3. Generate a starter config here `~/.claude/skills/config.json` and copy the content below:

```jsonc
{
  "skill_sources": [
    {
      "type": "github",
      "url": "https://github.com/The-Smol-Lab/skills/tree/main/skills/curated/ai-development",
      "comment": "Curated AI development skills from this repo"
    },
    {
      "type": "github",
      "url": "https://github.com/The-Smol-Lab/skills/tree/main/skills/curated/software-engineering",
      "comment": "Curated software engineering skills from this repo"
    },
    {
      "type": "github",
      "url": "https://github.com/The-Smol-Lab/skills/tree/main/skills/curated/utilities",
      "comment": "Curated utility skills from this repo"
    },
    {
      "type": "github",
      "url": "https://github.com/The-Smol-Lab/skills/tree/main/skills/experimental",
      "comment": "Experimental skills that may change frequently"
    }
  ],
  "embedding_model": "all-MiniLM-L6-v2",
  "default_top_k": 5,
  "max_skill_content_chars": null,
  "comment_max_chars": "Set to an integer (e.g., 5000) to truncate skill content, or null for unlimited",
  "load_skill_documents": true,
  "comment_load_docs": "Load additional files (scripts, references, assets) from skill directories",
  "max_image_size_bytes": 5242880,
  "comment_max_image": "Maximum image file size (5MB). Larger images store URL only",
  "allowed_image_extensions": [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"],
  "text_file_extensions": [".md", ".py", ".txt", ".json", ".yaml", ".yml", ".sh", ".r", ".ipynb", ".xml"],
  "auto_update_enabled": true,
  "comment_auto_update": "Enable automatic hourly skill updates (checks at :00 of each hour)",
  "auto_update_interval_minutes": 60,
  "comment_interval": "Check for updates every N minutes (synced to clockface hours)",
  "github_api_token": null,
  "comment_token": "Optional GitHub personal access token for 5000 req/hr (default: 60 req/hr)"
}
```

5. Restart OpenCode. In prompts, ask it to read and follow a specific skill (for example: “Use the `skill-creator` skill. Follow it step by step.”).

## Contributing
- Add new skills under the appropriate category.
- Keep skills self-contained and focused on a single domain or workflow.
- Prefer links to authoritative references and include runnable scripts where helpful.

## License
MIT — see [LICENSE](LICENSE).
