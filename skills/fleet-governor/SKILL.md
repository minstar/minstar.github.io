---
name: fleet-governor
description: >-
  Report on everything long-running at once — Slurm jobs and the autoretry/watch loops feeding them
  — and classify each as HEALTHY, WASTEFUL, FUTILE, or ORPHAN/STALE. Separates transient failure
  (preemption, node loss: retry is correct) from deterministic failure (ImportError, missing file,
  bad config: retrying can never clear it), which is the distinction no retry loop makes on its own.
  Reports only; killing is a human decision. Use when checking on running work, when a retry loop
  has been up a long time, when jobs keep failing, or before submitting more work.
  Triggers - "/fleet-governor", "돌고 있는거 확인", "job 상태", "fleet 점검", "루프 살아있나",
  "재시도 계속 도는데", "뭐가 돌고 있지".
trigger: /fleet-governor
---

# /fleet-governor — what is alive, and is it doing anything

An autoretry loop is *right* to resubmit a preempted job and *wrong* to resubmit a deterministic
one, and nothing in the stack tells the two apart. `EXP-001` priced that confusion at **224
single-digit-second resubmissions** across three arms — the science was fine, the arms finished, and
224 queue slots went to a module name that had never been created.

Checker: `assets/fleet.py`. It reports; it never kills.

## Usage

```
python3 ~/.claude/skills/fleet-governor/assets/fleet.py
python3 ~/.claude/skills/fleet-governor/assets/fleet.py --since 3days
python3 ~/.claude/skills/fleet-governor/assets/fleet.py --json
```

Exit `0` = nothing needs attention · `1` = at least one FUTILE / WASTEFUL / ORPHAN finding.

## The verdicts

| Verdict | Signature | What it means |
|---|---|---|
| `HEALTHY` | completions, or preemptions with no fast-fails | Working as intended. Preemption on a preemptible partition is **normal and is not a result.** |
| `WASTEFUL` | ≥5 fast-fails **alongside** completions | Real work is landing, but a deterministic error is also being resubmitted. The dangerous one — the completions make it look fine. |
| `FUTILE` | last ≥2 attempts all failed <10s with the same exit code, or ≥5 fast-fails and zero completions | Deterministic. More retries cannot help. Stop the loop and read the log. |
| `ORPHAN / STALE` | a loop with **no supervision evidence** — no declared-jobname/token/version link to a queued job, no recent job end, and no log line within its own poll window — or alive ≥3 days with none of the hard signals | A watcher outliving its run, often from a session nobody remembers. |

**The fast-fail signature** is the load-bearing idea: `FAILED` + identical exit code + elapsed
`00:00:0X`. A process that dies in two seconds never reached the work; it failed at import, at a
missing path, or at config parse. Preemption and time limits land as `CANCELLED`/`TIMEOUT` with
hours of elapsed time, so the two never collide.

## Reading the report

1. **Fix `FUTILE` before submitting anything else** — it is consuming queue slots for nothing.
2. **`WASTEFUL` is the one that hides.** Completions in the same window make the arm look healthy;
   the fast-fail column is the tell. Check it even when results are landing.
3. **`ORPHAN / STALE` needs a look, not a reflex kill.** A long-lived watcher may be legitimately
   waiting on a slow upstream (a conversion, a queue). Read its log first; the tool prints the pid
   rather than killing it precisely because that call is not mechanical.
4. **Serving jobs**: when the consuming eval is done, `scancel` immediately — an idle server bills
   GPU-hours against nothing.

## Composition

- **→ exp-loop** — a `FUTILE`/`WASTEFUL` verdict is a **procedural** miss, never a scientific one.
  Discard the numbers, fix, re-run; do not score it against a hypothesis.
- **→ lesson-loop** — route the cause. If it is mechanically detectable before submission, it
  belongs in `harness-guard` instead of in prose.
- **← harness-guard** — most `FUTILE` causes are preventable at submit time; the `module-refs`
  check exists because of EXP-001.

## Gotchas

- **Do not wire this to auto-kill.** The classifier is a heuristic over `sacct` states; a false
  `FUTILE` that scancels a real run costs far more than a missed one. Report, then decide.
- **Generic tokens create both false alarms and blind spots.** Matching a loop to its job on words
  like `eval` or `train` once hid a genuine 11-day orphan, because an unrelated path contained
  `eval`. The matcher uses distinctive tokens only, with **age as an independent second signal** —
  keep both; either alone misses cases.
- **A loop taking its job name as an argument will not match on its filename.** Match on the whole
  command line; `autoretry.sh <name> ...` is the common shape here.
- **Version-style arm names never survive word-token matching** (2026-08-15, three false orphan
  flags in one morning). `v36` is 3 chars — under the 4-char tokenizer floor — and `v36s` is under
  the 5-char containment floor, so `autoretry_v36{,s}.sh` could *never* link to jobs
  `<rl-run>-v36{,s}` while `perfroll`/`neweval` linked fine. The matcher now reads what the loop
  itself exposes, in order of authority: the JOBNAME its script declares (via `/proc/<pid>/fd/255`),
  boundary-exact version tokens (`v36` ≠ `v36s`, so arms never cross-link), a recent `sacct` end for
  the declared name, and its own log (`/proc/<pid>/fd/1`) written within its own poll interval
  (parsed from the script's `POLL=`/`sleep`). A loop with any of these is a supervisor; a genuine
  orphan — job gone AND log quiet past the poll window — still flags. `.chain_*`/`.retry_*` hidden
  chains are recognized as loops too; before 2026-08-15 they were invisible to this tool entirely.
- **`--since` matters.** A window shorter than the retry cadence makes a futile loop look new.
- **HEALTHY is not "correct".** It means nothing is *obviously* wasted. Whether the run is
  well-posed is `exp-loop`'s question, not this one's.
