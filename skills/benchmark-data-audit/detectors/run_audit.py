#!/usr/bin/env python3
"""CLI: run deterministic data-audit detectors over a JSONL trajectory dataset.

Usage
-----
  python run_audit.py --data D.jsonl --field-map field_map.yaml \
      --detectors answer_in_cot,unsupported_correct --limit 200 --out probe.jsonl

  python run_audit.py --data D.jsonl --field-map field_map.yaml \
      --out flags.jsonl --aggregate            # all detectors + calibration report

Per-benchmark thresholds, fuzzy evidence, etc:
  --threshold search_volume=30 --threshold query_redundancy=0.55
  --opt unsupported_correct.evidence_mode=ngram --opt context_bloat.metric=ratio
  --benchmark browsecomp                       # load a preset threshold bundle

Output
------
flags.jsonl: one row per (sample, detector) with score / threshold / flagged /
reason / evidence. With --aggregate also writes <out>.calibration_report.json
next to the out file and prints a summary table.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calibration import aggregate  # noqa: E402
from detectors import (  # noqa: E402
    AnswerInCoT, AnswerItemDup, AnswerRecallNoTool, AnswerSourceRetrieval,
    ConfidenceSaturation, ContextBloat, CoTLengthFloor, CrudStateAssertion,
    FabricatedToolArgs, FabricatedToolOutput, FutileRetryLoop, GraderSpeculationInCoT,
    HallucinatedToolName, LanguageMixing, MalformedToolCall, NoToolCall,
    OverAnswering, PostCompletionLoop, PostSubmitRefusal, QueryRedundancy,
    RedundantBrowsing, SearchVolume, StepCount, UncitedSourceClaim,
    UngroundedOutputValue, UnsupportedCorrect,
)
from record import RecordLoader, dig  # noqa: E402

REGISTRY = {
    d.name: d for d in [
        AnswerInCoT, UnsupportedCorrect, SearchVolume, QueryRedundancy,
        ContextBloat, ConfidenceSaturation, StepCount, RedundantBrowsing,
        GraderSpeculationInCoT, LanguageMixing, FabricatedToolOutput,
        FutileRetryLoop, UncitedSourceClaim, PostCompletionLoop, CoTLengthFloor,
        PostSubmitRefusal, AnswerRecallNoTool, AnswerSourceRetrieval,
        HallucinatedToolName, MalformedToolCall, NoToolCall, FabricatedToolArgs,
        UngroundedOutputValue, OverAnswering, AnswerItemDup, CrudStateAssertion,
    ]
}

# Per-benchmark threshold presets. Seed values; tune from your score
# distributions and the references/*.md evidence base, then commit changes here.
BENCHMARK_PRESETS = {
    # browsecomp family ≈ p90-p95 of the MEASURED search_260605 (78k) audit
    # (context p90=26k/p95=37k, step p90=91/p95=129, search p90=19/p95=28).
    "browsecomp":      {"search_volume": 25, "query_redundancy": 0.5, "step_count": 90, "context_bloat": 30000},
    "livebrowsecomp":  {"search_volume": 25, "query_redundancy": 0.5, "step_count": 90, "context_bloat": 30000},
    "k-browsecomp":    {"search_volume": 25, "query_redundancy": 0.5, "step_count": 90, "context_bloat": 30000},
    "deepsearchqa":    {"search_volume": 20, "query_redundancy": 0.5, "context_bloat": 30000},
    "widesearch":      {"search_volume": 40, "query_redundancy": 0.45, "step_count": 60},
    "ko-widesearch":   {"search_volume": 40, "query_redundancy": 0.45, "step_count": 60},
    "deepresearch":    {"search_volume": 50, "context_bloat": 20000, "step_count": 80},
    "report-generation": {"search_volume": 50, "context_bloat": 20000, "step_count": 80},
    # MCP/long-horizon thresholds ≈ p90-p95 of the MEASURED mcp_260625 (89k) audit
    # (step p90=59/p95=65, search p90=14/p95=20, context p90=35k/p95=42k). Re-tune
    # from your own --aggregate percentiles per dataset.
    "mcp-atlas":       {"step_count": 60, "search_volume": 20, "context_bloat": 42000},
    "mcp-mark":        {"step_count": 60, "search_volume": 20, "context_bloat": 42000},
    "tool-decathlon":  {"step_count": 70, "context_bloat": 45000, "redundant_browsing": 1},
    "deepplanning":    {"step_count": 100, "context_bloat": 60000},
    "tau2":            {"step_count": 40, "context_bloat": 30000},
    "tau3":            {"step_count": 60, "context_bloat": 40000},
}


def load_field_map(path: str) -> dict:
    import yaml  # local import so the message is clear if pyyaml is missing
    with open(path) as f:
        return yaml.safe_load(f) or {}


def iter_rows(path: str):
    """Yield (idx, row dict) from a .jsonl file OR a HuggingFace arrow dataset
    directory / .arrow shard (streamed, no full JSONL materialization)."""
    import glob
    if os.path.isdir(path) or path.endswith(".arrow"):
        import pyarrow as pa
        shards = (sorted(glob.glob(os.path.join(path, "data-*.arrow")))
                  if os.path.isdir(path) else [path])
        if not shards:
            raise SystemExit(f"no .arrow shards under {path}")
        idx = 0
        for shard in shards:
            try:
                reader = pa.ipc.open_stream(pa.OSFile(shard, "rb"))
                while True:
                    try:
                        b = reader.read_next_batch()
                    except StopIteration:
                        break
                    if b is None:
                        break
                    for row in pa.Table.from_batches([b]).to_pylist():
                        yield idx, row
                        idx += 1
            except pa.lib.ArrowInvalid:
                for row in pa.ipc.open_file(pa.OSFile(shard, "rb")).read_all().to_pylist():
                    yield idx, row
                    idx += 1
        return
    with open(path) as fin:
        for idx, line in enumerate(fin):
            line = line.strip()
            if line:
                try:
                    yield idx, json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"[warn] bad JSON at line {idx}: {e}", file=sys.stderr)


def parse_kv(items, cast_val=str):
    out = {}
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"expected key=value, got {it!r}")
        k, v = it.split("=", 1)
        out[k.strip()] = cast_val(v.strip())
    return out


def parse_opts(items):
    """--opt detector.key=value -> {detector: {key: value}}."""
    out: dict = {}
    for it in items or []:
        if "=" not in it or "." not in it.split("=", 1)[0]:
            raise SystemExit(f"--opt expects detector.key=value, got {it!r}")
        lhs, v = it.split("=", 1)
        det, key = lhs.split(".", 1)
        out.setdefault(det.strip(), {})[key.strip()] = v.strip()
    return out


def main():
    ap = argparse.ArgumentParser(description="Deterministic trajectory data-audit.")
    ap.add_argument("--data", required=True, help="input JSONL")
    ap.add_argument("--field-map", required=True, help="field_map.yaml")
    ap.add_argument("--detectors", default="all", help="comma list or 'all'")
    ap.add_argument("--out", default="flags.jsonl")
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    ap.add_argument("--aggregate", action="store_true", help="write calibration report + summary")
    ap.add_argument("--only-flagged", action="store_true", help="emit only flagged rows")
    ap.add_argument("--benchmark", default="", help=f"preset: {', '.join(BENCHMARK_PRESETS)}")
    ap.add_argument("--threshold", action="append", help="name=value (repeatable)")
    ap.add_argument("--opt", action="append", help="detector.key=value (repeatable)")
    ap.add_argument("--group-by", default="", help="dotted field; with correctness enables "
                    "difficulty_saturation (per-group solve-rate ≈0/≈1 = no learning signal)")
    ap.add_argument("--sat-low", type=float, default=0.0, help="solve-rate ≤ this ⇒ always-fail")
    ap.add_argument("--sat-high", type=float, default=1.0, help="solve-rate ≥ this ⇒ always-solve")
    args = ap.parse_args()

    fmap = load_field_map(args.field_map)
    loader = RecordLoader(fmap)

    if args.detectors == "all":
        names = list(REGISTRY)
    else:
        names = [n.strip() for n in args.detectors.split(",") if n.strip()]
        unknown = [n for n in names if n not in REGISTRY]
        if unknown:
            raise SystemExit(f"unknown detectors: {unknown}; have {list(REGISTRY)}")

    thresholds = {}
    if args.benchmark:
        preset = BENCHMARK_PRESETS.get(args.benchmark.lower())
        if preset is None:
            raise SystemExit(f"unknown --benchmark {args.benchmark!r}")
        thresholds.update({k: float(v) for k, v in preset.items()})
    thresholds.update(parse_kv(args.threshold, float))
    opts = parse_opts(args.opt)

    detectors = [REGISTRY[n](**opts.get(n, {})) for n in names]

    n_samples = 0
    skipped = {n: 0 for n in names}
    scored = {n: 0 for n in names}
    flagged = {n: 0 for n in names}
    score_lists = {n: [] for n in names}
    conf_correct = []
    groups = {}  # group key -> [correct bools] for difficulty_saturation

    with open(args.out, "w") as fout:
        for idx, row in iter_rows(args.data):
            if args.limit and n_samples >= args.limit:
                break
            rec = loader.load(row, idx)
            n_samples += 1
            conf_correct.append((rec.confidence, rec.correct))
            if args.group_by and rec.correct is not None:
                gk = dig(row, args.group_by)
                if gk is not None:
                    groups.setdefault(str(gk), []).append(rec.correct)

            for det in detectors:
                res = det.run(rec)
                if res.skipped:
                    skipped[det.name] += 1
                    if not args.only_flagged:
                        fout.write(json.dumps({
                            "sample_id": rec.sample_id, "detector": det.name,
                            "skipped": True, "reason": res.reason,
                        }, ensure_ascii=False) + "\n")
                    continue
                scored[det.name] += 1
                score_lists[det.name].append(res.score)
                thr = thresholds.get(det.name, det.default_threshold)
                is_flag = det.is_flagged(res.score, thr)
                if is_flag:
                    flagged[det.name] += 1
                if is_flag or not args.only_flagged:
                    fout.write(json.dumps({
                        "sample_id": rec.sample_id, "detector": det.name,
                        "score": round(res.score, 6), "threshold": thr,
                        "flagged": is_flag, "reason": res.reason,
                        "evidence": res.evidence,
                    }, ensure_ascii=False) + "\n")

    # summary
    print(f"\naudited {n_samples} samples; flags -> {args.out}")
    print(f"{'detector':<24}{'scored':>8}{'skipped':>9}{'flagged':>9}{'rate':>8}")
    print("-" * 58)
    for n in names:
        rate = (flagged[n] / scored[n]) if scored[n] else 0.0
        print(f"{n:<24}{scored[n]:>8}{skipped[n]:>9}{flagged[n]:>9}{rate:>8.2%}")

    # difficulty_saturation (group-level; H-05) — needs --group-by + correctness
    if args.group_by:
        multi = {g: c for g, c in groups.items() if len(c) >= 2}
        sat_low = [g for g, c in multi.items() if sum(c) / len(c) <= args.sat_low]
        sat_high = [g for g, c in multi.items() if sum(c) / len(c) >= args.sat_high]
        print(f"\ndifficulty_saturation (group-by {args.group_by}):")
        print(f"  groups={len(groups)} multi-rollout={len(multi)} "
              f"always-fail(≤{args.sat_low})={len(sat_low)} always-solve(≥{args.sat_high})={len(sat_high)}")
        if not multi:
            print("  (no group has ≥2 rollouts — single-rollout SFT data can't show solve-rate)")
        with open(os.path.splitext(args.out)[0] + ".difficulty.json", "w") as f:
            json.dump({"always_fail": sat_low, "always_solve": sat_high,
                       "n_groups": len(groups), "n_multi": len(multi)}, f, ensure_ascii=False)

    if args.aggregate:
        report = aggregate(flagged, scored, n_samples, conf_correct, score_lists)
        rpath = os.path.splitext(args.out)[0] + ".calibration_report.json"
        with open(rpath, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        cal = report["calibration"]
        print(f"\ncalibration -> {rpath}")
        print(f"  accuracy={cal['accuracy']} mean_conf={cal['mean_confidence']} "
              f"ECE={cal['ece']} Brier={cal['brier']} ceiling={cal['ceiling_fraction']}")


if __name__ == "__main__":
    main()
