# Skills Catalog

A curated library of reusable "skills" for coding agents. Each skill bundles guidance, references, and optionally scripts so agents can execute domain-specific tasks consistently.

## What's in this repo

- **Curated skills** organized by domain under `skills/curated/`
- **Experimental skills** under `skills/experimental/`
- Each skill includes a `SKILL.md` plus optional `references/`, `scripts/`, and `templates/`

## How to use

1. Pick a skill that matches your task
2. Read the skill's `SKILL.md` for scope and usage
3. Use any referenced docs or scripts to complete the task

## Using with OpenCode (native skills)

OpenCode loads skills from `~/.config/opencode/skill`. Use the one-liner below to download curated and experimental skills into that folder:

```bash
bash -c '
  set -e
  repo="https://github.com/The-Smol-Lab/skills.git"
  out="$HOME/.config/opencode/skill"
  tmp="$(mktemp -d)"

  git clone --depth 1 --filter=blob:none --sparse "$repo" "$tmp"
  git -C "$tmp" sparse-checkout set \
    skills/curated/ai-development \
    skills/curated/software-engineering \
    skills/curated/utilities \
    skills/experimental

  mkdir -p "$out"
  rsync -a "$tmp/skills/curated/ai-development/" "$out/"
  rsync -a "$tmp/skills/curated/software-engineering/" "$out/"
  rsync -a "$tmp/skills/curated/utilities/" "$out/"
  rsync -a "$tmp/skills/experimental/" "$out/"

  rm -rf "$tmp"
  echo "Merged into $out"
'
```

To add more sources, repeat the same pattern with a different `repo` URL and `sparse-checkout` paths, keeping the same `out` folder so everything merges into `~/.config/opencode/skill`.

MCP-specific setup has been moved to `config_examples/claude-skills-mcp.md`, with configs under `config_examples/claude-skills-mcp/`.

## More skill sources

| Source | Description |
|--------|-------------|
| [SkillsMP](https://skillsmp.com/) | A community-run marketplace that indexes tens of thousands of GitHub-hosted skills using the open `SKILL.md` standard, with search and category browsing to discover and download skills |
| [Claude Plugins Skill Registry](https://claude-plugins.dev/skills) | A community-maintained, open-source registry that auto-indexes public GitHub skills and lets you browse and install them for Claude, Codex, OpenCode, and other assistants |

## Contributing

- Add new skills under the appropriate category
- Keep skills self-contained and focused on a single domain or workflow
- Prefer links to authoritative references and include runnable scripts where helpful

## License

MIT — see [LICENSE](LICENSE)
