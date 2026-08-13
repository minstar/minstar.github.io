---
name: benchmark-data-audit
description: >-
  Audit and construct training data for agentic benchmarks (Search:
  BrowseComp/DeepSearchQA/DeepResearch/ReportGeneration/WideSearch/Ko-WideSearch/LiveBrowseComp/K-BrowseComp;
  MCP: MCP-mark/MCP-Atlas/Tool-Decathlon; Long-horizon: DeepPlanning; Tau2/Tau3).
  Use when reviewing or filtering a custom JSONL/arrow dataset of model trajectories
  to (1) detect harmful/contaminated samples — answer leakage in CoT,
  unsupported-correct (right-for-wrong-reason), excessive/redundant search,
  context bloat, saturated confidence — via deterministic formulas, and
  (2) decide what data to build to raise a benchmark, grounded in the target
  frontier models' technical reports / system cards / citing papers. Turns
  hypotheses about bad data into reproducible metrics + flags. Triggers:
  "데이터 검수", "trajectory 오염 탐지", "answer leakage", "over-search 분석",
  "benchmark 데이터 구성", "confidence calibration".
---

# benchmark-data-audit

Replaces hours of manual trajectory staring with **deterministic, reproducible
detectors** plus a literature-grounded data-construction guide. Built around the
gpt-oss `simple_browser` `search`/`open`/`find` taxonomy so browsing behavior is
audited per-verb.

## When to use
- You have a dataset `D` of model rollouts (reasoning + tool calls + answers +
  optional confidence) for any listed benchmark and want to **flag risky samples
  before training**.
- You have an **intuition** ("this benchmark over-searches", "confidence is
  always 100%") and want to (a) express it as a metric over `D` and (b) check
  whether the literature confirms it / offers a fix.
- You're planning **what data to create** and want the levers the target reports
  actually attribute gains to.

## Layout
- `schemas/schema.md` — the canonical normalized record every detector reads.
- `schemas/field_map.example.yaml` — copy to `field_map.yaml`, point it at YOUR
  field names. Edited **once**; all detectors then work. Supports both a chat
  `messages[]` array (e.g. open2_official `context`) and a flat tool-call list.
- `detectors/` — runnable Python. `README.md` has the **formal math** for each
  detector; `run_audit.py` is the CLI; `arrow_to_jsonl.py` converts HF arrow
  datasets to JSONL (pyarrow only, no `datasets` dep).
- `references/` — evidence base: `sources.md` (where external analyses live +
  seed URLs), `hypotheses.md` (harvested external-claim ledger → detector map,
  10 frontier sources as of 2026-06-30), and per-benchmark files (`browsecomp.md`
  worked example). Filled via Workflow C.

There are **26 detectors** (formal math in `detectors/README.md`):
- **8 core**: answer_in_cot, unsupported_correct, search_volume, query_redundancy,
  context_bloat, confidence_saturation, step_count, redundant_browsing.
- **+18 harvested** from frontier reports + benchmark papers: grader_speculation_in_cot,
  language_mixing, fabricated_tool_output, futile_retry_loop, uncited_source_claim,
  post_completion_loop, cot_length_floor, post_submit_refusal, answer_recall_no_tool,
  answer_source_retrieval, hallucinated_tool_name, malformed_tool_call, no_tool_call,
  fabricated_tool_args, ungrounded_output_value, over_answering, answer_item_dup,
  crud_state_assertion (state-based CRUD verification — see references/mcp_state_verification.md).
- Plus group-mode **difficulty_saturation** via `run_audit --group-by <field>` (per-group
  solve-rate ≈0/≈1; needs ≥2 rollouts/group). `run_audit` reads JSONL **or** HF arrow dirs.

---

## Workflow A — detect bad data in an existing D (deterministic)

0. **(arrow input)** Convert HF arrow shards to JSONL first:
   ```bash
   python detectors/arrow_to_jsonl.py /path/to/search_260605 --out D.jsonl --limit 2000
   ```

1. **Map your schema (once).**
   ```bash
   cp schemas/field_map.example.yaml field_map.yaml
   # edit field_map.yaml: dotted paths to your fields. See schemas/schema.md.
   uv pip install --system --break-system-packages pyyaml   # if missing
   ```

2. **Dry-run on a slice** to sanity-check the mapping (skipped-rate should be low):
   ```bash
   python detectors/run_audit.py --data D.jsonl --field-map field_map.yaml \
     --detectors answer_in_cot,unsupported_correct --limit 200 --out /tmp/probe.jsonl
   ```
   A high `skipped` count means the mapping isn't reaching a field — fix
   `field_map.yaml`, not the detector.

3. **Full audit** (all detectors + dataset calibration report):
   ```bash
   python detectors/run_audit.py --data D.jsonl --field-map field_map.yaml \
     --benchmark browsecomp --out flags.jsonl --aggregate
   ```
   Read the summary table (flag rate per detector) + `flags.calibration_report.json`.

4. **Tune thresholds from the score distribution** (the score is the raw formula
   output, independent of threshold). Examples:
   ```bash
   python detectors/run_audit.py --data D.jsonl --field-map field_map.yaml \
     --threshold search_volume=30 --threshold query_redundancy=0.55 \
     --threshold answer_in_cot=0.4 \
     --opt unsupported_correct.evidence_mode=entity \
     --opt unsupported_correct.support_threshold=0.3 \
     --only-flagged --out flags_strict.jsonl
   ```

5. **Act on flags.** `flags.jsonl` has one row per (sample, detector) with
   `score`, `threshold`, `flagged`, `reason`, `evidence`. Join back on
   `sample_id` to quarantine/remove or build a review queue. Because the metrics
   are deterministic, `(D, field_map, thresholds)` always reproduces the same
   flag set — diff two runs to audit a cleaning step.

6. **Validate the hypothesis** (does removing flagged data help?). Train/eval
   with vs. without the flagged subset; the flag columns make the ablation a
   one-line filter. Record the outcome in the relevant `references/*.md`.

### Gold-less SFT trajectories (no answer/correct/confidence column)
For accepted SFT traces (e.g. open2_official), the trajectory's own final answer
is used as the target and the sample is treated as correct:
```bash
python detectors/run_audit.py --data D.jsonl --field-map field_map.yaml \
  --benchmark browsecomp \
  --opt unsupported_correct.assume_correct=true \
  --opt unsupported_correct.evidence_mode=entity \
  --opt answer_in_cot.evidence_mode=entity \
  --out flags.jsonl --aggregate
```
`answer_in_cot` is **graded**: default flags only strong leakage (answer never
grounded, or stated before the first search); add `--threshold answer_in_cot=0.4`
to also surface the normal hypothesize-then-verify population for separate review.

## Workflow B — express a NEW intuition as a detector
1. Write the hypothesis as a formula over the normalized record (notation in
   `detectors/README.md`).
2. Add a `Detector` subclass (read only from `Record` → stays schema-agnostic),
   register it in `run_audit.py:REGISTRY`, document the math in the README.
3. Run it; inspect the score distribution (`--aggregate` prints percentiles);
   pick a threshold. Done — reproducible and shareable.

## Workflow C — harvest OTHER people's analyses, not just your own intuitions
Goal: systematically pull external hypotheses (labs' system cards, the
benchmark's paper, citing papers, model-org reports) about data quality / failure
modes / search behavior / calibration, and turn each into a detector mapping you
can confirm on `D`.

1. **Discover sources.** Start from `references/sources.md` (seed URLs + source
   types + standing discovery queries). Add new frontier releases as they ship.
2. **Harvest (fan out).** One focused subagent per source — read it, extract
   every claim of the form *(benchmark, claim, evidence, proposed fix)*, and map
   each to one of the 8 detectors or `NEW: <name>`. **Separate quotation from
   your interpretation.** Use the fan-out prompt in `sources.md`.
3. **Log.** Append harvested rows to `references/hypotheses.md` with citation
   URLs and `status: harvested`. This ledger is the external counterpart to your
   own intuitions.
4. **Map & act.** For each claim: existing detector → record threshold guidance
   in the per-benchmark `references/<benchmark>.md`; `NEW:` → add it via
   Workflow B.
5. **Confirm on D.** Run the mapped detector on your data; check whether the
   flagged subset behaves as the claim predicts. Update `status` to
   `confirmed-on-D` / `refuted-on-D` (with numbers) so it isn't re-litigated.

> Keep `references/<benchmark>.md` for the synthesized, benchmark-scoped view
> (levers + failure-mode→detector table); keep `hypotheses.md` as the raw,
> source-cited harvest log feeding it.

## Conventions
- Detectors NEVER guess: missing fields → `skipped`, never a wrong flag.
- `score` = raw formula value (higher = more suspicious where meaningful);
  `flagged` applies the threshold. Keep them separate.
- Keep the audit deterministic — no LLM calls inside detectors. LLM-as-judge
  belongs in a separate, clearly-labeled non-deterministic pass.
- Answer-matching detectors (`answer_in_cot`, `unsupported_correct`) are precise
  only with a CONCISE answer string. With long restated answers use
  `evidence_mode=entity` and treat output as a review queue, not ground truth.
