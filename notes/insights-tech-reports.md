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
<summary><strong>GPT-5.5 System Card</strong> · OpenAI, April 2026</summary>

*OpenAI's system card for GPT-5.5, a reasoning model aimed at long-horizon real-world
work (coding, research, cross-tool agentic action), covering Preparedness-Framework
capability evals with heavy focus on computer-use confirmation protocols,
agent-vs-user-work separation, and coding-agent misalignment monitoring.*

**From the report**
> To resample internal coding-agent trajectories they built a tool-response simulator with access to codebase state; realism was checked against a GPT-5.4-Thinking judge tasked with picking the real trajectory, which won only 52.5% of the time. — §7.2
> The 0–4 severity misalignment monitor has 97.6% recall on 21 human-labeled sev-3 transcripts, but under full category ablation recall collapses to 49.6%, and 95% of current sev-3 traffic would be labeled ≥ sev-2 while fewer than half would be labeled sev-3. — §7.2.1
> Destructive-action avoidance rises to 0.90 (vs 0.86 for GPT-5.4-Thinking); on long rollouts "Perfect reversion" jumps to 0.52 (vs 0.18) — agents were trained to revert their own changes while protecting simulated user work. — §3.3
> Cyber is treated High-but-not-Critical: CTF-Professional pass@12 96.3% (saturating), cyber-range combined 93.33% (vs 73.33%) attributed to "persistence at exploitation," but no verifier-confirmed full-chain Critical exploit. — §9.1.2

**My read**
- *What I'd look at:* §7.2's tool-response simulator + the 52.5% discriminator — essentially a learned world-model + fidelity verifier, reusable for validating synthesized environments; and §7.2.1's monitor-recall collapse (97.6→49.6 under ablation) as a quantified anti-Goodhart caution about how much an LLM-judge-as-reward misses out-of-taxonomy behavior.
- *Where it meets my notes:* **AgentPlanet** — the tool-response simulator is a learned world-model surrogate with a 52.5% fidelity discriminator, and §9.1.2 puts deterministic-oracle rewards (hidden tests, medal thresholds, exploit success) next to an LLM judge — the same oracle-vs-judge factorization. **Over-reflection** — GPT-5.5's flagged failures are *over-action* ("overeager action when only asked questions," "persistence at exploitation"), and the 86.4%-coverage situation×action subcategorization mirrors my per-type repair.

[Source (PDF)](https://deploymentsafety.openai.com/gpt-5-5/gpt-5-5.pdf)

</details>

<details>
<summary><strong>Gemini 3.1 Pro — Model Card</strong> · Google DeepMind, February 2026</summary>

*A model card for Gemini 3.1 Pro (evaluated in "Thinking (High)"), reporting headline
benchmark scores across agentic tool-use, coding, search, and long context — and
deferring all architecture/training details to the Gemini 3 Pro card.*

**From the report**
> Agentic coding: Terminal-Bench 2.0 68.5%, SWE-Bench Verified 80.6%, SWE-Bench Pro (Public) 54.2%. — benchmarks table
> Tool use: tau2-bench Telecom 99.3% / Retail 90.8%, MCP Atlas 69.2%, APEX-Agents 33.5%. — benchmarks table
> Search: BrowseComp 85.9% (Search + Python + Browse); Humanity's Last Exam 44.4% (no tools) vs 51.4% (Search (blocklist) + Code). — benchmarks table
> Long context: up to 1M tokens / 64K output, but MRCR v2 drops from 84.9% at 128k to 26.3% at 1M. — specs + table

**My read**
- *What I'd look at:* the agentic cluster — tau2-bench Telecom 99.3% near-ceiling vs APEX-Agents collapsing to 33.5% is the spread between saturated and unsaturated agentic verifiers — and MRCR v2's 84.9→26.3 collapse as the load-bearing "1M context" caveat. It's a thin iteration card: no RL/reasoning-training method or knowledge cutoff is stated, so don't cite it for training claims.
- *Where it meets my notes:* **AgentPlanet** — tau2-bench Telecom essentially saturated at 99.3% is a deterministic-verifier benchmark hitting its ceiling, an anti-Goodhart data point that motivates harder auto-curriculum and verifier batteries. **Over-reflection** — BrowseComp 85.9% and Terminal-Bench 2.0 68.5% are an external single-model reference on the browsing/long-horizon surface my analysis runs on.

[Source (model card)](https://deepmind.google/models/model-cards/gemini-3-1-pro/)

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
<summary><strong>Nemotron 3 Nano: Open, Efficient MoE Hybrid Mamba-Transformer for Agentic Reasoning</strong> · NVIDIA, December 2025</summary>

*Technical report for Nemotron 3 Nano 30B-A3B, an open MoE hybrid Mamba-Transformer
(31.6B total / 3.2B active) post-trained with SFT + large-scale multi-environment
RL-from-verifiable-rewards via the open-sourced NeMo Gym / NeMo RL stack, a
GenRM-based RLHF stage, and FP8 quantization.*

**From the report**
> "We employ a unified RLVR stage, training on all environments simultaneously… single environment training often results in un-recoverable degradation of other benchmarks." — §3.2
> NeMo Gym factors an RL environment into three server types — agents (rollout kernel), models (inference wrapper preserving tokens/log-probs), and resources ("provides a verification API for computing rewards from a given rollout"). — §3.2.4
> Auto-curriculum: drop tasks the SFT checkpoint already passes 100%, model each domain's target pass-rate as a Gaussian sliding easy→hard, and re-profile with the best checkpoint at plateau. — §3.2.2
> GenRMs "generalize better than traditional Bradley-Terry models, reducing the risk of reward hacking"; Group Relative Length Control cuts verbosity "30%… without sacrificing accuracy." — §3.3
> FP8 post-training quantization with selective BF16: the 6-of-52 attention layers and their preceding Mamba layers stay BF16, giving "~99% median accuracy recovery compared to the BF16 model." — §4.2–4.3

**My read**
- *What I'd look at:* §3.2.4 NeMo Gym (agents / models / resources, where the resource server is a verification API that computes reward) — a productized version of what env-synth/dive-synth build; and §3.2.2's Gaussian sliding-pass-rate auto-curriculum, directly transplantable to a self-evolving loop.
- *Where it meets my notes:* **AgentPlanet** — the env-factored-into-servers-with-a-verifier design plus "train on all envs at once + re-profile at plateau" are exactly the verifier-battery + self-evolving-curriculum patterns. **Over-reflection** — Group Relative Length Control penalizes group-relative reasoning length while gating a conciseness bonus, separating length inflation from reward hacking — the same over-thinking pathology as my stop/pivot reward. **Energy floor** — §4's per-layer FP8 sensitivity + FP8 KV-cache-for-throughput is concrete quantization + KV-compression evidence (a language model, so the world-model tie is a stretch).

[Source (PDF)](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Nano-Technical-Report.pdf)

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
<summary><strong>Kimi K2.5: Visual Agentic Intelligence</strong> · Moonshot AI (Kimi Team), February 2026</summary>

*An open multimodal agentic model trained with joint text-vision pre-training, text-only
"zero-vision" SFT, and text+vision RL. Its headline is "Agent Swarm," which trains an
orchestrator to decompose a task into heterogeneous sub-problems run concurrently by
frozen subagents.*

**From the report**
> Agent Swarm vs single-agent (Table 6): BrowseComp 60.6% → 78.4% (+17.8pp); WideSearch Item-F1 72.7% → 79.0% (past Claude Opus 4.5's reported 76.2%); in-house Swarm Bench 41.6% → 58.3%.
> PARL reward = λ1·r_parallel (vs serial collapse) + λ2·r_finish (vs spurious parallelism) + r_perf; λ1, λ2 are annealed to zero, with a decoupled trainable-orchestrator + frozen-subagents design "to prevent credit-assignment ambiguity and training instability." — §3
> Visual RL improves text benchmarks "without observable degradation of language capabilities": MMLU-Pro 84.7→86.4, GPQA-Diamond 84.3→86.4, LongBench v2 56.7→58.9. — Table 2
> Agent Swarm cuts latency "up to 4.5×" vs single-agent, with a CriticalSteps metric constraining parallelization to avoid wasteful subagent spawning. — §5.2

**My read**
- *What I'd look at:* §3's PARL reward — r_finish penalizes "spurious parallelism" and r_parallel prevents "serial collapse," both auxiliary weights annealed to zero — a concrete anti-degeneracy reward-shaping recipe I could mirror in a state-conditioned stop/pivot reward; and whether the +17.8pp BrowseComp gain is genuine orchestration or search-recall recovery via fan-out.
- *Where it meets my notes:* **AgentPlanet** — the decoupled trainable-orchestrator vs frozen-subagents split (which role gets gradient) plus the three-term anti-Goodhart reward is role-factorization + reward-integrity design. **Over-reflection** — r_finish against spurious parallelism and CriticalSteps against wasteful spawning are the stop/pivot control I want, measured on my exact BrowseComp/WideSearch suite.

[Source (arXiv 2602.02276)](https://arxiv.org/abs/2602.02276)

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
<summary><strong>Olmo 3</strong> · Allen Institute for AI (Ai2), December 2025</summary>

*A fully-open 7B/32B family released with the entire "model flow" — every training
stage, checkpoint, dataset, and code dependency from base through Think/Instruct/RL-Zero —
plus new data (Dolma 3, Dolci), an RLVR framework (OlmoRL), and an RL-from-base setup
(RL-Zero) built to study how pretraining data affects RL without contamination.*

**From the report**
> Rewards are domain-specific: math a rule-based SymPy verifier, code a test-case verifier on AWS Lambda, instruction-following a binary constraint-checker, and general chat an LM-judge (Qwen3 32B, thinking off) scoring [0,1] — mixing verifiable and non-verifiable rewards over ~100K prompts across 4 domains. — §4.4.1
> RL-Zero negative control: training the base model with random/spurious rewards yields no benchmark gains, confirming eval decontamination; a domain mix gives lower train reward yet equal/better downstream, preventing over-optimization / reward-hacking. — §6.2 / §4.5
> OlmoRL layers DAPO/Dr-GRPO advances (zero-gradient filtering, active sampling, token-level loss, no-KL, clip-higher, truncated importance sampling, no-std-dev normalization) for a 4× RL-training speedup; infra ablation 6.34→21.23 Mtok, MFU 0.30%→1.01%. — §4.4.1 / Table 23
> Olmo 3.1 Think 32B is reported as the strongest fully-open thinking model to date, competitive with Qwen 3 32B while trained on ~6× fewer tokens (MATH 96.2, AIME 2025 78.1). — Table 1

**My read**
- *What I'd look at:* §4.4.1 + Fig 16 — the per-domain split of deterministic oracles (SymPy / test-cases / constraint-checks) vs an LM-judge for open-ended chat is exactly the oracle-vs-judge reward-channel design I care about, with a recipe for which domain gets which; and the §6.2 spurious-reward negative control as a runnable anti-Goodhart probe.
- *Where it meets my notes:* **AgentPlanet** — the deterministic-verifier-vs-LM-judge split, the random-reward negative control that verifies decontamination, and the "domain mix curbs reward-hacking" finding are a concrete verifier/invariant battery as meta-reward. **Over-reflection** — OlmoRL response-length dynamics, dropped length-control verifiers, explicit 32K/16K/8K caps, and §3.3 eval-noise handling touch my sequence-cap and eval-noise confounds.

[Source (arXiv 2512.13961)](https://arxiv.org/abs/2512.13961)

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
