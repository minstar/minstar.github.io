---
name: paper-voice
description: Draft or refine a paper section in minstar's voice — progressive elaboration, concrete-first hook, running example — while preserving every number/hedge, year-ordering citations, and verifying the build. Use for writing/polishing minstar's papers (e.g. the OpenBioRQ line).
trigger: /paper-voice
---

# /paper-voice — write & refine in minstar's paper voice

Apply minstar's house writing style to a section or draft and then verify it. Encodes the points he
established while writing OpenBioRQ (companion memory: `minstar_writing_method`). For heavy
page-limit restructuring (main ↔ appendix), compose with `/paper-main-appendix`.

## Usage
```
/paper-voice <section.tex>     # refine an existing section in the voice
/paper-voice draft <blocks>    # draft a new section from a block plan, in the voice
/paper-voice recheck           # full re-review: build warnings, number-consistency, cite/ref integrity, redundancy
```
Use for minstar's papers (OpenBioRQ at `…/healthcare-research/paper_writing/`); not for code.

## The voice — five moves
1. **Progressive elaboration (the core).** Every claim is unpacked by the next clause/sentence so the
   reader sees *why/how* — never state-and-move-on. Introduce the unpacking with `:` or `---`, but keep
   punctuation light (see *Restraint* below).
   *"necessary, but badly insufficient: [unpack]." · "One might expect these to rise and fall
   together. In biomedical research, they come apart and are opposite to what other fields report."*
2. **Concrete-first hook.** Open a section/paper with a REAL, specific example (verbatim from the
   data), then generalize — not an abstract assertion.
3. **Running example.** Keep that opening example as a representative thread and reuse it as the
   canonical instance at each major step *(e.g. "the opening example is one: PMID 34407296, an
   ophthalmology paper cited for a vaccine claim")*.
4. **Plain & intuitive.** Short declarative sentences; lead with the **precise** figure *("roughly
   15.9%")*, optionally softened with "roughly"/"~" — the ratio-gloss *("one in six")* is now dropped
   (minstar 2026-06-19); prefer the exact number. **Unpack abstract nouns into a plain clause:** *"the
   failure is one of provenance"* → *"one of linking the claim to its source."* Set up a contrast then
   subvert it *("looks like proof---but…"; "I find X, yet Y")*.
5. **Block-structured planning, flowing prose.** Plan a section as ordered blocks (e.g. positioning →
   core mechanism → why-trustworthy → contributions), then render them as **flowing prose** — the
   OpenBioRQ intro dropped its `\paragraph{}` subheads, bold inline leads, and `itemize`, compressing
   the trust block to inline *(1)(2)(3)* (minstar 2026-06-19). Plan in blocks; don't expose the
   scaffold as headers.

**Person.** Match the author count: **single-author papers use first-person singular "I/my"**
(OpenBioRQ — minstar 2026-06-19); multi-author papers use "we" (his DMIS-era corpus). Reader-inclusive
"we" stays in either *("how do we know the question is open?")*. When refining a single-author draft,
harmonize stray editorial "we/our" → "I/my".

**Restraint — strip decoration (minstar 2026-06-19).** The OpenBioRQ rewrite consistently cut clutter; match it:
- **Light punctuation** — cut decorative or stacked `---` and unnecessary commas. A secondary aside
  reads better as a comma clause (*"assumption---a known answer---and"* → *"assumption, a known answer,
  and"*) or its own short sentence; keep `---` to ~1 per sentence, for the one real unpack/contrast (move 1).
- **Minimal inline emphasis** — strip decorative `\emph`/`\textbf` (*`\emph{exists}`* → exists,
  *`\emph{do}`* → do); reserve emphasis for the one load-bearing concept (`\emph{unsolved}`) and the artifact name.
- **Plain approximations** — prefer the bare figure or a word over `$\sim$`/`$\approx$`
  (*`$\approx\!15.9\%$`* → `15.9%`; *`$\sim$54%`* → "almost 54%").
- **Plain words over arcane terms** (move 4) — *provenance* → "linking the claim to its source";
  *gradient* → "range". ⚠️ But keep one term per load-bearing concept (terminology-consistency
  feedback) — don't half-rename a named finding (e.g. "capability gradient" in §5).
- **Cut redundant re-explanation** — once a point is unpacked, don't restate it later. The rewrite
  deleted *"The danger has simply moved."*, *"What protects reliability is not whether a citation
  exists, but whether it supports the claim."*, and the *"This is why an existence check offers only
  false comfort … primary contribution"* sentence — each re-explained the already-stated
  existence≠correctness / L1-vs-L2 point.

## minstar's own-paper conventions (macro structure)
Paper-level scaffold distilled from his 1st/2nd-author corpus (Self-BioRAG, OLAPH, SysGen, ConNER) —
what the five moves sit inside. Full inventory + quoted evidence + caveats: `authored_corpus_style.md`
(this dir). Apply when drafting a whole section/paper.

*Prose*
- **Name ONE artifact and lead with it** — "we introduce/propose [Name]" in abstract and intro; the
  paper *is* the named thing.
- **Abstract on a 5-move rail:** broad context → "However/Despite" gap → "we introduce [Name]" → one
  concrete number → "we believe / we release" closer.
- **★Abstract mode "간결·핵심만" (minstar hand-set, 2026-07-21, over-reflection paper — PREFERRED
  for his current papers):** the abstract is the claim chain ONLY, one move per short declarative
  sentence, on the rail: capability-inversion hook ("know not only how to X, but also when to
  stop") → definition ("what I call \emph{...}: [one-clause behavior]") → universality stated
  qualitatively (no per-model numbers) → thesis ("learned rather than incidental") → ONE
  measurement pair only (e.g. "63\% ... whereas a standard detector identifies only about 20\%")
  → intervention in one sentence → experiment in one sentence (model + the variant names) → null
  /headline result in one sentence → "These results suggest ..." hedge → one-sentence
  prescription closer. HARD RULES: at most ~2 numbers in the whole abstract (the single most
  load-bearing pair); NO mechanism detail, NO taxonomy inventory, NO token/volume counts, NO
  secondary methodological caveats (they live in the body); keep the minimal honesty hedge
  inline ("the trajectories I can verify"); "however" allowed once. When he hands a draft in
  this shape, fix grammar and FACTS (arm names, what is preserved vs dropped) but keep his
  sentence order and wording.
- **Intro opens broad, narrows in ~3 sentences** (field generality → specific domain need); gap stated
  as an explicit **"However" at a generalization/domain-mismatch failure**, phrasing reused
  abstract↔intro. ⚠️ His DMIS-era intros open GENERAL — but for **OpenBioRQ use the concrete-first
  hook (move 2)** (minstar-confirmed 2026-06-17); reserve the broad open for other venues.
- **Contributions:** the DMIS-era default is **~4 numbered "I/We [verb]…" sentences**
  (introduce/propose/prove/demonstrate), **last = the open-source release** (data+code+weights, sizes).
  ⚠️ **OpenBioRQ drops the explicit `itemize`** and folds contributions into flowing prose / inline
  *(1)(2)(3)* (minstar 2026-06-19; SysGen already folded into prose) — prefer flowing prose unless the
  venue/reviewer expects an explicit list.
- **Report signed deltas, metric named** — "7.2% absolute improvement", in-cell "(+score)"; always an
  **"Average"** column.

*Figures* (complements `## Figures` below)
- **Fig 1 = conceptual "before-vs-ours" / "(A)/(B)/(C)" diagram around ONE concrete worked example**
  (e.g. OLAPH's "Lexapro"), with a **long, self-contained caption** that narrates each panel + states
  the takeaway. ~4 figures — tables carry the weight.
- **Default Fig 1 to single-column** (`\columnwidth`); reserve full-width (`figure*`) for when the
  diagram genuinely needs it — OpenBioRQ moved its motivation quadrant full-width → single-column (2026-06-19).
- **Place a figure at its first `\ref{}`** (minstar 2026-06-19) — it should land on the same page as the
  first textual reference, or the page just before/after, never floated pages away. Put `\begin{figure}`
  in the source right before the referencing paragraph and use `[t]`/`[b]`; if it drifts far, move the
  source location or tighten the placement specifier rather than leaving it stranded from its `\ref`.

*Tables* (the workhorse — ~8–15)
- **Main table:** rows = systems in tiers (proprietary / open / ours) × cols = benchmarks + **Average**.
  Result-cell emphasis has TWO documented modes (pick one): **bold best within a fair-comparison
  bracket** (Self-BioRAG) *or* baseline + **(+delta) in parens, no bold-best** (OLAPH).
- **Component-removal ablation** titled "Effect of each [X] component" + appendix **sensitivity sweeps**.
- **Qualitative case-study table with a color/italics legend in the caption** (e.g. italics = retrieved,
  blue = retrieval-grounded, red = parametric) to expose the mechanism on one real example.

*Full-text moves (section-level; full set + quotes in `authored_corpus_style.md`)*
- **Open method/data sections with a one-sentence-per-step roadmap**, each step ending `(Section~\ref{...})`;
  introduce equations as "…as below," + display + **"where [every symbol] refers to…"**.
- **Structure results as numbered RQs** (`\paragraph{RQ N.}`); **lead with the claim, then point at the
  table** ("We observe/find … in Table~X", "We depict … in Figure~X") — not the raw number; flag the
  headline with **"We want to highlight that…"/"Surprisingly,…"**.
- **Conclusion = concede→However→claim**; limitations as "One limitation could be… Also,… Finally,…",
  each softened by "However, our approach…".
- **Connectives:** Thus / To this end / In detail / In other words / However / Overall / In summary.
  ⚠️ OLAPH-era avoids `---` (colon + (e.g.) instead); OpenBioRQ uses `---`.

## LaTeX formatting (his house style)
Concrete recipes from his real OLAPH source — full guide + snippets in `latex_style.md`. Fingerprint:
**table** = `\caption` above + `{\resizebox{1.0\textwidth}{!}{ booktabs tabular }}{}` + `\vspace{-10pt}`,
headers bold, in-cell breaks via nested `{@{}c@{}}` tabulars (not `\makecell`), **no rules/colors/dashes**;
**figure** = side-by-side `\includegraphics[width=.48\columnwidth]` + ` \\` (never real `subfigure`), or
`wrapfigure{R}` + negative `\vspace`; **captions** 3–6 sent. ending on the takeaway, bold the system name
mid-sentence; **equations** numbered + "where"-gloss, operators as `\text{}`; **emphasis** =
`\textsc{SystemName}` + `\textbf{Dataset}` + `\paragraph{Lead.}`. Many preamble packages
(`makecell`/`subcaption`/`cleveref`/`soul`) are **loaded-but-unused** — don't assume them. Citations,
`\texttt`, and em-dash differ by venue (table in `latex_style.md`).

## Non-negotiables
- **Faithfulness.** Examples must be REAL (from the data), never fabricated — doubly so in
  citation/faithfulness work.
- **Numbers from FACTS.md** (single source of truth); never drift one. Preserve every honesty
  **hedge** (judge-relative estimate, expert validation deferred, decoding-sensitive, frozen-core
  churns) — keep it, just make it flow.
- **Citations.** Order multi-key `\cite{a,b,c}` by year (old→new); NO space after commas (this AAAI
  setup turns `\cite{a, b}` into an undefined `" b"` key). `\href`/`\citep` are undefined here (no
  hyperref/natbib) — use plain text and `\cite`.
- **Author's own prose — don't overwrite it.** minstar hand-writes key passages. For OpenBioRQ the
  **entire abstract, the entire introduction, and the Fig 1 caption** are his current hand-authored
  versions (rewritten 2026-06-19 in the single-author "I" voice, with the PMID~34407296 hook). Do NOT
  rewrite these in a refine pass; improve *around* them, or propose a change and **ask first**. When
  unsure whether he wrote a passage (abstract / any opening / caption), ASK before editing rather than
  rewrite.

## BibTeX — adding a reference
Pull entries from Google Scholar, then **strip to the essentials** before they touch the `.bib`.
1. Search the paper on Google Scholar → click the **cite** link (the `"` quote icon under the
   result) → **BibTeX** in the popup. That opens a
   `https://scholar.googleusercontent.com/scholar.bib?q=info:…&output=citation&…` URL holding the
   raw entry — fetch/copy it.
2. Keep the cite key **verbatim** and only **four fields**: `title`, `author`, `year`, and the venue
   (`journal` for `@article`, `booktitle` for `@inproceedings`). Drop everything else —
   `volume`/`number`/`pages`/`publisher`/`organization`/`address`/`editor`/`month`/`url`/`doi`.

Example — as fetched → kept:
```bibtex
% fetched from scholar.bib
@article{jeong2024improving,
  title={Improving medical reasoning through retrieval and self-reflection with retrieval-augmented large language models},
  author={Jeong, Minbyul and Sohn, Jiwoong and Sung, Mujeen and Kang, Jaewoo},
  journal={Bioinformatics},
  volume={40},
  number={Supplement\_1},
  pages={i119--i129},
  year={2024},
  publisher={Oxford University Press}
}
% kept in the .bib
@article{jeong2024improving,
  title={Improving medical reasoning through retrieval and self-reflection with retrieval-augmented large language models},
  author={Jeong, Minbyul and Sohn, Jiwoong and Sung, Mujeen and Kang, Jaewoo},
  journal={Bioinformatics},
  year={2024}
}
```
Then cite per the **Citations** rule above (year-ordered, no space after commas).

## Process
1. Read `FACTS.md` + the target section (and the block plan, if new).
2. Draft/refine in the voice; preserve all numbers + hedges; year-order cites.
3. Build: `cd paper_writing && bash build_preview.sh` (tectonic preview; the true ≤7-page count is
   Overleaf pdfLaTeX+Times — the local preview over-estimates ~10–15%, no Times).
4. **Verify (don't skip):**
   - undefined refs/citations = 0 (`grep -icE 'undefined (reference|citation)|Citation .* undefined' main_xetex.log`)
   - number integrity: per-section number-multiset diff vs a `.bak_*` backup — any number you
     *removed* must still live elsewhere in the paper or in FACTS.
   - Read the changed preview pages — confirm it reads well and tables/figures/equations are intact.
5. **Fit the page** (if over): trim REDUNDANCY and restated detail that already lives in the
   appendix/§5 — never load-bearing content, hedges, or numbers. Gauge body length by where
   "References" starts in the preview (×0.83–0.85 ≈ real pp). For structural main↔appendix moves, use
   `/paper-main-appendix`.

## Figures (when relevant)
Keep the body figure set MINIMAL — a hero set covering the key findings; detail figures go to the
appendix. Deck cleanup/regeneration can run async (a background agent) and must change only STYLE
(snap to the `figstyle.py` palette), never a plotted or annotated number; regenerate with the
torchtitan python.

**Designing a NEW figure (PowerPoint):** follow his build order — concept + a formal `{before}→{after}`
definition box → scaffold empty phase-headers (quadrant / dashed columns / banner swimlanes) → one fixed
icon per role & color per concept across all panels → same template per baseline (minus one capability,
read L→R) → embed a REAL color-coded worked example in every panel → then iterate only labels, never the
layout. Full visual grammar + icon/color vocabulary + build sequence: `figure_construction.md`.

Related memories: `minstar_writing_method`, `healthcare_paper_build_toolchain`. Related skill:
`/paper-main-appendix`.
