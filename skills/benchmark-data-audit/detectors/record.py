"""Normalized trajectory record + a loader that maps a custom JSONL row onto it.

A `Record` is the ONLY thing detectors read. Map your dataset once in
field_map.yaml; every detector then works unchanged. See schemas/schema.md.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

# Markers that introduce a concise final answer; tried in order.
_ANSWER_MARKERS = [
    r"(?:\*\*)?\s*answer\s*(?:\*\*)?\s*[:：]\s*(.+)",
    r"(?:\*\*)?\s*final answer\s*(?:\*\*)?\s*[:：]\s*(.+)",
    r"정답\s*[:：]\s*(.+)",
    r"답\s*[:：]\s*(.+)",
]
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CITE = re.compile(r"【[^】]*】")


def extract_answer(content: str, cfg: Optional[dict] = None) -> str:
    """Pull a concise answer span out of a long final message.

    Order: explicit "Answer:"/"정답:" marker -> last **bolded** span -> full text.
    Citation markers (【..】) are stripped. answer_in_cot/unsupported_correct are
    only reliable on a CONCISE answer; a full restated paragraph echoes the
    question and produces false matches.
    """
    if not content:
        return ""
    cfg = cfg or {}
    text = _CITE.sub(" ", content)
    if cfg.get("regex"):
        m = re.search(cfg["regex"], text, re.IGNORECASE | re.DOTALL)
        if m:
            return _BOLD.sub(r"\1", m.group(1)).strip(" .*\n")
    for pat in _ANSWER_MARKERS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            # keep only the first line of the captured span
            span = m.group(1).splitlines()[0]
            return _BOLD.sub(r"\1", span).strip(" .*\n")
    if cfg.get("prefer_bold", True):
        bolds = _BOLD.findall(text)
        if bolds:
            return bolds[-1].strip(" .*\n")
    return text.strip()


# --------------------------------------------------------------------------- #
# dotted-path access into arbitrary nested dict/list, with JSON-string parsing #
# --------------------------------------------------------------------------- #
def dig(obj: Any, path: Optional[str]) -> Any:
    """Resolve a dotted path like 'a.b.0.c' against nested dict/list.

    Each hop: if the current value is a JSON string it is parsed first, so
    function.arguments (often a JSON string) resolves transparently. Returns
    None on any miss instead of raising.
    """
    if path is None or path == "":
        return obj
    cur = obj
    for key in path.split("."):
        if isinstance(cur, str):
            try:
                cur = json.loads(cur)
            except (ValueError, TypeError):
                return None
        if isinstance(cur, dict):
            cur = cur.get(key)
        elif isinstance(cur, list):
            try:
                cur = cur[int(key)]
            except (ValueError, IndexError):
                return None
        else:
            return None
        if cur is None:
            return None
    return cur


def _as_text(v: Any) -> str:
    """Coerce a value to text. Lists of {text/content} parts are concatenated."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        out = []
        for item in v:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                out.append(str(item.get("text") or item.get("content") or ""))
        return "\n".join(p for p in out if p)
    if isinstance(v, dict):
        return str(v.get("text") or v.get("content") or "")
    return str(v)


@dataclass
class Step:
    index: int
    role: str                          # assistant | tool | user | system
    text: str = ""                     # reasoning/content emitted at this step
    tool_name: Optional[str] = None
    tool_category: Optional[str] = None  # search | open | find | other
    tool_query: Optional[str] = None     # the query/arg string of the call
    tool_args: Any = None                # parsed argument object (dict) when available
    tool_response: Optional[str] = None  # the observation returned to the model


@dataclass
class Record:
    sample_id: str
    question: str = ""
    gold_answer: Optional[str] = None
    pred_answer: Optional[str] = None
    correct: Optional[bool] = None
    confidence: Optional[float] = None   # normalized to [0, 1]
    reasoning: str = ""                  # full concatenated CoT (assistant text)
    final_answer_raw: str = ""           # last assistant content, UNstripped (citations intact)
    steps: list[Step] = field(default_factory=list)
    tool_registry: dict = field(default_factory=dict)  # exposed tool_name -> param schema
    state_assertions: dict = field(default_factory=dict)  # gold CRUD spec (expected/allowed/outputs)
    raw: dict = field(default_factory=dict)

    # ---- convenience views used by detectors ---------------------------- #
    def tool_steps(self) -> list[Step]:
        return [s for s in self.steps if s.tool_name]

    def by_category(self, cat: str) -> list[Step]:
        return [s for s in self.steps if s.tool_category == cat]

    def queries(self, cat: str = "search") -> list[str]:
        return [s.tool_query for s in self.by_category(cat) if s.tool_query]

    def tool_responses(self) -> list[str]:
        return [s.tool_response for s in self.steps if s.tool_response]

    def reasoning_segments(self) -> list[str]:
        """Assistant text in order; index aligns with self.steps positions."""
        return [s.text for s in self.steps if s.role == "assistant" and s.text]


# --------------------------------------------------------------------------- #
#                                  loader                                      #
# --------------------------------------------------------------------------- #
class RecordLoader:
    """Builds Record objects from raw JSONL rows using a field_map dict."""

    def __init__(self, fmap: dict):
        self.fmap = fmap or {}
        self.taxonomy = self.fmap.get("taxonomy", {}) or {}

    def categorize(self, tool_name: Optional[str]) -> Optional[str]:
        if not tool_name:
            return None
        name = str(tool_name).casefold()
        for cat, patterns in self.taxonomy.items():
            for p in patterns or []:
                if re.search(str(p).casefold(), name):
                    return cat
        return "other"

    # -- scalar fields ---------------------------------------------------- #
    def _confidence(self, row: dict) -> Optional[float]:
        spec = self.fmap.get("confidence")
        if spec is None:
            return None
        if isinstance(spec, str):
            path, scale = spec, 1.0
        else:
            path, scale = spec.get("path"), float(spec.get("scale", 1) or 1)
        v = dig(row, path)
        if v is None:
            return None
        try:
            c = float(v) / scale
        except (ValueError, TypeError):
            return None
        return max(0.0, min(1.0, c))

    def _correct(self, row: dict, gold: Optional[str], pred: Optional[str]) -> Optional[bool]:
        path = self.fmap.get("correct")
        if path:
            v = dig(row, path)
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float)):
                return bool(v)
            if isinstance(v, str):
                if v.strip().lower() in {"true", "1", "yes", "correct"}:
                    return True
                if v.strip().lower() in {"false", "0", "no", "incorrect", "wrong"}:
                    return False
        # fall back to exact normalized gold==pred only if both present
        if gold and pred:
            from text_utils import normalize
            return normalize(gold) == normalize(pred)
        return None

    # -- steps ------------------------------------------------------------ #
    def _steps_from_messages(self, row: dict) -> list[Step]:
        spec = self.fmap["messages"]
        msgs = dig(row, spec.get("path", "messages")) or []
        role_f = spec.get("role_field", "role")
        content_f = spec.get("content_field", "content")
        asst = set(spec.get("assistant_roles", ["assistant"]))
        tool_roles = set(spec.get("tool_roles", ["tool", "function"]))
        tc_field = spec.get("tool_calls_field", "tool_calls")
        name_path = spec.get("tool_name_path", "function.name")
        args_path = spec.get("tool_args_path", "function.arguments")
        query_field = spec.get("query_field")  # dotted path *within* parsed args
        reasoning_f = spec.get("reasoning_field")  # assistant CoT separate from content
        steps: list[Step] = []
        final_answer = ""
        i = 0
        for m in msgs:
            if not isinstance(m, dict):
                continue
            role = str(m.get(role_f, ""))
            content = _as_text(m.get(content_f))
            if role in tool_roles:
                steps.append(Step(index=i, role="tool", tool_response=content))
                i += 1
                continue
            if role in asst:
                # CoT to scan = reasoning field if present, else the content
                cot = _as_text(m.get(reasoning_f)) if reasoning_f else ""
                text = cot or content
                # a non-empty content on an assistant turn is a (possibly final) answer
                if content:
                    final_answer = content
                tcs = m.get(tc_field) or []
                if not isinstance(tcs, list):
                    tcs = [tcs]
                if tcs:
                    for tc in tcs:
                        name = dig(tc, name_path)
                        args = dig(tc, args_path)
                        if isinstance(args, str):  # function.arguments is usually a JSON string
                            try:
                                args = json.loads(args)
                            except (ValueError, TypeError):
                                pass
                        q = dig(args, query_field) if query_field else None
                        if q is None:
                            q = _as_text(args) or None
                        steps.append(
                            Step(
                                index=i,
                                role="assistant",
                                text=text,
                                tool_name=str(name) if name else None,
                                tool_category=self.categorize(name),
                                tool_query=str(q) if q else None,
                                tool_args=args if isinstance(args, dict) else None,
                            )
                        )
                        i += 1
                        text = ""  # attach reasoning text only to first call
                else:
                    steps.append(Step(index=i, role="assistant", text=text))
                    i += 1
            else:  # user/system
                steps.append(Step(index=i, role=role or "user", text=content))
                i += 1
        self._last_final_answer = final_answer
        return steps

    def _steps_from_tools(self, row: dict) -> list[Step]:
        spec = self.fmap["tools"]
        calls = dig(row, spec.get("path", "tool_calls")) or []
        name_f = spec.get("name_field", "name")
        query_f = spec.get("query_field", "query")
        resp_f = spec.get("response_field", "response")
        reason_f = spec.get("reasoning_field")  # optional per-call reasoning
        steps: list[Step] = []
        for i, c in enumerate(calls):
            if not isinstance(c, dict):
                continue
            name = dig(c, name_f)
            steps.append(
                Step(
                    index=i,
                    role="assistant",
                    text=_as_text(dig(c, reason_f)) if reason_f else "",
                    tool_name=str(name) if name else None,
                    tool_category=self.categorize(name),
                    tool_query=(lambda q: str(q) if q else None)(dig(c, query_f)),
                    tool_response=_as_text(dig(c, resp_f)) or None,
                )
            )
        return steps

    def _tool_registry(self, row: dict) -> dict:
        """Map exposed tool name -> its JSON parameter schema, from field_map.tool_registry.
        Lets fabricated/hallucinated-tool-name and malformed-arg checks ground against
        the env's actual tool surface (the open2_official `tools` column)."""
        spec = self.fmap.get("tool_registry")
        if not spec:
            return {}
        raw = dig(row, spec.get("path", "tools"))
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (ValueError, TypeError):
                return {}
        if not isinstance(raw, list):
            return {}
        name_path = spec.get("name_path", "function.name")
        params_path = spec.get("params_path", "function.parameters")
        reg = {}
        for item in raw:
            name = dig(item, name_path)
            if name:
                reg[str(name)] = dig(item, params_path) or {}
        return reg

    def _state_assertions(self, row: dict) -> dict:
        """Gold CRUD spec for crud_state_assertion, from field_map.state_assertions.
        Mirrors the deterministic, trajectory-checkable slice of τ-bench/τ²/BFCL/AppWorld:
        expected write actions (action-matching), an allowed-write allowlist (collateral),
        and required output strings (τ r_output / τ² COMMUNICATE). See
        references/mcp_state_verification.md. Absent on gold-less SFT data -> {}."""
        spec = self.fmap.get("state_assertions")
        if not spec:
            return {}
        base = dig(row, spec.get("path")) if spec.get("path") else row
        if not isinstance(base, (dict, list)):
            return {}
        def _list(key, default):
            v = dig(base, spec.get(key, default))
            if isinstance(v, str):
                try:
                    v = json.loads(v)
                except (ValueError, TypeError):
                    return []
            return v if isinstance(v, list) else []
        out = {
            "expected_actions": _list("expected_actions_field", "expected_actions"),
            "allowed_actions": _list("allowed_actions_field", "allowed_actions"),
            "required_outputs": _list("required_outputs_field", "required_outputs"),
        }
        return out if any(out.values()) else {}

    def load(self, row: dict, idx: int) -> Record:
        gold = _as_text(dig(row, self.fmap.get("gold_answer"))) or None
        pred = _as_text(dig(row, self.fmap.get("pred_answer"))) or None
        sid_path = self.fmap.get("sample_id")
        sid = dig(row, sid_path) if sid_path else None  # don't dig(None)->whole row
        sid = str(sid) if sid is not None else f"row{idx}"

        self._last_final_answer = ""
        if "messages" in self.fmap:
            steps = self._steps_from_messages(row)
        elif "tools" in self.fmap:
            steps = self._steps_from_tools(row)
        else:
            steps = []

        # messages mode: if no explicit pred_answer path, use the last assistant
        # content (the trajectory's own final answer) — needed for SFT data that
        # has no separate answer column. Reduce it to a concise span so that
        # answer-matching detectors don't fire on the restated question.
        if not pred and "messages" in self.fmap and self._last_final_answer:
            pred = extract_answer(self._last_final_answer, self.fmap.get("answer_extract"))

        # reasoning: explicit path wins; else concat assistant text
        reasoning = ""
        rspec = self.fmap.get("reasoning")
        if rspec:
            rpath = rspec if isinstance(rspec, str) else rspec.get("path")
            reasoning = _as_text(dig(row, rpath))
        if not reasoning:
            reasoning = "\n".join(s.text for s in steps if s.role == "assistant" and s.text)

        return Record(
            sample_id=sid,
            question=_as_text(dig(row, self.fmap.get("question"))),
            gold_answer=gold,
            pred_answer=pred,
            correct=self._correct(row, gold, pred),
            confidence=self._confidence(row),
            reasoning=reasoning,
            final_answer_raw=self._last_final_answer or (pred or ""),
            steps=steps,
            tool_registry=self._tool_registry(row),
            state_assertions=self._state_assertions(row),
            raw=row,
        )
