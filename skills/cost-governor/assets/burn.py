#!/usr/bin/env python3
"""Track paid-API spend from a run's OWN per-call records, and gate on a hard ceiling.

Two failures this encodes, both of which have already happened:

  1. **Never poll an account balance.** A balance moves for reasons unrelated to this run (other
     jobs, other people, credits, refunds). Reading it as "my spend" once produced a 170x
     over-estimate and killed a healthy fleet. The only admissible source is the per-call cost the
     run itself recorded.
  2. **Never extrapolate from arithmetic alone.** Multi-round agentic evals have come in at 5-10x
     a per-call estimate, because rounds multiply and retries are invisible in the estimate. Price
     a measured pilot, then scale.

    python3 burn.py 'runs/**/calls.jsonl' --ceiling 500
    python3 burn.py <dir> --ceiling 1000 --project 60000
    python3 burn.py <glob> --ceiling 500 --json

Exit 0 = under ceiling. Exit 1 = at or over ceiling (a driver loop should stop). Exit 2 = the
records could not be trusted (too many unparsed) — treated as blocking, not as zero.
"""
import argparse
import glob as globmod
import json
import os
import sys

# Keys seen in the wild, in priority order. A record may nest under "usage".
COST_KEYS = ("cost", "total_cost", "cost_usd", "usd", "price")


def find_cost(rec):
    """Return (cost, how) or (None, reason). Never guesses a price from tokens."""
    if not isinstance(rec, dict):
        return None, "not an object"
    for container, prefix in ((rec, ""), (rec.get("usage") or {}, "usage."),
                              (rec.get("response") or {}, "response."),
                              ((rec.get("response") or {}).get("usage") or {}, "response.usage.")):
        if not isinstance(container, dict):
            continue
        for k in COST_KEYS:
            if k in container:
                v = container[k]
                if isinstance(v, (int, float)):
                    return float(v), prefix + k
                try:
                    return float(str(v).lstrip("$")), prefix + k
                except (TypeError, ValueError):
                    return None, "unparseable %s%s=%r" % (prefix, k, v)
    return None, "no cost field"


def iter_files(target):
    if os.path.isdir(target):
        for root, _dirs, files in os.walk(target):
            for fn in files:
                if fn.endswith((".jsonl", ".ndjson")):
                    yield os.path.join(root, fn)
    else:
        for p in sorted(globmod.glob(target, recursive=True)):
            if os.path.isfile(p):
                yield p


def main():
    ap = argparse.ArgumentParser(description="Sum per-call spend and gate on a ceiling.")
    ap.add_argument("target", help="directory, file, or glob of jsonl call records")
    ap.add_argument("--ceiling", type=float, required=True, help="hard USD ceiling")
    ap.add_argument("--project", type=int, default=0,
                    help="extrapolate to this many total records (uses measured $/record)")
    ap.add_argument("--max-unparsed", type=float, default=0.02,
                    help="fraction of records allowed to lack a cost field (default 2%%)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    files = list(iter_files(a.target))
    if not files:
        print("burn: no jsonl records matched %r" % a.target, file=sys.stderr)
        return 2

    total, priced, unparsed, bad_lines = 0.0, 0, 0, 0
    reasons, sources = {}, {}
    for p in files:
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        rec = json.loads(ln)
                    except json.JSONDecodeError:
                        bad_lines += 1
                        continue
                    c, how = find_cost(rec)
                    if c is None:
                        unparsed += 1
                        reasons[how] = reasons.get(how, 0) + 1
                    else:
                        total += c
                        priced += 1
                        sources[how] = sources.get(how, 0) + 1
        except OSError as exc:
            print("burn: cannot read %s (%s)" % (p, exc), file=sys.stderr)

    seen = priced + unparsed
    per = (total / priced) if priced else 0.0
    frac_unparsed = (unparsed / seen) if seen else 1.0
    projected = per * a.project if a.project else None

    out = {"files": len(files), "records": seen, "priced": priced, "unparsed": unparsed,
           "bad_json_lines": bad_lines, "spend_usd": round(total, 4),
           "usd_per_record": round(per, 6), "ceiling_usd": a.ceiling,
           "pct_of_ceiling": round(100.0 * total / a.ceiling, 1) if a.ceiling else None,
           "projected_usd": round(projected, 2) if projected is not None else None,
           "cost_field": max(sources, key=sources.get) if sources else None}

    if a.json:
        print(json.dumps(out, indent=2))
    else:
        print("burn: %d file(s), %d record(s)" % (len(files), seen))
        print("  spend        $%.2f  (%.1f%% of $%.2f ceiling)"
              % (total, out["pct_of_ceiling"] or 0.0, a.ceiling))
        print("  per record   $%.6f   from field `%s`" % (per, out["cost_field"]))
        if projected is not None:
            print("  projected    $%.2f at %d records" % (projected, a.project))
        if unparsed or bad_lines:
            print("  UNPRICED     %d record(s) (%.1f%%), %d unreadable line(s)"
                  % (unparsed, 100.0 * frac_unparsed, bad_lines))
            for why, n in sorted(reasons.items(), key=lambda x: -x[1])[:3]:
                print("               %-28s %d" % (why, n))

    # --- gates, in order of severity
    if seen and frac_unparsed > a.max_unparsed:
        print("\nBLOCKED: %.1f%% of records carry no cost field (limit %.1f%%). The total above is an "
              "UNDER-estimate, so the ceiling cannot be trusted. Fix the recorder before spending more."
              % (100.0 * frac_unparsed, 100.0 * a.max_unparsed))
        return 2
    if total >= a.ceiling:
        print("\nSTOP: $%.2f has reached the $%.2f ceiling. Cancel the fleet." % (total, a.ceiling))
        return 1
    if projected is not None and projected >= a.ceiling:
        print("\nSTOP BEFORE SCALING: measured $%.6f/record projects to $%.2f at %d records, over the "
              "$%.2f ceiling. Re-scope or raise the ceiling deliberately — do not discover this at "
              "record %d." % (per, projected, a.project, a.ceiling, a.project))
        return 1
    print("\nunder ceiling.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
