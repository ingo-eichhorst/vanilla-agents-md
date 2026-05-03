# vanilla-agents-md

A fast, lightweight, cross-platform format for instructing coding agents.

Live site: https://ingo-eichhorst.github.io/vanilla-agents-md/

A satirical homage to [vanilla-js.com](https://vanilla-js.com), applied to [AGENTS.md](https://agents.md). The joke writes itself: AGENTS.md is just a Markdown file.

The page cites Gloaguen et al., [arXiv:2602.11988](https://arxiv.org/abs/2602.11988) (2026), which found that AGENTS.md files actually reduce coding-agent task success rates and increase costs by 20%+ — making the "production deployment is empty" gag literally peer-reviewed.

## What's in here

- `index.html` — the page (single file, inline CSS/JS, no build).
- `bench/` — real benchmarks for the "Speed Comparison" tables. See [bench/RESULTS.md](bench/RESULTS.md) and [bench/results.json](bench/results.json).
- `PRODUCTION.md` — verified list of public GitHub repos that are clearly AI-built but ship with no context file (no `AGENTS.md`, no `CLAUDE.md`, no `.cursorrules`).
- `vanilla_specs.txt` — the full specification.

## Run the benchmarks

```
python3 -m venv bench/.venv
bench/.venv/bin/pip install pyyaml jsonschema
bench/.venv/bin/python bench/bench.py --seconds 3
```

This regenerates `bench/results.json` and `bench/RESULTS.md` on your hardware.

## Local preview

```
open index.html
```

That's it. No build, no dependencies. Vanilla.
