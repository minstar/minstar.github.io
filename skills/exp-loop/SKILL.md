---
name: exp-loop
description: >-
  Run one turn of the discovery loop over a training/eval experiment: state a falsifiable
  hypothesis with a PREDICTED number, pre-flight it through harness-guard, submit, watch, extract
  the real number from raw logs (never from a summary), score the prediction, and write the result
  plus the next experiment into the ledger. Use when starting an SFT/RL run or an eval sweep,
  when a submitted job finishes and the numbers need reading, or when deciding what to run next.
  Triggers - "/exp-loop", "실험 시작", "가설 세우고 돌리자", "이 job 결과 정리", "다음에 뭐 돌릴까",
  "eval 결과 확인", "실험 ledger".
trigger: /exp-loop
---

# /exp-loop — hypothesis → run → measure → fold back

The loop that makes a week of GPU time compound instead of accumulate. Its whole value is in two
places most experiment tracking skips: **a number predicted before the run**, and **the number
extracted from the raw log rather than from someone's summary.**

Ledger: `<daily-notes>/EXPERIMENT_LEDGER.md` (create if absent).
This is a record, not an input to compute nodes — it does not need shared storage.

## Usage

```
/exp-loop new "<hypothesis>"     # stage 1-2: sharpen the hypothesis, pre-flight, submit
/exp-loop watch <JOBID...>       # stage 3: track to completion
/exp-loop measure <JOBID|path>   # stage 4-5: extract real numbers, score the prediction
/exp-loop next                   # stage 6: propose the next experiment from the ledger
/exp-loop status                 # every open experiment and its state
```

## Stage 1 — Hypothesis (refuse to proceed without a prediction)

An entry cannot open without all four:

- **Claim**: one sentence, mechanistic. "v6 variant-B raises MCP-Atlas because think-only data
  removes ReAct-pattern contamination" — not "v6 variant-B is better".
- **Predicted number + interval**: the metric, the direction, and *how much* — "MCP-Atlas
  28.1% → 29.5±1.0". Committing to a number is what converts a run into evidence.
- **Falsifier**: what result would make you abandon the claim, stated now.
- **Cost**: GPU-hours or $ estimate, and — for anything hitting a paid API — the ceiling at which
  you cancel.

If you cannot state the prediction, the experiment is not ready; the honest move is a cheap probe
first. **A run with no prior prediction can still be recorded, but mark it `exploratory` — it does
not get to claim confirmation afterwards.** Post-hoc prediction is how a pipeline convinces itself
it understands something it does not.

## Stage 2 — Pre-flight (gate)

Call **harness-guard** on the submission script. Do not submit on a WARN you have not read. This
gate exists because the expensive failures in this pipeline are procedural, not scientific — a
wrong path, a stale script, a non-shared home directory.

Additionally, by hand:
- The script being submitted is the **current** one — submit wrappers have referenced stale sbatch
  files across refactors (e.g. after a retriever server/local switch).
- The comparison is **matched**: same eval harness, same prompt, same decode settings, same
  checkpoint-selection rule as the baseline you will compare against. An unmatched comparison
  produces a number you will have to throw away.

## Stage 3 — Watch

```bash
sacct -j <JOBID> --format=JobID,JobName%60,State%15,Elapsed --noheader
```

Prefer a background monitor over polling by hand. Record in the ledger the moment state changes to
`FAILED`/`TIMEOUT`/`PREEMPTED` — with preemptible partitions, preemption is normal and is **not** a
result; requeue and note it. Do not let a preemption get scored as a failed hypothesis.

## Stage 4 — Measure (raw logs only)

**The rule from `CLAUDE.md` §4, mechanized: read the number out of the raw output yourself.** Not
from a progress summary, not from a previous message, not from a subagent's report, not from the
last line of a script that may have exited early.

For every number that goes in the ledger, record **where it came from**: file path + how it was
extracted. A number without a provenance line is not admissible.

Checks that have caught real errors here:
- **Completion**: does the output contain the expected number of examples? Silent partial output
  (a truncated generation cap, an early exit) reads as a real, lower score.
- **Noise floor**: at temperature 1.0 a single rollout on browsing-style benchmarks flips ~20% of
  items. **A delta smaller than the noise floor is not a result** — require n_repeats ≥ 3 and report
  the spread, or say explicitly that the comparison is underpowered.
- **The flag actually applied**: some runners ignore a CLI limit when an experiment config is
  passed. Confirm the effective config in the log, not the command you typed.
- **Cost**: sum the per-call cost from the run's own records rather than polling an account balance
  — balance moves for reasons unrelated to this run.

## Stage 5 — Score the prediction

Write the outcome against the *prediction*, not against the baseline alone:

```
predicted 29.5 ±1.0  |  observed 28.4 (n=3, spread 27.9–29.0)  |  MISS (low)
```

Then classify the miss, because the classification is what determines the next move:

- **Scientific miss** — the mechanism was wrong. This is a result. Update the claim, keep it here.
- **Procedural miss** — wrong path, stale script, mismatched harness, partial output. This is **not**
  a result: discard the number, fix, re-run, and hand the cause to **lesson-loop**.
- **Underpowered** — the delta is inside the noise floor. Not a result. Either add repeats or
  redesign for a bigger effect.

Keeping these apart is the single highest-value discipline in the loop; conflating them lets a
pipeline bug masquerade as a finding, and lets a real finding get blamed on the infrastructure.

## Stage 6 — Fold back (this is what makes it a loop)

1. **Append to the ledger** (template below).
2. **Update the running calibration line**: hits / total, and mean signed prediction error. If
   predictions are systematically optimistic, that is itself a finding about how the pipeline is
   being reasoned about — and it is invisible without this tally.
3. **Propose the next experiment**, chosen against the ledger rather than against enthusiasm:
   - the largest *unexplained* gap between prediction and observation
   - the cheapest run that would discriminate between two live explanations
   - anything currently blocking a downstream decision
   Prefer the experiment that **shrinks an interval**, not the one that confirms a belief.
4. **Route any procedural cause** to `lesson-loop`.

## Ledger entry template

```markdown
## EXP-<NNN> · YYYY-MM-DD · <short name>          [open|done|discarded]
- **Claim**: <mechanistic sentence>
- **Predicted**: <metric> <baseline> → <predicted ± interval>       (or `exploratory`)
- **Falsifier**: <what would kill the claim>
- **Cost**: <estimate> / cancel at <ceiling>
- **Setup**: script `<path>` · job `<id>` · partition <preemptible-partition> · baseline `<run/ckpt>`
- **Observed**: <value> (n=<repeats>, spread <lo>–<hi>)
- **Provenance**: `<log path>` via `<extraction command>`
- **Verdict**: HIT | MISS(scientific) | MISS(procedural, discarded) | UNDERPOWERED
- **So what**: <the decision this changes>
- **Next**: <EXP-NNN or "none">
```

## Gotchas

- **The prediction is the product.** A ledger of results without predictions is a logbook; it does
  not build the calibration that tells you which of your beliefs about the pipeline are load-bearing.
- **Preemption is not evidence.** On `<preemptible-partition>`, requeue and continue; never score it.
- **Re-run the baseline when the harness changes.** A baseline measured under an older harness is not
  a valid comparator; carrying it forward silently is the most common way a "gain" evaporates later.
- **Serve jobs are part of the cost.** When an eval that needed a served model is done, `scancel` the
  serving job immediately — an idle server bills GPU-hours against nothing.
- **Do not let a summary become the source.** Every propagation step (log → script → summary →
  message) is a place a number can change. Go back to the log.
- **`exploratory` is an honest label, not a demotion.** Use it freely; what is not allowed is
  relabeling an exploratory run as a confirmation after seeing the result.

## Composition

- **→ harness-guard** — stage 2 gate.
- **→ lesson-loop** — every procedural miss.
- **← lesson-loop** — a lesson tagged as scientific rather than procedural belongs in this ledger,
  not in `tasks/lessons.md`.
