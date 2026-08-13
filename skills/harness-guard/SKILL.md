---
name: harness-guard
description: >-
  Pre-flight a Slurm submission or serving script before sbatch: partition, shared-vs-unshared
  storage, conda env, input/checkpoint paths, uv cache, flashinfer workspace, ROCR unset, HF_HOME,
  requeue safety, stale script references. Runs an executable checker rather than a prose
  checklist, so the rules fire every time. The gate stage of the discovery loop and the
  destination for any lesson that is mechanically detectable. Use before submitting any job,
  when a job failed for a procedural reason, or when installing a new check.
  Triggers - "/harness-guard", "sbatch 전 점검", "제출 전 확인", "pre-flight", "job 왜 죽었지",
  "이 스크립트 돌려도 돼?".
trigger: /harness-guard
---

# /harness-guard — the checks that run every time

`CLAUDE.md` already carries the pre-submission checklist, and jobs still died on the same four
things. The difference here is that the checklist **executes**: a rule nobody has to remember is
the only kind that holds up at 2am on the eighth resubmission.

Checker: `assets/preflight.py`. Every check in it exists because that failure actually happened.

## Usage

```
python3 ~/.claude/skills/harness-guard/assets/preflight.py <script.slurm>
python3 ~/.claude/skills/harness-guard/assets/preflight.py <script> --strict   # WARN blocks too
python3 ~/.claude/skills/harness-guard/assets/preflight.py <script> --json     # for exp-loop
```

Exit `0` = clear to submit · `1` = at least one FAIL (or a WARN under `--strict`) · `2` = no script.

## The contract

- **FAIL blocks.** Do not submit. Do not "just try it" — every one of these has already cost a
  queue slot and a debugging session.
- **WARN must be read and accepted out loud.** Say which WARN you are accepting and why. An
  unexamined WARN is a FAIL you have not met yet.
- **SKIP is honest, not clean.** It means the check could not evaluate (feature not used, path
  templated). Never read SKIP as PASS.
- **A check that errors reports SKIP with the exception**, never PASS. A checker that lies about
  coverage is worse than no checker, because it stops you looking.

## What it checks, and why each is there

| Check | Level | The failure it encodes |
|---|---|---|
| `partition` | FAIL | Only `<preemptible-partition>` may be used; `<standard-partition>` is off-limits |
| `shared-storage` | FAIL/WARN | `<home>` is **not** shared across Slurm nodes — inputs, scripts and checkpoints must sit under `<shared-work>` or `<shared-fs>` |
| `conda-env` | FAIL | Training always runs in the `torchtitan` env; another env silently trains with the wrong stack |
| `paths-exist` | FAIL | Literal input/checkpoint paths that no longer exist after a refactor — the most common procedural failure |
| `script-refs` | FAIL | A submit wrapper pointing at a moved/renamed sbatch file runs the wrong thing or dies late |
| `uv-cache` | FAIL | On requeue a shared uv cache collides and the job FAILs immediately; needs a per-job `UV_CACHE_DIR` |
| `rocr` | FAIL | The cluster sets ROCR and CUDA visible devices together; verl workers die until `ROCR_VISIBLE_DEVICES` is unset |
| `flashinfer` | WARN | A shared flashinfer JIT cache causes ninja build failures across concurrent jobs |
| `hf-home` | WARN | Unset `HF_HOME` lands the cache in an unshared home dir; `/tmp` here is tmpfs and has filled mid-run |
| `requeue` | WARN | Requeue into a reused run dir collides with the previous attempt's state |
| `serve-teardown` | WARN | `scancel` the serving job the moment its consumer eval finishes — an idle server bills GPU-hours against nothing |

## What it deliberately does NOT check

Say these out loud before submitting; the checker cannot see them:

- **Retriever mode match** — server-based vs local retriever must agree between the submit wrapper
  and the sbatch file. Also verify the retriever env actually has `fastapi`, `uvicorn`, `faiss`,
  `torch`, `transformers` — a partial env fails only once the job is running.
- **Input data *count*** — the checker confirms a path exists, not that it holds the expected number
  of rows. A silently truncated dataset trains fine and scores low.
- **Comparison matching** — same harness, prompt, decode settings and checkpoint-selection rule as
  the baseline. Unmatched comparisons produce numbers that have to be thrown away.
- **Cost ceiling** — for anything hitting a paid API, state the cancel threshold before starting,
  and remember paid-API code gets reviewed three times before it runs.

## Installing a new check (this is how the loop closes)

`lesson-loop` routes anything mechanically detectable here. To install one:

1. **Write the detector as a one-liner first** and confirm it fires on the real failing script.
2. Add a `check_<name>(c)` function in `assets/preflight.py` returning
   `r(id, LEVEL, title, evidence, fix)`; append it to `CHECKS`.
   - `FAIL` only if submitting anyway is *always* wrong. Otherwise `WARN`.
   - Return `SKIP` with a reason whenever the condition does not apply — never `PASS`.
   - The `fix` string must be actionable on its own; it is what gets read under time pressure.
3. **Prove it both ways**: run against a script that has the defect (expect FAIL/WARN) and one that
   does not (expect PASS/SKIP). A check only verified in one direction is how false confidence gets
   installed.
4. `python3 -c "import ast,io;ast.parse(io.open('assets/preflight.py').read())"` must pass.
5. Add the row to the table above, then delete the corresponding entry from `tasks/lessons.md` —
   the lesson has become a check and no longer needs prose.

## Gotchas

- **Over-broad checks get the whole tool ignored.** Encode the specific condition that failed, not a
  blanket ban. One noisy FAIL and the next person starts skipping the run.
- **Expansion is one level deep and heuristic.** Heavily templated scripts will produce SKIPs — that
  is the checker being honest, and it means you check those by hand.
- **A green run is not a correctness proof.** It says the known procedural traps are clear; it says
  nothing about whether the experiment is well-posed. That is `exp-loop`'s job.

## Composition

- **← lesson-loop** — every lesson with a real `detector:` line lands here.
- **← exp-loop** — stage-2 gate before every submission.
- **→ exp-loop** — `--json` output is consumable as the pre-flight record for the ledger entry.
