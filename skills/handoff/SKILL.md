---
name: handoff
description: >-
  Transfer work to another session so it survives a wrong address, a dead session, or a context
  compaction — by writing a handoff document into the TARGET repo and sending only a pointer.
  Includes an addressability check, because the name on a tmux window is not the name SendMessage
  resolves and the session carrying a work-shaped name is often the one that cannot be messaged.
  Use when work will continue in another session, when handing a diagnosis to whoever owns the code,
  or when a session is about to end with something unfinished.
  Triggers - "/handoff", "다른 세션에 넘겨", "인계", "넘겨줘", "이어서 진행", "세션 인계",
  "hand off", "누구한테 넘기지".
trigger: /handoff
---

# /handoff — the document is the handoff, the message is a pointer

On 2026-08-14 a diagnosis meant for the session labelled `<health-rl-run>-rebuttal` went to three unrelated
sessions. The name on the tmux window is a **label**; the name `SendMessage` resolves is an
**address**; they are different namespaces and that day they had an empty intersection. The target
had a 43-day-old shell and had never registered as a peer at all.

The recovery was that the writeup was already sitting in the target repo. That is the rule:

> **A document in the target repo survives a wrong address, a dead session, and a compaction.
> A message survives none of them.**

Checker: `assets/handoff.py`.

## Usage

```
python3 ~/.claude/skills/handoff/assets/handoff.py targets              # who can actually be reached
python3 ~/.claude/skills/handoff/assets/handoff.py new <slug> --dir <TARGET repo>
python3 ~/.claude/skills/handoff/assets/handoff.py check <doc.md>       # is it handover-ready?
```

Exit `0` fine · `1` incomplete/unaddressable · `2` bad invocation.

## Process

1. **Write the doc first, into the target's repo** — not yours. The receiver finds it by working
   there; that is the whole point. `new` scaffolds it.
2. **Fill it in**, then `check` it. It is not ready while template prose is still showing.
3. **Resolve the address** with `targets` plus `ListAgents` in your session. Only a name that
   appears in `ListAgents` can receive a message.
4. **Send a pointer, not the contents** — the path, plus what decision it blocks and by when. If the
   target is not addressable, ask the user to paste the pointer; do not guess.

## Addressing: the trap, stated plainly

- A **tmux window name** (`<health-rl-run>-rebuttal`, `<rl-run>-paper`) is what you see and what you will be
  told to use. It resolves nothing.
- An **addressable peer name** is what `SendMessage` takes. Only these can receive.
- **The correlation runs backwards.** Windows with work-shaped names are usually long-lived
  sessions, and long-lived sessions are the ones missing from the peer list. The generic `claude`
  windows are the ones that register. *The more a window looks like the right target, the more
  likely it cannot be messaged.*
- **Never `tmux send-keys` into a live interactive session.** Text already typed at its prompt will
  be mangled by the injection — on the day this skill was written, the target had unsent input
  sitting there. Ask the user to paste instead.

## What the doc must carry

`check` enforces seven sections, each because a receiver's first questions are predictable:

| section | the question it answers |
|---|---|
| Symptom | what is observably wrong, with real numbers |
| Root cause | the mechanism — layered only if each layer changes the conclusion above it |
| Blast radius | what else is affected (the section senders skip and receivers most need) |
| Evidence / provenance | file paths + the exact command per number, so the work can be checked |
| What to fix | in order, cause before symptom |
| How to verify | a command that shows the problem, and shows it gone |
| **What I changed** | usually "nothing — analysis only". The receiver's first fear is that their working tree moved under them. |

## Gotchas

- **Don't paste the findings into the message.** They go stale the moment you edit the doc, and the
  receiver ends up with two versions. Send the path.
- **Say what it blocks and when.** "Read this" gets queued; "read this before you interpret the four
  evals landing in ~2h" gets read.
- **Placeholders in code are not unfilled slots.** `--a <baseline file>` is usage syntax the reader
  substitutes; `<what else is affected>` is an unfilled slot. The checker strips code fences and
  inline spans before looking — a checker that flags finished documents is one nobody runs twice.
- **A checker that matches vocabulary cannot enforce structure.** `check` originally searched the
  whole document for phrases, and on 2026-08-15 it failed in *both* directions at once: it rejected a
  finished doc because "아무것도 바꾸지 않았습니다" was not the one Korean phrasing it knew
  (`건드리지`), while `blast radius` was satisfied by the bare word "scope" or "affected" appearing
  anywhere — so a document with no sections at all passed six of seven rules. It now matches
  **headings**, accepts synonym headings (a heading naming the actual consequence — "Why this breaks
  comparisons" — beats a generic "Blast radius" and must not be failed for it), and rejects a heading
  with nothing under it. Regression set, run on every change: every real `HANDOFF*.md` on disk must
  pass, and a vocabulary-only document must fail.
- **Broadcasting to every live session is not a fallback.** It reaches people who then have to
  decide it is not theirs. If you cannot address it, say so and hand the pointer to the user.

## Composition

- **← lesson-loop / exp-loop** — a diagnosis whose fix belongs to someone else's code leaves through
  here rather than sitting in your ledger.
- **→ the receiver** — the doc's "What to fix" is their entry point; keep it ordered and causal.
