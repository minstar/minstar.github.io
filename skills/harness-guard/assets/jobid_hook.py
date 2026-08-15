#!/usr/bin/env python3
"""PostToolUse(Bash): after an sbatch, print the tracking command for the job it created.

Reads the hook payload on stdin. The previous version read $TOOL_INPUT / $TOOL_OUTPUT, which Claude
Code does not set, so it never printed anything (see hook_input.py).

Purely informational — always exits 0.
"""
import json
import re
import sys

SUBMITTED = re.compile(r"Submitted batch job (\d+)")


def text(v):
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return "\n".join(str(v.get(k, "")) for k in ("stdout", "stderr", "output", "content", "result"))
    if isinstance(v, list):
        return "\n".join(text(x) for x in v)
    return "" if v is None else str(v)


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0
    ti = d.get("tool_input")
    cmd = (ti.get("command") or "") if isinstance(ti, dict) else (ti or "")
    if "sbatch" not in str(cmd):
        return 0

    out = ""
    for k in ("tool_response", "tool_output", "response", "output"):
        if k in d:
            out = text(d[k])
            break

    ids = SUBMITTED.findall(out)
    if not ids:
        return 0
    j = ",".join(ids)
    print("[hook] submitted %s. Track: sacct -j %s --format=JobID,JobName%%60,State,Elapsed"
          % (("job " + ids[0]) if len(ids) == 1 else ("%d jobs" % len(ids)), j))
    return 0


if __name__ == "__main__":
    sys.exit(main())
