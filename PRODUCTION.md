# Production deployments — verification log

Public GitHub repositories that:

1. were built (or substantially co-authored) by a coding agent, and
2. ship with **no** context file — no `AGENTS.md`, no `CLAUDE.md`, no `.cursorrules`, no `.windsurfrules`, no `.clinerules`, no `.github/copilot-instructions.md`, no `.aider.conf.yml`, no `.cursor/`, no `.claude/`, no `.windsurf/`.

Verified 2026-05-03 via the GitHub REST API.

## Methodology

For each candidate repo:

- **AI authorship** confirmed via at least one of:
  - Commits with `Co-Authored-By: Claude` / `Cursor` / etc. trailers, **or**
  - Commits authored directly by `Claude <noreply@anthropic.com>` or a known bot account, **or**
  - Repo README / description claiming AI authorship.
- **Absence of context files** confirmed via `gh api repos/{owner}/{repo}/contents/<path>` returning 404 for each known agent-config path.

## Repositories

### [rdumasia303/deepseek_ocr_app](https://github.com/rdumasia303/deepseek_ocr_app)

- ~1,803 stars; last push 2026-03-31.
- React + FastAPI OCR app powered by DeepSeek-OCR; PDF processing and multi-format export.
- Description (verbatim): *"A quick vibe coded app for deepseek OCR."*
- AI evidence: commit [`3dac0741`](https://github.com/rdumasia303/deepseek_ocr_app/commit/3dac0741) carries `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`. Feature work landed via PRs from `claude/add-pdf-support-…` branches.

### [deutsia/deutsia-radio](https://github.com/deutsia/deutsia-radio)

- 44 stars; last push 2026-05-02.
- Privacy-focused Android radio player supporting I2P, clearnet, and Tor streaming.
- Description states *"built with Claude Code"*.
- AI evidence: 39 of the 100 most-recent commits are authored directly by `Claude <noreply@anthropic.com>`. Examples: [`2cf424e9`](https://github.com/deutsia/deutsia-radio/commit/2cf424e9), [`1c8a1e0c`](https://github.com/deutsia/deutsia-radio/commit/1c8a1e0c).

### [dannystuart/carousel-standalone](https://github.com/dannystuart/carousel-standalone)

- 8 stars; last push 2026-04-17.
- Themed card carousel with Fantasy and Cosmos visual modes.
- README states: *"Built entirely through conversation with Claude Code."*
- AI evidence: 16 of 18 commits carry `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`. Example: [`e4548a61`](https://github.com/dannystuart/carousel-standalone/commit/e4548a61).

### [nraford7/CrateBot5](https://github.com/nraford7/CrateBot5)

- 5 stars; last push 2026-04-12.
- Audio-fingerprinting and ML-driven music-analysis suite for DJs (Swift, includes ML models).
- Description states *"Built with Claude Code."*
- AI evidence: 26 of 27 recent commits carry `Co-Authored-By: Claude`. Example: [`cf4e25ba`](https://github.com/nraford7/CrateBot5/commit/cf4e25ba).

### [enablement-ch/clio-ghostwriter](https://github.com/enablement-ch/clio-ghostwriter)

- 6 stars; last push 2026-03-09.
- Open-source LinkedIn ghostwriter pipeline (scrape → topic ID → write → QA → ClickUp), driven by a Slack bot.
- README states *"Built with Claude Code."*
- AI evidence: commit [`c11e5571`](https://github.com/enablement-ch/clio-ghostwriter/commit/c11e5571) carries `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`.

## Repos checked and excluded

### Julian-Ivanov/jarvis-voice-assistant

- 42 stars, "Built with Claude Code" in description and lots of Claude-authored commits — but the repo *does* contain `CLAUDE.md` and a `.claude/` directory, so it doesn't satisfy criterion (2). Listed here for transparency.

## Reproducing the check

```sh
# Authorship:
gh api repos/{owner}/{repo}/commits | jq -r '.[].commit.message' | grep -i 'Co-Authored-By: Claude\|Co-Authored-By: Cursor'
gh api repos/{owner}/{repo}/commits | jq -r '.[].commit.author.email'   # look for noreply@anthropic.com

# Context-file absence (each should 404):
for path in AGENTS.md CLAUDE.md .cursorrules .windsurfrules .clinerules \
    .github/copilot-instructions.md .aider.conf.yml; do
  printf '%-40s ' "$path"
  gh api -i repos/{owner}/{repo}/contents/$path 2>/dev/null | head -1
done
```
