# BrowseComp / LiveBrowseComp / K-BrowseComp

> Worked example of the template. Fill the `[URL: …]` placeholders during a
> Workflow C research pass — the intuitions below are seeded from in-house
> observation, NOT yet literature-confirmed. Treat unconfirmed rows as TODO.

## What it measures
Hard browsing QA with **short, verifiable answers** (a name, number, or entity).
The model must locate obscure facts behind multi-hop constraints. Short-answer
format is what makes `answer_in_cot` / `unsupported_correct` precise here.

## Data-construction levers  (→ to RAISE the score)
- Evidence-grounded answers — keep only trajectories whose final answer is
  supported by a tool response (`unsupported_correct` survivors). — [URL: …]
- Query diversity — multi-angle decomposition beats repeated near-identical
  queries (`query_redundancy`). — [URL: …]
- Best-of-N / rejection-SFT — winning rollouts are partly luck (search surfaces
  the answer); prompt-only gains are bounded. — see memory `browsecomp_*`

## Failure modes in trajectories  (→ to DETECT & remove)
| failure mode | symptom in D | detector | threshold / note | source |
|---|---|---|---|---|
| answer known a priori | answer in reasoning before first search | answer_in_cot | τ=0.5 (flags score≥0.75) | in-house |
| memory-recited correct | correct but answer in no observation | unsupported_correct | assume_correct=true, τ=0.5 | in-house |
| over-searching | search count ≈2× peer models | search_volume | τ=25 (preset) | in-house |
| redundant queries | high pairwise query similarity | query_redundancy | τ=0.5 | in-house |
| context bloat | accumulated results crowd context | context_bloat | τ=8000 tok | in-house |
| confidence saturates | confidence ≈100% regardless of correctness | confidence_saturation + calibration | ceiling_fraction, ECE | in-house |

## Open intuitions (status — updated from the 2026-06-30 harvest, see hypotheses.md)
- "long search chains hurt via context noise" — **CONFIRMED (external, multi-lab)**:
  GLM-5 keep-recent-k=5 → BrowseComp +6.7; DeepSeek-V3.2 compact@80%-of-128K → +16.2;
  Mythos 86.9% at 4.9× fewer tokens/task; Gemini MRCR 128k→1M drops 84.9→26.3. Tie
  `context_bloat` threshold to a fraction of the context window. → still confirm on YOUR D.
- "answer known a priori / memory-recited" — **CONFIRMED (external)**: Mythos runs a
  no-tool closed-book BrowseComp pass (24.0% correct; ≤5k-tok 15.1% = memorization upper
  bound); WebSailor reconstructs traces to "prevent answer leakage". → strongest test is the
  no-tool ablation (H-20 `answer_recall_no_tool`); `answer_in_cot`/`unsupported_correct` are
  the within-trajectory proxies.
- "confidence saturates at 100%, ECE uninformative" — **partially external**: Opus 4.8 &
  Mythos both adopt **net = correct − incorrect** + abstention rather than ECE alone. Needs a
  confidence field in the rollout; check `calibration.ceiling_fraction` + net-score.
- "BrowseComp over-searches ~2× peers" — **nuance flagged**: GPT-5.5/Mythos show high search
  ≠ failure (bottleneck is lead-selection *judgment*, not breadth); measure `search_volume`
  p50/p90 vs a peer AND correlate with correctness before treating volume as bad.

## Recommended audit command
```bash
# eval rollouts WITH gold + confidence:
python detectors/run_audit.py --data rollouts.jsonl --field-map field_map.yaml \
  --benchmark browsecomp --out flags.jsonl --aggregate

# gold-less SFT trajectories (open2_official search_*): use the trajectory's own
# answer, assume accepted-correct, entity match for short answers:
python detectors/run_audit.py --data D.jsonl --field-map field_map.yaml \
  --benchmark browsecomp \
  --opt unsupported_correct.assume_correct=true \
  --opt unsupported_correct.evidence_mode=entity \
  --opt answer_in_cot.evidence_mode=entity \
  --out flags.jsonl --aggregate
```
