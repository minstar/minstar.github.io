---
name: lesson-loop
description: >-
  Capture a lesson from a correction, failure, or surprising finding, then ROUTE it to the
  one place that will actually change future behavior — a CLAUDE.md rule, a specific skill's
  Gotchas, an executable harness-guard check, a settings.json hook, or memory — and verify the
  target fires. The self-evolving arm of the discovery loop; feeds skill-forge (edits) and
  harness-guard (checks). Use when minstar corrects something, a job/eval fails in a way that
  cost time, an assumption turns out wrong, or he asks to record a lesson.
  Triggers - "/lesson-loop", "lesson 기록", "교훈 정리", "같은 실수 방지", "이거 룰로 만들어",
  "lessons.md 업데이트", "왜 또 틀렸지".
trigger: /lesson-loop
---

# /lesson-loop — capture, route, verify

`tasks/lessons.md` died at 706 bytes because it was a *destination without a routing rule*.
Everything felt worth writing, so nothing got written, and nothing that was written ever changed
behavior. This skill fixes the two halves that were missing: **deciding where a lesson goes**, and
**proving the destination actually fires.**

The governing standard: **a lesson that cannot change a future decision is not a lesson.** If you
cannot name the file it edits and the moment it would have fired, drop it.

## Usage

```
/lesson-loop                       # harvest this session's lessons, route each
/lesson-loop "<the lesson>"        # route one specific lesson
/lesson-loop --review              # re-read tasks/lessons.md, retire stale rules, find un-routed entries
/lesson-loop --dry-run             # classify + show the diffs, write nothing
```

## Step 1 — Harvest (be strict, most things are not lessons)

Scan the session (or the stated incident) for candidates. A candidate is one of:

- **A correction** — minstar said "no", "그거 아니야", redirected the approach, or repeated an
  instruction you had already been given.
- **A failure that cost time** — a job died, a script silently produced partial output, an eval
  reported a number that turned out wrong, a fetch returned the wrong thing.
- **A refuted assumption** — you believed X about the cluster/data/API and X was false.
- **A confirmed approach** — minstar explicitly endorsed a method ("이렇게 계속 해줘"). These matter
  as much as corrections and are the ones most often lost.

**Reject** anything that is: a fact the repo already records (code structure, a fixed bug, git
history), a one-off environment hiccup with no pattern, or a restatement of an existing rule. When
in doubt, apply the recurrence test — *would this plausibly happen again in a different task?* No →
drop it.

## Step 2 — Classify and route (the missing piece)

Every surviving candidate goes to exactly **one** primary target. Pick by asking what kind of thing
would have prevented it:

| If the lesson is… | Route to | Why there |
|---|---|---|
| **Mechanically detectable** — a path, a flag, an env var, a partition, a version | `harness-guard` check (`assets/preflight.py`) | A check runs every time; prose does not. **Prefer this route whenever it is possible.** |
| **Detectable at tool-call time** — a dangerous command shape, a post-action follow-up | `settings.json` hook (PreToolUse/PostToolUse) | Fires without the agent remembering to look |
| **Specific to one workflow** the skill under-specified | that skill's `## Gotchas` (hand to **skill-forge**) | Loads exactly when that workflow runs |
| **A cross-cutting behavioral rule** for how to work | project `CLAUDE.md` | Loads every session |
| **A durable fact about environment/infra/people** | auto-memory (`memory/*.md` + `MEMORY.md` line) | Survives sessions, recalled by relevance |
| **Judgment that resists mechanization** | `tasks/lessons.md` | The honest home for "you have to think here" |

Routing rules that matter:

- **Mechanize first.** If a check *could* catch it, writing prose instead is the failure mode that
  killed the old file. Downgrade to prose only after you have tried and failed to write the check.
- **One primary target, plus a pointer.** Duplicating the same rule into CLAUDE.md *and* a skill
  *and* memory guarantees three copies drifting apart. Put it in one place; if another place needs
  to know, add a one-line pointer to the primary.
- **Never put content in `MEMORY.md`** — it is an index. One line, pointing at the memory file.
- **Corrections from minstar carry the `why`.** A rule without its reason gets over-applied to cases
  it was never meant for; record the reason in the same entry.

## Step 3 — Write the entry

Every `tasks/lessons.md` entry, and every lesson handed to another target, carries five fields:

```markdown
## YYYY-MM-DD — <one-line symptom, concrete>
- **증상**: what was observed, with the actual command/number/error.
- **원인**: the mechanism, not the symptom restated.
- **룰**: the behavior change, phrased as something you can obey mid-task.
- **검증**: how you know the rule works — the command, the check, the file it now lives in.
- **detector**: `<a command that would have caught this>`  — or `none (judgment)` if genuinely
  unmechanizable. **A `detector:` that is not `none` is a bug report against harness-guard:** it
  means the check exists as a one-liner and has not been installed yet.
```

The `detector:` line is what makes this file self-liquidating. Entries with a real detector should
*leave* the file as they become checks; entries that stay are the irreducibly judgmental ones.

## Step 4 — Verify the destination fires (non-negotiable)

Writing is not landing. Prove it:

- **harness-guard check** → run `assets/preflight.py` against a script that has the defect and
  confirm it FAILs, and against a clean script and confirm it does not.
- **hook** → construct the matching tool input and confirm the hook output appears (or the call is
  blocked). A hook with a bad regex is worse than no hook — it teaches you it is covered.
- **skill Gotchas** → confirm the edited skill still parses (frontmatter intact) and, if it ships a
  workflow asset, that the asset still passes `node --check` / imports.
- **CLAUDE.md rule** → read it back in context and check it does not contradict an existing rule.
- **memory** → the file exists, has valid frontmatter, and `MEMORY.md` has exactly one new line.

If verification fails, the lesson is **not** recorded — fix the target and re-verify.

## Step 5 — Report

Print a routing table so the decision is auditable:

```
lesson                                   → target                        verified
arXiv HTTP serves a different paper      → auto-tech-report Gotchas +     ✓ node --check
                                           fetch_verify verify prompt
```

## `--review` mode

Run periodically, or when a rule feels stale:

1. Read `tasks/lessons.md` top to bottom.
2. For each entry with a `detector:` that is not `none` — **promote it** to a harness-guard check
   and delete it from the file. This is the file's main way of shrinking.
3. For each entry, ask whether the named file/flag/path still exists. A rule about a deleted script
   is noise; delete it and say so.
4. Flag contradictions between `tasks/lessons.md`, `CLAUDE.md`, and skill Gotchas. Contradictions
   are how a rule-set stops being obeyed.
5. Report: entries promoted, entries retired, contradictions found.

## Composition

- **→ skill-forge** — when the target is a skill, hand the lesson over rather than editing by hand;
  skill-forge owns the skill-edit quality bar and the re-verification.
- **→ harness-guard** — a `detector:` line is a check specification. Hand it over.
- **← exp-loop** — a failed experiment whose failure was *procedural* (wrong path, wrong partition,
  stale script) rather than scientific comes here. A hypothesis that was simply wrong does **not** —
  that belongs in the experiment ledger, and confusing the two pollutes both.

## Gotchas

- **The old file died of permissiveness, not neglect.** Resist writing the interesting-but-inert
  observation. One routed, verified lesson beats ten recorded ones.
- **Do not let a lesson become a global ban.** "X broke once" → a check for the specific condition,
  not "never use X". Over-broad rules get quietly ignored, which costs you the rule *and* the trust
  in the rule-set.
- **Confirmed approaches decay fastest.** They feel like they need no recording because nothing went
  wrong. Record them; they are what prevents relitigating a settled decision.
- **Date every entry absolutely** (`2026-08-13`, not "today"), and convert relative dates in the
  lesson body too — these are read months later.
