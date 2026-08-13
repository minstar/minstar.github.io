"""Detector base class and the per-(sample, detector) result row.

Contract every detector obeys:
  * reads ONLY from a Record (stays schema-agnostic),
  * makes NO LLM / network calls (stays deterministic),
  * returns `score` = the raw formula value (never thresholded),
  * returns `skipped=True` when a required field is missing — NEVER a wrong flag.
The CLI applies the threshold to produce `flagged`. Keep them separate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from record import Record


@dataclass
class Result:
    detector: str
    score: Optional[float]            # raw formula value; None iff skipped
    skipped: bool = False
    reason: str = ""                  # human-readable explanation
    evidence: dict = field(default_factory=dict)  # supporting numbers/snippets


class Detector:
    name: str = "base"
    # if True, higher score = more suspicious -> flag when score > threshold.
    # if False, lower score = more suspicious -> flag when score < threshold.
    higher_is_worse: bool = True
    default_threshold: float = 0.5

    def __init__(self, **opts: Any):
        self.opts = opts

    def opt(self, key: str, default: Any) -> Any:
        v = self.opts.get(key, default)
        # CLI passes everything as strings; coerce to the default's type.
        if isinstance(default, bool) and isinstance(v, str):
            return v.strip().lower() in {"1", "true", "yes"}
        if isinstance(default, int) and not isinstance(default, bool) and isinstance(v, str):
            return int(v)
        if isinstance(default, float) and isinstance(v, str):
            return float(v)
        return v

    def run(self, rec: Record) -> Result:  # pragma: no cover - abstract
        raise NotImplementedError

    # helpers for subclasses
    def skip(self, reason: str) -> Result:
        return Result(self.name, None, skipped=True, reason=reason)

    def emit(self, score: float, reason: str = "", **evidence: Any) -> Result:
        return Result(self.name, float(score), reason=reason, evidence=evidence)

    def is_flagged(self, score: float, threshold: float) -> bool:
        return score > threshold if self.higher_is_worse else score < threshold
