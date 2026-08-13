---
name: cost-governor
description: >-
  Price a paid-API run before it scales and gate it on a hard USD ceiling, using the run's OWN
  per-call cost records — never an account balance, which moves for unrelated reasons. Blocks when
  the recorder is under-reporting, when spend reaches the ceiling, and when a measured pilot
  projects over the ceiling at full scale. Use before launching anything that calls a paid API,
  while a synthesis/eval fleet is burning, or when setting a budget for a round of experiments.
  Triggers - "/cost-governor", "비용 확인", "얼마 썼지", "예산", "돈 얼마나 나가", "cost ceiling",
  "스케일 올려도 돼?", "API 비용".
trigger: /cost-governor
---

# /cost-governor — measure the pilot, then decide the scale

Estimates for multi-round agentic runs have come in at **5–10× low**, because rounds multiply and
retries never appear in the arithmetic. And the obvious instrument — the account balance — is the
wrong one: it moves for reasons unrelated to this run, and reading it as "my spend" once produced a
**170× over-estimate that killed a healthy fleet**.

So this skill enforces one discipline: **price a measured pilot from the run's own per-call records,
then project.** Nothing else is admissible evidence about cost.

Checker: `assets/burn.py`.

## Usage

```
python3 ~/.claude/skills/cost-governor/assets/burn.py <dir|glob> --ceiling 500
python3 ~/.claude/skills/cost-governor/assets/burn.py <glob> --ceiling 1000 --project 60000
python3 ~/.claude/skills/cost-governor/assets/burn.py <glob> --ceiling 500 --json
```

Exit `0` under ceiling · `1` at/over ceiling **or** projected over · `2` records untrustworthy.

Exit `1` and `2` are both blocking — wire the call into a driver loop so the fleet stops on its own.

## The three gates

| Gate | Trips when | Why it exists |
|---|---|---|
| **Ceiling** | summed per-call spend ≥ ceiling | The stop that should have been automatic. Cancel the fleet. |
| **Projection** | measured $/record × target N ≥ ceiling | Catches the overrun **before** it happens. This is the gate that pays for itself. |
| **Trust** | >2% of records carry no cost field | A recorder that silently drops costs makes the total an under-estimate, so the ceiling never trips. Reported spend that is *too low* is the dangerous failure, not the obvious one. |

The trust gate is the non-obvious one and the reason this is a script rather than a habit. A cost
tracker that skips malformed records reports a comfortable number right up until the bill arrives.

## The workflow

1. **Set the ceiling first, in writing**, before any paid call. A ceiling decided after seeing the
   spend is not a ceiling.
2. **Run a pilot** — a few hundred records, not a few. Price it with `burn.py`.
3. **Project to full scale** with `--project N`. If it trips, re-scope or raise the ceiling
   *deliberately*; do not discover it at record N.
4. **Gate the driver loop** on the exit code so the fleet stops without a human watching.
5. **Record the measured $/record in the experiment ledger** alongside the result. Cost per accepted
   item is a property of the pipeline worth tracking across versions, not a one-off.

## What counts as a record

Any JSONL line carrying a per-call cost — the checker looks for `cost` / `total_cost` / `cost_usd` /
`usd` / `price`, at top level or nested under `usage`, `response`, or `response.usage`. It **never
infers a price from token counts**: a wrong price table produces a confident wrong number, which is
worse than an explicit "no cost field".

If your recorder does not write per-call cost, fix the recorder — that is the prerequisite, and the
trust gate will block until it is done.

## Gotchas

- **Never poll an account balance for this.** It is not your run's spend. This has already caused a
  170× false reading and a needless fleet kill.
- **Never sum an estimate.** Only the run's own recorded per-call cost counts.
- **Watch the denominator.** `$/record` over *attempted* records and over *accepted* records are
  different numbers; the second is the one that matters when a filter drops most output. State which
  one you are quoting.
- **Paid-API code gets reviewed three times before it runs.** The gate protects against overrun, not
  against a bug that calls the API in a loop.
- **A raised ceiling must be written down with a reason.** Silently raising it converts the gate into
  a formality, which is the same as not having it.

## Composition

- **← exp-loop** — stage 1 requires a cost estimate and a cancel threshold; this produces both.
- **→ exp-loop** — the measured $/record belongs in the ledger entry.
- **→ fleet-governor** — when the ceiling trips, that skill shows what is still alive and needs
  cancelling.
- **→ lesson-loop** — a blown estimate is a calibration finding worth recording, not just an incident.
