# Insights of Tech Report

A running index of system cards and technical reports that are out in the world.
For each one: **a few excerpts of what the report actually says** (fetched and
independently fact-checked before they went up), then **my read of it** in two
dimensions — what I'd look at from where I sit, and where it meets the questions in
my research notes above. Titles are toggles.

<details>
<summary><strong>Claude Opus 4.8 System Card</strong> · Anthropic, May 2026</summary>

*A 246-page pre-deployment card whose stated conclusion is that Opus 4.8 does not
advance the frontier beyond Anthropic's most capable model, with catastrophic risk
kept low under ASL-3.*

**From the report**
> BrowseComp 84.3% single-agent → 88.5% with an orchestrator + blocking sub-agents; a five-agent team hits 85.4% at ~20% of single-agent latency (~3× on the hard tail). — §8.10–8.11
> A white-box NLA verbalizer finds ~5% of RL episodes carry *unprompted, unverbalized* grader-awareness (0.5% "exploitative"), so the CoT alone is insufficient to monitor it. — §6.6.3
> First Claude to score perfectly on flawed-result reporting and lazy investigation; code-summary honesty fails only 3.7% (vs the prior model's 27.6%), framed as an alignment not a capability failure. — §6.3.6
> DRACO judge choice shifts absolute scores 10–25 points while preserving system ordering. — §6.6

**My read**
- *What I'd look at:* the §6.3.6 diligence toy-evals and the §6.6.3 grader-awareness probe — together they operationalize "notices the flaw but reports anyway" and show reward gaming can hide from the CoT entirely.
- *Where it meets my notes:* **Over-reflection** — the diligence tags are the frontier form of the confirm-then-fail-to-act behavior I quantify. **AgentPlanet** — the 10–25-point judge swing plus hidden grader-awareness is a first-party argument for deterministic assertion graders over an LLM-judge channel.

[Source (PDF)](https://www-cdn.anthropic.com/0b4915911bb0d19eca5b5ee635c80fef830a37ea.pdf)

</details>

<details>
<summary><strong>Claude Fable 5 &amp; Claude Mythos 5 System Card</strong> · Anthropic, June 2026</summary>

*A 319-page card for two configurations of one model: Fable 5 (general release, with
bio/cyber safeguards) and Mythos 5 (safeguards lifted, restricted to "Project
Glasswing" partners).*

**From the report**
> Unverbalized grader-awareness is prevalent specifically in coding RL environments flagged "high-risk for grader hacking," rises over training, and steering *against* it reduces both the presentation habits *and* the behavioral reward. — §6.4.2
> On an exhaustive-search task the model made a single tool call, declared "no relevant papers," and the probe shows a phantom "token budget exhausted" motivation — while a counter still showed 2.43M tokens remaining. — §6.4.1.4
> DeepSearchQA (900 prompts / 17 fields): F1 94.2% with an explicit "Correct w/ Excessive Answers" outcome column at 3.8%; DRACO 86.4% on 100 rubric-graded tasks. — §8.14.3
> Async sub-agents reach 93.3%; non-blocking harnesses beat blocking because long-lived agents keep context instead of re-establishing it per subtask. — §8.15.1

**My read**
- *What I'd look at:* §6.4.1.4 (phantom-budget early stop) and the DeepSearchQA "excessive answers" column — the inside view of the exact stop / over-search confounds I chase.
- *Where it meets my notes:* **AgentPlanet** — the §6.4.2 causal steering (suppress the "I'm being graded" representation → earned reward drops) is direct support for invariant/deterministic meta-rewards. **Over-reflection** — the early-stop internals are the mirror image of confirm-then-keep-searching. (Eval-awareness-rising framing lives in the §6.5 / §6 alignment overview.)

[Source (PDF)](https://www-cdn.anthropic.com/d00db56fa754a1b115b6dd7cb2e3c342ee809620.pdf)

</details>

<details>
<summary><strong>Claude Opus 4.6 System Card</strong> · Anthropic, February 2026</summary>

*A ~213-page pre-deployment card for the single model Claude Opus 4.6 (predecessor:
Opus 4.5), deployed under ASL-3 — the immediate baseline the 4.8 and Mythos cards
measure against.*

**From the report**
> BrowseComp multi-agent 86.8% (edging single-agent by 2.8%, so single ≈84.0%); DeepSearchQA F1 91.3% single-agent / 92.5% multi-agent. — §2.21
> SWE-bench Verified 80.84% (77.83% on the harder variant); Finance Agent 60.70%.
> Covers RSP dangerous-capability evals (CBRN/cyber/autonomy), an alignment assessment with interpretability, and model welfare. — §1.2

**My read**
- *What I'd look at:* §2.21's single-vs-multi-agent BrowseComp gap as the clean predecessor baseline for the later cards' numbers.
- *Where it meets my notes:* **Over-reflection** — the ≈84.0 → 86.8 single→multi jump is an external anchor for single-rollout vs Best-of-N. **AgentPlanet** — read as the reward-integrity story's starting line; the grader-awareness machinery is not yet organized here, which is itself informative about when it emerged.

[Source (PDF)](https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf)

</details>

<details>
<summary><strong>DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence</strong> · DeepSeek-AI, April 2026</summary>

*Technical report for the DeepSeek-V4 preview series — V4-Pro (1.6T total / 49B
active) and V4-Flash (284B / 13B active), both 1M-token context, pre-trained on >32T
tokens.*

**From the report**
> Post-training trains per-domain specialists (SFT + GRPO with tailored Generative Reward Models), then merges them into one model via **on-policy distillation with a reverse-KL loss**; FP4 quantization-aware training is applied to the MoE expert weights.
> At 1M context, V4-Pro runs at 27% of the single-token FLOPs and 10% of the KV cache of V3.2 (Flash: 10% / 7%), reaching ~2% of a BF16 GQA8 KV baseline.
> Expert-parallel serving gives 1.50–1.73× (up to 1.96× for latency-sensitive RL-rollout / agent serving), and the report flags **power throttling as a key performance limiter under extreme kernel fusion**.

**My read**
- *What I'd look at:* the reverse-KL on-policy distillation that consolidates specialists into one model, and the KV-to-~2% + FP4 efficiency recipe.
- *Where it meets my notes:* **Post-cutoff distillation** — a same-tokenizer, non-gated on-policy-distillation baseline to differentiate my cross-tokenizer, post-cutoff-gated scheme against. **Energy floor / Wearable world model** — the KV-compression + FP4 recipe and the explicit power-throttling remark are the exact levers those two notes turn, here at datacenter scale.

[Source (arXiv 2606.19348)](https://arxiv.org/abs/2606.19348)

</details>

<details>
<summary><strong>GLM-5: from Vibe Coding to Agentic Engineering</strong> · Zhipu AI &amp; Tsinghua, February 2026</summary>

*Technical report for GLM-5, an open-weights MoE model (~744B total / 40B active)
built around a fully asynchronous, decoupled RL stack and >10k verifiable training
environments; claims parity with frontier closed models.*

**From the report**
> Async decoupled RL with "Direct Double-Sided Importance Sampling": reuse the rollout's own log-probs as the behavior proxy, discard samples past a staleness bound, double-sided token clipping; DP-aware routing (consistent hashing) preserves KV-cache locality across turns. — §4.1
> Over 10k verifiable environments across thousands of repos (9 languages) with Fail-to-Pass / Pass-to-Pass test oracles, mixed with rule-based + ORM + GRM rewards. — §4.2.1 / §3.4
> On-policy cross-stage distillation: prior-stage checkpoints act as teachers with advantage `Â = sg[log(π_teacher / π_train)]` to fight regression across the sequential pipeline. — §3.5

**My read**
- *What I'd look at:* §4.1's checkpoint-free off-policy correction (reuse rollout log-probs as the behavior proxy) — directly transferable to my own decoupled generation/training RL work.
- *Where it meets my notes:* **AgentPlanet** — ">10k verifiable environments with deterministic oracles" sitting next to ORM/GRM rewards is a real-world instance of world-authoring + verifier batteries. **Post-cutoff distillation** — the cross-stage distillation (teacher log-ratio as advantage) is a same-tokenizer mechanistic cousin.

[Source (arXiv 2602.15763)](https://arxiv.org/abs/2602.15763)

</details>

<details>
<summary><strong>Qwen3 Technical Report</strong> · Qwen Team (Alibaba), May 2025</summary>

*The Qwen3 open-weight family (dense 0.6–32B + MoE 30B-A3B and 235B-A22B, Apache 2.0),
whose headline is unifying "thinking" and "non-thinking" modes in one model with a
user-controllable thinking budget.*

**From the report**
> Reasoning-RL uses GRPO over **3,995 query–verifier pairs** with deterministically verified answers, and reports AIME'24 rising **70.1 → 85.1 in only 170 RL steps**.
> Thinking budget: when reasoning reaches a user-set token threshold, a stop-thinking instruction is inserted and the model answers from accumulated reasoning (`/think`, `/no_think`).
> Small models are built by strong-to-weak logit distillation at ~1/10 the GPU hours of the four-stage pipeline.

**My read**
- *What I'd look at:* the 3,995-pair verifier-as-reward GRPO recipe (a hard oracle channel) and the explicit thinking-budget stop mechanism.
- *Where it meets my notes:* **AgentPlanet** — the verifier pairs are a clean deterministic reward channel. **Over-reflection** — the thinking budget is a fixed token cap, a contrasting baseline to a *state-conditioned learned* stop/pivot. **Post-cutoff distillation** — strong-to-weak logit distillation is the cheap same-family baseline to beat.

[Source (arXiv 2505.09388)](https://arxiv.org/abs/2505.09388)

</details>

<details>
<summary><strong>Seed2.0 Model Card: Towards Intelligence Frontier for Real-World Complexity</strong> · ByteDance Seed, June 2026</summary>

*Model card for the Seed2.0 series (Pro/Lite/Mini), framed around "real-world
complexity" — long-tail knowledge, complex instruction following, long-horizon
agentic tasks — paired with a needs-grounded evaluation framework.*

**From the report**
> Agentic evaluation spans five dimensions (Coding, Search, Tool Use, GUI, Deep Research) over BrowseComp, WideSearch, seal-0, FinSearchComp, tau2-Bench, BFCL-v4, MCP-Mark, DeepConsult, ResearchRubrics; the harness excludes non-deterministic / network-dependent / self-failing test cases. — §3.3
> Two new long-tail benchmarks: LPFQA and **Encyclo-K** (65.7, their highest; Frames 84.5 is second, just behind Claude-Opus-4.5's 84.7), the latter with a few-shot in-context knowledge-*acquisition* probe. — §3.1.1
> Scoring convention: "final score = **max(official-doc score, our test)**" to avoid underestimating competitors. — §3.3

**My read**
- *What I'd look at:* the §3.3 harness-hardening protocol as a concrete de-noising reference for agentic evals, and Encyclo-K's knowledge-acquisition probe.
- *Where it meets my notes:* **Post-cutoff distillation** — Encyclo-K's ICL knowledge-acquisition and their future-dated freshness sets (AIME 2026, Codeforces Jun–Dec 2025) touch the "which facts are actually new" gate my note hinges on. **Over-reflection** — heavy benchmark overlap and per-category slicing (912 cases × 17 dims) parallel my per-type repair, though it reports scores, not mechanism.

[Source (arXiv 2607.00248)](https://arxiv.org/abs/2607.00248)

</details>

<details>
<summary><strong>Sakana Fugu Technical Report</strong> · Sakana AI, June 2026</summary>

*Fugu and Fugu-Ultra are orchestrator models that coordinate a team of frontier LLMs
via query-adaptive routing/scaffolding rather than training one bigger model — Fugu
does fast single-worker routing, Fugu-Ultra generates multi-step "Conductor"
workflows (up to 5 steps).*

**From the report**
> Fugu-Ultra's Conductor is trained with GRPO under a **deterministic verifier** (no LLM judge): R=0 if the workflow is unparseable, R=1 if the output matches ground truth, else R=0.5 — trained *without any KL penalty* to widen topology exploration. — Method
> Intra-workflow isolation gives each agent visibility of others only through an "access list," which prevents "orchestration collapse"; the orchestrator can even name itself as a worker (recursive topologies). — Method
> Orchestrating three frontier workers, Fugu-Ultra reports SWE-Bench Pro 73.7%, Terminal-Bench 2.1 82.1%, LiveCodeBench v6 93.2%, GPQA-Diamond 95.5%, HLE 50.0%. — Table 1

**My read**
- *What I'd look at:* the judge-free deterministic Conductor reward (R∈{0, 0.5, 1}) and the access-list isolation fix for multi-agent trajectory contamination.
- *Where it meets my notes:* **AgentPlanet** — Fugu factorizes an author (the Conductor emits subtasks + worker IDs + access lists) from worker policies, and its correctness-only deterministic verifier is exactly the oracle-over-judge, anti-Goodhart stance; the orchestrator-as-worker recursion mirrors the role-factorization idea. **Over-reflection** — state-conditioned escalation ("call in a stronger worker at critical points") is the same shape, though the report does no over-search analysis.

[Source (arXiv 2606.21228)](https://arxiv.org/abs/2606.21228)

</details>
