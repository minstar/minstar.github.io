#!/usr/bin/env python3
"""Extract a field from a Claude Code hook payload on stdin.

Hooks receive JSON on STDIN — {hook_event_name, tool_name, tool_input, tool_use_id, and on
PostToolUse a tool_response} — and NO $TOOL_INPUT / $TOOL_OUTPUT environment variables. Every hook
in this settings.json was written against those env vars, so all three were inert from the day they
were installed until 2026-08-15: the shell expanded them to the empty string, the guard's grep
never matched, and the hook exited 0 having done nothing. An inert gate is indistinguishable from a
passing one, which is why this was found by an audit rather than by a failure.

One extractor, used by every hook, so the payload shape is understood in exactly one place.

    cmd=$(python3 hook_input.py command  <<< "$PAYLOAD")   # the Bash command about to run / just ran
    out=$(python3 hook_input.py output   <<< "$PAYLOAD")   # PostToolUse: what it printed

Prints an empty string and exits 0 on anything it cannot parse. A hook that dies on an unexpected
payload takes the tool call with it; failing open is the only safe default here.
"""
import json
import sys


def _text(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        for k in ("stdout", "output", "content", "text", "result", "stderr"):
            if isinstance(v.get(k), str) and v[k]:
                return v[k]
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "\n".join(_text(x) for x in v)
    return str(v)


def main():
    field = sys.argv[1] if len(sys.argv) > 1 else "command"
    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(d, dict):
        return 0

    if field == "command":
        ti = d.get("tool_input")
        if isinstance(ti, dict):
            sys.stdout.write(str(ti.get("command") or ti.get("cmd") or ""))
        elif isinstance(ti, str):
            sys.stdout.write(ti)
    elif field == "output":
        for k in ("tool_response", "tool_output", "response", "output"):
            if k in d:
                sys.stdout.write(_text(d[k]))
                break
    elif field == "tool":
        sys.stdout.write(str(d.get("tool_name") or ""))
    else:
        sys.stdout.write(_text(d.get(field)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
