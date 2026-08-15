#!/usr/bin/env python3
"""Is the head of this file list a SAMPLE, or is it one STRATUM?

Sorted globs cluster by directory, which usually means by arm, benchmark, or condition. When that
happens the first N files are not a random sample of the corpus — they are the first stratum or
two at full weight and the rest at zero, and every statistic computed on them is conditioned on
that. This tool says whether it happened.

PROVENANCE, because it matters for how much you should trust the tool's premise. It was written
2026-08-15 to mechanize what looked like the shared cause of three wrong conclusions that day.
Its first run REFUTED that premise for the two cases the author could check: the 40-file slice
blamed for a bad blast-radius writeup was in fact representative (bench TVD 0.029; MCQ share
96.0% in the head vs 94.1% in the corpus — the corpus is 94% MCQ). Those two misses had different
causes, and this tool would have caught NEITHER:

  - reading the first rows of a list the author had just sorted BY THE VARIABLE UNDER TEST, so the
    "sample" was the extreme. Sort, then compute a summary statistic; do not read the top rows.
  - asserting an output-side mechanism ("the think text is scored as the answer") from an
    input-side field, without ever joining to the output field. raw_output is not submitted.

So: this checks one real failure mode, and it is cheap. It is not a general guard against
concluding from a bad slice, and it should not be cited as one.

    python3 slice_check.py "<glob>" --head 40
    python3 slice_check.py "<glob>" --head 40 --key bench     # force a key
    python3 slice_check.py "<glob>" --head 40 --shuffle       # would a random sample be ok?

Exit 0 = the head is representative on every key tried.
Exit 1 = it is not; the report names the stratum that is missing or over-weighted.
Exit 2 = bad invocation / nothing matched.

The honest fix is almost never a bigger N. It is: run the full set (these corpora sweep in
seconds), or sample randomly and say so.
"""
import argparse
import collections
import glob as globmod
import os
import random
import re
import sys

# Absence is the failure that actually bit: a stratum at >=1% of the corpus and 0% of the head is
# not "under-represented", it is unobserved, and no amount of care with the head can recover it.
MISSING_FLOOR = 0.01
TVD_LIMIT = 0.25


def keys_for(path):
    """Candidate stratum keys. Both are cheap and one of them is almost always the real one."""
    d = os.path.basename(os.path.dirname(path))
    b = os.path.basename(path)
    # benchmark-ish prefix: leading run of non-digit, non-timestamp tokens
    stem = re.split(r"[._]\d|\.jsonl|\.json|_transcripts|_multiturn", b)[0]
    return {"dir": d or "(root)", "bench": stem or "(none)"}


def dist(paths, key):
    c = collections.Counter(keys_for(p)[key] for p in paths)
    n = max(1, len(paths))
    return c, {k: v / n for k, v in c.items()}


def report(paths, head_paths, key, label):
    cf, pf = dist(paths, key)
    ch, ph = dist(head_paths, key)
    missing = [k for k, p in pf.items() if p >= MISSING_FLOOR and ph.get(k, 0.0) == 0.0]
    tvd = 0.5 * sum(abs(pf.get(k, 0) - ph.get(k, 0)) for k in set(pf) | set(ph))
    bad = bool(missing) or tvd > TVD_LIMIT

    print("\nkey=%-6s (%s)   TVD=%.3f%s" % (key, label, tvd, "   <-- UNREPRESENTATIVE" if bad else ""))
    print("  %-28s %12s %12s" % ("stratum", "full", label))
    for k, _ in cf.most_common(12):
        f, h = pf.get(k, 0.0), ph.get(k, 0.0)
        mark = "  MISSING" if (f >= MISSING_FLOOR and h == 0.0) else ""
        print("  %-28s %6d %4.0f%% %6d %4.0f%%%s" % (k[:28], cf[k], 100 * f, ch.get(k, 0), 100 * h, mark))
    if len(cf) > 12:
        print("  ... %d more strata" % (len(cf) - 12))
    if missing:
        print("  %d stratum/strata present in the corpus and ABSENT from %s: %s"
              % (len(missing), label, ", ".join(sorted(missing)[:6])))
    return bad


def main():
    ap = argparse.ArgumentParser(description="Is a head-slice a sample or a stratum?")
    ap.add_argument("pattern", help="glob, quoted (use ** with recursive paths)")
    ap.add_argument("--head", type=int, default=40)
    ap.add_argument("--key", choices=["dir", "bench", "both"], default="both")
    ap.add_argument("--shuffle", action="store_true",
                    help="also evaluate a random sample of the same size, for comparison")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    paths = sorted(globmod.glob(a.pattern, recursive=True))
    if not paths:
        print("slice_check: nothing matched %r" % a.pattern, file=sys.stderr)
        return 2
    if a.head >= len(paths):
        print("head=%d covers the whole corpus (%d files) — nothing to check." % (a.head, len(paths)))
        return 0

    head = paths[:a.head]
    print("corpus %d files · head %d (%.0f%%)" % (len(paths), len(head), 100 * len(head) / len(paths)))

    keys = ["dir", "bench"] if a.key == "both" else [a.key]
    bad = any(report(paths, head, k, "head[:%d]" % a.head) for k in keys)

    if a.shuffle:
        rnd = random.Random(a.seed)
        samp = rnd.sample(paths, a.head)
        sbad = any(report(paths, samp, k, "random[%d]" % a.head) for k in keys)
        print("\nrandom sample of the same size is %s."
              % ("ALSO unrepresentative — the corpus needs a full sweep" if sbad
                 else "representative — if you must subsample, sample randomly and say so"))

    if bad:
        print("\nThe head is a stratum, not a sample. Any statistic from it is conditioned on that.")
        print("Fix: sweep the full set (these corpora take seconds), or sample randomly and label it.")
        return 1
    print("\nHead is representative on every key tried. (Still cheaper to sweep the full set.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
