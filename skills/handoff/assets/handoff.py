#!/usr/bin/env python3
"""Hand work to another session without losing it to a bad address.

Two failures on 2026-08-14 produced this. Work meant for the session labelled `<health-rl-run>-rebuttal` went
to three unrelated sessions, because the name on the tmux window is NOT the name SendMessage
resolves — and the session that carries a work-shaped name is often an old one that never registered
as an addressable peer at all. The one that mattered had a 43-day-old shell.

So the rule this encodes: **the document is the handoff; the message is only a pointer.** A doc in
the target repo survives a wrong address, a dead session, and a context compaction. A message does
none of those things.

    python3 handoff.py targets                     # addressable peers vs tmux windows, side by side
    python3 handoff.py new <slug> --dir <repo>     # scaffold a handoff doc
    python3 handoff.py check <doc.md>              # does the doc carry what a receiver needs?

Exit 0 = fine. Exit 1 = something is missing or unaddressable. Exit 2 = bad invocation.
"""
import argparse
import os
import re
import subprocess
import sys

REQUIRED = [
    ("symptom", r"##\s*Symptom|^\*\*Symptom|증상"),
    ("evidence", r"provenance|Provenance|evidence|Evidence|근거|출처"),
    ("root cause", r"[Rr]oot cause|원인"),
    ("blast radius", r"[Bb]last radius|scope|Scope|범위|affected"),
    ("what to fix", r"[Ww]hat to fix|수정|[Nn]ext steps|fix \(in order\)"),
    ("how to verify", r"[Hh]ow to verify|검증|[Vv]erify a fix"),
    ("what I changed", r"[Nn]othing .* changed|changed by me|건드리지|Analysis only|analysis only"),
]

TEMPLATE = """# HANDOFF — {title}

**Found**: {date}
**Status**: diagnosed, not fixed. / in progress — see below.
**Why it matters**: <the decision this blocks, and any deadline>

---

## Symptom

<what is observably wrong, with the actual numbers/commands — not a description of the description>

## Root cause

<the mechanism. If there are layers, number them: each layer should change the conclusion of the
one above it, otherwise it is detail rather than a layer.>

## Blast radius

<what else is affected. This is the section receivers skip writing and most need to read.>

## Evidence / provenance

<file paths and the exact command that produced each number. A number without this is not
admissible — the receiver cannot check your work, and will not trust it.>

## What to fix (in order)

1. <the change that removes the cause, not the symptom>
2. ...

## How to verify a fix

```bash
<a command the receiver can run to see the problem, and see it gone>
```

## What I changed

**Nothing** — analysis only. / <exact list of files touched>

<State this explicitly. A receiver's first question is whether their working tree moved under them.>
"""


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ""


def tmux_windows():
    out = sh("tmux list-panes -a -F '#{pane_id}\t#{window_name}\t#{pane_current_command}\t#{pane_current_path}'")
    rows = []
    for ln in out.splitlines():
        f = ln.split("\t")
        if len(f) >= 4 and f[2].strip() in ("claude", "node"):
            rows.append({"pane": f[0], "name": f[1], "cmd": f[2], "cwd": f[3]})
    return rows


def cmd_targets(a):
    wins = tmux_windows()
    print("tmux windows running an agent (%d):" % len(wins))
    for w in wins:
        print("  %-6s %-28s %s" % (w["pane"], w["name"][:28], w["cwd"]))

    print("\nAddressable peers: run ListAgents in your session — this script cannot see them.")
    print("""
Then compare the two lists by hand, because they are different namespaces:

  * A tmux window name is a LABEL. It is what you see and what you will be told to use.
  * An addressable peer name is what SendMessage resolves. Only that one can receive a message.

The trap: a window carrying a work-shaped name (`<health-rl-run>-rebuttal`, `<rl-run>-paper`) is usually an
OLD session, and older sessions are the ones missing from the peer list. The generically-named
`claude` windows are the ones that register. So the more a window looks like the right target, the
more likely it cannot be messaged.

If the target is not in the peer list:
  1. Write the handoff doc anyway (`handoff.py new`) — that is the real delivery.
  2. Ask the user to paste a pointer into that window. Do NOT `tmux send-keys` into a live
     interactive session: text already typed at its prompt will be mangled by the injection.""")
    return 0


def cmd_new(a):
    d = os.path.abspath(a.dir)
    if not os.path.isdir(d):
        print("handoff: no such directory: %s" % d, file=sys.stderr)
        return 2
    date = a.date or sh("date +%Y-%m-%d").strip()
    slug = re.sub(r"[^a-z0-9_]+", "_", a.slug.lower()).strip("_")
    path = os.path.join(d, "HANDOFF_%s_%s.md" % (slug, date.replace("-", "")))
    if os.path.exists(path) and not a.force:
        print("handoff: %s already exists (use --force to overwrite)" % path, file=sys.stderr)
        return 2
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(TEMPLATE.format(title=a.title or a.slug.replace("_", " "), date=date))
    print("wrote %s" % path)
    print("\nFill it in, then hand the receiver ONE line: the path plus why it is urgent.")
    print("Keep the doc in the TARGET repo, not yours — the receiver finds it by working there.")
    return 0


def cmd_check(a):
    if not os.path.exists(a.doc):
        print("handoff: no such file: %s" % a.doc, file=sys.stderr)
        return 2
    text = open(a.doc, encoding="utf-8", errors="replace").read()
    missing = [name for name, rx in REQUIRED if not re.search(rx, text)]
    # Only PROSE placeholders count. Two classes of angle-bracket look like template slots but are
    # not, and flagging either taught a finished document to read as unfinished:
    #   - content, e.g. `<tool_call>` / `<function=think>` — no spaces, so the space test drops it;
    #   - usage syntax inside code, e.g. `--a <baseline file>` — real, and the reader IS meant to
    #     substitute it, so strip code fences and inline spans before scanning.
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    prose = re.sub(r"`[^`\n]*`", "", prose)
    placeholders = [m for m in re.findall(r"<[a-z][^>\n]{9,}>", prose) if " " in m]

    print("checking %s (%d chars)" % (a.doc, len(text)))
    for name, rx in REQUIRED:
        print("  [%s] %s" % ("ok  " if re.search(rx, text) else "MISS", name))
    if placeholders:
        print("\n  %d unfilled placeholder(s): %s"
              % (len(placeholders), ", ".join(p[:40] for p in placeholders[:4])))
    if missing or placeholders:
        print("\nNot ready to hand over.")
        if missing:
            print("  missing sections: %s" % ", ".join(missing))
        if placeholders:
            print("  the template is still showing through — a receiver reads that as 'not my problem yet'")
        return 1
    print("\nReady. Deliver the path, not the contents — and say what decision it blocks.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Hand work to another session, durably.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("targets", help="tmux windows vs addressable peers")
    t.set_defaults(fn=cmd_targets)

    n = sub.add_parser("new", help="scaffold a handoff doc in the target repo")
    n.add_argument("slug")
    n.add_argument("--dir", required=True, help="the TARGET repo, not yours")
    n.add_argument("--title", default="")
    n.add_argument("--date", default="")
    n.add_argument("--force", action="store_true")
    n.set_defaults(fn=cmd_new)

    c = sub.add_parser("check", help="is the doc complete enough to hand over?")
    c.add_argument("doc")
    c.set_defaults(fn=cmd_check)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
