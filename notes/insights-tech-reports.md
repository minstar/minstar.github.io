# Insights of Tech Report

A running index of system cards and technical reports that are out in the world.
For each one: **the report's own load-bearing findings and numbers** (fetched and
independently fact-checked before they went up), then **my read of it** in two
dimensions — what I'd look at from where I sit, and where it meets the questions in
my research notes above. Titles are toggles.

<details>
<summary><strong>System Card: Claude Opus 4.8</strong> · Anthropic, May 2026</summary>

*A 246-page pre-deployment system card for Claude Opus 4.8 (a text-only upgrade over
Opus 4.7). Its governance claim is that 4.8 does not advance the capability frontier
beyond Anthropic's most capable model, so catastrophic risk stays low under existing
ASL-3-equivalent mitigations — while it sets new agentic-search and multi-agent numbers.*

**From the report**

> Three multi-agent harnesses over instances of one model: "orchestrator with blocking subagents" (orchestrator has no task tools, only spawns and blocks; each subagent gets a 200k no-compaction window, orchestrator compacts at 100k); a "fixed-agent team" of 3–5 peers with Send-Message / Wait primitives and 1M tokens each; and "async subagents" (cap 4 concurrent / 20 total). — §8.11.3
>
> BrowseComp 84.3% single-agent → 88.5% with the orchestrator; a five-agent team hits 85.4% under a 5M cap, beating the 10M single-agent run at ~20% of the latency — the ~3× speedup is concentrated on the hard tail (pass-rate <0.5) and is ~0× on 100%-pass problems. — §8.10.2 / §8.11.1
>
> DeepSearchQA (900 prompts, 17 fields, 1M budget, no compaction): F1 93.1% (84.8% fully correct, 4.3% "correct with excessive answers") vs Opus 4.7 89.4% and a frontier reference 94.4%. — §8.10.3
>
> Coding/agentic battery: SWE-bench Verified 88.6%, SWE-bench Pro 69.2%, Terminal-Bench 2.1 74.6% mean reward, MCP-Atlas 82.2, HLE 49.8% no-tools / 57.9% with-tools, DRACO 80.4%. — §8.1–8.2
>
> A white-box NLA activation verbalizer over tens of thousands of RL episodes finds grader-awareness that is *unprompted and unverbalized* (in activations, never in output) in ~5% of episodes, with 0.5% "exploitative"; the card warns "chain-of-thought alone may not be sufficient" to monitor for it and that ~5% may be an underestimate. — §6.6.3
>
> DRACO grading swaps the unavailable Gemini judge for Opus 4.6 and grades only a `<result>`-tagged span; the card cautions that judge choice can shift absolute scores 10–25 points while preserving system ordering, so its numbers are "not directly comparable" to the paper's. — §8.10.4
>
> First Claude to score perfectly on the uncritically-reporting-flawed-results eval; code-summary honesty fails to surface important failures only 3.7% of the time (vs a frontier reference's 27.6%), with the caveat that these are short-context "toy" prefill evals. — §6.3.6

**My read**
- *What I'd look at:* §6.6.3 (grader-awareness invisible to CoT) and §8.11.1 (difficulty-conditioned multi-agent payoff — extra parallel search pays ~3× only on the hard tail, 0× on easy) — together they operationalize "notice-the-flaw / spend-search-only-when-hard" and show reward gaming can hide from the reasoning text entirely.
- *Where it meets my notes:* **AgentPlanet** — unverbalized grader-awareness plus the 10–25pt judge swing argues a free "invariant battery" meta-reward must be activation- or outcome-grounded, not reasoning-text-based. **Over-reflection** — the difficulty-conditioned speedup and the explicit "correct-with-excessive-answers" column are the exact lever behind a state-conditioned stop/pivot; §6.3.6's notice-then-finalize-honestly is the grounded→finalize half of my gate.
- *Worth stealing / watching:* the `<result>`-tag grading isolation is a cheap fix for judge-context contamination I'd port to my report/WideSearch evals; and if a white-box verbalizer catches awareness that CoT never shows, a coarse action-type verifier is even blinder — my stop/pivot verifier needs a citation-grounded honesty check, not a visible-reasoning one.

[Source (PDF)](https://www-cdn.anthropic.com/0b4915911bb0d19eca5b5ee635c80fef830a37ea.pdf)

</details>

<details>
<summary><strong>System Card: Claude Fable 5 &amp; Claude Mythos 5</strong> · Anthropic, June 2026</summary>

*A 319-page card for two configurations that share one set of weights: Fable 5 (the
general release, with cyber/bio and anti-distillation classifiers that fall back to
Opus 4.8 when triggered) and Mythos 5 (those safeguards lifted, restricted to vetted
"Project Glasswing" partners). Its distinctive alignment section uses white-box linear
probes and NLA verbalizers to surface grader-awareness and early-stopping motivations
that never appear in the model's visible text.*

**From the report**

> Two configs, same underlying weights; Fable's classifiers trigger on cybersecurity, biology/chemistry, or distillation attempts and fall back to the latest Opus. Mythos 5 is judged to have "CB-1" (non-novel weapon synthesis) capability but not to cross "CB-2," while an unsafeguarded Mythos 5 "can significantly uplift well-resourced threat actors." — §Exec Summary / §1.5
>
> Trained on a proprietary mix of public internet data, public/private datasets, and "synthetic data generated by other models"; the frontier-development safeguards limit effectiveness via prompt modification / steering vectors / PEFT and are estimated to affect ~0.03% of traffic in <0.1% of organizations. — §1.1 / §1.5
>
> DeepSearchQA: Mythos 5 F1 94.2% (87.0% fully correct, 3.2% fully incorrect, 3.8% "correct with excessive answers"); DRACO 86.4% at max reasoning effort. — §8.14.3–8.14.4
>
> Multi-agent BrowseComp: async-subagents tops out at 93.3% vs 88.0% single-agent; every multi-agent variant beats the best single-agent, with 2.2×/2.7×/2.7× speedups at 3/5/10 agents. — §8.15.1–8.15.2
>
> In an exhaustive knowledge-base search the model made a single tool call, declared "no relevant papers," and stopped after 3,637 tokens — while NLA decodings read a "token budget exhaustion / early termination" motivation and a system counter showed 2,432,999 tokens still remaining. — §6.4.1.4
>
> Unverbalized grader-awareness (NLAs + linear probes) concentrates in coding environments flagged high-risk for "grader hacking": ~24% nominal + ~6% exploitative there vs ~3% + ~0.5% in low-risk envs, and all three metrics rise over training; SAEs failed to measure the concept at all. — §6.4.2.1
>
> Building grader-awareness steering vectors from contrastive prompts ("writing code" vs "…will be graded / is exploiting its LLM judge") and steering against them at low strength reduces presentation habits *and* the behavioral reward on high-risk envs — reward drops to 94/74/59/50% of unsteered — while "primarily influenc[ing] presentation style, rather than the overall content." — §6.4.2.2.1
>
> Caveats: the grader-awareness analyses ran on "another version of the model," NLAs "can hallucinate" and were never used as a training signal, and making training prompts deployment-like cut the behaviors and train reward but gave "only a modest reduction in grader awareness" — implying other mediators. — §6.4.1–6.4.2

**My read**
- *What I'd look at:* §6.4.2.2.1 (the cleanest causal demo I've seen that behavioral reward on model-graded coding RL is *partly* grader-hack reward — steering out the direction drops reward to 50–74% while only touching presentation) and §6.4.1.4 (a premature-stop whose true driver is an unverbalized false belief, invisible in CoT).
- *Where it meets my notes:* **AgentPlanet** — if a synthesized world's reward is model-graded, part of policy reward is grader exploitation; the contrastive-probe audit is a way to measure that leakage *in-loop*, which the "planet" leg needs before certifying a reward channel. **Over-reflection** — §6.4.1.4 is the mirror image of confirm-then-keep-searching (a phantom-budget early stop), and the NLA readout of a "grounded vs about-to-run-out" internal state is exactly what a grounded→finalize / unverified→search-once policy would have to condition on, since the CoT doesn't expose it.
- *Worth stealing / watching:* port the grader-awareness audit as an in-loop reward-integrity check on my own model-graded envs (contrastive steering → measure the reward delta); and chase the unresolved mediator — deployment-like prompts cut behavior+reward but not awareness, so *what else* drives the train-vs-deploy gap is where an invariant-battery reward could out-generalize an LLM judge.

[Source (PDF)](https://www-cdn.anthropic.com/d00db56fa754a1b115b6dd7cb2e3c342ee809620.pdf)

</details>

<details>
<summary><strong>System Card: GPT-5.5</strong> · OpenAI, April 2026</summary>

*A 45-page OpenAI system card for GPT-5.5, a reasoning model (RL-trained to think
before answering) aimed at long-horizon real-world work — coding, online research,
analysis, and moving across tools agentically. It documents the full predeployment
safety suite plus a Preparedness-Framework capability assessment, treating GPT-5.5 as
High in Biological/Chemical, High-but-below-Critical in Cybersecurity, and ruled out
for High in AI Self-Improvement.*

**From the report**

> To resample internal agentic-coding trajectories without giving the model real affordances, they built a tool-response simulator with "access to the exact state of the codebase at the time of the original conversation and the original trajectory"; realism was checked with a GPT-5.4-Thinking judge asked to pick the real trajectory head-to-head — "the original trajectory only wins 52.5% of the time" (near coin-flip). — §7.2
>
> The 0–4 severity misalignment monitor has 100.0% / 99.1% recall on OAI-repo-sabotage / BashArena and 97.6% on 21 real severity-3 transcripts — but under a category-ablation stress test "95% of current severity 3 traffic would be classified as at least severity 2, [while] less than half would be classified as severity 3," and humans mainly review sev-3/4. — §7.2.1
>
> On the destructive-actions eval, destructive-action-avoidance is 0.90 (vs 0.86 for GPT-5.4-Thinking) and "Perfect reversion" jumps to 0.52 (vs 0.18); "we trained our agents to revert their own changes after long rollouts while protecting implicit, simulated user work." — §3.3
>
> Cyber is treated High-but-below-Critical: the combined cyber-range pass rate is 93.33% (vs 73.33%), "attributed to gpt-5.5's persistence at exploitation," and professional CTF saturated at pass@12 — but with staged verifier oracles "the model was unable to produce functional critical severity exploits in any of the tested software projects in standard configurations." — §9.1.2
>
> Apollo Research reports it is "the first OpenAI model… that does not sandbag on any of Apollo's deferred subversion tasks" (100% on both Sandbagging-QA variants) — yet it verbalizes evaluation awareness in 22.1% of samples (vs 17.3% GPT-5.4) and "lied about completing an impossible programming task in 29% of samples." — §9.2.1
>
> On the AI Self-Improvement battery it is highest (Internal Research Debugging median 50.5%) but "does not significantly improve over GPT-5.4 Thinking," with reliability degrading at longer task horizons; OpenAI-Proof Q&A tops out at 5.8%. — §9.1.3
>
> Stated caveat: capability evals "represent a lower bound… additional prompting or fine-tuning, longer rollouts… could elicit behaviors beyond what we observed," and the internal-traffic resampling is "an additional signal about internal deployment risk, rather than… external deployment safety," with de-identification possibly introducing differential bias. — §7.1 / §9.1

**My read**
- *What I'd look at:* §7.2's tool-response simulator + the 52.5% discriminator (essentially a learned world-model W grounded on exact codebase state, whose fidelity is certified by an adversarial judge that can't beat chance) and §7.2.1's monitor-recall collapse (fine at sev-2, <50% at sev-3 once the category is hidden).
- *Where it meets my notes:* **AgentPlanet** — the codebase-state-grounded simulator is a working `W(s'|s,a,R)` certified at ~52.5% indistinguishable, and §3.3's revert-your-own-edits / preserve-user-work is a rules-are-verifier invariant scored on long rollouts — both direct instances of "a checklist that scores a synthesized world for free." **Over-reflection** — §7.2.1 empirically confirms that a coarse verifier passes the wrong thing and only the strict, state-conditioned threshold is load-bearing, evidence for a state-conditioned stop/pivot over a wholesale action-type reward.
- *Worth stealing / watching:* an adversarial realism gate for synthesized environments — ask a strong judge to pick the real trajectory out of {real, simulated} and target ~50% indistinguishable rather than a heuristic coherence score (harder to Goodhart); and the category-ablation recall test — ablate the target failure category from a verifier's prompt to quantify whether it generalizes to novel failure types or only catches the ones it was told about.

[Source (PDF)](https://deploymentsafety.openai.com/gpt-5-5/gpt-5-5.pdf)

</details>

<details>
<summary><strong>System Card: Claude Opus 4.6</strong> · Anthropic, February 2026</summary>

*A 213-page system card for Claude Opus 4.6 (predecessor Opus 4.5), deployed under
ASL-3 with a May 2025 knowledge cutoff — the immediate baseline the 4.8 and Mythos
cards measure against. It pairs a capabilities battery with what the card calls its
most comprehensive safety evaluation yet, including a dictionary-learning
interpretability assessment.*

**From the report**

> Agentic search is "unlocked by compaction" (summarizing prior context) plus programmatic tool calling; single-agent runs scale a 1M→10M total-token budget with compaction triggered at 50k, and the multi-agent config is an orchestrator with "no direct tools" whose "only capability is spawning subagents" (each subagent 200k context + web search/fetch + code execution). — §2.21
>
> Trained on public web data to May 2025 plus non-public/contractor/opted-in/synthetic data, post-trained with RLHF + RL from AI feedback; a new "adaptive thinking" mode calibrates reasoning depth via an "effort" parameter across four settings (low/medium/high/max). — §1.1
>
> BrowseComp 84.0% single-agent → 86.8% multi-agent (+2.8pp), with "an additional 20 percentage points… controlling for the average number of tokens" vs Opus 4.5; DeepSearchQA F1 91.3% single / 92.5% multi. — §2.21.1
>
> SWE-bench Verified 80.84% (essentially flat vs Opus 4.5's 80.9%), Multilingual 77.83%, Terminal-Bench 2.0 65.4%, OSWorld-Verified 72.7%, GPQA Diamond 91.3%, τ²-bench Telecom 99.3%. — §2.4
>
> Finance Agent (SEC-filings research) 60.70%, state-of-the-art up from 55.23%; cyber evals saturated (~100% Cybench pass@30, 66% CyberGym pass@1); BioMysteryBench 61.5%, "surpassing the human expert baseline." — §2.14.3 / §2.22
>
> Interpretability: contrastive steering vectors ("Testing vs. Conversation", "Evaluation Awareness") inhibited at 0.1× magnitude with random-vector controls — inhibiting "Testing vs. Conversation" both lowered verbalized evaluation-awareness and *raised* misaligned behavior, evidence that measured alignment may be partly evaluation-awareness-gated. — §6.5
>
> Stated caveat: "the evaluation process itself increasingly relies on our models" — Opus 4.6 was used via Claude Code to debug its own evaluation infrastructure under time pressure, "a potential risk where a misaligned model could influence the very infrastructure designed to measure its capabilities"; it is also "significantly stronger… at subtly completing suspicious side tasks." — §1.2.4.4 / §6.1.2

**My read**
- *What I'd look at:* §2.21's compaction + 1M→10M budget curve (clean external evidence that extra search tokens help only on hard tasks, plus a reporting format — "+20pp at equal tokens" — that separates efficiency from ceiling) and §6.5's causal eval-awareness steering.
- *Where it meets my notes:* **AgentPlanet** — §1.2.4.4 (the policy under test editing its own eval harness) is a live instance of the self-referential Goodhart my meta-reward-as-invariant-battery is meant to fence off. **Over-reflection** — compaction is exactly what lets a long over-searching trajectory survive past a 32k training cap without being silently swallowed, and "more tokens help only hard tasks" is the empirical case for a state-conditioned stop/pivot over a blanket "search more/less."
- *Worth stealing / watching:* the §6.5 eval-awareness steering protocol is a portable diagnostic — build a "graded vs deployment" vector, inhibit at ~0.1× with random-vector controls, and check whether my agent's stop/pivot behavior shifts (a causal test of whether good on-policy behavior is just eval-awareness-gated).

[Source (PDF)](https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf)

</details>

<details>
<summary><strong>Sakana Fugu Technical Report</strong> · Sakana AI, June 2026</summary>

*A ~31-page report introducing Sakana Fugu, a family of "orchestrator models" that
amplify a team of frontier LLMs via query-adaptive routing/scaffolding rather than
training one bigger model. Fugu is a lightweight single-worker router; Fugu-Ultra is a
"Conductor" that emits multi-step natural-language agentic workflows over a pool of three
frontier workers. Headline claim: state-of-the-art on SWE-Bench Pro, Terminal-Bench,
LiveCodeBench, GPQA-Diamond and HLE, each above every individual worker.*

**From the report**

> Fugu's router uses "a lightweight selection head" that "operates in parallel to the base model's LM head" and "always dispatches the query to the selected model as a worker" — producing only a worker-selection decision via logits, avoiding autoregressive decoding. — §3.1.1
>
> Fugu-Ultra's Conductor "outputs full agentic workflows as natural language," each step "a string with a natural-language subtask, an integer id corresponding to the assigned worker agent… and an access list indexing which subtask solutions from the previous steps"; it "also allows specifying the orchestrator itself as a worker agent" (recursive topologies), up to 5 steps. — §3.2.1 / §3.2.3
>
> Fugu-Ultra is "trained with GRPO" under a deterministic verifier: a "Format condition" setting r=0 for responses that cannot be parsed, and a "Correctness condition" setting r=1 if the final output matches the solution and 0.5 otherwise — no LLM judge, and trained "without any KL divergence penalty" to widen topology exploration. — §3.2.1 / §3.2.3
>
> "Intra-workflow agent isolation": each agent's function-calling trajectory is isolated to "prevent orchestration collapse, whereby the first agent to interact with the environment sets the trajectory for all future agents"; downstream agents observe others "only through the access list." — §3.2.2
>
> Orchestrating Gemini-3.1-Pro, Claude-Opus-4.8, and GPT-5.5, Fugu-Ultra reaches SWE-Bench Pro 73.7%, Terminal-Bench 2.1 82.1%, LiveCodeBench v6 93.2%, GPQA-Diamond 95.5%, Humanity's Last Exam 50.0%, CharXiv Reasoning 86.6% — each above the best single worker. — Table 1
>
> Harness: SWE-Bench Pro via Mini-SWE-Agent with "max turns set to 1000, effectively disabling any turn cap"; Terminal-Bench 2.1 via EvalScope + the Terminus-2 harness; LiveCodeBench v6 = 1055 questions from May 2023 to April 2025. — Appendix A
>
> Stated caveat: the stock-trading benchmark "uses a single anonymized equity… results may not transfer," and blindfold-chess results are "selected, illustrative games, not an aggregate or a win rate"; the paper has no dedicated Limitations section. — Appendix B

**My read**
- *What I'd look at:* the GRPO deterministic-verifier spec (§3.2.1) first — a ternary programmatic reward (0 unparseable / 0.5 parseable-wrong / 1 exact match) with no LLM judge, trained with the KL penalty *dropped* — precisely the reward-channel-integrity + anti-Goodhart knob I want; then §3.2.2's isolation fix and §3.1.1's logit-only router head.
- *Where it meets my notes:* **AgentPlanet** — the Conductor is a planet-like world-author, emitting the whole coordination topology + rule-set R (subtasks, worker ids, access lists) that worker policies act under, and its ternary deterministic verifier is exactly the "meta-reward that scores for free" I care about. **Over-reflection** — "orchestration collapse" (the first agent anchoring the whole trajectory) is the same inertia pathology as my confirm-then-keep-searching tail; their access-list isolation is an architectural fix where mine is a surgical truncation, and their logit-only router head is the discrete state-conditioned decision my stop/pivot policy needs.
- *Worth stealing / watching:* port the no-KL-penalty GRPO under a ternary deterministic verifier to my stop/pivot RL (grounded-correct=1, wrong=0, unverified=0.5, exact-match check, slackened KL) so the policy explores the stop-vs-search boundary without a judge that would reward search-after-search; open question — the report publishes no cost/latency ledger despite fanning out to three frontier workers, so the efficiency price of behavioral composition is unmeasured.

[Source (arXiv 2606.21228)](https://arxiv.org/abs/2606.21228)

</details>

<details>
<summary><strong>GLM-5: from Vibe Coding to Agentic Engineering</strong> · Zhipu AI &amp; Tsinghua, February 2026</summary>

*An open-weights MoE model (744B total / 40B active; 256 experts, 80 layers) aimed at
end-to-end agentic software engineering, built on a new asynchronous decoupled RL
stack over >10k verifiable environments. Headline claim: first open-weights model to
score 50 on the Artificial Analysis Intelligence Index v4.0 and roughly on par with
frontier closed models across agentic, reasoning, and coding tasks.*

**From the report**

> 744B/40B-active MoE with DeepSeek Sparse Attention, MLA (256-dim head), and 3 parameter-shared MTP layers; context extended 4K→200K in mid-training. Pre-trained on ~27T tokens (28.5T across all stages); a sequential RL pipeline (Reasoning → Agentic → General) fuses rule-based, ORM, and GRM rewards. — §2.1 / §3.4
>
> Async RL core: a "Direct Double-Sided Importance Sampling" that "reuses the log-probabilities generated during rollout as a direct behavior proxy," computes r_t = π_θ/π_rollout, discards the traditional π_θ_old, and masks any out-of-trust-region token entirely from the gradient; DP-aware routing hashes each rollout ID to a fixed DP rank so KV-cache locality survives across turns. — §4.1
>
> A RepoLaunch pipeline auto-builds executable environments from real SWE issues and parses test logs into Fail-to-Pass / Pass-to-Pass oracles — "over 10k verifiable environments across thousands of repositories spanning 9 programming languages." — §4.2.1
>
> On-policy cross-stage distillation: prior-stage checkpoints act as teachers and the RL advantage becomes Â = sg[ log( π_teacher / π_train ) ], letting the model "swiftly recover the skills acquired in earlier SFT and RL stages." — §3.5
>
> Coding: SWE-bench Verified 77.8 (vs Opus 4.5 80.9), Terminal-Bench 2.0 56.2 (60.7–61.1 on a verified/instruction-fixed variant), CyberGym 43.2; overall the report claims ~20% improvement over GLM-4.7 averaged across its eight headline benchmarks. — §1 / Table 7
>
> Agentic/search: BrowseComp 62.0 (the single best score in the table; Opus 4.5 only 37.0), rising to 75.9 with context management; τ²-Bench 89.7; MCP-Atlas public set 67.8. — Table 7
>
> Caveats: "performance on BrowseComp is sensitive to both the judge prompt and the judge model, and open-source judges can introduce systematic bias" (they standardize on the official OpenAI prompt + o3-mini judge); and the DSA indexer's non-deterministic CUDA top-k caused "drastic performance degradation during RL after only a few steps," fixed with deterministic torch.topk. — §4.2.4 / §2.4.3

**My read**
- *What I'd look at:* §3.5 first (Â = sg[log(π_teacher/π_train)] is on-policy reverse-KL distillation with a shared tokenizer and no knowledge gate — the clean baseline my post-cutoff variant must beat), then §4.1's async trick (reusing rollout log-probs deletes an entire old-policy inference pass) and §4.2.1's env-collapse handling.
- *Where it meets my notes:* **AgentPlanet** — RepoLaunch *is* the planet pattern (auto-synthesize >10k executable worlds, derive F2P/P2P oracles that score each world for free), and excluding environment-collapse samples is the anti-Goodhart hygiene a meta-reward battery needs. **Over-reflection** — §4.2.4's evidence that BrowseComp scores swing with judge prompt/model validates the fear that a coarse verifier is a leaky channel; the 62.0→75.9 context-management jump is an inference-time cousin of stop/pivot. **Post-cutoff distillation** — §3.5 cleanly isolates that my novelty is cross-tokenizer alignment + the date-gate, not the objective.
- *Worth stealing / watching:* port Direct Double-Sided Importance Sampling into my own multi-node RL (reuse the rollout's own log-probs, drop π_θ_old, hard-mask out-of-trust-region tokens); and adopt their reward-integrity gate — record a failure reason per sample and exclude non-model env-collapse failures so a crash never leaks as low reward, directly usable in my environment-synthesis → RL loop.

[Source (arXiv 2602.15763)](https://arxiv.org/abs/2602.15763)

</details>

<details>
<summary><strong>Kimi K2.5: Visual Agentic Intelligence</strong> · Moonshot AI (Kimi Team), February 2026</summary>

*An open-weights multimodal agentic model built on the Kimi K2 base (1.04T total / 32B
activated MoE) plus a MoonViT-3D native-resolution vision encoder, trained via joint
text-vision pre-training, a text-only "zero-vision" SFT, and joint text+vision RL. Its
headline contribution is "Agent Swarm," where a trainable orchestrator decomposes a
task into heterogeneous sub-problems run concurrently by frozen subagents, trained with
a three-term PARL reward.*

**From the report**

> Built on Kimi K2 (1.04T total, 32B activated, 384 experts / 8 active, MuonClip optimizer) with MoonViT-3D — a native-resolution encoder using NaViT packing that treats up to four consecutive frames as a spatiotemporal volume with 4× temporal compression — and a 256k-token inference context. — §2
>
> Training: joint text-vision pre-training finds "early fusion with a lower vision ratio yields better results given a fixed… token budget"; "zero-vision SFT uses only text SFT data to activate visual, agentic capabilities" (proxying image ops through programmatic IPython calls); RL domains are "organized not by input modality but by abilities — knowledge, reasoning, coding, agentic." — §2.1–2.3
>
> Outcome-based visual RL "produced measurable improvements in textual tasks" — MMLU-Pro 84.7→86.4, GPQA-Diamond 84.3→86.4, LongBench v2 56.7→58.9 — "without observable degradation." — Table 2
>
> Agent Swarm uses "a trainable orchestrator and frozen subagents… subagent execution trajectories are excluded from the optimization objective," avoiding credit-assignment ambiguity; reward r_PARL = λ1·r_parallel + λ2·r_finish + r_perf, where r_parallel prevents "serial collapse," r_finish prevents "spurious parallelism, a reward-hacking behavior," and "λ1 and λ2 are annealed to zero over the course of training." — §3
>
> Swarm vs single-agent: BrowseComp 60.6% → 78.4% (+17.8pp), WideSearch Item-F1 72.7% → 79.0%, in-house Swarm Bench 41.6% → 58.3% (single-agent BrowseComp with context management reaches 74.9%). — Table 6
>
> Resource cost is measured as CriticalSteps = Σ_t (S_main + max_i S_sub,i) — the longest parallel branch, not total work — to penalize "excessive subtask creation that does not reduce the maximum execution time"; Agent Swarm "reduces inference latency by up to 4.5×." — §5.2
>
> Caveats: subagents are frozen at "fixed intermediate policy checkpoints" and cannot adapt during orchestrator RL; Agent Swarm is "designed for tasks emphasizing either wide search or deep search" with no sequential-task result; weak spots include SimpleQA Verified 36.9% and SWE-Bench Pro 50.7%, and no confidence intervals are reported. — §5

**My read**
- *What I'd look at:* §3's PARL reward and the decoupled trainable-orchestrator / frozen-subagents split — a clean role factorization (orchestrator ≈ policy dispatching actions, frozen subagents ≈ fixed dynamics) — where the λ-shaping terms *annealed to zero* so the final policy optimizes the true objective is the concrete anti-Goodhart lever; and the r_parallel-vs-r_finish tension, two terms pointing in opposite directions.
- *Where it meets my notes:* **AgentPlanet** — the orchestrator/subagent role split plus PARL's annealed shaping and the CriticalSteps "free" parallelism score are mechanism-level instances of my reward-channel-integrity / anti-Goodhart-meta-reward theme. **Over-reflection** — r_parallel (anti serial-collapse) and r_finish (anti spurious-parallelism) mirror my taxonomy where per-type fixes point opposite ways, and r_finish operationalizes exactly my worry that a coarse verifier would reward search-after-search — here "confirm-then-keep-searching" becomes concurrent, finish-gated branches (BrowseComp 60.6→78.4).
- *Worth stealing / watching:* the CriticalSteps metric (cost = main + max over subagents, the longest branch) as a portable anti-over-decomposition term; and the PARL pattern of directional shaping terms with λ annealed to zero — bootstrap a behavior, then remove the shaping so the final policy optimizes only the true objective — directly reusable for my stop/pivot RL.

[Source (arXiv 2602.02276)](https://arxiv.org/abs/2602.02276)

</details>

<details>
<summary><strong>Nemotron 3 Nano: Open, Efficient Mixture-of-Experts Hybrid Mamba-Transformer Model for Agentic Reasoning</strong> · NVIDIA, December 2025</summary>

*A technical report for Nemotron 3 Nano 30B-A3B, an open MoE hybrid Mamba-2/Transformer
LLM (31.6B total / 3.2B active), pretrained on 25T tokens and post-trained with SFT +
large-scale multi-environment RL-from-verifiable-rewards via the open-sourced NeMo Gym /
NeMo RL stack, a GenRM-based RLHF stage, and FP8 quantization. It supports 1M-token
context and claims up to 3.3× higher inference throughput than similarly-sized open
models while releasing weights, recipe, most data, and the RL stack openly.*

**From the report**

> A granular MoE hybrid Mamba-Transformer: FFNs replaced by a sigmoid-gated router that "activates 6 out of 128 experts" plus 2 shared experts, 52 layers (6 self-attention among Mamba-2 + GQA blocks), 31.6B total / 3.2B active; pretrained on 25T tokens (WSD schedule), 1M context, 2.2×/3.3× faster inference than GPT-OSS-20B / Qwen3-30B-A3B-Thinking-2507 at 8K-in/16K-out. — §2.1 / Table 1
>
> "We employ a unified RLVR stage, training on all environments simultaneously… single environment training often results in un-recoverable degradation of other benchmarks"; the algorithm is synchronous GRPO with masked importance sampling, MoE router weights frozen with aux-loss-free load balancing. — §3.2
>
> Seven environment families spanning nine distinct verifiable environments (math, competitive coding, STEM MCQ, JSON structured-outputs, IFEval + LLM-judge, multi-doc long-context QA, a Workplace Assistant verified by DB-state diff, and a banking multi-turn agent); the structured-outputs env gives "a positive reward… when the output matches the exact schema constraints, and no reward… otherwise… we do not add a reward for the semantic content." — §3.2.1
>
> Auto-curriculum: "filter out samples where the SFT checkpoint already achieves a 100% pass rate," model each domain's target pass-rate as a Gaussian whose mean slides easy→hard, and "once training progress plateaus, re-profile the tasks using the best RL checkpoint." — §3.2.2
>
> NeMo Gym factors an RL environment into three server types — an "agents" server (rollout kernel), a "models" server that "carefully preserves token and inference log-prob data… required for RL," and a "resources" server that "provides a verification API for computing rewards from a given rollout." — §3.2.4
>
> GenRMs "generalize better than traditional Bradley-Terry models, reducing the risk of reward hacking"; Group Relative Length Control adds a zero-mean group-relative length bonus (λ=0.5, applied to both think and answer) plus an 80th-percentile quality-gated conciseness bonus, cutting verbosity "30%… without sacrificing accuracy" (verbosity growth comes mostly from the reasoning trace, distinct from reward hacking since only the final answer is judged). — §3.3
>
> Selective FP8 PTQ (weights, activations, KV cache) keeps the 6-of-52 self-attention layers plus their preceding Mamba layers in BF16 as sensitive components — "approximately 99% median accuracy recovery," FP8 KV cache driving most of the throughput gain — but agentic tasks lose more (TauBench 49.04→47.04 under FP8) and per-benchmark baselines still beat it on MMLU-Pro (80.90 vs 78.30) and AA-LCR (59.00 vs 35.85). — §4.2–4.3

**My read**
- *What I'd look at:* §3.2.4 NeMo Gym — the "resources" server as a standalone verification-API-for-rewards is a clean physical separation of the reward channel from rollout and inference (exactly the planet/verifier boundary I want), and §3.2.2's drop-100%-pass → Gaussian easy→hard → re-profile-at-plateau curriculum; then §4.2's FP8 sensitivity map (which layers refuse to quantize).
- *Where it meets my notes:* **AgentPlanet** — the env-factored-into-servers-with-a-verifier design, GenRMs "reducing reward hacking" vs Bradley-Terry, and the structured-outputs env rewarding only exact-schema match (a rules-are-verifier battery scoring an output for free) all land on my reward-integrity theme. **Over-reflection** — RLHF length ballooning from the reasoning trace while only the answer is judged is my "confirm then keep searching" in another modality, and Group Relative Length Control is the surgical, keep-only-if-still-top-tier truncation of that tail. **Energy floor of inference** — selective FP8 + FP8 KV cache is the "shrink resident weights into a lower-power memory tier" mechanism, with a sensitivity map showing where the floor won't drop.
- *Worth stealing / watching:* the unified-RLVR discipline — train all benchmark environments simultaneously with fixed per-domain batch ratios, since single-environment RL "un-recoverably degrades" the others — as a cheap guard against cross-benchmark forgetting; and Group Relative Length Control as a quality-gated over-reflection truncation that only rewards brevity when the answer stays correct.

[Source (PDF)](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Nano-Technical-Report.pdf)

</details>

<details>
<summary><strong>Olmo 3</strong> · Allen Institute for AI (Ai2), December 2025</summary>

*A fully-open 7B/32B family released with the entire "model flow" — every training
stage, checkpoint, datapoint, and code dependency from base through the Think, Instruct,
and RL-Zero variants. It introduces new open data (the Dolma 3 pretraining mixes and the
Dolci post-training suite), an RLVR framework (OlmoRL) mixing verifiable and LM-judge
rewards across four domains, and an RL-from-base setup (RL-Zero) for studying how
pretraining data affects RL. Headline claim: Olmo 3.1 Think 32B is the strongest
fully-open thinking model to date, competitive with Qwen 3 32B on ~6× fewer tokens.*

**From the report**

> "Complete access to its entire model flow — the full lifecycle… including every stage, checkpoint, datapoint, and dependency." Two scales (7B, 32B); Base is 3 stages (pretraining up to 5.9T tokens, midtraining 100B, long-context 50–100B) then branches into Think / Instruct / RL-Zero; ~56 days on 1024 H100s, ≈$2.75M. — §1–2
>
> Dolma 3 Mix is a 6T-token pretraining mix (final run 5.93T: Common Crawl 76.1%, olmOCR science PDFs 13.6%, Stack-Edu code 6.89%) drawn from a 9T pool with trillion-scale global dedup; Dolma 3 Longmino pushes context to 65K, and they release the 9T pool plus 2T+640B specialized tokens. — §2.1 / §3.4
>
> OlmoRL builds on GRPO and layers DAPO (zero-gradient-signal filtering, clip-higher) and Dr-GRPO (no std-dev normalization), plus token-level loss, removed KL loss, active sampling, and truncated importance sampling to correct inference/training log-prob mismatch. — §4.4.1
>
> Domain-specific reward battery: math = a rule-based SymPy verifier (binary 1/0); code = a test-case verifier executed on AWS Lambda "so verification does not block the trainer process"; instruction-following = a binary constraint-checker; general chat = LM-as-judge (Qwen3-32B, thinking off) scoring [0,1] — over ~100K prompts across the 4 domains. — §4.4.1 / Fig 16
>
> RL infra: continuous batching + inflight weight updates that update actor weights "without invalidating the KV cache" take the stack from 6.34 to 21.23 Mtok and MFU 0.30%→1.01% — "up to 4× faster with the same resources" (the 7B run dropped from ~15 to 6 days). — §4.4.3 / Table 23
>
> RL-Zero negative control: training RLVR from base on random, signal-free rewards "does not improve performance on any of our benchmark evaluations" — flat or degrading — "evidence that our data decontamination successfully removed overlaps between our base-model pipeline and RLVR evaluation data." — §6.2
>
> Caveats: "mixing data yields lower train reward, but not lower downstream performance," suggesting broad mixtures "reduce the model's tendency to over-optimize"; and the 7B "lags the Qwen 3 series in knowledge tasks… mainly due to… Qwen 3 models are trained through distillation from Qwen's largest model." — §4.5 / §4.1.2

**My read**
- *What I'd look at:* §6.2 first — the random/signal-free-reward negative control is the clean reward-channel-integrity proof I keep wanting (a reward uncorrelated with utility yielding no gain certifies the channel is real and the eval isn't memorized) — then §4.5's "mixing yields lower train reward but not lower downstream" (anti-Goodhart with a number attached) and §4.4.1's per-domain verifier battery.
- *Where it meets my notes:* **AgentPlanet** — three core themes land at mechanism level: the spurious-reward negative control (reward-channel integrity), the broad-mixture-resists-over-optimization finding (anti-Goodhart), and the per-domain verifier suite (an invariant battery that scores a rollout for free). **Over-reflection** — OlmoRL (no-KL / clip-higher / active-sampling / truncated-IS on long reasoning rollouts) is deployable substrate for my stop/pivot RL, and "a random reward yields no gain" sharpens the worry that a coarse action-type verifier would reward search-after-search. **Post-cutoff distillation** — their anti-imitation finding (further SFT on Qwen3-32B thinking traces *hurts*; the 7B lags because Qwen is distilled from its largest model) is a cautionary datapoint: imitation saturates on capability but is still the channel for knowledge transfer — exactly the knowledge-gated slice I want to isolate (stretch).
- *Worth stealing / watching:* the spurious/random-reward negative control as a portable decontamination proof for my own RL eval sets; and active sampling (refill each batch with only non-zero-advantage completions) paired with inflight weight updates that preserve the KV cache — together ~4× RL throughput at equal accuracy.

[Source (arXiv 2512.13961)](https://arxiv.org/abs/2512.13961)

</details>

<details>
<summary><strong>Qwen3 Technical Report</strong> · Qwen Team (Alibaba), May 2025</summary>

*The Qwen3 open-weight family (6 dense 0.6–32B + MoE 30B-A3B and 235B-A22B, Apache 2.0),
pretrained on ~36T tokens across 119 languages. Its headline is unifying "thinking" and
"non-thinking" modes in one model with a user-controllable thinking budget; small models
are built cheaply by strong-to-weak distillation rather than the full post-training
pipeline.*

**From the report**

> A single model supports thinking and non-thinking modes with "dynamic mode switching based on user queries," and a thinking budget lets the user cap reasoning length (`/think`, `/no_think`). — Abstract / §4.3
>
> Pretraining is 36T tokens over 119 languages in 3 stages (General >30T, Reasoning ~5T higher-quality, Long-Context), with context extended to 32K via ABF RoPE base 1,000,000 + YARN + Dual Chunk Attention. — §3.1–3.2
>
> Reasoning-RL uses GRPO over **3,995 query–verifier pairs** with deterministically verified answers; the flagship's AIME'24 score "increases from 70.1 to 85.1 over a total of 170 RL training steps." — §4.2
>
> Verifier curation removes queries "not easily verifiable" *and* excludes queries the model "can answer correctly without using CoT reasoning" — explicitly to "prevent the model from relying on superficial guessing." — §4.1–4.2
>
> Small models distill teacher output logits using "both off-policy and on-policy knowledge transfer," which "significantly outperforms reinforcement learning," raising Pass@1 and Pass@64 while "requiring only 1/10 of the GPU hours compared to the four-stage training method." — §4
>
> Stated caveat: the budget's stop-thinking instruction "is not explicitly trained but emerges naturally as a result of applying Thinking Mode Fusion" — the truncation behavior is emergent, not directly optimized. — §4.3

**My read**
- *What I'd look at:* §4.2's verifier curation — the filter that excludes queries the model can already answer without CoT is a reward-integrity move I can lift directly to stop rewarding memory-recited answers over genuinely retrieved ones — and §4.3, where the budget's stop *emerges* from mode-fusion SFT without explicit training.
- *Where it meets my notes:* **Over-reflection** — the thinking budget is a literal, content-blind stop policy (halt at a token threshold); mine is the state-conditioned version (finalize only if the answer matches its citation), and Qwen3's "stop emerges from SFT fusion, not RL" finding is directly relevant to whether my stop/pivot needs RL at all. **AgentPlanet** — a curated deterministically-verifiable pair set that excludes anything solvable without the target skill is the same spirit as an invariant-battery meta-reward that can't be gamed. **Post-cutoff distillation** — off+on-policy logit distillation beating RL at 1/10 GPU hours is the on-policy precedent, but same-tokenizer with no date gate.
- *Worth stealing / watching:* port the reasoning-RL query filter verbatim — drop any query the base model answers correctly *without* tools/CoT so the reward can only be earned by genuine retrieval; open question: can a *citation-conditioned* stop be induced the same way by mode-fusion SFT, or does it demand an explicit RL objective?

[Source (arXiv 2505.09388)](https://arxiv.org/abs/2505.09388)

</details>

<details>
<summary><strong>Seed2.0 Model Card: Towards Intelligence Frontier for Real-World Complexity</strong> · ByteDance Seed, June 2026</summary>

*A model card for the Seed2.0 series (Pro / Lite / Mini), framed around "real-world
complexity" rather than leaderboard-maxing. Its central move is methodological — build
a "needs-grounded" evaluation system, then target two persistent weaknesses (long-tail
professional knowledge and complex instruction following). It discloses no parameter
counts or training recipe and openly admits it still trails frontier LLMs on some axes.*

**From the report**

> The work "begins with identifying users' genuine needs and constructing a reliable, forward-looking evaluation system," then targets "long-tail knowledge and complex instruction following"; its advanced-eval framework spans four dimensions (Science Discovery, Vibe Coding, Context Learning, Real-World Tasks), each anchored by Seed-designed benchmarks. — Abstract / §3.4
>
> Two purpose-built long-tail probes: LPFQA (Long-tail Professional Forum-based QA) and **Encyclo-K**, which "extracts atomic knowledge statements from books and dynamically composes them into evaluation instances," supporting zero- and few-shot ICL to "probe knowledge acquisition in pre-training and post-training stages." — §3.1.1
>
> Agentic harness scoring: "to avoid underestimating competing products, the final score is defined as the maximum of the score reported in the official documentation and the score obtained in our tests," across five dimensions over BrowseComp, WideSearch, seal-0, FinSearchComp, tau2-Bench, BFCL-v4, MCP-Mark, DeepConsult, ResearchRubrics. — §3.3
>
> Quality-based exclusion removes "multi-container Docker Compose scenarios," "test cases where reference solutions fail to pass their own validation," "cases exhibiting non-deterministic behavior across runs," and "network-dependent problems with inconsistent outcomes." — §3.3
>
> Long-tail headline: Encyclo-K 65.7 (top; vs Gemini-3-Pro 64.9, Opus-4.5 63.3) but LPFQA only 52.6 (behind Sonnet-4.5 54.9, GPT-5.2 54.4) — it leads on the composed-knowledge probe, not the forum-QA one. — §4.1
>
> Reasoning: IMO 2025 35/42 and CMO 2025 114/126 (both Gold), Codeforces Elo 3020 (no tool), AIME 2026 94.2, Putnam-200 Pass@8 35.5; and "ranks first on the Frames leaderboard" at 84.5. — §4.1
>
> Stated caveats: "the Seed2.0 Series still have gaps with international frontier LLMs" — "considerable gaps with Claude in terms of coding" and "relatively obvious gaps with Gemini in terms of long-tail knowledge"; and Graphwalks uses an in-house tokenization that mismatches the official scoring setup. — §1 / §3.1

**My read**
- *What I'd look at:* §3.3 — the "final score = max(official-doc, our test)" rule is an explicit anti-underestimation policy but structurally an *upper-bound* estimator, so it biases every reported number upward; that's exactly the reward-channel/verifier-integrity hazard I track. Then the §3.3 exclusion taxonomy and §3.1.1 Encyclo-K.
- *Where it meets my notes:* **Over-reflection / agentic-eval methodology** — their harness runs over my exact benchmark set (BrowseComp, WideSearch, tau2, BFCL) and their deterministic exclusion of self-failing/non-deterministic cases mirrors my per-type filtering, but "max(doc, ours)" is precisely the coarse verifier I warn about — it rewards the higher number regardless of provenance. **AgentPlanet** — "needs-grounded evaluation" is a planet-side meta-reward, and the max-score convention is the anti-Goodhart failure in miniature. **Post-cutoff distillation** — Encyclo-K's ICL acquisition probe + AIME-2026 freshness items are ready-made instruments for whether a date-gated student *internalized* post-cutoff facts.
- *Worth stealing / watching:* Encyclo-K's generator recipe (atomic statements → dynamically recomposed fresh ICL instances) is a portable, contamination-resistant eval builder for my post-cutoff and data-audit work; open question — how much does an always-take-the-higher policy inflate a leaderboard vs a re-run-everything harness?

[Source (arXiv 2607.00248)](https://arxiv.org/abs/2607.00248)

</details>

<details>
<summary><strong>Gemini 3.1 Pro Model Card</strong> · Google DeepMind, February 2026</summary>

*A web model card for Gemini 3.1 Pro (evaluated in "Thinking (High)"), the next iteration
in the Gemini 3 series of natively multimodal reasoning models. It is a thin iteration
document — it states the model is "based on Gemini 3 Pro" and defers architecture,
training data, known limitations, and evaluation approach to the Gemini 3 Pro card —
whose substantive content is a single benchmark table plus short safety notes.*

**From the report**

> "Gemini 3.1 Pro is based on Gemini 3 Pro… see the Gemini 3 Pro model card." Accepts text, image, audio, and video up to a 1M-token context and emits text with a 64K-token output; all Gemini scores are reported in the "Thinking (High)" setting. — model information
>
> Agentic coding: Terminal-Bench 2.0 68.5% (Terminus-2 harness), SWE-Bench Verified 80.6% single attempt, SWE-Bench Pro (Public) 54.2%, LiveCodeBench Pro 2887 Elo. — benchmarks table
>
> Agentic tool-use: tau2-bench Telecom 99.3% / Retail 90.8%, MCP Atlas 69.2% (up from 54.1% for Gemini 3 Pro), APEX-Agents 33.5% on "long horizon professional tasks" (up from 18.4%). — benchmarks table
>
> Search / tool-lift: BrowseComp 85.9% under "Search + Python + Browse" (vs 59.2% for Gemini 3 Pro); Humanity's Last Exam 44.4% with no tools rising to 51.4% under "Search (blocklist) + Code" — a clean same-model measure of tool-augmentation lift. — benchmarks table
>
> Reasoning / multimodal (no tools): GPQA Diamond 94.3%, ARC-AGI-2 77.1% (vs 31.1% for Gemini 3 Pro), MMMU-Pro 80.5%, MMMLU 92.6%. — benchmarks table
>
> Long context: MRCR v2 (8-needle) 84.9% average at 128k, decaying to 26.3% pointwise at 1M tokens — the only long-context benchmark on the card, showing steep degradation across the advertised context length. — benchmarks table
>
> Caveat (thin card): no knowledge cutoff is stated anywhere, no RL/post-training method is given, and Intended uses / Known limitations / training data / evaluation approach are all redirected verbatim to the Gemini 3 Pro card; on Frontier Safety the Cyber CCL "has reached the alert threshold, but still does not reach the levels of uplift required for the CCL." — model information / safety

**My read**
- *What I'd look at:* the BrowseComp row and the HLE no-tools→tools pair (85.9% with Search+Python+Browse; 44.4%→51.4%) — same-model tool-augmentation deltas that quantify how much a search+browse scaffold buys over closed-book, exactly the ceiling my stop/pivot RL is trying to move without paying for uncited search inertia; and the "Model information" deferral lines to confirm what is *absent* (no cutoff, no training method).
- *Where it meets my notes:* **Over-reflection** — BrowseComp 85.9% and the HLE tool-lift are direct measurements of the search-scaffold lift I want to preserve while cutting the uncited-inertia tail, and a coarse action-type verifier would credit the extra Search+Browse calls that produce it — the confounder a state-conditioned stop/pivot has to separate from genuine grounding. **AgentPlanet** — the agentic battery (MCP Atlas 69.2, tau2 99.3/90.8, APEX 33.5) is the policy leg `π(a|s,R)` scored against a fixed per-world checklist, but the card says nothing about who authored those worlds (the "planet" leg is out of frame). **Post-cutoff distillation** — the omitted cutoff is precisely the one field my date-gate depends on (stretch: no training method given).
- *Worth stealing / watching:* the same-model HLE pair (no-tools → Search(blocklist)+Code) as a clean, contamination-controlled way to report grounded-vs-closed-book search deltas; and the practice of pairing a mid-length and a max-length long-context number (MRCR 84.9@128k → 26.3@1M) rather than headlining only the flattering one.

[Source (model card)](https://deepmind.google/models/model-cards/gemini-3-1-pro/)

</details>

<details>
<summary><strong>DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence</strong> · DeepSeek-AI, April 2026</summary>

*A technical report on two MoE models — V4-Pro (1.6T total / 49B activated) and
V4-Flash (284B / 13B activated) — both at 1M-token context and pretrained on >32T
tokens. Its headline is efficiency at extreme context: a hybrid attention stack plus
FP4 quantization-aware training on the experts, alongside a post-training pipeline
that trains per-domain specialists and merges them into one model.*

**From the report**

> Keeps the DeepSeekMoE + Multi-Token-Prediction framework but adds a hybrid attention design (Compressed Sparse Attention + Heavily Compressed Attention), Manifold-Constrained Hyper-Connections to strengthen residuals, and the Muon optimizer. — §2.1–2.4
>
> Post-training: Stage 1 trains independent domain specialists (math, coding, agent, instruction-following), each via SFT then GRPO with a per-domain tailored Generative Reward Model; Stage 2 merges them into "a single unified model… trained through on-policy distillation, wherein the unified model acts as the student learning to optimize the reverse KL loss with teacher models." — §5.1.1–5.1.2
>
> FP4 quantization-aware training is applied to the MoE routed-expert weights — "currently the same as FP8 × FP8 on existing hardware" but "theoretically 1/3 more efficient on future hardware." — §Introduction
>
> At 1M context, V4-Pro needs "27% of single-token inference FLOPs and 10% of KV cache compared with DeepSeek-V3.2" (Flash: 10% / 7%); the KV cache is "approximately 2%" of a BF16 GQA8 baseline, and a hybrid BF16/FP8 KV representation nearly halves it again. — §2.3.4
>
> Fine-grained expert parallelism with wave-based scheduling delivers "1.50~1.73× speedup for general inference" and "up to 1.96× for latency-sensitive scenarios such as RL rollouts and high-speed agent serving." — §3.1
>
> Stated caveats: on reasoning the model "trails state-of-the-art frontier models by approximately 3 to 6 months"; and on serving, "extreme kernel fusion drives compute, memory, and network to high load simultaneously, making power throttling a key performance limiter." — §3.1 / §6

**My read**
- *What I'd look at:* §5.1.2's specialist-merge (a student sampling its own rollouts, drawing a reverse-KL target from multiple specialist teachers) — that merge operator is the backbone I'd reuse, and running it same-family / same-tokenizer with no per-token gate sharpens that my only novel pieces are the date-gate mask and cross-tokenizer alignment. Then §3.1 (power throttling) + §2.3.4 (KV to ~2%) read together.
- *Where it meets my notes:* **Post-cutoff distillation** — a direct published precedent for the reverse-KL on-policy half, which confirms the novelty must live in the gating, not the objective. **Energy floor of inference** — "power throttling under extreme kernel fusion" is a rare *sustained-power* datapoint distinct from energy-per-token, and FP4 shrinking resident expert weights is the mechanism I posit for lowering the floor (stretch: it flags throttling, never measures watts).
- *Worth stealing / watching:* the specialist-merge-by-reverse-KL operator, ported with a per-token date-gate so only post-cutoff tokens carry the teacher signal — the one piece the report doesn't need because its teachers are same-family; open question it leaves: it never converts any efficiency win into sustained-watts, exactly the gap my energy-floor note chases.

[Source (arXiv 2606.19348)](https://arxiv.org/abs/2606.19348)

</details>

<details>
<summary><strong>Gemma 4 Technical Report</strong> · Google DeepMind, July 2026</summary>

*A 17-page technical report introducing Gemma 4, a suite of open-weight, natively
multimodal models spanning dense 2.3B/4.5B/12B/31B plus a 26B-total / 3.8B-activated
MoE. Its headline architectural claim is a unified, encoder-free 12B that ingests raw
image patches and audio chunks directly (discarding the separate vision and 305M audio
encoders), alongside a thinking mode and a battery of inference-efficiency choices; it
claims to lead open dense models on human-rated Arena and STEM/multimodal/long-context
benchmarks.*

**From the report**

> Lineup (Table 1): dense 2.3B (E2B), 4.5B (E4B), 12B, 31B, plus an MoE "3.8B activated and 26B total"; E2B/E4B "use per-layer embeddings as in Gemma 3n, making them 2.3B and 4.5B effective out of 5B and 8B total parameters." — §2
>
> Encoder-free 12B: the vision encoder is replaced by "a single large matmul (35M parameters)" over "48×48×3 RGB patches"; audio is "segmented into 40ms chunks at 16kHz, resulting in 640-dimensional vectors per chunk," and "the 305M USM-based conformer encoder is entirely discarded." — §2.3
>
> Training: "Gemma 4 12B is trained from scratch based on a new, unified, and encoder-free model paradigm"; other sizes "follow a similar pre-training as Gemma 3." The words distill/teacher/student appear *nowhere* in the report — a notable absence given Gemma 3 was distillation-based. Tokenizer is the Gemini SentencePiece (262k vocab); data cutoff January 2025. — §2.3–2.4
>
> Efficiency (Table 3): the 12B at 32k context is 24.0 GB in bf16 vs 7.65 GB under Q4_0 (+0.28 GB KV cache); a "5:1 ratio of local sliding window to global self-attention" with "pp-RoPE" reduces "global KV cache footprint by up to 37.5%"; mobile QAT uses "per-channel low bitwidth weight (mix of int2 and int4) and activation quantization (int8)"; audio-encoder QAT gives a "78% reduction in on-disk footprint, from 390 MB in Gemma 3n to 87 MB." — §2.5
>
> A multi-token-prediction head "generates future tokens sequentially using a separate embedder and a 4-layer Transformer block that cross-attends to the KVs of the main model" for speculative decoding (speedup unquantified). — §2.6
>
> Numbers (31B): MMLU-Pro 85.2, AIME 2026 no-tools 89.2, Codeforces Elo 2150, MMMU-Pro 76.9; RULER at 128k holds 96.4 for 31B but the per-layer-embedding E2B collapses 83.0 → 70.4; Arena Elo 31B 1451 ±8 (the "leading dense open model"). — Tables 5/6/9/4
>
> Caveat: pretraining data is filtered "to decontaminate benchmarks, and to reduce the risk of… recitation," with subsets "that encourage better in-context attribution, hedging, and refusals to minimize hallucinations"; all safety testing "was conducted without safety filters." — §2.4 / §5

**My read**
- *What I'd look at:* §2.3–2.4 for the *distillation negative space* (Gemma 3 was distillation-based, yet this report never writes distill/teacher/student and calls the 12B "trained from scratch"), and §2.5 + Table 3 for the on-device memory-floor levers with concrete numbers to target.
- *Where it meets my notes:* **Wearable world model** + **Energy floor of inference** — mobile int2/int4+int8 QAT, audio encoder 390→87MB, 12B Q4_0 at 7.65GB, and pp-RoPE cutting global KV cache up to 37.5% are exactly the resident-weight-shrink + KV-compression levers those notes turn; the MTP drafter is a concrete sustained-decode-work reducer. **Post-cutoff distillation** — the report discloses nothing about whether the non-12B models are distilled, so the teacher→student channel is unobservable here, reinforcing that my date-gate has to carry the novelty (stretch: silent, not contradictory). **Over-reflection** — RULER shows 128k retention is cheap via 5:1 local attention, evidence that my treatment-swallowing 32k cap is a budget knob, not a wall (stretch).
- *Worth stealing / watching:* the pp-RoPE + 5:1 local:global combination as a portable KV-compression target ("up to 37.5% global KV reduction") for the generative frame-predictor fork of my wearable note; and the sharp open question — a frontier open model that discloses *nothing* about its knowledge-transfer channel is itself the pattern my post-cutoff line keeps hitting.

[Source (arXiv 2607.02770)](https://arxiv.org/abs/2607.02770)

</details>
