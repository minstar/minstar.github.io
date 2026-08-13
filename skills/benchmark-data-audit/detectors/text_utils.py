"""Deterministic text utilities shared by all detectors.

No randomness, no I/O, no LLM calls. Every function is a pure transform of its
inputs so that (text, params) -> output is reproducible across runs and machines.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable

# Keep latin letters/digits, Hangul, CJK, Hiragana/Katakana; everything else -> space.
_KEEP = re.compile(
    r"[^0-9a-zÀ-ɏ"      # latin + latin extended
    r"가-힣"             # Hangul syllables
    r"㄰-㆏"             # Hangul compatibility jamo
    r"一-鿿"             # CJK unified
    r"぀-ヿ]+",          # Hiragana + Katakana
    re.IGNORECASE,
)

# Short, language-agnostic stopwords for entity-mode matching. Intentionally tiny:
# the goal is to drop glue words, not to do real NLP.
_STOP = {
    "the", "a", "an", "of", "to", "in", "on", "at", "for", "and", "or", "is",
    "are", "was", "were", "be", "by", "with", "as", "that", "this", "it", "其",
    "은", "는", "이", "가", "을", "를", "의", "에", "와", "과", "도", "로",
}


def normalize(text: str) -> str:
    """NFKC + casefold + keep-only-word-chars + collapse whitespace.

    Korean/CJK survive; punctuation and markup become single spaces.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", str(text)).casefold()
    text = _KEEP.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text: str) -> list[str]:
    """Whitespace tokens of the normalized string."""
    n = normalize(text)
    return n.split() if n else []


def content_tokens(text: str, min_len: int = 2) -> list[str]:
    """Tokens with stopwords and very short tokens removed (for entity matching)."""
    return [t for t in tokens(text) if len(t) >= min_len and t not in _STOP]


def char_ngrams(text: str, n: int = 3) -> set[str]:
    """Set of character n-grams over the normalized, space-stripped string."""
    s = normalize(text).replace(" ", "")
    if len(s) < n:
        return {s} if s else set()
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    """Jaccard similarity of two sets. Empty/empty -> 0.0."""
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def match(answer: str, text: str, mode: str = "normalized", n: int = 3) -> float:
    """How well `answer` is contained in `text`, in [0, 1].

    - normalized: 1.0 iff normalized answer is a substring of normalized text.
    - ngram:      |ngrams(answer) ∩ ngrams(text)| / |ngrams(answer)|  (recall of
                  the answer's character n-grams). Robust to small edits/word order.
    - entity:     fraction of the answer's content tokens present in text's tokens.
    """
    if not answer or not text:
        return 0.0
    if mode == "normalized":
        na, nt = normalize(answer), normalize(text)
        if not na:
            return 0.0
        # token-boundary aware substring: pad with spaces so "us" doesn't hit "bus"
        return 1.0 if f" {na} " in f" {nt} " or na == nt else 0.0
    if mode == "ngram":
        ga = char_ngrams(answer, n)
        if not ga:
            return 0.0
        gt = char_ngrams(text, n)
        return len(ga & gt) / len(ga)
    if mode == "entity":
        ea = content_tokens(answer)
        if not ea:
            return 0.0
        et = set(content_tokens(text))
        return sum(1 for t in ea if t in et) / len(ea)
    raise ValueError(f"unknown match mode: {mode!r}")


def script_ratios(text: str) -> dict:
    """Fraction of *letter* characters in each script. Non-letters ignored.

    Returns {latin, hangul, cjk, kana, other, n_letters}. Deterministic; used by
    language_mixing to measure target-vs-foreign script contamination in CoT.
    """
    counts = {"latin": 0, "hangul": 0, "cjk": 0, "kana": 0, "other": 0}
    n = 0
    for ch in text or "":
        if not ch.isalpha():
            continue
        n += 1
        o = ord(ch)
        if ("a" <= ch.lower() <= "z") or (0x00C0 <= o <= 0x024F):
            counts["latin"] += 1
        elif 0xAC00 <= o <= 0xD7A3 or 0x3130 <= o <= 0x318F:
            counts["hangul"] += 1
        elif 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
            counts["cjk"] += 1
        elif 0x3040 <= o <= 0x30FF:
            counts["kana"] += 1
        else:
            counts["other"] += 1
    out = {k: (v / n if n else 0.0) for k, v in counts.items()}
    out["n_letters"] = n
    return out


def approx_tokens(text: str) -> int:
    """Cheap, tokenizer-free token estimate: ~4 chars/token, deterministic."""
    if not text:
        return 0
    return max(len(text) // 4, len(text.split()))
