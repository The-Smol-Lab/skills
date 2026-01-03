# skills
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
OpenCode can access this repo through an MCP server. The simplest option is to expose the `skills/` folder via the filesystem MCP server.

1. Clone this repo somewhere on your machine.
2. Add an MCP server to your OpenCode config (`~/.config/opencode/opencode.json` or a per-project `opencode.json`):

```jsonc
{
  "mcp": {
    "smol_skills": {
      "type": "local",
      "command": [
        "npx",
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/absolute/path/to/the-smol-lab/skills/skills"
      ]
    }
  }
}
```

3. Restart OpenCode. In prompts, ask it to read and follow a specific skill (for example: “Use the `skill-creator` skill at `skills/curated/utilities/skill-creator/SKILL.md`. Follow it step by step.”).

## Contributing
- Add new skills under the appropriate category.
- Keep skills self-contained and focused on a single domain or workflow.
- Prefer links to authoritative references and include runnable scripts where helpful.

## License
MIT — see [LICENSE](LICENSE).
