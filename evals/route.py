# ABOUTME: Tests whether a description line routes requests to implicit-state-machines.
# ABOUTME: A tool-less model picks one skill from a list; a hit is the skill's name on the first line.
"""Usage: uv run --no-project python evals/route.py --out DIR --desc NAME=TEXT_OR_FILE [--desc ...]
          [--reps 3] [--model sonnet] [--jobs 8]

For each description, each case in routing.json runs --reps times. The model sees the
neighbor skills from routing.json plus implicit-state-machines with that description, and
answers with one skill name or "none". Raw answers land in <out>/<name>/<case>-<rep>.txt.
The table printed at the end counts first-line picks of implicit-state-machines.
"""
import argparse
import json
import os
import random
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = "implicit-state-machines"


def frontmatter_description(text):
    for line in text.splitlines():
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip()
    return text.strip()


def prompt_for(skills, request, seed):
    names = sorted(skills)
    random.Random(seed).shuffle(names)
    listing = "\n".join(f"- {n}: {skills[n]}" for n in names)
    return (
        "You are a coding agent. These skills are available:\n\n"
        f"{listing}\n\n"
        "A user sends the request below. Which one skill do you load first?\n"
        "Answer with the skill's exact name alone on the first line, or `none` if no skill fits. "
        "Then give one sentence of reasoning.\n\n"
        f"Request: {request}"
    )


def one(out, name, skills, case, request, rep, model):
    path = out / name / f"{case}-{rep}.txt"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_EFFORT_LEVEL"}
        cmd = ["claude", "-p", "--safe-mode", "--tools", "", "--model", model,
               prompt_for(skills, request, f"{case}-{rep}")]
        res = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, env=env,
                             cwd=out)
        path.write_text(res.stdout or f"(no output) {res.stderr[:500]}")
    lines = path.read_text().strip().splitlines()
    first = lines[0] if lines else ""
    return name, case, first.strip().strip("`*").lower() == SKILL


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--desc", action="append", required=True, help="name=description text, or name=path/to/SKILL.md")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()
    cfg = json.loads((HERE / "routing.json").read_text())
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    jobs, names = [], []
    for spec in a.desc:
        name, _, value = spec.partition("=")
        text = frontmatter_description(Path(value).read_text()) if Path(value).is_file() else value
        names.append(name)
        skills = dict(cfg["neighbors"], **{SKILL: text})
        for case, c in cfg["cases"].items():
            for rep in range(1, a.reps + 1):
                jobs.append((out, name, skills, case, c["request"], rep, a.model))
    hits = {}
    with ThreadPoolExecutor(a.jobs) as pool:
        for name, case, hit in pool.map(lambda j: one(*j), jobs):
            hits[(name, case)] = hits.get((name, case), 0) + hit
    print(f"picks of {SKILL} out of {a.reps} (want = should it be picked)")
    print("case".ljust(24) + "want".ljust(6) + "".join(n.ljust(10) for n in names))
    for case, c in cfg["cases"].items():
        print(case.ljust(24) + ("yes" if c["expect"] else "no").ljust(6)
              + "".join(str(hits[(n, case)]).ljust(10) for n in names))


if __name__ == "__main__":
    main()
