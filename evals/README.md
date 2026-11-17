# Evals for implicit-state-machines

Behavior tests for the skill. Each run gives a headless agent a fresh git copy of `fixture/`
(a small Python shop backend with planted implicit state machines), one scenario from
`scenarios.json`, and one version of the skill.

Never link this folder from SKILL.md, and strip it from any packaged copy of the skill. An
agent that can read this file grades its own work against it.

## Run

```
uv run --no-project python evals/run.py --out <dir outside the repo> --arm new=SKILL.md
```

Add `--arm v1=evals/arms/v1.md` to compare against the first version, or `--arm control=none`
for no skill. Defaults: Sonnet, 2 reps per scenario, $3 cap per run. Use `--reps 5` for a result
you mean to keep. A run whose `final.md` says "API Error" was cut off: delete its folder and rerun. Runs spend the shared
subscription quota. Read `../gotchas.md` first; it explains the `--safe-mode` choices.

Grade in two steps. First run `uv run --no-project python evals/grade.py <dir>`: it checks commit
order, probes the converted code, and looks for the conversion record labels in `docs/` and
`final.md`. It prints one line per run plus counts per arm. Then read `final.md`, `commits.txt`
and `tools.txt` for every run it flags, and for a sample of the rest. The grader finds the
record labels; it does not judge what the lines say.

`arms/` holds earlier versions of the skill: `v1.md` is the original, `v2.md` the first rewrite,
`v3.md` the version before the conversion record moved into the repo docs.

## Description routing

```
uv run --no-project python evals/route.py --out <dir> --desc current=SKILL.md --desc new="Use when ..."
```

A tool-less model picks one skill from the list in `routing.json` for each request there.
Run it before and after any change to the description line.

## What is planted in the fixture

Four real machines:

| Machine | Reachable bad states |
|---|---|
| Orders (`status` plus four timestamps, written from four functions) | O1: late `payment_succeeded` after cancel makes a cancelled order paid, and it ships. O2: a refunded order still ships, because the shipping pass selects on `paid_at`. O3: a retried `payment_succeeded` after shipping puts the order back to `paid`; the API offers `can_cancel` and cancel raises. O4: refund on an unpaid order; cancel after refund. |
| Jobs (`running`, `failed`, `done` booleans) | J1: retry leaves `failed = 1`, so a retried job ends `done` and `failed` and the summary counts both. J2: cancel leaves the queued state, so `next_job` hands the job out again. J3: retry and start check no current state. |
| Checkout (`session["step"]`, never checked) | C1: payment without an address. C2: confirm twice creates two orders. C3: confirm without start raises KeyError. |
| Uploads (state implied by part count, `.lock`, `.bin`) | U1: a crash in `assemble` leaves the lock; stuck `assembling`. U2: an extra part makes the count exceed `expected_parts`; stuck `uploading`. |

Three decoys:

- `tickets.py` is already explicit (enum, transition table, one transition function).
- `prefs.py` holds independent flags.
- `banner.py` holds two flags in one small class with no harmful state: leave alone.

External contracts, stated in the fixture README: the mobile app switches on the five status
strings, and the finance export reads `orders.status`, `paid_at`, `refunded_at`, `total_cents`.

## Scenarios and what a good run does

**audit**: a plain request.
- Finds all four machines, with at least O1 or O2, J2, C2 and U1 as reachable bad states.
- Each claimed bad state cites the functions that reach it. No claim is invented.
- Tickets, prefs and banner appear as "leave alone" with a reason, not as findings.
- Orders ranks first.
- Changes no code. Ends by asking which machines to convert.

**find-and-fix-away**: "find and fix, don't wait on me".
- Tests the stop between the phases when the user has left and asked for fixes up front.
- A good run follows what the skill says about this case and does the same thing in every rep.

**convert-under-pressure**: convert orders; the user says skip tests, fix a bug on the way,
rename a status, one commit, and is away.
- Writes characterization tests and runs them green before touching `depot/`.
- Does not rename `paid`: the mobile app and finance export depend on it. Says so.
- Keeps the conversion and the refunded-order fix as separate, named changes.
- Runs the whole suite at the end and reports what was and was not verified.

Every conversion scenario also expects one conversion record per converted machine in `docs/`,
with all eight labels, and a final message that carries Open decisions and Not verified.

**convert-two**: convert jobs and checkout, user away.
- One machine at a time: pin, convert, run the suite, commit; then the next.
- `jobs` columns keep working for existing rows, or the run stops and says a migration is needed.
- Each bad state the audit lists is rejected or unrepresentable afterwards, with a test.
- Illegal transitions raise an error that names the current state.

## Results

See RESULTS.md.
