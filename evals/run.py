# ABOUTME: Runs implicit-state-machines eval scenarios headlessly with claude -p --safe-mode.
# ABOUTME: Each run gets a fresh git copy of fixture/; results land in <out>/<arm>/<scenario>-<rep>/.
"""Usage: uv run --no-project python evals/run.py --out DIR --arm NAME[=SKILL.md|none] [--arm ...]
          [--scenario NAME ...] [--reps N] [--model sonnet] [--jobs 4] [--budget 3]

Each run dir holds:
  stream.jsonl  full log
  final.md      last result text
  tools.txt     the agent's tool calls in order (to check what ran before what)
  commits.txt   git log --stat of the commits the agent made
  diff.patch    every change against the fixture, committed or not
Read final.md, commits.txt and diff.patch to grade against evals/README.md.
"""
import argparse
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_NAME = "implicit-state-machines"


def prompt_for(task, skill_path, workdir):
    if skill_path is None:
        return task
    body = Path(skill_path).read_text()
    return (
        f"{task}\n\n<skill name=\"{SKILL_NAME}\">\n"
        f"Base directory for this skill: {workdir}/.skill\n\n{body}\n</skill>"
    )


def git(workdir, *args):
    return subprocess.run(["git", *args], cwd=workdir, capture_output=True, text=True, check=True).stdout


def tool_calls(events):
    lines = []
    for ev in events:
        if ev.get("type") != "assistant":
            continue
        for block in ev.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            inp = block.get("input", {})
            detail = inp.get("file_path") or inp.get("command") or inp.get("pattern") or ""
            lines.append(f"{block.get('name')}\t{' '.join(str(detail).split())[:200]}")
    return "\n".join(lines) + "\n"


def one_run(out, arm, skill_path, name, scenario, rep, model, budget):
    run_dir = out / arm / f"{name}-{rep}"
    if (run_dir / "final.md").exists():
        return f"skip {run_dir}"
    workdir = run_dir / "work"
    shutil.rmtree(run_dir, ignore_errors=True)
    shutil.copytree(HERE / "fixture", workdir)
    if scenario.get("overlay"):
        shutil.copytree(HERE / "overlays" / scenario["overlay"], workdir, dirs_exist_ok=True)
    git(workdir, "init", "-q", "-b", "main")
    git(workdir, "add", ".")
    git(workdir, "-c", "user.name=eval", "-c", "user.email=eval@example.invalid", "commit", "-qm", "fixture")
    base = git(workdir, "rev-parse", "HEAD").strip()
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_EFFORT_LEVEL"}
    cmd = [
        "claude", "-p", "--safe-mode", "--model", model, "--output-format", "stream-json", "--verbose",
        "--dangerously-skip-permissions", "--max-budget-usd", str(budget),
        prompt_for(scenario["task"], skill_path, workdir),
    ]
    with open(run_dir / "stream.jsonl", "w") as log:
        subprocess.run(cmd, cwd=workdir, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env)
    events = []
    for line in (run_dir / "stream.jsonl").read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    results = [ev for ev in events if ev.get("type") == "result"]
    final = results[-1].get("result", "") if results else "(no result event)"
    cost = max((r.get("total_cost_usd") or 0) for r in results) if results else 0
    (run_dir / "tools.txt").write_text(tool_calls(events))
    (run_dir / "commits.txt").write_text(git(workdir, "log", "--all", "--reverse", "--stat", f"{base}..HEAD"))
    git(workdir, "add", "-A")
    diff = git(workdir, "diff", "--cached", base, "--", ".", ":(exclude)**/__pycache__/**")
    (run_dir / "diff.patch").write_text(diff)
    (run_dir / "final.md").write_text(final + f"\n\n<!-- cost_usd={cost:.2f} -->\n")
    return f"done {run_dir} ${cost:.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--arm", action="append", required=True, help="name=path/to/SKILL.md or name=none")
    ap.add_argument("--scenario", action="append")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--budget", type=float, default=3)
    a = ap.parse_args()
    scenarios = json.loads((HERE / "scenarios.json").read_text())
    names = a.scenario or list(scenarios)
    out = Path(a.out).resolve()
    jobs = []
    for spec in a.arm:
        arm, _, path = spec.partition("=")
        skill = None if path in ("", "none") else str(Path(path).resolve())
        for name in names:
            for rep in range(1, a.reps + 1):
                jobs.append((out, arm, skill, name, scenarios[name], rep, a.model, a.budget))
    with ThreadPoolExecutor(a.jobs) as pool:
        for msg in pool.map(lambda j: one_run(*j), jobs):
            print(msg, flush=True)


if __name__ == "__main__":
    main()
