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
import glob as globmod
import json
import math
import os
import random
import re
import sys

ID_KEYS = ("id", "task_id", "question_id", "qid", "idx", "index", "example_id")
SCORE_KEYS = ("correct", "score", "em", "exact_match", "pass", "passed", "reward", "acc", "accuracy")

# A "degenerate" answer is one the harness recorded but that cannot be a real answer — most often a
# trailing tool call captured after an episode ran out of turns. These score wrong automatically, so
# if two arms differ in how often they produce one, the comparison is partly a format-compliance
# contest. Detected by default on whatever free-text answer field is present.
ANSWER_FIELDS = ("submitted", "prediction", "response", "output", "answer", "generation")
# A harness that records WHY there is no answer beats any pattern over the answer string. When
# `answer_source` is present, "none" is authoritative and the regex is not consulted — that removes
# the encoding-specific blind spot that once under-counted one arm at 1.3% when it was 8.5%. The
# pattern below stays as the fallback for files written before the field existed; keep its
# definition in step with the harness-side NON_ANSWER predicate (XML | JSON-form | empty).
SOURCE_FIELDS = ("answer_source",)
NO_ANSWER_VALUES = {"none", "no_answer", "null", "", "missing"}
# Two tool-call encodings reach the answer field, and missing either UNDER-counts non-response on
# exactly the arms that use it. The XML form covers most arms; a base-model arm emitted the JSON form
# instead, which took its measured non-response from 1.3% to 8.5% once counted. Because the encoding
# is arm-specific, an incomplete detector understates the gap on precisely the comparison that needs
# it. Keep the JSON pattern tight — `{"name": ..., "arguments": ...}` — so a legitimate JSON answer
# is not swept up.
DEGENERATE_RX = re.compile(
    r"<tool_call>|<function=|^\s*$"
    r'|^\s*\{\s*"(?:name|function|tool_name)"\s*:\s*"[^"]+"\s*,\s*"(?:arguments|parameters)"\s*:',
    re.I)

Z_CI = 1.96      # two-sided 95%
Z_POWER = 0.84   # 80% power


TRUEY = {"true", "yes", "y", "correct", "pass", "passed", "1", "1.0"}
# Deliberately excludes "", "none", "null": a MISSING score is not a zero. Scoring it as incorrect
# silently biases the mean down and makes an arm look worse than it is — the same under-report trap
# that makes a broken cost recorder report a comfortable number. Missing cells are skipped and
# counted instead.
FALSEY = {"false", "no", "n", "incorrect", "fail", "failed", "0", "0.0"}


def to_score(v):
    """Coerce a score cell to float. Real harnesses write booleans as the STRINGS 'True'/'False'."""
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in TRUEY:
            return 1.0
        if s in FALSEY:
            return 0.0
        return float(s)                        # raises for genuinely unparseable cells
    raise ValueError("unparseable score %r" % (v,))


def _records(path):
    """Dict records from JSONL, or from a JSON document holding a list of per-item results."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        stripped = fh.read(512).lstrip()
        fh.seek(0)
        if stripped.startswith("["):
            for rec in json.load(fh):
                yield rec
            return
        if stripped.startswith("{"):
            try:
                doc = json.load(fh)
            except json.JSONDecodeError:
                doc = None                     # JSONL whose first line happens to be an object
            if isinstance(doc, dict):
                named = [v for k, v in doc.items()
                         if k in ("results", "items", "records", "predictions", "samples")
                         and isinstance(v, list)]
                lists = named or [v for v in doc.values()
                                  if isinstance(v, list) and v and isinstance(v[0], dict)]
                if lists:
                    for rec in lists[0]:
                        yield rec
                    return
                # A single-record JSONL file parses as one object with no per-item list. If it
                # carries an id and a score it IS the record, not a malformed wrapper.
                if any(k in doc for k in ID_KEYS) and any(k in doc for k in SCORE_KEYS):
                    yield doc
                    return
                raise ValueError("%s: JSON object has no per-item list (keys: %s)"
                                 % (os.path.basename(path), sorted(doc)[:10]))
            fh.seek(0)
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            try:
                yield json.loads(ln)
            except json.JSONDecodeError:
                continue


def load(path):
    """({id: score}, dupes, score_key, {id: degenerate?}) from JSONL or a JSON results file."""
    rows, flags, id_key, score_key, ans_key, src_key = {}, {}, None, None, None, None
    dupes = skipped = 0
    for rec in _records(path):
        if not isinstance(rec, dict):
            continue
        if id_key is None:
            id_key = next((k for k in ID_KEYS if k in rec), None)
            score_key = next((k for k in SCORE_KEYS if k in rec), None)
            ans_key = next((k for k in ANSWER_FIELDS if k in rec), None)
            src_key = next((k for k in SOURCE_FIELDS if k in rec), None)
            if id_key is None or score_key is None:
                raise ValueError("%s: cannot find an id field %s and a score field %s in %r"
                                 % (os.path.basename(path), ID_KEYS, SCORE_KEYS, sorted(rec)[:10]))
        if id_key not in rec or score_key not in rec:
            continue
        try:
            v = to_score(rec[score_key])
        except (TypeError, ValueError):
            skipped += 1                       # counted and reported, never silently dropped
            continue
        k = str(rec[id_key])
        if k in rows:
            dupes += 1
        rows[k] = v
        if src_key is not None and src_key in rec:
            flags[k] = str(rec[src_key]).strip().lower() in NO_ANSWER_VALUES
        elif ans_key is not None and ans_key in rec:
            flags[k] = bool(DEGENERATE_RX.search(str(rec[ans_key])))
    if skipped:
        print("  NOTE: %s — %d record(s) had an unparseable %s and were excluded"
              % (os.path.basename(path), skipped, score_key), file=sys.stderr)
    if not rows:
        raise ValueError("%s: no usable records" % path)
    return rows, dupes, score_key, flags


def siblings(path):
    """How many repeat runs of this benchmark sit next to the chosen file."""
    base = os.path.basename(path)
    m = re.match(r"^(.*?)[_-]?\d{6,}", base)          # strip the run timestamp
    if not m or not m.group(1):
        return 0
    return len(globmod.glob(os.path.join(os.path.dirname(path) or ".", m.group(1) + "*")))


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
    A, dupA, keyA, flagA = load(a.a)
    B, dupB, keyB, flagB = load(a.b)
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
    # Name the files. A glob like `<bench>_multiturn_*.json` is ambiguous when an arm has repeat
    # runs, and which one it resolves to moves the number by about the noise floor — so the output
    # has to say what it actually read.
    print("  A = %s" % os.path.basename(a.a))
    print("  B = %s" % os.path.basename(a.b))

    # Repeat-count parity. Promoted from a lesson: one arm had three runs of a benchmark and the
    # other had one, so a glob silently picked one of three on one side, and the side with a single
    # run had no run-level error bar at all. A ceiling measured on the repeated arm cannot be
    # applied to the un-repeated one.
    na, nb = siblings(a.a), siblings(a.b)
    if na and nb and na != nb:
        print("  REPEAT ASYMMETRY: A has %d run(s) of this benchmark, B has %d." % (na, nb))
        print("      The arm with more runs has a measurable rerun spread; the other does not.\n"
              "      Do not carry a noise floor across them, and say which file each side used.")
    elif na and na > 1:
        print("  note: %d run(s) of this benchmark exist per arm — this compares ONE of them" % na)
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

    # Degeneracy parity — the check that would have caught EXP-004 automatically.
    confounded = False
    both = [k for k in shared if k in flagA and k in flagB]
    if both:
        ra = sum(1 for k in both if flagA[k]) / len(both)
        rb = sum(1 for k in both if flagB[k]) / len(both)
        print("  non-answers (tool-call/empty)  A %.1f%%  B %.1f%%   delta %+.1fpp"
              % (100 * ra, 100 * rb, 100 * (rb - ra)))
        if abs(rb - ra) >= 0.02:
            clean = [k for k in both if not flagA[k] and not flagB[k]]
            print("\n  WARNING: the arms differ by %.1fpp in how often they emit something that cannot be an\n"
                  "  answer. Those score wrong automatically, so part of the delta above is format\n"
                  "  compliance, not capability." % (100 * abs(rb - ra)))
            # Worst/best-case bounds over the unanswered items (Manski-style). Non-answers score
            # wrong as measured, so the observed delta is already the "all non-answers wrong" corner;
            # the opposite corner assigns them all correct. Together they bracket what the delta
            # could become if extraction were fixed, WITHOUT conditioning on anything post-treatment.
            lo_d = mean([(1.0 if flagB.get(k) else B[k]) - (0.0 if flagA.get(k) else A[k])
                         for k in both])
            hi_d = mean([(0.0 if flagB.get(k) else B[k]) - (1.0 if flagA.get(k) else A[k])
                         for k in both])
            print("  Bounds over the unanswered items (no post-treatment conditioning):\n"
                  "      delta lies in [%+.4f, %+.4f] once every non-answer is resolved either way"
                  % (min(lo_d, hi_d), max(lo_d, hi_d)))
            if len(clean) >= 30:
                cd = [B[k] - A[k] for k in clean]
                cl, ch = paired_bootstrap(cd, a.iters, a.seed)
                print("  Among the %d item(s) where both arms answered: delta %+.4f [%+.4f, %+.4f]"
                      % (len(clean), mean(cd), cl, ch))
                print("  CAUTION: that subset conditions on a POST-TREATMENT variable — answering is\n"
                      "  itself affected by the arm — so the two sides are different populations and\n"
                      "  a null there is NOT evidence of no capability effect. Use it to describe,\n"
                      "  never to refute. The bracket above is the quantity that bounds the truth.")
                # Only claim confounding when the bounds themselves cannot exclude zero.
                confounded = (min(lo_d, hi_d) <= 0 <= max(lo_d, hi_d))
            else:
                print("  Too few items where both arms answered (%d) to re-estimate." % len(clean))
                confounded = (min(lo_d, hi_d) <= 0 <= max(lo_d, hi_d))

    if (lo > 0 or hi < 0) and confounded:
        print("\nDIFFERENTIAL NON-RESPONSE: the headline delta %+.4f is a valid TOTAL effect, but the arms\n"
              "differ in how often they answer at all, and once the unanswered items are resolved either\n"
              "way the delta can cross zero. So the headline is real and reportable as an effect on\n"
              "answer COMMITMENT — it is not a capability delta, and it is not refuted either. Report\n"
              "the non-response gap as the finding, fix extraction, and re-run before claiming a\n"
              "capability effect in either direction." % d)
        return 0
    if lo > 0 or hi < 0:
        print("\nSIGNIFICANT: the 95%% CI excludes zero. Delta %+.4f is above this design's noise." % d)
        if abs(d) < this_mde:
            print("CAUTION: the delta (%+.4f) is SMALLER than this design's MDE (%+.4f). That is not a\n"
                  "contradiction — MDE is the effect this design detects 80%% of the time, and you can\n"
                  "clear the CI below it — but it is exactly the profile of a result that fails to\n"
                  "replicate: an effect this size lands inside the CI on a rerun roughly as often as\n"
                  "not. Replicate before this becomes a claim." % (d, this_mde))
        print("Report n, the CI and the flip rate alongside the number.")
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
        r, _dup, _k, _f = load(p)
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
