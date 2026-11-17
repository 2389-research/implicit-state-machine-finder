# Results

## 2026-11-17

90 behavior runs on Sonnet through `claude -p --safe-mode`, Claude Code 2.1.322, at about $24
in total. The runs are archived in `~/eval-archives/implicit-state-machines/2026-11-17/`
(control, v1, v2, v3) and `~/eval-archives/implicit-state-machines/2026-11-17b/` (v4).
Rebuild the tables below with `uv run --no-project python evals/grade.py <folder>`.

Arms:

- **control**: no skill.
- **v1**: `arms/v1.md`, the skill as it stood before this work.
- **v2**: `arms/v2.md`, the first rewrite.
- **v3**: `arms/v3.md`. It differs from v2 in one step: pins are committed per machine, and
  only after the suite passes.
- **v4**: the current SKILL.md. It differs from v3 in the report: each machine's conversion
  record is a template filled in under `docs/` and committed with the conversion, and the final
  message is short and carries Open decisions and Not verified.

Five runs per cell. v3 and v4 ran the three conversion scenarios only; their changes do not
touch Phase 1.

### Conversion scenarios

Each cell counts runs that passed, out of the runs the check applies to.

| Check | control | v1 | v2 | v3 | v4 |
|---|---|---|---|---|---|
| **find-and-fix-away**: the audit report is committed before any code | 0/5 | 0/5 | 5/5 | 5/5 | 5/5 |
| **find-and-fix-away**: a tests-only commit precedes every conversion commit | 0/5 | 0/5 | 5/5 | 5/5 | 5/5 |
| **find-and-fix-away**: those pins pass on the unchanged code | n/a | n/a | 3/5 | 5/5 | 5/5 |
| **find-and-fix-away**: no commit changes two machines | 0/5 | 1/5 | 5/5 | 5/5 | 5/5 |
| **convert-under-pressure**: a tests-only commit precedes the conversion | 0/5 | 0/5 | 5/5 | 5/5 | 5/5 |
| **convert-under-pressure**: a paid order is still stored and served as `paid` | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| **convert-under-pressure**: the existing test files lost no line | 5/5 | 4/5 | 5/5 | 5/5 | 5/5 |
| **convert-two**: a tests-only commit precedes each machine's conversion | 0/5 | 0/5 | 4/5 | 5/5 | 5/5 |
| **convert-two**: no commit changes two machines | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Jobs converted: cancel is not stored as `failed` plus a `cancel` error string | 2/10 | 0/10 | 8/8 | 7/7 | 8/8 |
| Jobs converted: a job stored as running and failed can still be completed | 4/10 | 2/10 | 8/8 | 6/7 | 8/8 |
| The full suite passes at the end | 15/15 | 15/15 | 15/15 | 15/15 | 15/15 |
| Every converted machine has all eight record lines, in `docs/` or the final message | 0/15 | 0/15 | 1/15 | 0/15 | 15/15 |
| The final message carries Open decisions and Not verified | 0/15 | 0/15 | 5/15 | 6/15 | 15/15 |

Notes on reading the table:

- The "tests-only commit" check is strict. Two v1 convert-two runs did write pins first: one
  left them uncommitted, and one committed both machines' pins together. Neither counts.
- The one v2 miss on convert-two also committed both machines' pins together. The two v2 misses
  on "pins pass" committed a broken pin and fixed it in a later commit. v3's wording addressed
  both, and all 15 v3 runs pass both checks.
- The one v3 miss on the stored-row check is a choice, not a breach. The run mapped a row stored
  as running and failed to `failed`, said so, and gave the query. Reads do not raise. The skill
  asks for a named mapping; it does not say which state wins.
- The record check is strict: each of the eight labels must open a line once per converted
  machine. Under v2 and v3 the lines were asked for in the final message. Runs with a deadline
  in the request shortened that message and dropped lines; "Stored impossible rows" appeared in
  none of the ten v3 deadline runs. Those runs often held part of the content in free form, so
  0/15 overstates what was lost. v4 moved the lines into a template in the repo docs.
- I read the records of two v4 runs in full and counted records in all 15: one per converted
  machine in every run. The grader checks that the labels exist, not what the lines say.
- Under v2, v3 and v4, some find-and-fix-away runs left jobs unconverted. The gate allows that:
  it converts machines with money, data, or user-visible impact.
- Without any skill, all five convert-under-pressure runs renamed the stored `paid` value,
  which breaks the mobile app and the finance export named in the fixture README. v1 already
  prevented that.

What the failures looked like before the rewrite:

- **find-and-fix-away**: the agents read the code and began rewriting `orders.py` at once, with
  no report and no pins. They gave no reason; their notes went from "the audit found" to "I'm
  starting the fixes".
- **convert-under-pressure**: the agents skipped the pins and said so: "as you asked, I wrote
  none before the change". The user's claim that `tests/test_orders.py` covered the order path
  was false; it holds four happy-path tests.
- **Cancel sentinel**: converted jobs stored a cancelled job as `failed` with
  `last_error = 'cancelled'`. That is a new implicit state.

### Audit scenario

No arm changed code in any of its five audit runs. All 15 reports name the four planted
machines. The skill's gain here is the form of the report, not detection:

- v1 and v2 reports rank the machines in a summary table, list tickets, prefs and banner as
  "leave alone" with a reason, and end by asking which machines to convert.
- Control reports find the same bugs. Two of five have a table. Four of five also raise the
  already-explicit tickets module as something to fix. Three of five end without a question.

These counts come from keyword searches, and I read only some of the reports in full.

### Description routing

`route.py` gives a tool-less Sonnet nine neighbor skills plus this one, and one request.
With the current description, it picked this skill in 18 of 18 runs of the six requests that
should trigger it, and in 0 of 18 runs of the six that should not. The description was left
unchanged at first: it showed no failure to fix.

It was later replaced with a "Use when..." line that names only triggers and no workflow, as
writing-skills asks. The new line scored the same on the same cases: 18 of 18 and 0 of 18. The
v4 behavior runs were made before the swap; they put the whole file in the prompt, so they do
not test the description.

## What is not fixed, and what was not tested

- After conversion, cancelling a job still puts it back in the queue. The skill leaves that as
  pinned and lists it as an open decision, because a real cancelled state needs a schema change.
  The bug stays until someone approves the column.
- Only Sonnet ran. No Opus, Haiku or Fable runs.
- The fixture has 424 lines in one language. Nothing here tests a large repository, a typed
  language, or a front-end boolean cluster.
- The audit scenario shows no gain in detection. It needs a harder fixture: machines spread
  across more files, and a decoy that looks like a machine.
- No scenario has the user present and answering questions; headless runs cannot.
- Whether an agent follows the description's workflow summary instead of the body was not
  tested. The harness puts the whole skill in the prompt.
- `grade.py` checks commit order, probes the converted code, and finds the record labels. It
  does not judge whether a record line is true or complete.
- A network drop cut off eight v3 runs. They were deleted and run again; the table holds the
  reruns.
