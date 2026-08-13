---
name: skill-forge
description: >-
  Audit an existing skill against how it actually got used and patch where it under-specified or
  misfired, or promote a repeated manual sequence into a new skill. The meta arm of the discovery
  loop — it is what performs the edit when lesson-loop decides a lesson belongs in a skill. Use
  when a skill produced a wrong or thin result, when you notice you have hand-done the same
  multi-step sequence more than twice, when writing a new skill, or when reviewing the skill set.
  Triggers - "/skill-forge", "스킬 개선", "스킬 감사", "이거 스킬로 만들자", "skill 만들어",
  "스킬이 왜 이렇게 했지", "SKILL.md 고쳐".
trigger: /skill-forge
---

# /skill-forge — audit, patch, promote

A skill is a bet that a future run will go better because of what you wrote down. `skill-forge`
settles that bet against evidence: what the skill *said*, versus what actually had to happen.

Two modes, one quality bar.

## Usage

```
/skill-forge audit <skill-name>        # this skill vs its real runs -> patches
/skill-forge audit --all               # sweep every skill, rank by evidence of drift
/skill-forge promote "<sequence>"      # a repeated manual sequence -> a new skill
/skill-forge new <name>                # scaffold from scratch
/skill-forge --dry-run                 # show diffs, write nothing
```

## Mode: `audit`

### 1. Read the skill as written
Load `SKILL.md` and every asset. Write down, explicitly, what it *promises*: the steps, the
non-negotiables, the gotchas it already knows.

### 2. Find what actually happened
Evidence, in order of value:

- **The output it produced** — the committed file, the published entry, the dataset. Compare against
  the skill's own stated standard. A skill that says "5–8 excerpts spanning method, training,
  numbers, eval, caveat" and produced entries with 3 has a measurable gap.
- **Session transcripts** under `~/.claude/projects/*/`, and workflow journals
  (`subagents/workflows/*/journal.jsonl` — one `result` line per agent).
- **The corrections that were applied** — if a verify pass or minstar corrected the same *kind* of
  thing twice, the skill under-specified it.
- **Manual steps the operator had to add** — anything you did by hand that the skill did not tell
  you to do is, by definition, a hole in the skill.

### 3. Classify each gap
| Gap | Fix |
|---|---|
| Instruction was **absent** | add the step where it belongs in the process, not as a trailing note |
| Instruction was **present but ignorable** — buried, hedged, or advisory | promote it to an explicit gate with a verb ("do not publish until…") |
| Instruction was **wrong** for the real environment | correct it and record the evidence in Gotchas |
| The **asset** (script/prompt) allowed the bad behavior | patch the asset — prose alone will not bind a subagent |
| The skill **fired at the wrong time** or not at all | fix the `description` triggers, not the body |

### 4. Patch — and patch the binding surface
The single most common failed repair is writing a lesson into `SKILL.md` prose when the behavior is
produced by an **asset** (a workflow script, a subagent prompt, a template). The subagent never reads
`SKILL.md`. **If a behavior is produced by an asset, the fix must land in that asset**, with the
`SKILL.md` note as documentation of *why*.

Where a fix lands, by symptom:

- Subagent returned something wrong/thin → the **prompt** in the asset (and the schema, if the shape
  was permitted).
- Skill did the wrong thing at the top level → `SKILL.md` process section.
- Skill did not fire, or fired on the wrong request → frontmatter `description` triggers.
- Same class of failure across several skills → this is a `CLAUDE.md` rule; hand back to
  **lesson-loop** for routing rather than patching N skills.

### 5. Verify (non-negotiable)
- Frontmatter still parses: `name` + `description` present, YAML valid.
- Every asset still loads: `node --check <asset>.js`, `python3 -c "import ast,io;ast.parse(io.open(p).read())"`.
- The gap is actually closed: re-run the failing case if it is cheap, or state precisely which
  future run would now catch it and how.
- No contradiction introduced against an existing instruction in the same skill.

### 6. Report
```
skill              gap                                        fix landed in            verified
auto-tech-report   arXiv HTTP can serve a different paper      SKILL.md Gotchas +       node --check ✓
                   (metadata right, render+text wrong)         fetch_verify verifyPrompt
```

## Mode: `promote`

Promote a manual sequence into a skill when **all three** hold:

1. **Done ≥3 times**, or twice with real cost the third time would repeat.
2. **The steps are stable**; only the inputs change.
3. **Getting it wrong has a cost** — money, a bad number, a wasted job, a public error.

If it fails (3), it is a shell alias or a note, not a skill. Skills carry maintenance cost; a skill
that only saves typing is a net loss.

Scaffold:

```
~/.claude/skills/<name>/
  SKILL.md          # frontmatter + process + gotchas
  assets/           # only what must bind behavior: scripts, prompts, templates
```

## The quality bar (applies to both modes)

A skill is finished when:

- **The `description` names real triggers**, including the Korean phrasings minstar actually types.
  The description is the *only* thing read when deciding whether to fire — it is a retrieval
  surface, not a summary.
- **The process is ordered and gated**, with at least one step that can fail and stop the run.
  A skill with no gate is a suggestion.
- **The gotchas are grounded in a real failure**, each with its symptom. "Be careful with X" is
  worthless; "X returned a different paper on 2026-08-13; fetch twice and diff" is a rule.
- **There is a verification step before declaring done** — the standard from `CLAUDE.md` §4:
  prove it worked (test, log, diff), do not assert it.
- **It says what NOT to do**, where an obvious-but-wrong path exists.
- **Confidentiality is handled** where the skill produces anything public — no model framed as a
  teacher/judge/base, no private infra codenames.

## Anti-patterns (learned from surveying the ecosystem)

- **The generic self-improver.** The most-installed "self-improving agent" skills are domain-free
  memory wrappers; without a domain, every lesson they capture converges to vague prose. A skill
  earns its keep by being *specific* — name the paths, the flags, the failure.
- **Prose that duplicates an asset.** Two copies of a rule drift; the asset wins because it is what
  actually executes. Keep the rule in the asset and *reference* it from prose.
- **Growth by accretion.** Every audit adds; nothing removes. When patching, also delete instructions
  that are now dead (the file they name is gone, the flag was removed). A skill nobody trusts to be
  current gets skimmed.
- **Gotchas as trivia.** If a gotcha never changes a decision, it is padding — cut it.

## Composition

- **← lesson-loop** — routes skill-targeted lessons here; skill-forge owns the edit + re-verification.
- **→ lesson-loop** — if an audit finds a gap that spans several skills, hand it back for routing to
  `CLAUDE.md` or a hook instead of patching each skill.
- **→ harness-guard** — a gap that is mechanically checkable belongs in the preflight checker, not in
  a skill's prose.
