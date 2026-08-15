#!/usr/bin/env python3
"""PreToolUse(Bash): stop irreversible commands, warn on the merely consequential ones.

Reads the hook payload on stdin (see hook_input.py for why the old $TOOL_INPUT version never fired).

TWO TIERS, deliberately — the original rule blocked `scancel`, `git reset --hard` and `rm -rf`
identically. That rule had never actually executed, so nothing revealed the problem with it: on this
cluster `scancel` is ROUTINE. There is a standing instruction to scancel a serving job the moment
its eval is done, because an idle server bills GPU-hours against nothing. A gate that blocks the
correct action every time is a gate that gets disabled within a day, and then `rm -rf` stops being
checked too.

  BLOCK (exit 2): rm -rf, git reset --hard, git clean -fd, mkfs, dd of=, > /dev/sd*
                  — irreversible, and rare enough that a prompt costs nothing.
  WARN  (exit 0): scancel — visible on stderr, does not stop the call.

PRECISION. The original matched with a bare `grep -iE '\\brm -rf\\b'`, which fires on
`grep -rn "rm -rf" .` and on any message that quotes the string — including this file's own
documentation. A guard whose findings are mostly false gets ignored, so matching here (a) removes
quoted spans first and (b) requires the token at COMMAND POSITION: start of line, or straight after
one of ; && || | & ( { or a newline.
"""
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

Q = re.compile(r"'[^']*'|\"[^\"]*\"")
# command position: start, or after a shell separator
CP = r"(?:^|[\n;&|(){}]|&&|\|\|)\s*(?:sudo\s+|nohup\s+|time\s+)*"

BLOCK = [
    (re.compile(CP + r"rm\s+(?:-[a-zA-Z]*\s+)*-?[a-zA-Z]*r[a-zA-Z]*f|" + CP + r"rm\s+(?:-[a-zA-Z]*\s+)*-?[a-zA-Z]*f[a-zA-Z]*r"),
     "rm -rf — recursive force delete"),
    (re.compile(CP + r"git\s+(?:-\S+\s+)*reset\s+(?:\S+\s+)*--hard"), "git reset --hard — discards commits/worktree"),
    (re.compile(CP + r"git\s+(?:-\S+\s+)*clean\s+(?:-\S+\s*)*-\S*f"), "git clean -f — deletes untracked files"),
    (re.compile(CP + r"mkfs(\.\w+)?\b"), "mkfs — formats a filesystem"),
    (re.compile(r"\bdd\s+[^\n]*\bof=/dev/"), "dd of=/dev/... — raw device write"),
    (re.compile(r">\s*/dev/sd[a-z]"), "redirect to a raw block device"),
]

WARN = [
    (re.compile(CP + r"scancel\b"), "scancel — cancels Slurm jobs; confirm the job ids are yours and finished"),
]


def strip_quoted(s):
    """Blank out quoted spans so a *mention* of a dangerous command is not a *use* of one."""
    return Q.sub(lambda m: " " * len(m.group(0)), s)


def main():
    raw = sys.stdin.read()
    try:
        import json
        d = json.loads(raw)
        ti = d.get("tool_input")
        cmd = (ti.get("command") or ti.get("cmd") or "") if isinstance(ti, dict) else (ti or "")
    except Exception:
        return 0                      # unparseable payload -> allow; never take the call down
    if not cmd:
        return 0

    probe = strip_quoted(str(cmd))

    hits = [why for rx, why in BLOCK if rx.search(probe)]
    if hits:
        sys.stderr.write("⛔ harness-guard: irreversible command blocked — %s\n" % hits[0])
        for h in hits[1:]:
            sys.stderr.write("   also: %s\n" % h)
        sys.stderr.write("   command: %s\n" % str(cmd)[:300])
        sys.stderr.write("   If this is intended, say so explicitly and it can be run deliberately.\n")
        return 2

    warns = [why for rx, why in WARN if rx.search(probe)]
    for w in warns:
        sys.stderr.write("⚠️  harness-guard: %s\n" % w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
