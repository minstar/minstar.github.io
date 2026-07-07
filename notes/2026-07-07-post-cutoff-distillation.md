# Teaching a model what happened after its cutoff

A knowledge cutoff is a wall a model can't see past: everything dated after it is
either missing or confabulated. The usual patches are retrieval at inference time
and periodic re-pretraining. This note sketches a third option I keep circling
back to — let a teacher that *has* seen the new facts hand them to a student token
by token, and reward only the tokens that carry knowledge the student couldn't
have known.

The rough shape:

```
memory cache of post-cutoff facts  ─update→  teacher
teacher  ─on-policy distillation→  student   (per-token reward, in the student's vocab,
                                              gated to post-cutoff knowledge only)
```

## The three moving parts

**On-policy distillation as the transport.** The student rolls out its own
trajectories, the teacher scores them per token, and the student learns from a
per-token reward — rather than being fed teacher text to imitate. This is the
[GKD](https://arxiv.org/abs/2306.13649) / [MiniLLM](https://arxiv.org/abs/2306.08543)
line (reverse-KL is the right divergence when the teacher outclasses the student —
mode-seeking, so the student doesn't smear probability over regions it can't
represent). What makes it more than an analogy here is that Thinking Machines Lab's
[On-Policy Distillation](https://thinkingmachines.ai/blog/on-policy-distillation/)
post (Oct 2025) already runs *almost exactly this loop* for the continual-learning
case: mid-train on new documents (which causes forgetting), then recover behavior
via on-policy distillation — they report retaining ~41% of the injected new-domain
knowledge while restoring instruction-following (IFEval 45→83), at a fraction of RL
compute. So the "inject new docs, then recover with OPD" skeleton is not
hypothetical.

**Different teacher, different tokenizer.** I want the teacher to be *whatever
strong model saw the new facts*, not a same-family sibling — so its tokenizer won't
match the student's, and the reward has to land in the student's own vocabulary.
This turns out to be the part that's basically solved. Cross-tokenizer on-policy
distillation via chunk alignment ([Breaking the Tokenizer Barrier](https://arxiv.org/abs/2606.09456),
2026) matches same-tokenizer OPD at ~4% of SFT FLOPs (≤8B so far), and the alignment
math has several working recipes —
[ULD](https://arxiv.org/abs/2402.12030) (optimal transport over logits),
[MultiLevelOT](https://arxiv.org/abs/2412.14528),
[DSKD](https://arxiv.org/abs/2406.17328) (project both into a shared space). I don't
get to claim novelty here; this is the *enabling* method I'd build on top of.

**A reward gated by date.** This is the piece with no prior art. Token-level rewards
exist ([FactTune](https://arxiv.org/abs/2311.08401) and the token-level RM line),
and post-cutoff measurement exists
([Dated Data](https://arxiv.org/abs/2403.12958),
[TemporalWiki](https://arxiv.org/abs/2204.14211)) — but nobody rewards distillation
*selectively by the date of the knowledge*. The bet is that the only transferable
signal lives in the delta: an updated teacher helps precisely because it carries
facts the student lacks, so you should reward the tokens that encode those facts and
leave the rest alone. Reward tokens the student already knew and you get no
gradient, or worse, you pay to re-teach correct memory.

## Why it might not work (the honest part)

- **Effective cutoff ≠ reported cutoff.** [Dated Data](https://arxiv.org/abs/2403.12958)
  shows a model's real cutoff drifts from its model card (stale CommonCrawl, dedup
  leakage). So "post-cutoff" can't be read off metadata — it needs per-fact probing,
  and a wrong label either rewards nothing or penalizes a fact the student had right.
- **Injected factoids forget fast.** Catastrophic forgetting of newly-memorized
  facts is the empirical default ([Continual Memorization of Factoids](https://arxiv.org/abs/2411.07175));
  the update has to *retain* new knowledge without eroding old capability, and the
  TML 41%-retention number is both the encouraging precedent and the bar to clear.
- **A confident-but-wrong teacher injects hallucinations token by token.** The reward
  is only as trustworthy as the memory-cache update and the labeler — exactly the
  reward-hacking failure the token-level-RM papers keep warning about.

## The crux

Everything except the date gate has a working precedent to borrow. The crux — and
the whole novelty — is building a reliable *automatic* token-level "post-cutoff
knowledge" mask: given a student rollout, decide which spans encode a fact dated
after this particular student's cutoff, and reward only those. Nail that and the
idea is a clean recombination of four mature primitives; leave it heuristic and the
reward is only as good as the labeler. That's the one component I'd prototype first.
