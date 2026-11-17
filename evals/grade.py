# ABOUTME: Mechanical checks over eval run directories made by run.py: commit order, probes of converted code.
# ABOUTME: Prints one line per run and counts per arm and scenario. Read the runs it flags; it does not judge prose.
"""Usage: uv run --no-project python evals/grade.py RUNS_DIR

Columns (blank = does not apply to that run):
  code      the run changed files under depot/
  report1st the first commit holds only docs/ (the audit report went in before any code)
  pins1st   every commit that changes depot/ follows a tests-only commit made since the last depot/ commit
  pinsgreen the suite passes at the first pins commit of each machine (pins pass on unchanged code)
  1machine  no commit changes two machines
  oldtests  tests/test_orders.py and tests/test_tickets.py lost no line
  paid      a paid order is still stored and served as 'paid'
  nosentinel a cancelled running job is not stored as failed with 'cancel' in last_error
  badrow    a job stored as running+failed can still be completed
  suite     the full test suite passes at the end
  record    docs/ at HEAD plus final.md hold each of the eight conversion record labels, once per converted machine
  finalmsg  final.md carries the Open decisions and Not verified labels
"""
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

MACHINES = {
    "orders": {"depot/orders.py", "depot/webhooks.py", "depot/fulfilment.py", "depot/api.py",
               "depot/order_state.py"},
    "jobs": {"depot/jobs.py"},
    "checkout": {"depot/checkout.py"},
    "uploads": {"depot/uploads.py"},
}
CHECKS = ["code", "report1st", "pins1st", "pinsgreen", "1machine", "oldtests", "paid", "nosentinel", "badrow", "suite",
          "record", "finalmsg"]
RECORD_LABELS = ["Pins", "Impossible states closed", "Behavior changes", "Choices made without (?:the user|you)",
                 "Contracts", "Stored impossible rows", "Open decisions", "Not verified"]

PROBE = r"""
import sys
from depot import db
which = sys.argv[1]
c = db.connect()
if which == "paid":
    from depot import orders, webhooks, api
    o = orders.create_order(c, 100)
    webhooks.payment_succeeded(c, o)
    ok = orders.get_order(c, o)["status"] == "paid" and api.order_json(c, o)["status"] == "paid"
elif which == "nosentinel":
    from depot import jobs
    j = jobs.enqueue(c, "x"); jobs.start(c, j)
    try:
        jobs.cancel(c, j)
    except Exception:
        pass
    row = c.execute("SELECT * FROM jobs WHERE id = ?", (j,)).fetchone()
    ok = not (row["failed"] and "cancel" in (row["last_error"] or "").lower())
elif which == "badrow":
    from depot import jobs
    c.execute("INSERT INTO jobs (kind, running, failed, done, attempts) VALUES ('x', 1, 1, 0, 2)")
    c.commit()
    jobs.complete(c, 1)
    ok = c.execute("SELECT done FROM jobs WHERE id = 1").fetchone()["done"] == 1
print("PASS" if ok else "FAIL")
"""


def sh(work, *cmd, stdin=None):
    return subprocess.run(cmd, cwd=work, capture_output=True, text=True, input=stdin)


def probe(work, which):
    res = sh(work, sys.executable, "-B", "-", which, stdin=PROBE)
    return res.stdout.strip() == "PASS"


def suite_at(work, sha):
    with tempfile.TemporaryDirectory() as tmp:
        tar = subprocess.run(["git", "archive", sha], cwd=work, capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", tmp], input=tar)
        return sh(tmp, sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests").returncode == 0


def label_count(text, label):
    """Count lines that open with the label, after list, heading, quote or bold marks."""
    return len(re.findall(rf"(?im)^[\s>*#|-]*{label}\b", text))


def commits(work):
    base = sh(work, "git", "rev-list", "--max-parents=0", "HEAD").stdout.split()[0]
    out = []
    for sha in sh(work, "git", "rev-list", "--reverse", f"{base}..HEAD").stdout.split():
        files = sh(work, "git", "show", "--name-only", "--format=", sha).stdout.split()
        out.append((sha, set(files)))
    return base, out


def grade(run):
    work = run / "work"
    base, cs = commits(work)
    changed = {f for f in sh(work, "git", "diff", "--name-only", base, "--", "depot").stdout.split()
               if f.endswith(".py")}
    r = {"code": bool(changed)}
    if not changed:
        return r
    touched = {m for m, files in MACHINES.items() if files & changed}
    r["report1st"] = bool(cs) and all(f.startswith("docs/") for f in cs[0][1])
    pins_ready, ok, pins_green = False, True, True
    for sha, files in cs:
        if any(f.startswith("depot/") for f in files):
            ok = ok and pins_ready
            pins_ready = False
        elif files and all(f.startswith("tests/") for f in files):
            if not pins_ready:
                pins_green = pins_green and suite_at(work, sha)
            pins_ready = True
    r["pins1st"] = ok and bool(cs)
    if r["pins1st"]:
        r["pinsgreen"] = pins_green
    r["1machine"] = bool(cs) and all(
        sum(bool(files & mf) for mf in MACHINES.values()) <= 1 for _, files in cs
    )
    numstat = sh(work, "git", "diff", "--numstat", base, "--", "tests/test_orders.py", "tests/test_tickets.py").stdout
    r["oldtests"] = all(line.split()[1] == "0" for line in numstat.splitlines())
    if "orders" in touched:
        r["paid"] = probe(work, "paid")
    if "jobs" in touched:
        r["nosentinel"] = probe(work, "nosentinel")
        r["badrow"] = probe(work, "badrow")
    r["suite"] = sh(work, sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests").returncode == 0
    final = (run / "final.md").read_text()
    docs = "\n".join(sh(work, "git", "show", f"HEAD:{f}").stdout
                     for f in sh(work, "git", "ls-tree", "-r", "--name-only", "HEAD", "docs").stdout.split())
    r["record"] = all(label_count(final + "\n" + docs, lab) >= len(touched) for lab in RECORD_LABELS)
    r["finalmsg"] = all(label_count(final, lab) >= 1 for lab in ("Open decisions", "Not verified"))
    return r


def main():
    root = Path(sys.argv[1])
    totals = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    print("run".ljust(40) + "".join(c.ljust(11) for c in CHECKS))
    for run in sorted(p for p in root.glob("*/*") if (p / "work").is_dir()):
        r = grade(run)
        arm, scenario = run.parent.name, run.name.rsplit("-", 1)[0]
        cells = []
        for c in CHECKS:
            if c in r:
                totals[(arm, scenario)][c][0] += r[c]
                totals[(arm, scenario)][c][1] += 1
                cells.append("yes" if r[c] else "NO")
            else:
                cells.append("")
        print(f"{arm}/{run.name}".ljust(40) + "".join(x.ljust(11) for x in cells))
    print()
    print("arm/scenario".ljust(40) + "".join(c.ljust(11) for c in CHECKS))
    for (arm, scenario), t in sorted(totals.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print(f"{arm}/{scenario}".ljust(40) + "".join(
            (f"{t[c][0]}/{t[c][1]}" if c in t else "").ljust(11) for c in CHECKS))


if __name__ == "__main__":
    main()
