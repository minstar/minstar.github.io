# The rollouts we throw away: FlashSAC as a recipe for search agents

I train search agents, and the most expensive thing my pipeline produces every day is a
rollout: thousands of reasoning tokens, a fistful of live search and MCP calls, whole minutes
of wall-clock spent waiting on other people's servers. The standard recipe — PPO/GRPO, same
as nearly everyone's — squeezes one or two gradient steps out of each trajectory and then
deletes it. That's the on-policy doctrine: data from anywhere but the current policy can't be
trusted, so nothing is kept. Robotics ran on the same doctrine for a decade — PPO everywhere,
rollouts disposable, salvation through faster simulators.
[FlashSAC](https://arxiv.org/abs/2604.04539) ([code](https://github.com/Holiday-Robot/FlashSAC)),
fresh off an outstanding-paper award, is the cleanest demonstration I've seen that the
doctrine was a choice, not a law. Its update-to-data ratio (UTD) on GPU simulators is
**2/1024** — two gradient updates per 1024 new transitions, a replay buffer doing the
remembering — and at that setting it beats PPO and strong off-policy baselines on both final
score and wall-clock across 60+ tasks in 10 simulators, then compresses sim-to-real humanoid
locomotion training from hours to minutes. This note is me working out what that recipe means
for agents that search instead of walk.

## What FlashSAC actually is

Three deliberate axes on top of an aggressive engineering floor.

**Cut updates; scale everything else.** The move is borrowed from supervised scaling laws:
gradient-update count is a quantity to minimize, not maximize. Conventional off-policy work
chased sample efficiency by pushing UTD *up* — more updates per transition, more
bootstrapping, more accumulated critic error. FlashSAC inverts it: 1024 parallel environments
feed batches of 2048 into a replay buffer of 10M transitions ("an order of magnitude larger
than the 1M commonly used"), and both actor and critic grow to 2.5M-parameter, six-layer
networks. Large by robot-control standards; a rounding error by ours — which is why the
recipe reads from here as an invitation rather than a wall.

**Stability as structure, not penalty.** Bootstrapped critics rot by feeding on their own
errors. FlashSAC's answer is not another loss term but hard bounds on the machinery itself:
every weight vector is projected back onto the unit-norm sphere after each update,
normalization parameters (γ, β) are projected to norm √d, RMSNorm bounds the features
entering the value heads, and batch norm plus residual connections keep gradient norms tame.
The critic is distributional — Q represented as a categorical distribution over atoms on
[G_min, G_max], trained by cross-entropy against the projected Bellman target with adaptive
reward scaling — so value learning becomes a bounded classification problem instead of an
unbounded regression. None of it is a regularizer the optimizer can trade away; the
constraints hold by construction. This is the
[SimbaV2](https://arxiv.org/abs/2502.15280) lineage (largely the same authors) pushed one
paper further.

**Exploration that remembers what it was doing.** Per-step Gaussian noise explores like
static. FlashSAC's *noise repetition* samples ε ~ N(0, I), holds it for k consecutive steps,
and draws k from a Zeta distribution P(k) ∝ k⁻ˢ — heavy-tailed, so mostly short holds with
the occasional long, committed stretch — for the price of one counter per environment.

Beneath all this sits the floor: a torch-compiled critical path (the weight projections,
target-network EMA, TD-target computation), a GPU-resident replay buffer, mixed precision
applied only where it doesn't stall, and `asymmetric_observation` — the critic sees
privileged simulator state the actor never will.

## The same problem wearing a different body

The reason I read a humanoid-locomotion paper twice is that its problem statement maps onto
agentic RL almost line for line:

| robotics, as FlashSAC frames it | search / MCP agents |
| --- | --- |
| PPO is the default: stable, but data is used once and discarded | PPO/GRPO is the default: a trajectory gets one or two updates, then deleted |
| rollouts are getting expensive (contact-rich sim, larger policies) | rollouts are *very* expensive: LLM decoding + live API/MCP calls + latency + per-call bills |
| high-dimensional state-action spaces (dexterous hands, humanoids) | absurdly high-dimensional actions: token sequences, tool + structured arguments |
| narrow on-policy distribution → poor value estimates elsewhere | only near-policy trajectories → thin coverage of tool-use patterns |
| importance sampling blows up in high-dim continuous actions | IS weights blow up over long token sequences — the same pathology |

So the question FlashSAC answers — *how do you reuse expensive interaction data through a
replay buffer without the bootstrapped critic falling apart?* — transplants intact. What
follows is the port, piece by piece, roughly in the order I'd trust it.

## The port

**Redefine the action before anything else.** A token-level transplant dies on arrival: the
action space is vocabulary-sized and episodes run thousands of steps. The workable
granularity is the turn — state = the context so far (conversation plus accumulated tool
results), action = one tool call (a search query; an MCP tool with arguments) or the decision
to stop and answer, critic = Q(context, tool call): *what is it worth to fire this query
now?* Episodes become 5–20 decisions, bootstrapping over that horizon is survivable, and
trajectories in the buffer stay reusable across policy versions. SAC's max-entropy term lands
somewhere pleasant: sustained diversity over tools rather than early collapse onto a
favorite, with auto-tuned temperature as the dial between exploratory search and committed
answering. None of this is virgin territory, and I don't want to claim someone else's gap:
[WebGPT](https://arxiv.org/abs/2112.09332) (2021) treated search as an environment but mostly
sidestepped RL for behavior cloning and rejection sampling;
[ArCHer](https://arxiv.org/abs/2402.19446) (2024) is precisely a turn-level off-policy critic
over utterances driving a token-level policy, demonstrated up to 7B; and the current
production norm, [Search-R1](https://arxiv.org/abs/2503.09516)-style GRPO (2025), is
resolutely on-policy. What FlashSAC contributes to this line is not the formulation — it's
evidence that the formulation was never the bottleneck. The missing pieces were the scaling
recipe and the stability stack.

**Translate the scaling recipe into agent infrastructure.** "1024 parallel environments"
reads naturally as an asynchronous rollout fleet — vLLM/SGLang servers over cached or mocked
tool environments. Async LLM-RL systems like [AReaL](https://arxiv.org/abs/2505.24298) (2025)
already tolerate stale trajectories, but as a necessary evil of keeping GPUs fed, patched
with a staleness-enhanced PPO. FlashSAC upgrades staleness from a tax to the operating point:
off-policy is the design, not the leak. And the low-UTD, wide-batch prescription is the
theory behind a piece of folklore every agent-RL practitioner knows — run GRPO for a second
epoch over the same rollouts and watch the run degrade. The paper's advice: don't grind more
updates out of the batch; widen the batch and the model instead.

**Bound the value function; don't fine it.** This is the piece I keep turning over. Our
field's stabilizer of record is the KL penalty — a soft fine, added to the loss, which the
optimizer may simply pay whenever the reward makes it worthwhile. FlashSAC's philosophy is
that stability you want unconditionally should be enforced structurally. For agents the
natural target is the value head or verifier trained by bootstrapping — exactly the artifact
everyone wants for process supervision, and exactly the one that keeps drifting: estimates
inflating until reward hacking reads as calibrated confidence. Port the stack whole:
weight-norm projection and RMSNorm-bounded features on the value head, gradient-norm bounds
against sparse-reward variance, and a categorical TD target — agent rewards are mostly
terminal and binary, returns are bimodal, and a cross-entropy target over atoms fits that
shape far better than L2 regression, the same conclusion value-learning-as-classification
reached on the way to scale ([C51](https://arxiv.org/abs/1707.06887), 2017;
[Stop Regressing](https://arxiv.org/abs/2403.03950), 2024).

**Give exploration a hold register.** Per-turn iid temperature sampling is the agent version
of per-step Gaussian noise: white, incoherent, averaging itself out. The noise-repetition
translation: sample an exploration mode at episode start — cast wide, dig deep, switch source
families — and hold it for k turns with k heavy-tailed. The implementation cost matches the
original's selling point, which is to say roughly zero: a conditioning line in the system
prompt, or a pinned sampling seed. Coherent exploration doesn't require apparatus; it
requires a held sample and a counter.

**Cached-corpus-to-live-web is sim-to-real.** The sim: a frozen search-index snapshot,
record-and-replay MCP responses, sandboxed mock APIs — orders of magnitude more throughput at
near-zero marginal cost. The real: the live web and live servers. Domain randomization
translates one-for-one — shuffle result order, inject distractor documents, perturb tool
schemas and latency and error rates, mix snapshot ages. And FlashSAC's headline result is the
promise here: once off-policy reuse plus stability make training fast, sim-to-real stops
being a research program and becomes a build step — tune against the snapshot in the morning,
deploy against the live web in the afternoon. (This is also the leg of
[my AgentPlanet factorization](AgentPlanet/index.html) where the world is materialized — the
cheap, checkable half.)

**Take the privileged critic; it's a config flag.** `asymmetric_observation=true` ports
without modification: at training time the critic sees gold answers, the full corpus, oracle
judgments; the actor sees only what deployment will show it. Reward models already do a soft
version of this implicitly. Turn-level value learning makes it an explicit architectural
choice, which is where it belongs.

**And with zero appetite for RL at all**, the critic alone earns rent: Q(context, candidate
tool call) is a learned verifier at branch points. Instead of best-of-n over whole
trajectories — n full rollouts, n full bills — prune at each decision. When rollouts dominate
cost, valuation at decision points is the only best-of-n you can afford; that's FlashSAC's
wall-clock argument re-run at inference time.

## Where the analogy strains

- **Actions aren't Gaussian.** SAC's machinery — tanh-Gaussian policies, entropy in
  continuous space, min-over-critics — assumes a geometry tool calls don't have: a discrete
  choice welded to structured text arguments. A
  [discrete-SAC](https://arxiv.org/abs/1910.07207) variant or a latent action embedding is a
  real design problem, not a footnote.
- **Reward is sparser here.** Control tasks often enjoy dense per-step shaping; agents get a
  terminal 0/1. That shrinks what bootstrapping buys and grows what it risks — which cuts
  both ways: it's the honest reason to hesitate, and the reason the norm-bounding stack
  matters *more* here than in the domain that invented it.
- **The environment itself moves.** Simulated physics is stationary; the web is not. An old
  trajectory isn't just off-policy, it's *off-environment* — the pages changed. The buffer
  needs machinery FlashSAC never did: timestamps, environment-version tags,
  freshness-weighted sampling.
- **We don't start from scratch.** A robot policy is born random; an agent is born knowing
  things. The "compensate with a bigger model" axis comes pre-paid — and the constraints have
  to be confined (value head, adapters) so that stabilizing the critic doesn't lobotomize the
  actor's prior.

## Where I'd actually start

Not with the full actor-critic loop. The cheapest falsifiable claim sits mid-stack: **does a
norm-bounded categorical turn-level critic stay calibrated on stale trajectories where an
unbounded regression critic drifts?** No SAC required — freeze a corpus snapshot behind a
record-and-replay tool layer, fill a buffer with trajectories from several older policy
checkpoints, train both critics (privileged, per the flag above), and plot calibration
against staleness. If bounding wins, the critic immediately pays for itself as an
inference-time branch-pruner — value delivered before any policy gradient is spent. Only then
does the full recipe — replay, a UTD of 2/1024-or-whatever-it-becomes, wide batches,
exploration modes held for k turns — deserve the GPUs.

The trajectory my agent burned this morning is still sitting in a log somewhere, priced like
a phone bill and used like scratch paper. FlashSAC's actual provocation is that the log was
the training set all along.
