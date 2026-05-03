"""
bench.py — measure two costs an agent toolchain pays for its config format:

    1. parse: open one config file from disk and turn it into something
       the agent can use (a string, a dict, an Element, ...).

    2. update: persist a change in agent guidance. For Vanilla AGENTS.md,
       that's editing one Markdown file. For ecosystems where each tool
       wants its own config, it's editing N files.

All fixtures under ./fixtures/ encode the same project instructions.

Usage
-----
    python bench.py [--seconds N]

Outputs
-------
    results.json  machine-readable
    RESULTS.md    human-readable summary
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import statistics
import sys
import tempfile
import time
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
RESULTS_JSON = ROOT / "results.json"
RESULTS_MD = ROOT / "RESULTS.md"

AGENTS_MD = FIXTURES / "AGENTS.md"
EMPTY_AGENTS_MD = FIXTURES / "AGENTS.md.production"
CURSORRULES = FIXTURES / ".cursorrules"
YAML_FILE = FIXTURES / "agent.yaml"
JSON_FILE = FIXTURES / "agent.json"
XML_FILE = FIXTURES / "agent.xml"
TOML_FILE = FIXTURES / "agent.toml"
SCHEMA_FILE = FIXTURES / "agent.schema.json"

SCHEMA = json.loads(SCHEMA_FILE.read_text())

# A representative list of per-tool agent-instruction files in use as of
# early 2026, before AGENTS.md emerged as a unified format. Twelve entries
# matches the table title on the page.
PER_TOOL_FILES = [
    ".cursorrules",
    ".windsurfrules",
    ".clinerules",
    ".github/copilot-instructions.md",
    ".aider.conf.yml",
    ".junie/guidelines.md",
    "CLAUDE.md",
    ".roomodes",
    ".codex/config.toml",
    ".factory/agent.md",
    ".continuerules",
    ".zedrules",
]


# ---------------------------------------------------------------------------
# parse benchmarks
# ---------------------------------------------------------------------------

def parse_agents_md() -> str:
    with open(AGENTS_MD, "r", encoding="utf-8") as f:
        return f.read()


def parse_agents_md_production() -> str:
    # Production AGENTS.md per Gloaguen et al. (2026): the file is empty,
    # so the read() returns "" immediately. Genuinely a no-op for the agent.
    with open(EMPTY_AGENTS_MD, "r", encoding="utf-8") as f:
        return f.read()


def parse_cursorrules() -> str:
    with open(CURSORRULES, "r", encoding="utf-8") as f:
        return f.read()


def parse_yaml() -> dict:
    with open(YAML_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_json() -> dict:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_json_with_schema() -> dict:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    jsonschema.validate(data, SCHEMA)
    return data


def parse_xml() -> ET.Element:
    return ET.parse(XML_FILE).getroot()


def parse_toml() -> dict:
    with open(TOML_FILE, "rb") as f:
        return tomllib.load(f)


PARSE_BENCHMARKS = [
    ("Vanilla AGENTS.md (production)", "open(empty AGENTS.md).read()", parse_agents_md_production),
    ("Vanilla AGENTS.md (with content)", "open(AGENTS.md).read()", parse_agents_md),
    (".cursorrules",      "open(.cursorrules).read()", parse_cursorrules),
    ("TOML",              "tomllib.load(open(agent.toml,'rb'))", parse_toml),
    ("JSON",              "json.load(open(agent.json))", parse_json),
    ("YAML",              "yaml.safe_load(open(agent.yaml))", parse_yaml),
    ("XML",               "ET.parse(agent.xml).getroot()", parse_xml),
    ("JSON + schema",     "jsonschema.validate(json.load(...), SCHEMA)", parse_json_with_schema),
]


# ---------------------------------------------------------------------------
# update benchmarks
# ---------------------------------------------------------------------------

def make_update_benchmarks(workdir: Path):
    content = AGENTS_MD.read_text()
    payload = (content + "\n\n## New section\nReminder.\n").encode()

    agents_dir = workdir / "agents_md"
    agents_dir.mkdir(exist_ok=True)
    per_tool_dir = workdir / "per_tool"
    per_tool_dir.mkdir(exist_ok=True)
    for name in PER_TOOL_FILES:
        (per_tool_dir / name).parent.mkdir(parents=True, exist_ok=True)

    target_agents_md = agents_dir / "AGENTS.md"

    def update_agents_md():
        # one file: Markdown at the repo root.
        with open(target_agents_md, "wb") as f:
            f.write(payload)

    def update_per_tool():
        # 12 files: one per tool. Same content, replicated.
        for name in PER_TOOL_FILES:
            with open(per_tool_dir / name, "wb") as f:
                f.write(payload)

    return [
        ("Vanilla AGENTS.md", "write(AGENTS.md)", update_agents_md),
        (f"Per-tool config files ({len(PER_TOOL_FILES)} files)",
         "for f in [.cursorrules, .windsurfrules, ...]: write(f)",
         update_per_tool),
    ]


# ---------------------------------------------------------------------------
# timing harness
# ---------------------------------------------------------------------------

def time_one(fn, target_seconds: float) -> tuple[float, int, list[float]]:
    """
    Run `fn` repeatedly for ~target_seconds, return
    (overall_ops_per_sec, total_ops, per_batch_ops_per_sec).

    Five batches so we can report stdev across batches.
    """
    for _ in range(50):
        fn()  # warm OS page cache + JIT-style warmup

    samples: list[float] = []
    total_ops = 0
    total_elapsed = 0.0
    n_batches = 5
    per_batch_target = target_seconds / n_batches

    for _ in range(n_batches):
        n = 100
        while True:
            t0 = time.perf_counter()
            for _ in range(n):
                fn()
            dt = time.perf_counter() - t0
            if dt >= per_batch_target * 0.8:
                break
            scale = (per_batch_target / max(dt, 1e-6)) * 1.2
            n = max(int(n * scale), n + 100)
        samples.append(n / dt)
        total_ops += n
        total_elapsed += dt

    return total_ops / total_elapsed, total_ops, samples


def run_suite(name: str, benchmarks, target_seconds: float):
    rows = []
    print(f"\n## {name}", flush=True)
    for label, snippet, fn in benchmarks:
        fn()  # smoke test
        ops, total, samples = time_one(fn, target_seconds)
        stdev = statistics.stdev(samples) if len(samples) > 1 else 0.0
        rows.append({
            "label": label,
            "snippet": snippet,
            "ops_per_sec": ops,
            "ops_per_sec_stdev": stdev,
            "iterations": total,
            "samples": samples,
        })
        rel = stdev / ops * 100 if ops else 0.0
        print(f"  {label:<40}  {ops:>14,.0f} ops/sec  "
              f"(±{rel:5.2f}%, n={total:,})", flush=True)
    rows.sort(key=lambda r: -r["ops_per_sec"])
    fastest = rows[0]["ops_per_sec"]
    for r in rows:
        r["relative"] = r["ops_per_sec"] / fastest
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=2.0,
                    help="approximate wall-time budget per benchmark (default: 2s)")
    args = ap.parse_args()

    print(f"# bench.py — {platform.python_implementation()} "
          f"{platform.python_version()}, {platform.machine()} / "
          f"{platform.system()} {platform.release()}", flush=True)
    print(f"# target: ~{args.seconds:.1f}s per format, 5 batches each", flush=True)

    parse_rows = run_suite("parse", PARSE_BENCHMARKS, args.seconds)

    with tempfile.TemporaryDirectory(prefix="vanilla-agents-bench-") as td:
        update_benchmarks = make_update_benchmarks(Path(td))
        update_rows = run_suite("update", update_benchmarks, args.seconds)

    out = {
        "meta": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "machine": platform.machine(),
            "system": f"{platform.system()} {platform.release()}",
            "yaml_version": yaml.__version__,
            "jsonschema_version": _jsonschema_version(),
            "target_seconds_per_bench": args.seconds,
            "fixtures": [p.name for p in sorted(FIXTURES.iterdir())],
            "per_tool_files": PER_TOOL_FILES,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "parse": parse_rows,
        "update": update_rows,
    }
    RESULTS_JSON.write_text(json.dumps(out, indent=2) + "\n")
    _write_markdown(out)
    print(f"\n# wrote {RESULTS_JSON.relative_to(ROOT.parent)} and "
          f"{RESULTS_MD.relative_to(ROOT.parent)}", flush=True)
    return 0


def _write_markdown(out: dict) -> None:
    m = out["meta"]
    lines = ["# Benchmark results", ""]
    lines.append(f"_{m['implementation']} {m['python']} on {m['machine']} / "
                 f"{m['system']}, PyYAML {m['yaml_version']}, "
                 f"jsonschema {m['jsonschema_version']}._")
    lines.append("")
    lines.append(f"_Generated {m['timestamp_utc']}._")
    lines.append("")

    lines.append("## Parse instructions for a coding agent")
    lines.append("")
    lines.append("Open one config file from disk and turn it into a usable "
                 "in-memory representation.")
    lines.append("")
    lines.append("| Format | Snippet | ops/sec | relative |")
    lines.append("|---|---|---:|---:|")
    for r in out["parse"]:
        lines.append(f"| {r['label']} | `{r['snippet']}` | "
                     f"{r['ops_per_sec']:,.0f} | {r['relative']*100:.2f}% |")
    lines.append("")

    lines.append(f"## Update instructions across {len(out['meta']['per_tool_files'])} "
                 "different coding agents")
    lines.append("")
    lines.append("Persist one change of agent guidance to disk. Vanilla "
                 "AGENTS.md writes one file; per-tool config writes the same "
                 "content to each tool's own dotfile.")
    lines.append("")
    lines.append("| Approach | Snippet | ops/sec | relative |")
    lines.append("|---|---|---:|---:|")
    for r in out["update"]:
        lines.append(f"| {r['label']} | `{r['snippet']}` | "
                     f"{r['ops_per_sec']:,.0f} | {r['relative']*100:.2f}% |")
    lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(f"- Each benchmark runs 5 batches at ~"
                 f"{m['target_seconds_per_bench']/5:.1f}s each, after a "
                 f"50-call warmup. Reported ops/sec is total ops divided by "
                 f"total elapsed wall-time, ± stdev across batches.")
    lines.append(f"- The parse bench includes file open + parse from disk. "
                 f"After warmup, file pages are in OS cache, so we mostly "
                 f"measure parser CPU cost.")
    lines.append(f"- The update bench writes to a fresh temp directory; "
                 f"each iteration overwrites the same path(s).")
    lines.append(f"- All fixtures encode the same project instructions "
                 f"(setup/build/test/style/PR/security).")
    lines.append("")
    lines.append("Reproduce:")
    lines.append("")
    lines.append("```")
    lines.append("python3 -m venv bench/.venv")
    lines.append("bench/.venv/bin/pip install pyyaml jsonschema")
    lines.append("bench/.venv/bin/python bench/bench.py")
    lines.append("```")
    lines.append("")

    RESULTS_MD.write_text("\n".join(lines))


def _jsonschema_version() -> str:
    try:
        from importlib.metadata import version
        return version("jsonschema")
    except Exception:
        return "unknown"


if __name__ == "__main__":
    sys.exit(main())
