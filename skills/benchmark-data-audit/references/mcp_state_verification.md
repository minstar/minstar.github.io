# State-based verification of CRUD tool/MCP tasks — methodology survey

How agentic benchmarks verify a **Create/Update/Delete/Read** task by the
**resulting environment state** (not answer text), and what each data provider
says they validated. Harvested 2026-06-30 (Workflow C). Q = grounded quote,
P = paraphrase; secondhand/not-found flagged inline.

## TL;DR — two paradigms, and what a trajectory auditor can actually check
- **End-state assertion** (write-capable, deterministic): MCPMark, Toolathlon,
  AppWorld, BFCL-v3, ToolSandbox, WebArena `program_html`, τ-bench, τ²-bench.
  Checks the *resulting env* (DB rows / files / object attributes), NOT the answer.
- **Answer/claim text** (read leg, or read-only benchmarks): MCP-Atlas (entirely),
  τ `r_output` / τ² COMMUNICATE, BFCL response-subset, AppWorld QA `answer`.

**Key constraint for THIS skill:** a full DB-state diff/hash needs a *live env +
initial-state snapshot to replay* — not available from a trajectory alone. The
deterministically **trajectory-checkable** subset is:
1. **action-matching** — the required write tool-call(s) appear in the trajectory
   (τ² `ACTION`, BFCL "correct getter was called", subset-match);
2. **required-output presence** — required value strings appear in the agent→user
   message (τ `r_output`, τ² `COMMUNICATE`);
3. **no-collateral / allowlist** — no write call outside the allowed set (AppWorld
   `C_allow`, Toolathlon "bucket should contain only…", BFCL ignore `_`-private).
→ implemented as the `crud_state_assertion` detector (needs a per-sample gold spec
in `field_map`). Full state-diff is documented below as the gold standard you wire
by *shipping initial-state + verifier* with the data (MCPMark / BFCL model).

## Per-benchmark mechanisms

### τ-bench (2406.12045, sierra-research/tau-bench) — DB-hash identity
- **Write**: `r_action` = agent-final-DB **SHA-256 identical** to a DB built by
  **replaying the task's gold `actions`** on a fresh load (`envs/base.py`:
  `gt_data_hash` vs `data_hash`). Whole serialized DB must match — not a row diff.
- **Read**: `r_output` = each required output string present (case-insensitive,
  comma-stripped substring) in an agent→user message.
- **Score**: `r = r_action × r_output ∈ {0,1}` — all-or-nothing.
- **Validated** (Q): relies on a "unique ground truth outcome database"; manual
  scenario+user-sim verification; on one 65.2% run, 4/40 failures were user-sim
  typos (fixed), 36 genuine. Reliability via **pass^k** (gpt-4o pass⁸ < 25% retail).
- **Ships**: gold `actions` + initial DB (`data_load_func`) + `outputs` → fully replayable.

### τ²-bench (2506.07982, sierra-research/tau2-bench) — configurable reward basis
- `reward = Π` over `reward_basis` (default `["DB","COMMUNICATE"]`):
  **DB** (hash vs reference-trajectory replay), **ENV_ASSERTION** (assertion fns on
  final state), **ACTION** (exact tool-call match, `ToolType.READ`/`WRITE` typed),
  **COMMUNICATE** (required strings), **NL_ASSERTION** (LLM judge — experimental/diagnostic).
- **Partial within a component, multiplicatively gated across** (any 0 → 0).
- **Ships**: `evaluation_criteria` (reference trajectory, basis, assertions). DB/ACTION/
  ENV/COMMUNICATE deterministic; **NL_ASSERTION needs an LLM** (non-deterministic).
- τ³/banking_knowledge (secondhand): RAG domain leans on **ACTION-match of retrieval
  calls** + COMMUNICATE (no DB mutation).

### MCPMark (2509.24002, eval-sys/mcpmark) — cleanest CRUD end-state verifier
- Per-task **`verify.py`** inspects final env state (DB rows, files, Notion pages,
  GitHub PRs/CI) — full CRUD, "validated automatically rather than LLM-as-Judge".
- **Binary per task**; partiality only across runs (pass@1/@4, Pass^4 = all 4 succeed).
- **Validated** (Q): verifiers avg **209.8 LOC**; tasks "cross-reviewed by human experts
  and a month-long community check"; env reset to original after each. 127 tasks/5 services.
- **Ships**: `verify.py` + 38 initial-state snapshots (gold encoded *as assertions in verify.py*).
- *Caveat*: verify.py internals from paper/README, not raw source.

### Toolathlon / Tool Decathlon (2510.25726, hkust-nlp/Toolathlon)
- Per-task `evaluation/main.py` runs against live env + reads agent workspace
  artifacts, compares to `groundtruth_workspace/` within tolerance
  (`validate_record_data(..., tolerance_pct=0.05)`) + **collateral checks**
  ("bucket should contain only the … log" → raises on `extra_scenarios`).
- **Binary per task** (`exit(1)` on first failed assertion); Pass^3 = consistency.
- **Ships**: `evaluation/`, `groundtruth_workspace/`, `initial_workspace/`, `task_config.json`;
  trajectories on HF. Needs per-task Docker / live env to replay.

### AppWorld (2407.18901, stonybrooknlp/appworld) — DB-diff with allowlist
- **Write**: state-based unit tests over the **DB diff** `D^Δ`: assert
  `C_expect ⊆ D^Δ` (all required changes present) **AND** `D^Δ ⊆ C_expect ∪ C_allow`
  (no out-of-allowlist change = collateral-damage control). ~8 (max 22) assertions/task.
- **Read**: QA tasks (~15%) carry a fixed `answer` field; compare returned answer to gold.
- **Score**: **TGC** = passed *all* tests (binary per task); **SGC** = all tasks in a scenario.
- **Validated**: path-independent (multiple valid solutions full credit); `no_op_pass/fail`
  guards against do-nothing scoring; ~1,780 unit tests / ~34K LOC API impl; ~0.6s/task.
- **Ships**: Setup (init DB) + Evaluation (unit tests) + Solution (train/dev only) + DB snapshots.

### BFCL v3/v4 (gorilla, ShishirPatil/gorilla) — backend-instance diff
- **Write**: execute model calls on stateful **backend class instances**, then diff
  the instance's **public attributes** (ignore `_`-private) vs a ground-truth instance.
  Multiple valid solutions OK if end-state matches.
- **Read**: **response-based** — the correct getter must be *called* (subset-match: correct
  if it contains the gold call set, extra calls allowed), not the value guessed.
- **Score**: all-or-nothing (must pass both checks in all turns).
- **Validated** (Q): "expert human labelers manually review all data points"; FP control =
  excluding `_`-private attrs. v4 deltas not found (inherits v3 design).
- **Ships**: checker + `func_source_code/` backend classes + Initial Config + gold call path
  → among the few that are **trajectory-replayable offline** (re-instantiate → replay → diff).

### ToolSandbox (2408.04682, apple/ToolSandbox) — milestone/minefield DAG
- **Milestones** (critical steps) + **Minefields** (must-not-occur) matched to per-turn
  **world-state snapshots** (all tool DBs + dialog) in topological order; similarity via
  exact / ROUGE-L / AST / tool_trace.
- **Score**: `score = scoreM+ × 𝕀(scoreM− = 0)` — **per-milestone partial credit**, hard
  minefield gate. (The only benchmark with real intra-task partial credit.)
- **Validated**: one annotator authors, the other "acts as an agent to validate milestones";
  user-sim hallucination ~6.9% over 1032 trajectories.
- **Ships**: milestone/minefield defs + scorer + 34 tools as Python fns + world-state DBs.

### WebArena (2307.13854) / VisualWebArena (2401.13649) — web analogy
- Per-task JSON eval config: **`program_html`** (locator + `required_contents` on resulting
  page/DB/URL state) for writes/nav; **`string_match`** (exact/must_include/fuzzy[GPT-4]) for
  reads; `url_match` (gold-in-pred). Multiplicative → effectively binary.
- **Validated** (Q, WebArena): double-annotation + tiebreak; fuzzy_match spot-check 39/40 ≈97.5%.
- VWA adds `eval_vqa` (VLM) + SSIM image match. **Ships** config_files + Docker.

## Summary table
| Benchmark | write check | read check | partial? | ships verifier+gold? | trajectory-only det? |
|---|---|---|---|---|---|
| τ-bench | full-DB SHA-256 vs gold-replay | required strings in msgs | ❌ | ✅ | ✅ replay |
| τ²-bench | DB-hash + ENV_ASSERTION + ACTION | COMMUNICATE; NL(LLM) | ⚠️ within/gated | ✅ | ⚠️ NL needs LLM |
| MCPMark | `verify.py` on final state | materialized→field-check | ❌ | ✅ (verify.py+init) | ⚠️ needs live MCP |
| Toolathlon | `evaluation/main.py` + collateral | workspace artifact==gold | ❌ | ✅ | ⚠️ needs Docker |
| AppWorld | DB-diff `C_expect⊆Δ⊆C_expect∪C_allow` | QA `answer` field | ❌ (TGC all-tests) | ✅ (test split: tests only) | ⚠️ needs Engine+initDB |
| BFCL v3 | backend-instance public-attr diff | getter-called subset-match | ❌ | ✅ | ✅ re-instantiate |
| ToolSandbox | milestone DAG vs snapshots | tool_trace value flow | ✅ per-milestone | ✅ | ✅ (ROUGE-L fuzzy edge) |
| WebArena | `program_html` state assert | string/ fuzzy(LLM) | ❌ | ✅ | ⚠️ live JS / LLM |
| MCP-Atlas | — (read-only, no writes) | LLM claim-coverage@0.75 | per-claim→0.75 gate | partial (claims) | ❌ LLM judge |

## Design takeaways (wired into the skill)
1. **Reads need their own leg** — a pure end-state diff can't catch a read. The dominant
   pattern is "materialize the read into inspectable state" (Toolathlon/MCPMark write a file
   then field-check) or "check the correct getter was *called*" (BFCL). → the auditor's
   read check = `required_outputs` present + (optional) `ungrounded_output_value`.
2. **No-collateral allowlist is the universal FP control** (AppWorld `C_allow`, Toolathlon
   extra-checks, BFCL ignore-private). → `crud_state_assertion` flags write calls outside
   `allowed_actions`.
3. **Offline trajectory-checkability requires shipping initial-state + verifier** (MCPMark
   model) or an in-process backend + gold instance (BFCL model). open2_official ships neither
   → `crud_state_assertion` skips on it; populate `field_map.state_assertions` for benchmark
   eval data (or record the verifier+initial-state when you synthesize MCP CRUD data).
