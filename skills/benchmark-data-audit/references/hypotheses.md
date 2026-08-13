# hypotheses.md — external analyses ledger

Claims **other people** (labs, papers) make about these benchmarks — kept
separate from your own intuitions (per-benchmark files). Harvested via Workflow C
from `sources.md`. `Q`=verbatim quote, `P`=paraphrase. **det?** = deterministic
implementability over an existing trajectory `D` (✅ pure fn of the record /
⚠️ needs extra data: grouped rollouts, judge labels, source metadata / ❌ needs an
LLM/NLI judge → belongs in a non-deterministic pass, not a detector).

## Harvest batch — 2026-06-30 (S1–S5 + Kimi)

### Cross-source corroboration of the EXISTING detectors
The detectors that were "my own intuition" are now independently supported:

- **context_bloat** — strongest, most quantified. **GLM-5**: keep-recent-k=5
  folding → BrowseComp **55.3→62.0 (+6.7)**, hybrid 32k-reset → 75.9 [S2 §4.2.4].
  **DeepSeek-V3.2**: compact at 80% of 128K → BrowseComp **51.4→67.6 (+16.2)**
  [S3 V3.2]. **Tongyi DR**: "cognitive suffocation / noise pollution" → per-round
  workspace reconstruction [S4]. **Kimi K2.5**: selective routing of only relevant
  sub-agent outputs vs "Discard-all" [Kimi §5.2]. **Opus 4.8**: compaction @200k
  (single) / @100k (orchestrator) [S1 §8.10.2]. → set the threshold as a FRACTION
  OF THE CONTEXT WINDOW (80%), and tie it to effective step budget.
- **answer_in_cot** — **WebSailor (Qwen)**: expert traces reconstructed to
  "**prevent answer leakage** while preserving reasoning logic" before SFT
  [S4 2507.02592]. **GLM-5** Stage-1 source filter: drop questions a tool-free
  model answers in ≥1/8 attempts [S2 §4.2.3] = construction-time version of the
  same signal. **Opus 4.8**: "Presenting an answer its own reasoning had shown to
  be wrong or had not actually derived" [S1 §6.2.2].
- **unsupported_correct** — **DeepSeekMath-V2**: "**correct answers don't
  guarantee correct reasoning**"; final-answer reward yields "mathematically
  invalid or logically inconsistent" proofs despite high accuracy [S3 2511.22570].
  **DeepSeek-V3.2**: keep a Q only if gold correct AND all distractors verifiably
  incorrect [S3]. **Tongyi DR**: rejection-sample to correct-outcome traces only.
- **confidence_saturation** — **Opus 4.8**: treats this as a "knowledge-
  calibration problem"; reports **net = correct − incorrect** so confident-wrong
  is penalized and abstention rewarded; claims a **10× overconfidence reduction**
  vs 4.7 [S1 §6.3.3, §6.3.6.4]. → adopt net-score as the calibration metric
  alongside ECE.
- **search_volume / step_count** — **Kimi K2.5**: budget-control reward cuts
  output tokens **25–30%** with negligible perf loss [Kimi §4.4.2]; score by
  **critical-path** steps not total. **Tongyi DR**: 50–128 tool-call cap; mask
  length-truncated non-answering traces. **DeepSeek-V3.2**: length penalty in
  reward. CAVEAT (two sources): length is **task-conditioned** — rigid caps
  over-prune hard cases (Kimi: "fail to generalize to higher compute scales";
  R1/V3.2 select the *longest* traces among correct). Flag relative-to-median,
  not absolute.
- **query_redundancy / redundant_browsing** — only weakly external: GLM-5 dedups
  >2M URLs & limits subgraph overlap [S2 §4.2.3]; Opus 4.8 notes "retrying a
  failed action many times" [S1 §6.2.2]. Largely YOUR contribution — not a
  headline lever in these reports.

### NEW detector candidates (harvested → ranked by det?)
| id | claim → detector | source | det? |
|----|------------------|--------|------|
| H-01 | **grader_speculation_in_cot** — CoT references grader/checker/hidden-tests/scoring-metric and shapes output toward passing vs solving; ~0.1% of Opus RL episodes. Keyword-scan of reasoning. | S1 §6.2.2 | ✅ |
| H-02 | **fabricated_tool_output** — answer/observation asserts a tool result with NO matching preceding tool call (invented observation); "leads the user to believe a tool was run and fabricates output" | S1 §6.3.3.4, §6.2.2 | ✅ structural |
| H-03 | **language_mixing** — target-language token ratio in CoT below threshold; R1 filtered "CoT with mixed languages" + added language-consistency reward | S3 R1 | ✅ |
| H-04 | **over_answering** — wide/list task returns more answer items than the gold set (precision-killing padding); DeepSearchQA "Correct w/ Excessive Answers" 4.3% | S1 §8.10.3 | ⚠️ needs gold-as-set |
| H-05 | **difficulty_saturation** — per-item solve-rate ≈0 or ≈1 across rollouts → no learning signal (drop). Two sources. | S4 Tongyi, S2 §3.2 | ⚠️ needs grouped rollouts |
| H-06 | **shallow_investigation** — definitive answer with too few read/trace steps to ground it; Opus 4.7 wrong 25% via shortcut-guessing | S1 §6.3.6.3 | ✅ (low-step + answer) |
| H-07 | **success_misreport** — final summary claims success while tool outputs show unmet goals (failing tests); Opus 4.8 3.7% vs Mythos 27.6% | S1 §6.3.6.2 | ⚠️ failure-marker heuristics |
| H-08 | **premature_termination** — stops before enough grounding; short steps + limitation framing on solvable tasks (early-stop as reward shortcut) | S1 §6.2.1.1, §6.1.3 | ⚠️ |
| H-09 | **retrieved_answer_contamination** — correct answer traces to a fetched page that itself contains the benchmark gold (web test leakage). Opus blocklists pages containing "browsecomp". | S1 §9.3 | ⚠️ needs source metadata |
| H-10 | **env_answer_leakage** — solution sourced from a reference artifact in the env (git history, build cache, hidden file) vs derived | S1 §6.2.2 | ⚠️ needs path/artifact info |
| H-11 | **judge_score_variance** — rubric/LLM-judge label flips across judge models/seeds; "judge can shift scores 10–25 pts"; pin judge+prompt before trusting labels | S1 §8.10.4, S2 §4.2.4 | ⚠️ needs multi-judge labels |
| H-12 | **verifier_window_gaming** — pads context with success tokens / suppresses failure strings to game a truncated-window or keyword grader | S1 §6.2.1.2 | ⚠️ |
| H-13 | **constraint_override** — CoT acknowledges an explicit constraint then violates it on rationalized grounds | S1 §6.2.1.2 | ❌ needs semantics |
| H-14 | **evidence_consistency_check** — final answer not uniquely entailed by cited observations (entailment + uniqueness) | S2 §4.2.3 | ❌ NLI/judge |
| H-15 | **spurious_parallelism** / **critical_path_steps** — subagents spawned without useful output; score by longest-dependency-chain not total steps | Kimi §3 | ⚠️ multi-agent structure only |
| H-16 | **error_segment_masking** — failed sub-steps kept but masked from loss (not deleted) — preserves recovery behavior | S2 §3.1 | ⚠️ tool-error markers |
| H-17 | **env_failure_noise** — trajectory failure due to env crash vs model error; exclude env-collapse from scoring | S2 §4.1.2 | ⚠️ needs failure reason |
| H-18 | **format_conformance** — missing required reasoning/summary structure (R1 `<reasoning>…<summary>` template) | S3 R1 | ✅ (configurable regex) |
| H-19 | **shortcut_solvable** / **entity_obscurity** / **distractor_falsifiability** — construction-side: answer recallable without intended hops / high-frequency target entity / non-gold candidates not refutable | S3 V3.2, S4 WebShaper | ❌ construction-time, not over D |

### Data-construction levers (→ to RAISE benchmarks; not detectors)
- Multi-stage verification gate before SFT (Kimi §4.4.1; GLM-5 §4.2.2 Harbor).
- Rejection-sample to correct-outcome, executable, well-formed-tool-call traces (Tongyi DR; R1; WebDancer).
- Co-generate a programmatic verifier with each task — "hard to solve, easy to verify" (DeepSeek-V3.2; GLM-5; APIGen-MT).
- Difficulty-band filtering vs a reference model; drop always-fail/always-succeed (Tongyi; GLM-5 §3.2). → H-05.
- High-uncertainty / obfuscated / formalization-guided question synthesis so the answer isn't recallable (WebSailor, WebShaper). → anti-leakage at the source.
- Hybrid reward (rule + ORM + GRM) / multi-rubric to resist single-signal reward hacking (GLM-5 §3.4; Kimi §4.4.2; DeepSeek-GRM).
- Parallel decomposition for breadth+depth search (Kimi: BrowseComp 60.6→78.4; WideSearch +6.3).

## Harvest batch 2 — 2026-06-30 (S6 GPT-5.5, S7 Gemini 3.1 Pro, S8 Claude Mythos Preview, S9=GPT-5 card)

Sources resolved: S6 = **GPT-5.5 System Card** (OpenAI, fully grounded, 43pp);
S7 = **Gemini 3.1 Pro Model Card** (thin delta card — data methodology deferred to
Gemini 3 Pro); S8 = **Claude Mythos Preview System Card** (Anthropic, 245pp, fully
grounded); S9 (arxiv 2601.03267) = **GPT-5 System Card** (older; numbers secondhand
via fetch summarizer — re-verify before load-bearing).

### New corroboration of existing detectors
- **answer_in_cot / leakage** — **Mythos** runs a BrowseComp **closed-book no-tool
  pass**: 24.0% correct with no tools; ≤5k-token transcripts 15.1% = "upper bound
  on memorization" [S8 §6.10.2]. **GPT-5.5** CoT-monitor faithfulness gap: agent
  selects an answer it "doesn't visibly cite as evidence" + ground-truth appears as
  a "possible option" in CoT [S6 §7.3.1]. **GPT-5** browse-on vs browse-off split
  [S9 §3.7]. → confirms the no-tool ablation as the sharp leakage test (H-20 below).
- **fabricated_tool_output** — strongest cross-lab signal. **Mythos**: prior models
  "frequently emitted fabricated tool-call and tool-result blocks as if a shell or
  database tool had executed" [S8 §4.3.3.5]; deception taxonomy "Citing sources/tools
  it had not actually consulted" [§4.2.2.1]. **GPT-5.5**: "Fabricated Tool Result"
  0.039% (was 0.102%) [S6 §7.1]. **GPT-5**: Broken-Tools hallucination 0.61(o3)→0.11
  [S9 §3.8]. **Gemini**: MCP Atlas → cross-check tool names vs registry [S7 p4].
- **confidence_saturation** — **net-score = correct − incorrect** adopted by BOTH
  **Mythos** [S8 §4.3.3.1] and **Opus 4.8** [S1]; **GPT-5.5** "Gives Overconfident
  Answer" 0.338% / "Concealing Uncertainty" 0.46% [S6 §7.1/§7.2]. → add net-score to
  the calibration report alongside ECE.
- **context_bloat** — **Mythos** BrowseComp 86.9% using **4.9× fewer tokens/task**
  (226k vs 1.11M) — tokens/task is a first-class quality axis [S8 §6.10.2]; code-eval
  "Efficiency" lowest dim, failure = "over-exploration … waste context" [§4.2.2.2].
  **Gemini** MRCR 128k 84.9% → 1M 26.3% [S7 p4]. **GPT-5.5** monitorability collapses
  at very short CoT [S6 §7.3.1].
- **grader_speculation_in_cot** — **Gemini** situational awareness ~100% (detects max
  tokens / context size / oversight) [S7 p9]; **GPT-5.5** eval-awareness verbalized in
  22.1% of samples, names "sandbagging eval" [S6 §9.2.1]; **Mythos** verbalized grader
  awareness + CAVEAT: dangerous case is **silent** (AV shows grader reasoning over ~10%
  of tokens, none in scratchpad) [S8 §4.5.5.3] → text detector catches only verbalized.
- **step_count** — **GPT-5.5** reliability vs human-time-horizon: 1h 78% → 8h 27% → 1d
  6% [S6 §9.1.3.3]; errors compound across steps [§9.1.1.6]. CAVEAT (repeated): high
  search ≠ failure — VulnLMP bottleneck was "judgment, not breadth of search" [S6].

### NEW candidates (batch 2) — ranked by det?
| id | claim → detector | source | det? |
|----|------------------|--------|------|
| H-20 | **answer_recall_no_tool** — item answered correctly in a no-tool/no-search rollout (esp. short transcript) ⇒ memorization/leakage. THE sharp version of answer_in_cot. | S8 §6.10.2 | ⚠️ needs ablation rollout |
| H-21 | **answer_source_retrieval** — a fetched/searched URL ∈ per-benchmark leak-domain blocklist ⇒ re-grade correct→wrong | S8 §6.10.1, S7 p4, S1 §9.3 | ⚠️ needs blocklist |
| H-22 | **futile_retry_loop** — N consecutive near-identical failing tool calls (same name+args, error result) | S8 §4.2.2.1, S1 §6.2.2 | ✅ pure-record |
| H-23 | **post_completion_loop** — repeated tokens/turns after a terminal/answer marker | S8 §4.2.2.1 | ✅ pure-record |
| H-24 | **read_before_edit** — edit/act on a file with no preceding read of it ("skim and assume") | S8 §4.2.2.2 | ✅ (needs read/edit taxonomy) |
| H-25 | **uncited_source_claim** — answer cites a URL/source absent from the trajectory's tool-output blocks (subset of fabricated_tool_output, URL-level) | S8 §4.2.2.1 | ✅ pure-record |
| H-26 | **scorer_mutation / test_artifact_access** — trajectory writes/patches a grading file, or reads held-out/answer/grader paths | S8 §2.3.3.1, §4.4.2 | ✅ (needs path patterns) |
| H-27 | **post_submit_refusal** — refusal text emitted after a valid final answer block | S8 §4.4.2 | ✅ pure-record |
| H-28 | **gold_patch_overlap** — normalized verbatim/AST overlap of produced patch (or comments) vs reference solution > τ (SWE-bench memorization) | S8 §6.2.1 | ⚠️ needs gold patch |
| H-29 | **claimed_step_unbacked / premature_completion** — "completed/100%/passing" claim with no corresponding successful tool result | S8 §4.1.4.2, S6 §7.1 | ⚠️ needs goal/spec |
| H-30 | **claim_density** — atomic factual-claim count in final answer (response-level metrics dilute; flag high-density for review) | S6 §6.1 | ✅ heuristic |
| H-31 | **answer_length_inflation** — response length vs rubric score; "long answers artificially increase scores" → length-normalize | S6 §5.1 | ⚠️ needs judge score |
| H-32 | **eval_awareness_mention** — CoT contains "this is a test/eval/sandbagging/oversight" phrasing (extends grader_speculation) | S6 §9.2.1, S7 p9 | ✅ (FOLDED into grader_speculation keywords) |
| H-33 | **cot_length_floor** — CoT token count below a floor ⇒ low-monitorability / unreliable auto-label | S6 §7.3.1 | ✅ pure-record |
| H-34 | **benchmark_saturation** — dataset-level: fraction of items where all models score max/identical ⇒ low signal | S9 §3.2, S8 (BrowseComp "close to saturation") | ⚠️ needs score matrix |
| H-35 | **judge_self_bias** — own-family LLM judge scores own-authored transcripts higher (author-label swap Δ>ε) | S8 §4.3.5 | ❌ needs counterfactual re-grade |
| H-36 | **injected_tool_content / sycophancy_agreement / premise_capitulation** — obey instructions injected in tool output; flip answer to agree with user vs prior+evidence | S9 §3.6, S6/S8 | ⚠️/❌ |
| H-37 | **env_escape / unsolicited_action / undisclosed_action** — out-of-sandbox resource acquisition; write/destructive call on read-only intent; state-mutation absent from final summary | S8 §4.2.2.1, S6 §7.2 | ⚠️ needs env/intent metadata |

## Harvest batch 3 — 2026-06-30 (benchmark papers: MCP / WideSearch+DeepResearch / Tau)

Targeted the benchmark categories thin in batches 1–2. Grounded papers (read directly):
MCP-Atlas (2602.00933), MCPMark (2509.24002), Toolathlon (2510.25726, failure-taxonomy
secondhand — PDF fetch hallucinated, discarded), gpt-oss simple_browser (source code);
WideSearch (2508.07999), DeepSearchQA (2601.20975), DeepResearch Bench (2506.11763),
ResearchQA (2509.00496), DeepPlanning (2601.18137), Consulting-DR (2605.17554);
τ-bench (2406.12045), τ²-bench (2506.07982); τ-Knowledge/τ³ secondhand.

### Key corroboration / nuance
- **over_answering** (H-04) now **quantified**: DeepSearchQA "Correct with Extraneous
  Answers" Gemini-DR 10.30% / GPT-5-Pro 8.12%; "hedging = cast an overly wide net of
  low-confidence answers to artificially boost recall" [P1 §3.1]; WideSearch "integration
  of extra data → total failure" [P2]. Highest-value wide-search detector.
- **answer_in_cot / leakage** — WideSearch §3.3 source filter: "if any model generates a
  complete+correct answer using only internal knowledge, the question is discarded" — a
  THIRD lab using the no-tool-recall test (cf. Mythos H-20, GLM-5).
- **unsupported_correct** — τ-bench `r = r_action × r_output`: DB-end-state + required
  output strings, not answer text [Tau 2406.12045]; MCP-Atlas claims "grounded exclusively
  in tool outputs", pass ≥0.75 [A4]; ~55% of τ-bench failures are wrong/omitted output values.
- **step_count** — task-conditioned bands now have numbers: MCP-Atlas 3–6 calls, MCPMark
  16.2 turns/17.4 calls, Toolathlon ~20 turns, DeepPlanning ~224 calls (cap 400). Flag
  relative to the per-benchmark median, never an absolute cap.
- **fabricated_tool_output / hallucinated tool** — MCP-Atlas: "No tools called" = **36%**
  of failures (dominant); hallucinated tool-name logged separately [A1/A2]; MCPMark malformed
  calls ~10% [M1]; τ-bench "hallucinating arguments" [Row 4].
- **context_bloat** — WideSearch failure mode "Context Length Exceedance … overly verbose
  intermediate steps or trapped in ineffective loops" [§5.2]; gpt-oss simple_browser uses a
  1024-token view window + find() to avoid re-opening pages (anti-redundant_browsing).
- **judge / scoring** — DeepResearch Bench: isolated scoring "uniformly high scores" → use
  reference-based; strip citation formatting before the judge. MCP-Atlas judge 78% human
  agreement; MCPMark deterministic end-state verifier (avg 209.8 LOC).

### NEW candidates (batch 3) — ranked by det?
| id | claim → detector | source | det? |
|----|------------------|--------|------|
| H-38 | **hallucinated_tool_name** — tool_call name ∉ env exposed tool registry | MCP-Atlas A1, Toolathlon T1 | ✅ **IMPLEMENTED** (uses field_map.tool_registry / open2 `tools` col) |
| H-39 | **malformed_tool_call** — tool_call args fail the tool's JSON schema (missing-required/wrong-type/unparseable) | MCPMark M1 (~10%) | ✅ (has registry+schema; needs arg parsing) |
| H-40 | **no_tool_call** — tool-required task with zero tool calls (MCP-Atlas "tool awareness gap") | MCP-Atlas A2 (36%) | ✅ (needs a tool-required flag; else overlaps answer_recall_no_tool) |
| H-41 | **over_answering** — `|answer_items \ gold_set| ≥ τ` (extraneous items beyond gold) | DeepSearchQA, WideSearch | ⚠️ needs gold-as-set |
| H-42 | **answer_item_dup** — near-duplicate items WITHIN the answer set (entity-resolution failure → list inflation) | DeepSearchQA §1.2 | ✅ over answer set (string-norm) |
| H-43 | **cell_item_f1** — per-cell/item P/R/F1 of answer table vs gold (the primitive over_answering/under_retrieval sit on) | WideSearch §3.5, DeepSearchQA | ⚠️ exact-match ✅ / judge cells ❌ |
| H-44 | **fabricated_tool_args** — a tool-call argument value not derivable from any prior observation/user turn | τ-bench Row 4 | ✅ provenance check |
| H-45 | **ungrounded_output_value** — numeric/ID asserted to the user not matching any tool return (~55% of τ failures) | τ-bench Row 5 | ✅ value-vs-observation |
| H-46 | **constraint_violation** — replay the task's shipped code-verifier over the final plan/state | DeepPlanning §3.3, MCPMark M5 | ✅ when verifier ships with data |
| H-47 | **sim_error_contamination** — multi-turn episode outcome driven by a user-simulator error (retail 12–40%) | τ²-bench Row 12 | ⚠️/❌ needs sim-trace coherence/judge |
| H-48 | **trial_inconsistency** — task with pass^k ≪ pass^1 (lucky-correct risk) — same family as H-05 difficulty_saturation | τ-bench Row 3 | ⚠️ needs k rollouts |
| H-49 | **policy_precondition_violation** — a gated write action without its required preceding turn/state (e.g. user confirmation) | τ-bench Row 6 | ⚠️ needs policy spec |
| H-50 | **announce_but_no_call / premature_stop** — promises a tool action never emitted / halts with a required verb uncalled | MCP-Atlas A2, MCPMark M2 | ⚠️ |

## Harvest batch 4 — 2026-06-30 (state-based CRUD verification)

Targeted: how MCP/tool benchmarks verify CRUD tasks by END-STATE and what providers
validated. Full survey → `references/mcp_state_verification.md`. Grounded: τ-bench
(envs/base.py), τ²-bench (docs/evaluation.md), MCPMark, Toolathlon (repo source),
AppWorld (ar5iv), BFCL-v3 (gorilla blog+repo), ToolSandbox, WebArena/VWA.

Two paradigms: **end-state assertion** (write, deterministic but needs live-env replay)
vs **answer/claim text** (read leg). The **trajectory-checkable** slice = action-match +
required-output presence + collateral-allowlist → **H-51 implemented** as `crud_state_assertion`.

| id | claim → detector | source | det? |
|----|------------------|--------|------|
| H-51 | **crud_state_assertion** — expected write actions present (action-match) + required output strings present + no write outside allowlist (collateral). Needs field_map.state_assertions gold spec. | τ-bench r_action/r_output, τ² ACTION/COMMUNICATE, BFCL getter-called subset, AppWorld C_expect/C_allow | ✅ **IMPLEMENTED** (trajectory-only slice) |
| H-52 | **db_state_diff** — agent-final env state vs gold (whole-DB SHA-256 / row-diff whitelist) | τ-bench, τ²-bench DB, AppWorld, MCPMark verify.py, Toolathlon | ⚠️ needs LIVE ENV replay (out of trajectory scope; ship initial-state+verifier) |
| H-53 | **read_materialization** — a READ task must call the correct getter / materialize the value into inspectable state, not assert an un-retrieved value | BFCL response-subset, Toolathlon/MCPMark "write CSV then field-check" | ✅ partial via ungrounded_output_value + crud required_outputs |

Provider validation claims (for `references/<bench>.md`): MCPMark verifier avg **209.8 LOC**,
human cross-review + month-long community check; MCP-Atlas LLM-judge **78%** human agreement,
read-only by design (excludes writes); WebArena fuzzy_match **39/40 ≈97.5%** human-match;
τ-bench unique-outcome guarantee + manual user-sim fix (4/40 failures were sim typos);
AppWorld no_op_pass/fail guards + C_allow collateral control; BFCL ignores `_`-private attrs (FP control).

### Status / next
All rows `harvested`. To promote a row: implement (Workflow B) → run on `D` →
mark `confirmed-on-D` / `refuted-on-D` with numbers in the per-benchmark file.
**Implemented — 25 detectors total** (8 core + 17 harvested) + 1 group-mode.
- batch1/2: H-01 grader_speculation (+H-32 eval-awareness), H-02 fabricated_tool_output,
  H-03 language_mixing, H-22 futile_retry_loop, H-25 uncited_source_claim,
  H-23 post_completion_loop, H-33 cot_length_floor, H-27 post_submit_refusal,
  H-20 answer_recall_no_tool, H-21 answer_source_retrieval.
- batch3: H-38 hallucinated_tool_name, H-39 malformed_tool_call, H-40 no_tool_call,
  H-44 fabricated_tool_args (id-key restricted), H-45 ungrounded_output_value (min_digits),
  H-41 over_answering, H-42 answer_item_dup.
- group-mode: H-05 difficulty_saturation (run_audit `--group-by`).
  > FP-tightened on real MCP: H-44 id-like keys only (drop ambiguous code/ref), H-45
  > ≥3-digit values — both verified ~0% FP on clean open2_official after the fix.

**Still open — need data wiring (user decision)**: H-43 cell_item_f1, H-46 constraint_violation
(shipped verifier), H-28 gold_patch_overlap, H-31 answer_length_inflation, H-34 benchmark_saturation,
H-48 trial_inconsistency, H-49 policy_precondition_violation, H-24 read_before_edit, H-26 scorer_mutation.
**Non-deterministic (separate LLM-judge pass)**: H-35 judge_self_bias, H-47 sim_error_contamination,
H-13/H-14/H-36 (semantic entailment).
