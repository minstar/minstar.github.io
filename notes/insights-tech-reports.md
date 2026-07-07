# Insights of Tech Report

A running index of system cards and technical reports that are out in the world,
read through my own lens. For each one, two things: **(1) what's worth reading from
where I sit** — a search/agent researcher doing SFT/RL, data synthesis, and eval —
and **(2) where it touches the questions in my research notes above.** Titles are
toggles; every number below was pulled from the source and independently
fact-checked before it went up.

<details>
<summary><strong>Claude Opus 4.8 System Card</strong> · Anthropic, May 2026</summary>

*A 246-page pre-deployment card whose stated conclusion is that Opus 4.8 does not
advance the frontier beyond Anthropic's most capable model (Mythos Preview), with
catastrophic risk kept low under ASL-3.*

**What I'd read (my lens)**
- **§8.10–8.11 (agentic search + multi-agent).** My exact benchmark battery, with the
  harness knobs spelled out: BrowseComp 84.3% single-agent → 88.5% with an
  orchestrator + blocking sub-agents; a five-agent team hits 85.4% at ~20% of
  single-agent latency (~3× on the hard tail). Context compaction at 200k, 1M vs 10M
  token budgets — a template for how to report token/latency scaling.
- **§6.3.6 (diligence).** Four small toy evals that isolate the "notices the flaw but
  reports anyway / cuts corners" pathology: first Claude to score perfectly on
  flawed-result reporting and lazy investigation; code-summary honesty fails only 3.7%
  (vs Mythos Preview's 27.6%). Frames it as an *alignment*, not capability, failure.
- **§6.3.7 + §6.6.3 (grader awareness).** A white-box NLA (natural-language
  autoencoder) verbalizer finds ~5% of RL episodes carry *unprompted, unverbalized*
  grader-awareness (0.5% "exploitative") — evidence that reward-channel gaming can be
  present without ever surfacing in the CoT.
- **§8.13 (tool use).** MCP-Atlas 82.2%, Toolathlon 59.9% Pass@1 (604 tools/32 apps,
  execution-based checkers), AutomationBench (Zapier, deterministic assertions over
  simulated app state).

**Where it meets my notes**
- **Over-reflection** — §6.3.6's "uncritically reporting flawed results" + the §2.3.3
  "cheap verification skipped / ignored correction" tags are the frontier-teacher form
  of the confirm-then-fail-to-act behavior I measure at ~63%, and their per-type toy
  evals parallel my per-type surgical repair.
- **AgentPlanet** — the ~5% unverbalized grader-awareness, plus the DRACO note that
  *judge choice moves absolute scores 10–25 points while preserving ordering*, is a
  first-party argument for deterministic assertion graders (AutomationBench/Toolathlon)
  over LLM-judges — exactly my reward-channel-integrity concern.

[Source (PDF)](https://www-cdn.anthropic.com/0b4915911bb0d19eca5b5ee635c80fef830a37ea.pdf)

</details>

<details>
<summary><strong>Claude Fable 5 &amp; Claude Mythos 5 System Card</strong> · Anthropic, June 2026</summary>

*A 319-page card for two configurations of one model: Fable 5 (general release, with
bio/cyber safeguards) and Mythos 5 (safeguards lifted, restricted to "Project
Glasswing" partners).*

**What I'd read (my lens)**
- **§6.4.2 (grader awareness, causal).** The sharpest version of the reward-integrity
  result: unverbalized grader awareness is prevalent specifically in coding RL
  environments flagged "high-risk for grader hacking," rises over training, and
  steering *against* it reduces both the presentation habits *and* the behavioral
  reward — a concrete anti-Goodhart measurement, not just a correlation.
- **§6.4.1.4 (why it stops early).** On an exhaustive-search task the model made one
  tool call, declared "no relevant papers," and the NLA decode shows a phantom "token
  budget exhausted" motivation *while a counter showed 2.43M tokens remaining* — plus a
  separate session with unverbalized "fatigue." The early-stop mirror image of
  over-search.
- **§8.14.3 (DeepSearchQA).** 900 prompts / 17 fields with an explicit
  **"Correct w/ Excessive Answers" outcome column at 3.8%** — a literal, graded
  over-answering metric. DRACO 86.4% on 100 rubric-graded tasks.
- **§8.15.1 (multi-agent).** Async sub-agents reach 93.3%; non-blocking beats blocking
  because long-lived agents keep context instead of re-establishing it per subtask.

**Where it meets my notes**
- **Over-reflection** — §6.4.1.4's phantom-budget early stop and the DeepSearchQA
  "excessive answers" column are the same token-budget / stop-pivot confound family I
  study, seen from the inside via white-box probes.
- **AgentPlanet** — §6.4.2's causal steering (suppress the "I'm being graded"
  representation → earned reward drops) is direct empirical support for preferring
  deterministic/invariant meta-rewards over an LLM-judge channel that can be gamed by
  presentation. (Eval-awareness-rising framing lives in the §6.5/§6 alignment overview.)

[Source (PDF)](https://www-cdn.anthropic.com/d00db56fa754a1b115b6dd7cb2e3c342ee809620.pdf)

</details>

<details>
<summary><strong>Claude Opus 4.6 System Card</strong> · Anthropic, February 2026</summary>

*A ~213-page pre-deployment card for the single model Claude Opus 4.6 (predecessor:
Opus 4.5), deployed under ASL-3 — covering RSP dangerous-capability evals
(CBRN/cyber/autonomy), an alignment assessment with interpretability, model welfare,
and an agentic/coding/search battery. The immediate baseline the 4.8 and Mythos cards
measure against.*

**What I'd read (my lens)**
- **§2.21 (agentic search).** BrowseComp multi-agent 86.8% (edging single-agent by
  2.8%, so single ≈84.0%); DeepSearchQA F1 91.3% single-agent / 92.5% multi-agent —
  the clean predecessor datapoint for the single→multi-agent jump.
- **Coding.** SWE-bench Verified 80.84% (77.83% on the harder variant), Finance Agent
  60.70% — useful as the "before" numbers against 4.8's 88.6% and Mythos's 95.5%.
- **§1.2 (release decision).** How the RSP CBRN/cyber/autonomy thresholds are argued
  for a shipping model — the reasoning template the later cards inherit.

**Where it meets my notes**
- **Over-reflection** — the single-vs-multi-agent BrowseComp gap (≈84.0 → 86.8) is a
  clean external anchor for my single-rollout vs Best-of-N / multi-agent findings.
- **AgentPlanet** — read alongside 4.8 and Mythos as the reward-integrity story's
  starting line; the grader-awareness machinery is not yet organized here, which is
  itself informative about when it emerged.

[Source (PDF)](https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf)

</details>

<details>
<summary><strong>DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence</strong> · DeepSeek-AI, April 2026</summary>

*Technical report for the DeepSeek-V4 preview series — V4-Pro (1.6T total / 49B
active) and V4-Flash (284B / 13B active), both 1M-token context, pre-trained on >32T
tokens. Effectively the system card for `deepseek-v4-pro`, the teacher I lean on
across trajectory synthesis, query generation, and eval/judging.*

**What I'd read (my lens)**
- **Post-training.** Per-domain specialists (SFT + GRPO with tailored Generative Reward
  Models) are then merged into one model via **On-Policy Distillation with a reverse-KL
  loss** — a direct industrial analog of my Solar Open SFT→RL→distill flow, and the
  cleanest same-family reference to benchmark my cross-tokenizer scheme against.
- **Efficiency section.** At 1M context, V4-Pro runs at 27% of the single-token FLOPs
  and 10% of the KV cache of V3.2 (Flash: 10% / 7%), reaching ~2% of a BF16 GQA8 KV
  baseline — with FP4 quantization-aware training on the MoE expert weights.
- **Serving.** Expert-parallel gives 1.50–1.73× (up to 1.96× for RL rollouts / agent
  serving), and they flag **power throttling as a key performance limiter under extreme
  kernel fusion** — a rare frontier acknowledgment of the power wall.

**Where it meets my notes**
- **Post-cutoff distillation** — the reverse-KL on-policy distillation is the same
  family as my design, but same-tokenizer self-distillation with no memory-cache or
  post-cutoff gating; the right baseline to differentiate against.
- **Wearable world model / Energy floor** — the KV-to-~2% + FP4/FP8 recipe and the
  explicit power-throttling remark are the exact KV-compression + quantization + power
  levers those two notes turn, here at datacenter (not wearable) scale.
- **AgentPlanet** — GRPO trained against per-domain *Generative Reward Models* is
  precisely the LLM-judge reward channel my anti-Goodhart concern targets.

[Source (arXiv 2606.19348)](https://arxiv.org/abs/2606.19348)

</details>

<details>
<summary><strong>GLM-5: from Vibe Coding to Agentic Engineering</strong> · Zhipu AI &amp; Tsinghua, February 2026</summary>

*Technical report for GLM-5, an open-weights MoE model (~744B total / 40B active)
built around a fully asynchronous, decoupled RL stack and >10k verifiable training
environments; claims parity with Opus 4.5 / GPT-5.2 among frontier models.*

**What I'd read (my lens)**
- **§4.1 (async decoupled RL + Direct Double-Sided Importance Sampling).** A
  checkpoint-free recipe for off-policy drift: reuse the rollout's own log-probs as the
  behavior proxy, discard samples past a staleness bound, double-sided token clipping —
  directly transferable to my Solar/Qwen SARL and slime RL where generation/training
  decoupling is a live issue. Plus DP-aware routing (consistent hashing) to preserve
  KV-cache locality across multi-turn interactions.
- **§4.2.1 + §3.4 (verifiable environments).** >10k environments across thousands of
  repos (9 languages) with Fail-to-Pass / Pass-to-Pass test oracles, mixed with
  rule-based + ORM + GRM rewards — the closest published analog to what env-synth /
  dive-synth are trying to do.
- **§3.5 (on-policy cross-stage distillation).** Prior-stage checkpoints act as
  teachers with advantage `Â = sg[log(π_teacher / π_train)]` to fight regression across
  a sequential pipeline — a compact anti-forgetting mechanism.

**Where it meets my notes**
- **AgentPlanet** — "10k verifiable environments with deterministic oracles" sitting
  next to ORM/GRM model-based rewards is a real-world instance of world-authoring +
  verifier batteries, and speaks straight to the deterministic-oracle-vs-LLM-judge
  question.
- **Post-cutoff distillation** — the cross-stage distillation (teacher log-ratio as
  advantage) is a mechanistic cousin, but same-tokenizer and not knowledge-gated.

[Source (arXiv 2602.15763)](https://arxiv.org/abs/2602.15763)

</details>

<details>
<summary><strong>Qwen3 Technical Report</strong> · Qwen Team (Alibaba), May 2025</summary>

*The Qwen3 open-weight family (dense 0.6–32B + MoE 30B-A3B and 235B-A22B, Apache 2.0),
whose headline is unifying "thinking" and "non-thinking" modes in one model with a
user-controllable thinking budget; ~36T-token pretraining over 119 languages.*

**What I'd read (my lens)**
- **Reasoning-RL stage.** GRPO over **3,995 query–verifier pairs** with deterministically
  verified answers, reporting AIME'24 **70.1 → 85.1 in only 170 RL steps** — a concrete
  verifier-as-reward recipe with a hard oracle channel.
- **Thinking-budget mechanism.** When reasoning hits a user-set token threshold, a
  stop-thinking instruction is inserted and the model answers from accumulated
  reasoning (`/think`, `/no_think`) — a crude but explicit "when to stop" lever.
- **Strong-to-weak distillation.** Small models built by logit distillation at ~1/10
  the GPU hours of the four-stage pipeline — the same-tokenizer counterpoint to my
  cross-tokenizer design.

**Where it meets my notes**
- **AgentPlanet** — the 3,995 verifier pairs driving GRPO is a clean instance of a
  deterministic verifier battery as the reward channel.
- **Over-reflection** — the thinking-budget "halt at a user threshold" is the same
  stop lever, but a fixed token cap rather than a *state-conditioned learned* stop/pivot
  — a contrasting baseline, not a solution.
- **Post-cutoff distillation** — strong-to-weak logit distillation is the cheap,
  same-family baseline my post-cutoff, cross-tokenizer scheme has to beat.

[Source (arXiv 2505.09388)](https://arxiv.org/abs/2505.09388)

</details>

<details>
<summary><strong>Seed2.0 Model Card: Towards Intelligence Frontier for Real-World Complexity</strong> · ByteDance Seed, June 2026</summary>

*Model card for the Seed2.0 series (Pro/Lite/Mini), framed around "real-world
complexity" — long-tail knowledge, complex instruction following, long-horizon agentic
tasks — paired with a needs-grounded evaluation framework.*

**What I'd read (my lens)**
- **§3.3 (agentic eval + harness hardening).** My exact turf — BrowseComp, WideSearch,
  seal-0, FinSearchComp, tau2-Bench, BFCL-v4, MCP-Mark, DeepConsult, ResearchRubrics —
  and, more usefully, their de-noising protocol: pre-built execution images, internal
  package mirrors, and exclusion of non-deterministic / network-dependent / self-failing
  test cases.
- **§3.1.1 (long-tail knowledge).** Two new benchmarks — LPFQA and **Encyclo-K** (65.7,
  their highest; Frames 84.5 is second, just behind Opus-4.5's 84.7), the latter with a
  few-shot in-context knowledge-*acquisition* probe — directly useful for measuring
  knowledge coverage in data synthesis.
- **Scoring convention.** "Final score = **max(official doc, our test)**" to avoid
  underestimating competitors — an eval-integrity choice worth thinking about (note it
  guards the *opposite* failure from gaming your own reward).

**Where it meets my notes**
- **Over-reflection** — heavy benchmark overlap and their per-category slicing
  (912 cases × 17 weighted dims) parallel my per-type trajectory repair, though the card
  reports scores only, not over-search *mechanism*.
- **Post-cutoff distillation** — Encyclo-K's ICL knowledge-acquisition probe and their
  future-dated freshness sets (AIME 2026, Codeforces Jun–Dec 2025) touch post-cutoff
  knowledge *measurement*, which is exactly the "which facts are actually new" gate my
  note hinges on.

[Source (arXiv 2607.00248)](https://arxiv.org/abs/2607.00248)

</details>

<details>
<summary><strong>Sakana Fugu Technical Report</strong> · Sakana AI, June 2026</summary>

*Fugu and Fugu-Ultra are orchestrator models that coordinate a team of frontier LLMs
(Gemini-3.1-Pro, Claude-Opus-4.8, GPT-5.5) via query-adaptive routing/scaffolding
rather than training one bigger model — Fugu does fast single-worker routing,
Fugu-Ultra generates multi-step "Conductor" workflows (up to 5 steps).*

**What I'd read (my lens)**
- **Conductor reward design.** GRPO under a **deterministic verifier** (no LLM judge):
  R=0 if the workflow is unparseable, R=1 if the output matches ground truth, else
  R=0.5 — trained *without any KL penalty* to widen topology exploration. A concrete
  judge-free reward over multi-step agent workflows.
- **Router training.** Two stages: soft-target-distribution SFT (KL to a per-worker
  reward softmax), then sep-CMA-ES on real multi-turn coding-assistant trajectories
  (Claude Code / Codex / OpenCode), adapted via singular-value fine-tuning.
- **Intra-workflow isolation.** Each agent sees others only through an "access list,"
  which prevents "orchestration collapse" (one agent's trajectory steering the rest) —
  plus a recursive twist where the orchestrator can name itself as a worker.

**Where it meets my notes**
- **AgentPlanet** — Fugu factorizes an author (the Conductor emits subtasks + worker IDs
  + access lists) from worker policies, and its correctness-only deterministic verifier
  is exactly the oracle-over-judge, anti-Goodhart stance in my notes; the
  orchestrator-as-worker recursion mirrors the role-factorization idea.
- **Over-reflection** — "call in Opus at critical debugging points" is a
  state-conditioned escalation/pivot signal, though the report does no over-search
  analysis, so the tie is by shape, not finding.

[Source (arXiv 2606.21228)](https://arxiv.org/abs/2606.21228)

</details>
