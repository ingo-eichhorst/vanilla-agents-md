# Benchmark results

_CPython 3.14.3 on arm64 / Darwin 24.6.0, PyYAML 6.0.3, jsonschema 4.26.0._

_Generated 2026-05-03T21:27:55Z._

## Parse instructions for a coding agent

Open one config file from disk and turn it into a usable in-memory representation.

| Format | Snippet | ops/sec | relative |
|---|---|---:|---:|
| Vanilla AGENTS.md (production) | `open(empty AGENTS.md).read()` | 71,479 | 100.00% |
| .cursorrules | `open(.cursorrules).read()` | 70,187 | 98.19% |
| Vanilla AGENTS.md (with content) | `open(AGENTS.md).read()` | 68,699 | 96.11% |
| JSON | `json.load(open(agent.json))` | 44,766 | 62.63% |
| XML | `ET.parse(agent.xml).getroot()` | 25,061 | 35.06% |
| TOML | `tomllib.load(open(agent.toml,'rb'))` | 8,329 | 11.65% |
| YAML | `yaml.safe_load(open(agent.yaml))` | 805 | 1.13% |
| JSON + schema | `jsonschema.validate(json.load(...), SCHEMA)` | 803 | 1.12% |

## Update instructions across 12 different coding agents

Persist one change of agent guidance to disk. Vanilla AGENTS.md writes one file; per-tool config writes the same content to each tool's own dotfile.

| Approach | Snippet | ops/sec | relative |
|---|---|---:|---:|
| Vanilla AGENTS.md | `write(AGENTS.md)` | 15,529 | 100.00% |
| Per-tool config files (12 files) | `for f in [.cursorrules, .windsurfrules, ...]: write(f)` | 1,204 | 7.75% |

## Methodology

- Each benchmark runs 5 batches at ~0.6s each, after a 50-call warmup. Reported ops/sec is total ops divided by total elapsed wall-time, ± stdev across batches.
- The parse bench includes file open + parse from disk. After warmup, file pages are in OS cache, so we mostly measure parser CPU cost.
- The update bench writes to a fresh temp directory; each iteration overwrites the same path(s).
- All fixtures encode the same project instructions (setup/build/test/style/PR/security).

Reproduce:

```
python3 -m venv bench/.venv
bench/.venv/bin/pip install pyyaml jsonschema
bench/.venv/bin/python bench/bench.py
```
