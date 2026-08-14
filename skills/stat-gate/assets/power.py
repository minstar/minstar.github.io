#!/usr/bin/env python3
"""Is this eval delta real, and if not, how many repeats would settle it?

Agentic evals are noisy in a specific way: at temperature 1.0 a single rollout on a browsing-style
benchmark flips a large fraction of items between identical runs. A delta smaller than that floor is
not a small result — it is *no* result, and reporting it as a gain is how a pipeline accumulates
findings that evaporate later.

Three modes:

    # 1. paired comparison — same items, two arms
    python3 power.py compare --a runA.jsonl --b runB.jsonl

    # 2. noise floor — two or more runs of the SAME config
    python3 power.py floor run1.jsonl run2.jsonl run3.jsonl

    # 3. design — how many items/repeats to detect a target delta
    python3 power.py design --n 500 --sd 0.45 --target 0.02

Records are JSONL with an id field and a score field, auto-detected from
{id, task_id, question_id, idx} and {correct, score, em, pass, reward, acc}.

Exit 0 = a verdict was produced. Exit 1 = SIGNIFICANT. Exit 2 = inputs unusable.
(The exit codes are deliberately not "0 = good": a driver should branch on the verdict, and
SIGNIFICANT is the case that changes what happens next.)
"""
import argparse
import json
import math
import os
import random
import sys

ID_KEYS = ("id", "task_id", "question_id", "qid", "idx", "index", "example_id")
SCORE_KEYS = ("correct", "score", "em", "exact_match", "pass", "passed", "reward", "acc", "accuracy")

Z_CI = 1.96      # two-sided 95%
Z_POWER = 0.84   # 80% power


def load(path):
    """{id: score} from a JSONL file. Raises on an unusable file rather than guessing."""
    rows, id_key, score_key = {}, None, None
    dupes = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            if id_key is None:
                id_key = next((k for k in ID_KEYS if k in rec), None)
                score_key = next((k for k in SCORE_KEYS if k in rec), None)
                if id_key is None or score_key is None:
                    raise ValueError("%s: cannot find an id field %s and a score field %s in %r"
                                     % (os.path.basename(path), ID_KEYS, SCORE_KEYS,
                                        sorted(rec)[:8]))
            if id_key not in rec or score_key not in rec:
                continue
            v = rec[score_key]
            v = 1.0 if v is True else 0.0 if v is False else float(v)
            k = str(rec[id_key])
            if k in rows:
                dupes += 1
            rows[k] = v
    if not rows:
        raise ValueError("%s: no usable records" % path)
    return rows, dupes, score_key


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def sd(xs):
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def paired_bootstrap(diffs, iters=5000, seed=0):
    """95% CI on the mean paired difference. Fixed seed so a rerun gives the same answer."""
    rnd = random.Random(seed)
    n = len(diffs)
    means = []
    for _ in range(iters):
        means.append(mean([diffs[rnd.randrange(n)] for _ in range(n)]))
    means.sort()
    lo = means[int(0.025 * iters)]
    hi = means[min(int(0.975 * iters), iters - 1)]
    return lo, hi


def required_n(sd_diff, target):
    """Paired-design n to detect `target` at 95%/80%."""
    if target <= 0 or sd_diff <= 0:
        return 0
    return int(math.ceil(((Z_CI + Z_POWER) * sd_diff / target) ** 2))


def mde(sd_diff, n):
    """Smallest delta this design could detect."""
    return (Z_CI + Z_POWER) * sd_diff / math.sqrt(n) if n > 0 else float("inf")


def cmd_compare(a):
    A, dupA, keyA = load(a.a)
    B, dupB, keyB = load(a.b)
    shared = sorted(set(A) & set(B))
    if not shared:
        print("no overlapping ids between the two files — an unpaired comparison is not "
              "interpretable here; align the item sets first", file=sys.stderr)
        return 2
    only_a, only_b = len(A) - len(shared), len(B) - len(shared)
    diffs = [B[k] - A[k] for k in shared]
    d = mean(diffs)
    s = sd(diffs)
    lo, hi = paired_bootstrap(diffs, a.iters, a.seed)
    flips = sum(1 for x in diffs if x != 0) / len(diffs)
    this_mde = mde(s, len(shared))
    need = required_n(s, abs(d)) if d else 0

    print("paired comparison on %d shared item(s)   [score field: %s/%s]" % (len(shared), keyA, keyB))
    print("  A mean        %.4f" % mean([A[k] for k in shared]))
    print("  B mean        %.4f" % mean([B[k] for k in shared]))
    print("  delta (B-A)   %+.4f   95%% CI [%+.4f, %+.4f]  (paired bootstrap, %d iters)"
          % (d, lo, hi, a.iters))
    print("  per-item flip rate %.1f%%   sd(diff) %.4f" % (100 * flips, s))
    print("  this design's MDE  %+.4f  (smallest delta it could detect at 95%%/80%%)" % this_mde)
    if only_a or only_b:
        print("  NOTE: %d item(s) only in A, %d only in B — excluded from the pairing" % (only_a, only_b))
    if dupA or dupB:
        print("  NOTE: duplicate ids collapsed (A:%d, B:%d) — last value won" % (dupA, dupB))

    if lo > 0 or hi < 0:
        print("\nSIGNIFICANT: the 95%% CI excludes zero. Delta %+.4f is above this design's noise." % d)
        print("Still report n, the CI and the flip rate alongside the number.")
        return 1
    print("\nUNDERPOWERED / NULL: the 95%% CI spans zero, so this run cannot distinguish "
          "%+.4f from no difference." % d)
    if need and need > len(shared):
        print("To resolve a delta of this size you would need ~%d paired items (have %d) — "
              "or more repeats per item to shrink sd(diff)." % (need, len(shared)))
    print("Do not report this as a gain. It is not a small result; it is no result.")
    return 0


def cmd_floor(a):
    runs = []
    for p in a.runs:
        r, _dup, _k = load(p)
        runs.append((os.path.basename(p), r))
    ids = set(runs[0][1])
    for _n, r in runs[1:]:
        ids &= set(r)
    ids = sorted(ids)
    if not ids:
        print("no ids shared across all runs", file=sys.stderr)
        return 2

    print("noise floor from %d run(s) of the same config, %d shared item(s)" % (len(runs), len(ids)))
    for name, r in runs:
        print("  %-40s mean %.4f" % (name[:40], mean([r[k] for k in ids])))
    means = [mean([r[k] for k in ids]) for _n, r in runs]
    spread = max(means) - min(means)

    # per-item disagreement across runs — the thing that actually moves a single-rollout number
    unstable = sum(1 for k in ids if len({r[k] for _n, r in runs}) > 1)
    print("\n  run-to-run mean spread   %.4f  (min %.4f, max %.4f)" % (spread, min(means), max(means)))
    print("  items that changed answer %d/%d = %.1f%%" % (unstable, len(ids), 100 * unstable / len(ids)))
    print("\nFLOOR: treat any delta at or below %.4f as indistinguishable from rerun noise "
          "at this repeat count." % spread)
    if len(runs) < 3:
        print("Two runs give a weak floor estimate — 3+ repeats is the working minimum.")
    return 0


def cmd_design(a):
    n_needed = required_n(a.sd, a.target)
    print("design check")
    print("  sd(paired diff)  %.4f" % a.sd)
    print("  target delta     %+.4f" % a.target)
    print("  required n       %d paired items (95%% CI, 80%% power)" % n_needed)
    if a.n:
        print("  planned n        %d  ->  MDE %+.4f" % (a.n, mde(a.sd, a.n)))
        if n_needed > a.n:
            print("\nUNDERPOWERED BY DESIGN: %d items cannot resolve %+.4f. Either raise n to ~%d, "
                  "add repeats per item to shrink sd, or pick a bigger intervention. Decide now — "
                  "not after the GPU time is spent." % (a.n, a.target, n_needed))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Decide whether an eval delta clears the noise floor.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("compare", help="paired A/B on the same items")
    c.add_argument("--a", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--iters", type=int, default=5000)
    c.add_argument("--seed", type=int, default=0)
    c.set_defaults(fn=cmd_compare)

    f = sub.add_parser("floor", help="noise floor from repeated runs of one config")
    f.add_argument("runs", nargs="+")
    f.set_defaults(fn=cmd_floor)

    d = sub.add_parser("design", help="required n / MDE before running")
    d.add_argument("--sd", type=float, required=True, help="sd of the paired difference")
    d.add_argument("--target", type=float, required=True, help="delta you want to be able to detect")
    d.add_argument("--n", type=int, default=0, help="planned number of paired items")
    d.set_defaults(fn=cmd_design)

    a = ap.parse_args()
    try:
        return a.fn(a)
    except (ValueError, OSError) as exc:
        print("stat-gate: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
