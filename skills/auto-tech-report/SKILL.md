---
name: auto-tech-report
description: Find tech reports / system cards, summarize each in detail (the report's own facts + what to read from minstar's lens + connections to his research notes), independently fact-check, and publish as a toggle entry in the "Insights of Tech Report" section of minstar.github.io. Also has a --horizons mode that reads his recent papers + notes + the catalog and proposes his next-paper directions (private). Use when minstar shares report/paper/system-card URLs to catalog, asks to find and write up recent frontier tech reports, or asks what his next paper should be. Triggers - "/auto-tech-report", "tech report 정리", "system card 요약해서 올려", "insights of tech report 추가", "다음 페이퍼 주제", "next paper 방향".
trigger: /auto-tech-report
---

# /auto-tech-report — catalog tech reports through minstar's lens, verified, onto the site

Turn one or more technical reports / system cards into fact-checked toggle entries in the
**Insights of Tech Report** section of the research-notes page. Each entry is **detailed** — a
substantive block of the report's own facts (5–8 attributed excerpts spanning method, training,
numbers, eval setup, and a caveat) followed by minstar's read of them (what to look at + where it
meets his notes, plus an optional "worth stealing") — and is independently verified before it goes
public.

## Usage

```
/auto-tech-report <url1> <url2> ...     # catalog these explicit sources (arXiv abs/pdf, system-card PDFs)
/auto-tech-report --find "<topic>"      # discover recent frontier reports on a topic, then catalog
/auto-tech-report --find                # discover notable reports/system cards since the last entry
/auto-tech-report <url> --no-push       # write + commit but do not push (review first)
/auto-tech-report --horizons            # read his recent papers + notes + the catalog -> propose his NEXT paper (private)
```

## What each entry looks like (excerpt, then my read)

Entries are **detailed, not thin** — the point of the catalog is to hold the concrete substance
(the actual method, the actual numbers, the eval setup, the caveats the report admits), so a reader
can learn the report from the entry without opening it. Two clearly-separated parts, so a reader can
always tell *the report's content* apart from *minstar's commentary on it*:

- **What-it-is line** — 2–3 neutral sentences: what the artifact is, its scale/scope (params, pages,
  dataset size), and its headline claim. No "my teacher / the model I use" framing.
- **From the report** — **5–8 excerpts**: the report's own load-bearing findings/numbers, each
  attributed to a section (`— §X`). Rendered as a blockquote. **Cover the spread** so the entry is
  substantive: (a) the core method/architecture, (b) the training recipe (data scale, distillation,
  RL/post-training), (c) 2–3 headline numbers, (d) the eval setup/harness detail, (e) at least one
  caveat/limitation *the report itself* states. These are the source's words/facts, not minstar's
  opinion. Do not put quotation marks implying verbatim unless it is verbatim; a tightly-attributed,
  fact-checked finding is fine. Prefer a precise number + its context over a vague sentence.
- **My read** — the commentary, in minstar's first person, explicitly *his thought about the excerpts
  above*, in up to three dimensions:
  1. *What I'd look at* — as a search/agent researcher doing SFT/RL, agent-trajectory data synthesis
     (env-synth/dive-synth), on-policy distillation, reward/verifier design, and agentic eval —
     which excerpts/sections are worth reading and why, at the mechanism level. Concrete, never
     generic praise. 2–3 sub-points are fine when the source earns them.
  2. *Where it meets my notes* — which research note(s) the source touches, named explicitly, and
     how (one clause per note). Only claim a connection the source supports; label a stretch a stretch.
  3. *Worth stealing / watching* (optional) — a concrete technique or number he'd port into his own
     work, or a sharp open question the report leaves. Include only when it rises above the connections.

## Confidentiality (hard rule — never leak internal dependencies)

The catalog is public. **Never identify any model as minstar's teacher, judge, base, or internal
training/eval dependency** — e.g. do not write "`<teacher-model>`, the teacher I lean on" or "the
model I use to synthesize trajectories / grade evals." If a source happens to be a model he uses
internally, catalog it **neutrally, exactly like any other external report** ("Technical report for
<teacher-model> …") and connect it to the notes by *mechanism*, not by disclosing that he uses it. Also
avoid internal infra/method codenames that aren't public (e.g. private RL-stack names) — say "my own
RL work" instead. The verify pass must flag any such leak before publishing.

## Where it publishes

- Repo: `minstar.github.io` (currently `<shared-work>/workspace/minstar/minstar.github.io`).
- File: `notes/insights-tech-reports.md` — a single markdown file; each report is a
  `<details><summary>…</summary>…</details>` toggle. Rendered by `renderInsights()` in
  `research-notes.html` as a pinned, open-by-default `.note-entry` above the dated notes.
- New reports are **appended/merged** into this file, ordered most-relevant-to-minstar first.

## Process

### 0. Build the lens (fresh each run)
Read the current `notes/*.md` (the dated research notes) and list their titles + one-line theses.
This becomes the `lens` string — so "connections" always reflect his *current* open questions, not a
stale list. As of writing, the notes are: **AgentPlanet** (tri-role world/policy/world-model,
reward-channel integrity, anti-Goodhart), **Over-reflection in search agents** (confirm-then-keep-
searching ~63%, per-type repair, state-conditioned stop/pivot RL), **Post-cutoff distillation**
(memory-cache teacher → on-policy distill across tokenizers, token-level reward gated to post-cutoff
knowledge), **Wearable world model** (KV-cache + quantization; latent-encoder vs generative fork),
**Energy floor of inference** (energy/token vs minimum sustained power; quant as the floor lever).
Also fold in his standing interests: agentic tool-use, long-horizon reasoning, RL/RLHF, reward
models & verifiers, distillation, data contamination/audit, world models, on-device efficiency, eval
methodology.

### 1. Resolve sources
- **Explicit URLs** → use as given. Give each a short `id` and a `hint` (e.g. "arXiv paper — fetch
  abs + html/pdf", "system-card PDF — fetch text, curl+Read fallback").
- **Discovery (`--find`)** → WebSearch/WebFetch for recent frontier technical reports and system
  cards (labs: Anthropic, OpenAI, Google/DeepMind, Qwen/Alibaba, DeepSeek, Zhipu/GLM, ByteDance/Seed,
  Meta, Mistral, Sakana, Kimi/Moonshot, etc.). Prefer ones that touch his notes (agentic RL,
  verifiers, distillation, efficiency, search eval). Dedup against titles already in
  `insights-tech-reports.md`. Confirm each candidate is real (fetch it) before cataloging.

### 2. Fetch + INDEPENDENTLY verify (mandatory — do not skip)
Run the bundled workflow, which does a `read` pass then an independent `verify` pass per source.
**Inline the run's data — do not pass it through `args`.** The `args` channel has repeatedly crashed
at `JSON.parse` on the nested `{sources, lens}` payload *before any agent runs*, so the reliable
pattern is:

1. Copy `assets/fetch_verify.workflow.js` to a scratch path.
2. Edit the `SOURCES` and `LENS` consts near the top: inline this run's sources
   (`{id, url, hint}` — put the sections/numbers to cover in `hint`) and the fresh **pure-ASCII**
   lens from step 0 (no ∏/π/·/→/subscripts/curly quotes — they crash the parse).
3. `Workflow({ scriptPath: "<scratch copy>.js" })` — no `args`.

The workflow returns `[{src_id, url, summary, verify}]`. On completion, read the returned data (if
truncated, read the run's `journal.jsonl` — one `result` line per agent). For 1–2 sources you may
instead spawn two subagents inline (one reader, one independent verifier) — but **never publish a
reader summary that has not been independently checked against the source.**

### 3. Apply verifier corrections → compose entries
For each source, take the verifier's `confirmed_title/org/date` and walk every `correction`,
fixing the summary. **Publish only verified facts.** If `verdict` is `major_issues`, rewrite the
entry from the verifier's confirmed content (do not publish the reader's version). If
`could_not_fetch`, skip the source and tell minstar. Build "From the report" from the verified
`excerpts` (5–8, spanning method / training / numbers / eval setup / a caveat); build "My read" from
`read_from_my_view` + `connections` + (if present) `worth_stealing`. **Apply every `leak_flag`**:
strip any teacher/judge/base/internal-dependency framing and any private infra codenames before the
text ever lands in the file.

### 4. Merge into the file
Write/extend `notes/insights-tech-reports.md`: keep the `# Insights of Tech Report` H1 + intro
paragraph, then one `<details>` per report (template below), most-relevant-first. Merge, don't
clobber — preserve existing entries, drop duplicates by title.

### 5. Verify render, then commit & push
- Structural check: balanced `<details>`/`<summary>` counts, exactly one H1, the file is referenced
  by `research-notes.html`, all `NOTES` files resolve.
- Real render check when possible: `npm i marked@12` in a scratch dir and `marked.parse()` the file;
  confirm the toggles + nested markdown (italics, bullets, links) render.
- Commit the md (+ html if the scaffold changed) and push to `master` (that branch **is** the
  GitHub Pages deploy — do not branch). End the commit message with the standard
  `Co-Authored-By:` / `Claude-Session:` trailers. Skip the push if `--no-push`.

## Mode: `--horizons` (next-paper directions)

A second thing this skill does: read minstar's **own recent papers** (last ~2 years) alongside his
research notes and the frontier tech-report catalog, and propose — from deliberately *new angles* —
what his **next paper** could be. The idea is that the catalog already holds "what the frontier is
doing" and the notes hold "what I'm chewing on"; crossing those against "what I've already shipped and
am uniquely good at" is where a non-obvious next paper falls out.

**This output is PRIVATE by default.** Next-paper ideas are strategic (a competitor could scoop them),
so — unlike the catalog — do **not** commit or push them to the public site. Write the deliverable to
a non-published path and surface it to minstar for review; only publish a distilled, sanitized version
if he explicitly asks (`--horizons --publish`). The site enumerates notes from a hardcoded `NOTES`
array in `research-notes.html`, so a stray file in `notes/` is not auto-rendered — but a committed
file is still fetchable by URL, so keep it out of the repo (or git-ignored) unless publishing.

Process:
1. **Run the horizons workflow** (`assets/horizons.workflow.js`, `scriptPath`, no `args`). It:
   - *Gather* (parallel): reads his authored corpus (`paper-voice/authored_corpus_style.md` + the
     `minstar_identity_scholar` memory + best-effort Scholar/arXiv for the newest papers), his research
     notes, and the `insights-tech-reports.md` catalog.
   - *Ideate* (parallel): six distinct crossing-angles (verifier-integrity, world-authoring,
     post-cutoff-distillation, efficiency×domain, over-reflection-RL, and a free/contrarian angle) each
     propose 1–2 candidate papers with a title, the new-perspective cross, the gap (grounded in a named
     report/note), why *he* is positioned, a cheap falsifiable first experiment, and an honest novelty line.
   - *Rank*: one higher-effort critic dedups, scores each on novelty / moat-fit / feasibility /
     timeliness, drops mere restatements of existing notes, keeps the top 3–5, and writes a
     cross-cutting "new perspective" reflection.
2. **Compose the deliverable** from the returned `{horizons, corpus, notes, frontier}` — a dated
   markdown with the meta-reflection up top, then one section per ranked direction (title · one-liner ·
   angle · gap · why he's positioned · first experiment · bridges · honest novelty · risk · scores).
3. **Deliver, don't publish.** Write it to a private path (e.g. a git-ignored `notes/_horizons/…`
   or a scratch file), `SendUserFile` it to minstar, and stop. Apply the same confidentiality rule —
   no model framed as his teacher/judge/base.

Refresh the corpus and catalog each run so the angles track his live trajectory, not a stale snapshot.

## Entry template

```markdown
<details>
<summary><strong>Exact Title</strong> · Org, Month Year</summary>

*2–3 sentences, neutral: what it is + scale/scope + headline claim (no "my teacher / the model I use" framing).*

**From the report**
> <core method / architecture> — §X
> <training recipe: data scale, distillation, RL/post-training> — §Y
> <headline number 1 + its context> — §Z
> <headline number 2> — §W
> <eval setup / harness detail> — §V
> <a caveat or limitation the report itself states> — §U

**My read**
- *What I'd look at:* <which excerpts/sections to read and the mechanism-level why; 2–3 clauses ok>.
- *Where it meets my notes:* **NoteA** — <mechanism connection>. **NoteB** — <mechanism connection (or why it's a stretch)>.
- *Worth stealing / watching:* <a technique/number I'd port, or an open question the report leaves — omit this line if nothing rises above the connections>.

[Source (arXiv NNNN.NNNNN)](https://arxiv.org/abs/NNNN.NNNNN)   <!-- or [Source (PDF)](url) -->

</details>
```

## Gotchas & lessons (learned the hard way)

- **Independent verification is non-negotiable.** In the first run, a system-card PDF carried a
  **hidden, non-rendering text layer** describing a *different* model; the reader summarized the
  hidden layer wholesale. The verify pass caught it by rasterizing the cover + checking PDF metadata.
  Always confirm identity against what actually *renders*, not just `pdftotext` output.
- **arXiv fetches can silently return the wrong paper — fetch twice and diff.** In the 2026-08-13 run,
  `arxiv.org/pdf/2608.02302` returned a PDF whose *metadata Title* was correct but whose text layer
  **and** rasterized cover were a different paper entirely (`2608.09836`); `arxiv.org/html/2608.02302`
  returned a third paper (`2608.02603`); and the abs page came back with a corrupted DOI. Re-fetching
  resolved all three, so the failure is the HTTP path, not the source. Fetch each arXiv surface (abs /
  html / pdf) **at least twice and confirm the responses are byte-consistent**, and cross-check the
  abs-page `citation_title` against the rasterized cover before trusting any of it. Note this is the
  *inverse* of the hidden-text-layer case above: there the metadata was wrong and the render was right;
  here the metadata was right and both the render and the text layer were wrong — so agreement between
  *two independent surfaces* is the check, never any single one.
- **Dates come from the source, not the arXiv ID.** An arXiv ID prefix (e.g. `2606.`) can imply a
  month that contradicts the stated "Submitted on …" date — trust the abs-page `citation_date`.
- **Never fabricate.** If a source can't be read, mark it `(UNVERIFIED)` and skip publishing it.
- **Never leak internal dependencies.** No model may be framed as minstar's teacher/judge/base
  (see Confidentiality above); catalog it neutrally and connect by mechanism. Scrub any such phrasing
  the reader agent produced, and have the verifier flag it. This bit the first run — `<teacher-model>`
  was published as "the teacher I lean on" and had to be neutralized.
- **Excerpt, then thought — keep them visibly separate.** "From the report" is the source's own
  facts (blockquote, attributed to a section); "My read" is minstar's commentary on them. A reader
  should never have to guess which is which. No generic "this is a strong report" bullets — name the
  section and the number.
- **Thin entries are the failure mode, not verbosity.** The earlier entries recorded only 3–4
  excerpts and a two-line read; the standard now is 5–8 excerpts that actually *cover* the report
  (method + training recipe + a few headline numbers + eval setup + a caveat the report admits) so a
  reader learns the report from the entry. If the reader agent returns fewer than 5 excerpts or omits
  the method/training/caveat, treat it like a verifier flag and re-fetch to enrich — do not publish
  the thin version. Still never pad with fluff: every excerpt is a fact with a section ref.
- **Inline the workflow's data; don't trust `args`.** The read→verify workflow's `args` channel
  crashed at `JSON.parse` before any agent ran on the nested `{sources, lens}` payload — twice, on
  both a Unicode and an all-ASCII lens — so the failure is the channel, not the content. The reliable
  fix is to copy the workflow, edit the inlined `SOURCES`/`LENS` consts, and run with `scriptPath`
  and no `args` (the asset now takes `args` only as a crash-proof best-effort override). Independently:
  keep the lens **pure ASCII** (prod/pi/*/->/s0, no subscripts or curly quotes) regardless of channel.
- **Keep the lens current.** Rebuild it from `notes/*.md` each run so connections track his live work.
- **master is the deploy branch.** Commit directly to `master`; do not open a feature branch.

## Files
- `assets/fetch_verify.workflow.js` — the read→verify catalog workflow. Inline its `SOURCES`/`LENS`
  consts and run with `scriptPath` (no `args`); reusable.
- `assets/horizons.workflow.js` — the `--horizons` next-paper workflow (Gather→Ideate→Rank). Reads his
  corpus + notes + catalog from disk; edit the CONFIG paths if they move. Output is private — deliver,
  don't push.
