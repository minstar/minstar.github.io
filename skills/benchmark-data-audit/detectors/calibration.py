"""Dataset-level calibration + flag-rate report (deterministic).

Per-sample detectors answer "is THIS row risky?"; this answers "is the DATASET
mis-calibrated / how often does each detector fire?". Written to
calibration_report.json by run_audit.py --aggregate.
"""
from __future__ import annotations

from statistics import mean, median
from typing import Optional


def _percentiles(xs: list[float], ps=(50, 75, 90, 95, 99)) -> dict:
    if not xs:
        return {f"p{p}": None for p in ps}
    s = sorted(xs)
    out = {}
    for p in ps:
        # nearest-rank, deterministic
        k = max(0, min(len(s) - 1, int(round((p / 100) * (len(s) - 1)))))
        out[f"p{p}"] = round(s[k], 4)
    return out


def calibration(conf_correct: list[tuple[float, Optional[bool]]], n_bins: int = 10) -> dict:
    """ECE, Brier, ceiling fraction over (confidence, correct) pairs.

    Only pairs where both confidence and correctness are known contribute to
    ECE/Brier. ceiling_fraction uses all pairs with a confidence value.
    """
    have_conf = [(c, y) for c, y in conf_correct if c is not None]
    labelled = [(c, y) for c, y in have_conf if y is not None]
    out: dict = {
        "n_with_confidence": len(have_conf),
        "n_labelled": len(labelled),
        "mean_confidence": round(mean([c for c, _ in have_conf]), 4) if have_conf else None,
        "ceiling_fraction": (round(sum(1 for c, _ in have_conf if c >= 0.99) / len(have_conf), 4)
                             if have_conf else None),
    }
    if not labelled:
        out.update(accuracy=None, ece=None, brier=None, bins=[])
        return out
    acc = mean([1.0 if y else 0.0 for _, y in labelled])
    brier = mean([(c - (1.0 if y else 0.0)) ** 2 for c, y in labelled])
    # ECE over equal-width bins
    bins = [[] for _ in range(n_bins)]
    for c, y in labelled:
        idx = min(n_bins - 1, int(c * n_bins))
        bins[idx].append((c, 1.0 if y else 0.0))
    ece = 0.0
    bin_rows = []
    n = len(labelled)
    for i, b in enumerate(bins):
        if not b:
            continue
        conf_b = mean([c for c, _ in b])
        acc_b = mean([y for _, y in b])
        gap = abs(acc_b - conf_b)
        ece += (len(b) / n) * gap
        bin_rows.append({
            "bin": f"[{i/n_bins:.1f},{(i+1)/n_bins:.1f})",
            "n": len(b), "avg_conf": round(conf_b, 4),
            "accuracy": round(acc_b, 4), "gap": round(gap, 4),
        })
    out.update(accuracy=round(acc, 4), ece=round(ece, 4), brier=round(brier, 4), bins=bin_rows)
    return out


def aggregate(results_by_detector: dict, scored_counts: dict, n_samples: int,
              conf_correct: list, score_lists: dict) -> dict:
    """Assemble the full report.

    results_by_detector: name -> #flagged
    scored_counts:       name -> #scored (not skipped)
    score_lists:         name -> list[float] of raw scores (for distributions)
    """
    flag_table = {}
    for name, scored in scored_counts.items():
        flagged = results_by_detector.get(name, 0)
        flag_table[name] = {
            "scored": scored,
            "skipped": n_samples - scored,
            "flagged": flagged,
            "flag_rate": round(flagged / scored, 4) if scored else None,
            "score_distribution": _percentiles(score_lists.get(name, [])),
            "score_median": round(median(score_lists[name]), 4) if score_lists.get(name) else None,
        }
    return {
        "n_samples": n_samples,
        "calibration": calibration(conf_correct),
        "detectors": flag_table,
    }
