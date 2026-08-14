---
name: stat-gate
description: >-
  Decide whether an eval delta is real before it becomes a claim: paired bootstrap CI on the same
  items, the measured noise floor from repeated runs of one config, and the required-n / minimum
  detectable effect for a planned comparison. Turns exp-loop's UNDERPOWERED verdict from a judgment
  call into a computed one. Use before reporting any A-vs-B number, when a gain looks small, when
  deciding how many repeats a sweep needs, or when a previously-reported gain fails to reproduce.
  Triggers - "/stat-gate", "이 차이 유의미해?", "노이즈인가", "몇 번 돌려야 해", "n_repeats",
  "유의성", "델타 진짜야", "재현이 안 되는데".
trigger: /stat-gate
---

# /stat-gate — is the delta real, and if not, what would settle it

Agentic evals are noisy in a specific, measurable way, and the failure mode is always the same
direction: a delta inside the noise gets written down as a gain, survives a few slides, and
evaporates when someone reruns it. **A delta below the floor is not a small result; it is no
result.**

Checker: `assets/power.py`. Three modes, all offline, no dependencies.

## Usage

```
python3 ~/.claude/skills/stat-gate/assets/power.py compare --a runA.jsonl --b runB.jsonl
python3 ~/.claude/skills/stat-gate/assets/power.py floor run1.jsonl run2.jsonl run3.jsonl
python3 ~/.claude/skills/stat-gate/assets/power.py design --sd 0.45 --target 0.02 --n 500
```

**Input**: JSONL, a JSON array, or a JSON summary document with a per-item list (`results`/`items`/
`records`/`predictions`/`samples`) — the shape real harnesses actually write. Each record needs an
id (`id`/`task_id`/`question_id`/`idx`) and a score (`correct`/`score`/`em`/`pass`/`reward`/`acc`),
auto-detected. Booleans written as the **strings** `"True"`/`"False"` are handled, because that is
what the harness emits.

**A missing score is not a zero.** Empty/`null` score cells are excluded and counted, never scored
as incorrect — silently converting missing to wrong biases the arm downward, which is the same
under-report trap that makes a broken cost recorder report a comfortable number. The exclusion count
prints to stderr; if it is large, fix the harness before trusting the comparison.

Exit `1` = SIGNIFICANT (the case that changes what you do next), `0` = a verdict was produced,
`2` = inputs unusable.

## The three questions

**1. `compare` — is B better than A?**
Pairs on item id and bootstraps the mean paired difference. Pairing is not optional: the same items
under two arms share their difficulty, so an unpaired mean comparison throws away most of the power
and is what makes small deltas look ambiguous. Reports delta, 95% CI, per-item flip rate, and this
design's MDE.

**2. `floor` — how much does the number move when nothing changes?**
Give it 2+ runs of the *same* config. This is the only honest source for "what counts as noise
here" — an assumed floor is a guess.

A result worth internalising, measured on a 500-item binary set with ~20% per-item instability:

| quantity | value |
|---|---|
| items that changed answer between runs | **19.4%** |
| run-to-run spread of the **mean** | **0.002** |

Flips cancel. The aggregate is far more stable than the per-item churn suggests — so a 2pp mean
delta can be real, while **any per-item claim** ("we fixed these 30 cases") at that flip rate is
nearly pure noise. Treat the two kinds of claim with completely different scepticism.

**3. `design` — before spending the GPU time.**
Given sd of the paired difference and the delta you care about, it prints the required n and the MDE
of the plan you have. Run this *before* the sweep. Discovering that 500 items could never have
resolved 2pp is much cheaper as arithmetic than as a week of runs.

## The reporting contract

A number leaves this skill with four things attached, or it does not leave:

1. **n** — paired items actually compared (not the item count you intended)
2. **the CI**, not just the point estimate
3. **the repeat count** and, if available, the measured floor
4. **which items were excluded** from the pairing and why

"MCP-Atlas 29.2%" is not a result. "29.2% vs 28.1%, +1.1pp, 95% CI [−0.4, +2.6], n=500 paired,
3 repeats, floor 0.2pp" is.

## Gotchas

- **Never compare across harness versions.** A baseline measured under an older harness is not a
  comparator. Re-run it; this is the most common way a gain evaporates later.
- **A rate-preserving null still shows movement.** When building a sanity fixture, note that
  flipping a fixed fraction of binary items *symmetrically* pushes the rate toward 0.5 — that is a
  real effect, not noise. A correct null re-draws from the same distribution. (This bit the
  construction of this skill's own test fixture: the tool was right and the test was wrong.)
- **MDE is a property of the design, not the result.** If MDE is +5pp, a reported +2pp gain was
  never measurable, regardless of which way it came out.
- **Significant *below* MDE is the replication-failure profile.** A delta can clear the 95% CI while
  sitting under the design's MDE — not a contradiction (MDE is the 80%-power threshold), but an
  effect that size lands inside the CI on a rerun about as often as not. The checker prints a
  CAUTION for exactly this case. Two results can both read "SIGNIFICANT" while one is safe to build
  on and the other needs a repeat; the point estimate alone does not distinguish them.
- **Measure the floor per benchmark, not once.** On the same checkpoint, one benchmark's run-to-run
  mean spread came in at 0.0101 and another's at 0.0030 — a 3× difference. A single global
  `n_repeats` rule therefore over-spends on one and under-powers the other.
- **Bootstrap seed is fixed** so a rerun reproduces the CI. If you change `--seed` and the verdict
  flips, the verdict was never stable — report that instead.
- **`compare` refuses unpaired data.** No overlapping ids means the comparison is not interpretable;
  align the item sets rather than falling back to comparing means.
- **Significance is not importance.** With enough items a trivial delta becomes significant. Ask
  whether the effect is large enough to change a decision before reporting it as one.

## Composition

- **← exp-loop** — stage 4/5. The `UNDERPOWERED` verdict is this skill's `compare` output; the
  predicted-vs-observed score should carry the CI.
- **→ exp-loop** — `design` output belongs in the stage-1 entry, so the prediction is registered
  against a design that could actually detect it.
- **→ lesson-loop** — a gain that fails to reproduce is a calibration finding, not just a bad run.
