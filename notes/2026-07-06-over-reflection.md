# Over-reflection: when the agent already knows the answer

Here is a trajectory that has been bothering me. A deepseek-v4-pro rollout in our
teacher corpus states the answer around round 2, confirms it against a real search
hit by round 5 — and then keeps searching for twenty-one more rounds before it
finally writes that same answer down. The extra rounds change nothing. The model
already knew, and already had the evidence, and searched anyway.

That is not a rare tail. Across 23,110 English keyed trajectories I tagged, the
"confirm, then keep searching" pattern is **63%** — and it barely moves with how
strictly I match the answer string (63.1% fuzzy, 62.5% exact). So over-reflection
isn't a 20% fringe I can filter away; it's the structural default of a search agent
distilled from a strong teacher. It shows up because the teacher is strong: any model
that can recall the answer before it searches will tend to search to *confirm* what it
already believes, and that habit gets baked into every trajectory we train on. The
user's read — that most frontier models do this — matches what I see in the one
frontier teacher I've measured end to end.

## Classifying it

The mistake would be to treat "searches too much" as one thing. It isn't. Two
questions separate the cases cleanly: did the model reason *first* (parametric recall)
or find evidence *first*; and once it had both stated the answer and seen supporting
evidence, how many more rounds did it search? Call that second number the
*post-confirmation* count, with a boundary at k=2. Seven types fall out:

| Type | What it is | Fix |
|---|---|---|
| A | reasoning-first, then a bounded check (≤2 rounds) | keep — healthy |
| B | reasoning-first, then over-searches a known answer | truncate / stop |
| C | never grounded, but states an answer anyway — search theater | re-ground / drop |
| D | evidence-first, states it, then over-searches | truncate / stop |
| E | never grounded, never even states it — pure recitation | drop |
| F | evidence-first, states it, stops | keep — normal |
| G | grounded but never states it — extraction lag | keep |

The whole point of the taxonomy is in that last column: **the fixes point in opposite
directions.** B and D searched too much after they already knew, so they want *less*
search. C and E never grounded at all, so they want *more*, or better, search. A
single "just be more efficient" intervention would truncate B and D correctly and make
C and E strictly worse — you'd be trimming the agents that should have kept looking. B
alone runs 25.7 rounds on average (confirmation at ~4.7, then +21), and 65% of grounded
trajectories keep searching six or more rounds past the point of confirmation.

## Telling the types apart in real data

Our production detector flagged about 21% of trajectories as "answered from memory,"
which is where the "~20%" number everyone quotes comes from. The gap to 63% is not
disagreement, it's detector blind spots, and finding them was half the work. Three
mattered. The largest source in the corpus (58% of it) has verbose gold answers, so a
verbatim-needle detector matches almost nothing there — a 0.04% flag rate, a near-total
blind spot. Type D is invisible in principle to a memory-first detector, because D
found its evidence legitimately and *then* over-searched. And the search engine echoes
the query back in the first line of its results, so a query leak reads as genuine
discovery unless you strip it.

My tagger closes those: it strips the SERP query-echo line, scans the tool-call
arguments and not just the reasoning (the answer often leaks into the query, not the
prose), and drops question-echo variants and keys that never appear in the model's own
final answer. Joined against the seed QA it keys 100% of the corpus. The takeaway I
keep returning to: you cannot separate these behaviors with a single needle over the
reasoning text; you need the evidence state and the post-confirmation dimension, or the
most harmful type (C, search theater) sails straight through a fail-open filter.

## Splitting it back into training

Because the prescriptions are opposite, the fix has to be per-type surgery, not a
blanket filter. Repair v1 does exactly that deterministically: for B and D it truncates
the *uncited* inertia tail — it cuts at the last round the final answer actually cites,
then reattaches the original final, so citation closure holds and no reference dangles —
while it drops C and E and keeps A, F, G. That removed about 119M tokens of pure
over-search across 6,774 rows and pulled the English average from 20.0 rounds down to
15.5 (−22.8%). It also found its own ceiling: for 7,793 rows the final answer genuinely
cites the tail, so a deterministic cut can't touch them without rewriting the answer.
Those are the cases that justify an RL leg later — a policy that learns to *stop* and
rewrite, not just a scalpel over the data.

That gives three training arms to compare: **as-is** (baseline), **wholesale-drop**
(the naive filter that deletes any memory-first trajectory), and **surgical-repair**.

## How I'll grade it — and the confound that already bit me

Accuracy on these benchmarks is noisy (roughly 20% flip between rollouts, so it needs
three or more repeats), but the number I care about — tool-call rounds per task — is
low-noise, so that's the primary signal. The eval design uses each benchmark for a
different job. **BrowseComp** (English) is primary, because repair only touches English
rows. **K-BrowseComp** (Korean) is the control: Korean passes through untouched, so the
arms should *not* differ there, and if they do the effect isn't repair. **LiveBrowseComp**
is the guard I trust most — post-cutoff questions whose answer cannot be in the
parameters, so it catches the opposite failure, the under-searching and hallucination
that a "search less" intervention could induce. **WideSearch** and **Ko-WideSearch**
are the breadth-regression monitor: cutting over-search must not cost set-enumeration
recall.

The first pass looked like a clean win. On English BrowseComp at N=40, surgical-repair
beat baseline beat wholesale-drop on every axis — fewest rounds (25.4 vs 29.0), half the
cap-hits (10% vs 18%), best accuracy (32.5% vs 27.5%), and it pulled back six of the
baseline's seven runaway rollouts where drop pulled back three. The K-BrowseComp control
even behaved: the arm gap collapsed from a spread of 6.9 rounds to 1.7, exactly the
causal signature I wanted. Wholesale-drop being *worse* than baseline was the satisfying
part — deleting whole memory-first trajectories also deletes the grounded-stop examples,
so the model over-searches more, which is the project's whole thesis in one result.

Then I looked at the training data and it came apart. The 32k sequence cap had already
done most of the work: uncapped English over-search is 63%, but the cap alone brings the
baseline arm to 53.5%, and repair targets the same long tail the cap was already
clipping. So the three arms trained on 92% identical questions and differ by only −0.43
rounds in-corpus. A −0.43 training difference producing a −3.6 eval difference is more
likely N=40 noise than a real effect — and the Korean "control" is then better explained
by *the arms being nearly the same model* than by repair being English-specific. So I'm
not claiming the win. The honest lesson, which survives regardless, is that **a training
sequence cap can silently swallow a data-repair treatment**: the real experiment is a
64k+ cap retrain where the tail survives training and repair is the only thing removing
it.

What's running now is a 4-model by 3-benchmark sweep (base plus the three arms, over
K-BrowseComp, LiveBrowseComp, and full English BrowseComp) to let large N call the
washout — if base ≈ repair, the cap neutralized everything and N=40 was noise, cleanly.
After that comes the RL leg: an evidence-anchored stop-pivot whose reward is
state-conditioned — grounded, so finalize only if the answer matches its citation;
unverified, so allow one more novel search. It has to be state-conditioned because a
coarse action-type verifier, the kind that only checks "was the next step a search,"
would happily reward search-after-search and reinforce the exact over-reflection I'm
trying to remove.
