# Using with OpenCode (MCP)

OpenCode can access this repo through the [K-Dense AI claude-skills-mcp](https://github.com/K-Dense-AI/claude-skills-mcp) server, which provides semantic search and progressive disclosure for skills.

## Setup Instructions

1. **Download skills into your local OpenCode skill folder**:

```bash
bash -c 'set -e; repo="https://github.com/The-Smol-Lab/skills.git"; out="$HOME/.config/opencode/skill"; tmp="$(mktemp -d)"; git clone --depth 1 --filter=blob:none --sparse "$repo" "$tmp"; git -C "$tmp" sparse-checkout set skills/curated/ai-development skills/curated/software-engineering skills/curated/utilities skills/experimental; mkdir -p "$out"; rsync -a "$tmp/skills/curated/ai-development/" "$out/"; rsync -a "$tmp/skills/curated/software-engineering/" "$out/"; rsync -a "$tmp/skills/curated/utilities/" "$out/"; rsync -a "$tmp/skills/experimental/" "$out/"; rm -rf "$tmp"; echo "Merged into $out"'
```

2. **Add the MCP server** to your OpenCode config (`~/.config/opencode/opencode.json` or a per-project `opencode.json`):

```jsonc
{
  "mcp": {
    "claude-skills": {
      "type": "local",
      "command": ["uvx", "claude-skills-mcp", "--config", "~/.config/opencode/claude-skills-mcp/config.json"]
    }
  }
}
```

   See the [official OpenCode MCP documentation](https://opencode.ai/docs/mcp-servers/) for more details.

3. **Create the skills config** at `~/.config/opencode/claude-skills-mcp/config.json` and copy the content below:

```jsonc
{
  "skill_sources": [
    {
      "type": "local",
      "path": "~/.config/opencode/claude-skills-mcp/The-Smol-Lab-skills/skills",
      "comment": "All skills from this repo (local clone, recursive)"
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
  "auto_update_enabled": false,
  "comment_auto_update": "Enable automatic hourly skill updates (checks at :00 of each hour)",
  "auto_update_interval_minutes": 60,
  "comment_interval": "Check for updates every N minutes (synced to clockface hours)",
  "github_api_token": null,
  "comment_token": "Token is unused by the backend for GitHub sources right now; local clone avoids API rate limits"
}
```

   - A local-only starter config is available at `config_examples/claude-skills-mcp/config.json`
   - A multi-repo local config is available at `config_examples/claude-skills-mcp/config_extreme.json`

4. **Why local + manual updates?**

   The current `claude-skills-mcp-backend` version does not pass `github_api_token` into GitHub API requests, which can trigger rate limits when loading skills from GitHub. Using a local clone avoids the API entirely. Update manually when you want the latest skills:

```bash
git -C ~/.config/opencode/claude-skills-mcp/The-Smol-Lab-skills pull --ff-only
```

5. **Mass clone (optional)**

   If you want to load multiple skill repos locally, keep them under one folder and point your config at each repo's `skills` directory:

```bash
mkdir -p "~/.config/opencode/claude-skills-mcp/skills-sources"

git clone https://github.com/anthropics/skills "~/.config/opencode/claude-skills-mcp/skills-sources/anthropics/skills"
git clone https://github.com/ComposioHQ/awesome-claude-skills "~/.config/opencode/claude-skills-mcp/skills-sources/ComposioHQ/awesome-claude-skills"
git clone https://github.com/huggingface/skills "~/.config/opencode/claude-skills-mcp/skills-sources/huggingface/skills"
git clone https://github.com/mrgoonie/claudekit-skills "~/.config/opencode/claude-skills-mcp/skills-sources/mrgoonie/claudekit-skills"
git clone https://github.com/obra/superpowers "~/.config/opencode/claude-skills-mcp/skills-sources/obra/superpowers"
git clone https://github.com/wshobson/agents "~/.config/opencode/claude-skills-mcp/skills-sources/wshobson/agents"
git clone https://github.com/openai/skills "~/.config/opencode/claude-skills-mcp/skills-sources/openai/skills"
git clone https://github.com/alirezarezvani/claude-skills "~/.config/opencode/claude-skills-mcp/skills-sources/alirezarezvani/claude-skills"
```

6. **Mass update (optional)**

   Pull the latest changes for every cloned repo:

```bash
for dir in ~/.config/opencode/claude-skills-mcp/skills-sources/*/*; do
  if [ -d "$dir/.git" ]; then
    git -C "$dir" pull --ff-only
  fi
done
```

   One-liner version:

```bash
for dir in ~/.config/opencode/claude-skills-mcp/skills-sources/*/*; do [ -d "$dir/.git" ] && git -C "$dir" pull --ff-only; done
```

7. **Restart OpenCode** and use skills in your prompts

   Example: _"Use the `skill-creator` skill. Follow it step by step."_
