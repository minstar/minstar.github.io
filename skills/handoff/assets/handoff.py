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

# Matched against HEADING TEXT, not against the whole document.
#
# The first version matched free prose anywhere in the file, and both directions were wrong:
#   - it MISSED a finished doc. "what I changed" accepted only `건드리지` among Korean phrasings,
#     so a doc that said "아무것도 바꾸지 않았습니다" — the same statement, different verb — failed.
#   - it PASSED a doc with no sections at all. `blast radius` accepted the bare word "scope" or
#     "affected"; `what to fix` accepted "수정"; `evidence` accepted "evidence". Any handover-shaped
#     prose satisfies six of seven rules by accident, so the gate was very nearly non-binding.
# A checker that validates vocabulary cannot enforce structure. These match the heading line.
# (name, heading pattern, alternative that also satisfies it anywhere in the doc)
#
# The heading patterns accept synonyms rather than one canonical title, because a heading that names
# the specific consequence — "Why this breaks comparisons: the artifact rate is arm-dependent" — is
# better writing than "Blast radius" and must not be failed for it. What is NOT accepted is the same
# word buried in a paragraph: the requirement is that a receiver scanning headings finds it.
#
# "what I changed" additionally accepts a bolded standalone declaration, because that is the form the
# statement actually takes in practice and it is just as findable. Plain prose does not count.
REQUIRED = [
    ("symptom",       r"^(symptom|증상|observed|what'?s wrong)", None),
    ("root cause",    r"^(root\s*cause|원인|why (it|this) (happens|fails)|mechanism)", None),
    ("blast radius",  r"^(blast\s*radius|영향|범위|scope|impact|what else|why this (breaks|affects)"
                      r"|affected)", None),
    ("evidence",      r"^(evidence|provenance|근거|출처|how i know)", None),
    ("what to fix",   r"^(what\s*to\s*fix|수정|fix\b|remediation|repair)", None),
    ("how to verify", r"^(how\s*to\s*verify|검증|verification|verify\b)", None),
    ("what I changed", r"^(what\s*i\s*changed|무엇을\s*바꿨|바꾼\s*것|내가\s*바꾼|변경\s*사항"
                       r"|changes? i made)",
     r"^\*\*[^*\n]*(nothing[^*\n]*chang|chang[^*\n]*by me|아무것도[^*\n]*(바꾸|고치)"
     r"|건드리(지|시)|analysis only)[^*\n]*\*\*"),
]

# A heading with nothing under it is not a section. 30 chars is below any real answer to these
# questions and above an accidental blank-with-a-link.
MIN_BODY = 30


def sections(text):
    """[(heading_text, body)] for ATX headings. Fences are skipped so `# comment` lines in a shell
    block are not read as headings — the docs here all carry reproduction commands."""
    out, cur, buf, fence = [], None, [], False
    for ln in text.splitlines():
        if re.match(r"^\s*(```|~~~)", ln):
            fence = not fence
        m = None if fence else re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", ln)
        if m:
            if cur is not None:
                out.append((cur, "\n".join(buf)))
            cur, buf = m.group(1), []
        else:
            buf.append(ln)
    if cur is not None:
        out.append((cur, "\n".join(buf)))
    return out


def section_status(text):
    """(missing, thin) by required-section name."""
    secs = sections(text)
    missing, thin = [], []
    for name, rx, alt in REQUIRED:
        body = next((b for h, b in secs if re.search(rx, h.strip(), re.I)), None)
        if body is None:
            if alt and re.search(alt, text, re.I | re.M):
                continue
            missing.append(name)
        elif len(re.sub(r"\s+", " ", body).strip()) < MIN_BODY:
            thin.append(name)
    return missing, thin

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
    missing, thin = section_status(text)
    # Only PROSE placeholders count. Two classes of angle-bracket look like template slots but are
    # not, and flagging either taught a finished document to read as unfinished:
    #   - content, e.g. `<tool_call>` / `<function=think>` — no spaces, so the space test drops it;
    #   - usage syntax inside code, e.g. `--a <baseline file>` — real, and the reader IS meant to
    #     substitute it, so strip code fences and inline spans before scanning.
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    prose = re.sub(r"`[^`\n]*`", "", prose)
    placeholders = [m for m in re.findall(r"<[a-z][^>\n]{9,}>", prose) if " " in m]

    print("checking %s (%d chars)" % (a.doc, len(text)))
    for name, _rx, _alt in REQUIRED:
        mark = "MISS" if name in missing else ("thin" if name in thin else "ok  ")
        print("  [%s] %s" % (mark, name))
    if placeholders:
        print("\n  %d unfilled placeholder(s): %s"
              % (len(placeholders), ", ".join(p[:40] for p in placeholders[:4])))
    if missing or thin or placeholders:
        print("\nNot ready to hand over.")
        if missing:
            print("  missing sections: %s" % ", ".join(missing))
        if thin:
            print("  heading present but nothing under it: %s" % ", ".join(thin))
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
