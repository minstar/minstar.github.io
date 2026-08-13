# minstar's authored-paper conventions — reference for `/paper-voice`

Distilled from Minbyul Jeong's **1st/2nd-author corpus** (the papers he led). This is the paper-level
scaffold the sentence-level "five moves" in `SKILL.md` sit inside. Companion memory:
`minstar_writing_method`. Every pattern below is tied to a real paper — cite the source paper when in
doubt, and keep the verification caveats at the bottom.

## Corpus (evidence basis)
**Read in depth** (abstract + intro + Fig 1 caption + main/ablation/case tables): Self-BioRAG, OLAPH,
SysGen. **OLAPH additionally read in FULL** (its entire ICLR-2025 LaTeX source — the basis for the
section-level voice below and the companion `latex_style.md`). **Read at abstract level:** Transferability-of-NLI-to-Biomedical-QA, ConNER. **Metadata only:**
Graph Transformer Networks (2nd author) + middle-author papers (out of scope).

| Title | Year | Venue | Jeong pos. | Corresponding? |
|---|---|---|---|---|
| Self-BioRAG (medical reasoning via retrieval + self-reflection) | 2024 | Bioinformatics / ISMB | 1st | No — Mujeen Sung + Jaewoo Kang (verified, PMC footnote) |
| OLAPH (factuality in biomedical long-form QA) | 2024 | arXiv | 1st | unknown |
| SysGen (system-message generation) | 2025 | arXiv (<org>) | 1st | unknown |
| ConNER (consistency for doc-level NER) | 2023 | Bioinformatics | 1st | likely PI — unverified |
| Regularization for Long NER | 2021 | arXiv | 1st | unknown |
| Transferability of NLI → Biomedical QA | 2020 | CLEF | 1st | unknown |
| Graph Transformer Networks | 2019 | NeurIPS | 2nd | No |

Caveat: Scholar/HTML rarely expose corresponding authors. Only Self-BioRAG was verified (Jeong =
leading, NOT corresponding). On DMIS-era papers treat the PI (Kang) as corresponding unless a footnote
says otherwise. Patterns below come from the three deeply-read papers + two abstracts.

## Prose
**Abstract — a 5-move arc** (every led abstract follows it): (1) broad context on LLM/domain capability
→ (2) a "However/Despite" limitation → (3) "we introduce [Named X]" → (4) one concrete numeric result →
(5) a forward-looking "we believe / we release" closer.
- Self-BioRAG: *"Recent proprietary large language models … have achieved a milestone…"* → *"However,
  when applying existing methods to different domain-specific problems, poor generalization becomes
  apparent…"* → *"we introduce Self-BioRAG…"* → *"a 7.2% absolute improvement on average over the
  state-of-the-art open-foundation model…"* → *"We release our data and code … and model weights (7B
  and 13B)."*
- OLAPH: *"…we introduce MedLFQA…"* + *"We also propose Olaph, a simple and novel framework…"* → *"a 7B
  LLM trained with our Olaph framework can provide long answers comparable to the medical experts'
  answers in terms of factuality."*

**Intro opens broad, narrows in ~3 sentences.** First sentence = a generality about LLMs/the field; by
sentence 3 he is on the specific domain need. **No cold-open anecdote, no opening statistic.**
- Self-BioRAG: *"The recent proprietary large language models (LLMs) such as ChatGPT, GPT-4, and BARD
  have succeeded in reaching near or comparable levels to human experts…"*
- ⚠️ His DMIS-era intros open *general*. But for **OpenBioRQ, use the concrete-first hook** (move 2 in
  `SKILL.md`) — minstar-confirmed (2026-06-17). The broad open is his earlier default; reserve it for
  other venues.

**Gap = explicit "However" pivot at a generalization / domain-mismatch failure**, and the tight phrasing
is **reused between abstract and intro**. Self-BioRAG: *"…poor generalization, leading to fetching
incorrect documents or making inaccurate judgments."*

**Contributions = ~4 numbered, parallel "We [verb]…" sentences**; stereotyped verbs *introduce / propose
/ prove / demonstrate*; the **last contribution is the open-source release** (data + code + weights, with
sizes). OLAPH lists exactly 4: *"(1) We introduce MedLFQA… (2) …two statements that can automatically
evaluate factuality… (3) We introduce the simple and novel Olaph framework… (4) …7B models can generate
long answers comparable to the medical experts' answers…"*
- Caveat: SysGen folds contributions into intro prose — the numbered-4 list is the DMIS-era default, not
  absolute.

**Tone:** plain, declarative, medium-length; mild hedges ("we believe", "could shed light on"); frames
his own method as **"simple and novel"**; occasionally anthropomorphizes the model as a domain expert
(*"…as a medical expert does."*). **Section names** are function-named; he splits *Experimental Settings*
from *Experiments* and reserves a dedicated *Analysis* section before *Conclusion*.

## Figures
- **Few figures (~4–5); tables dominate.**
- **Fig 1 = a conceptual pipeline / "before-vs-ours" diagram anchored to ONE concrete worked example**,
  not a results plot:
  - OLAPH Fig 1: impoverished old (Q+A) vs. enriched MedLFQA format, via a real patient question about
    **"Lexapro"** (definition / advantages / disadvantages / side-effects). Caption is 4+ sentences.
  - Self-BioRAG Fig 1: labeled **(A)/(B)/(C)** comparison of plain-LM vs. RAG vs. Self-BioRAG; caption
    walks through each panel.
  - SysGen Fig 1: pipeline teaser naming the eight system-message functionalities.
- **Captions are long, self-contained, example-driven** — they narrate the figure and state the takeaway
  so it reads without the body text.

## Tables
- **The workhorse: ~8–15 tables** (OLAPH 8, SysGen 13, Self-BioRAG 15 incl. appendix); heavy appendix use
  for sensitivity/ablation.
- **Main results table:** rows = systems/models grouped into **tiers (proprietary / open / open+ours)**,
  cols = benchmarks/metrics + a final **"Average"** column. **Bold = best within a fair-comparison
  bracket** (e.g. per parameter-size class), not globally.
  - OLAPH Table 2 groups each cell into **three metric families — Words Composition / Semantic Similarity
    / Factuality** and shows the baseline with the **+Olaph delta in parentheses** in-cell.
- **Component-removal ablation** titled *"Effect of each [X] component"* — Self-BioRAG Table 6
  progressively removes Reflective Tokens → Biomedical Corpora → MedCPT Retriever → Instruction Sets with
  per-row deltas — plus **hyperparameter sensitivity sweeps in the appendix** (OLAPH α and threshold
  sweeps).
- **Qualitative case-study table with a color/italics legend in the caption.** Self-BioRAG Table 8:
  *"Retrieved evidence is written in italics. Blue-colored text comprises segments connected to key
  information from retrieved evidence, while red-colored text consists of segments tied to the model's
  parametric knowledge."*

## Apply-it checklist
1. Ship ONE named artifact; write "we introduce/propose [Name]" in abstract AND intro.
2. Abstract on the 5-move rail (context → However-gap → introduce[Name] → one number → believe/release).
3. Intro opens broad, narrows in ~3 sentences — EXCEPT OpenBioRQ, which uses the concrete-first hook (see above).
4. Gap = explicit "However" at a generalization/domain-mismatch failure; reuse phrasing abstract↔intro.
5. ~4 numbered "We [verb]…" contributions; last = open-source release (data+code+weights, with sizes).
6. Report signed deltas with the metric named ("7.2% absolute improvement", in-cell "(+score)"); always
   an "Average" column.
7. Fig 1 = conceptual before-vs-ours / (A)/(B)/(C) around one concrete worked example; long
   self-contained caption.
8. Lean on tables (~8–15) over figures (~4); main table = tiered rows × benchmarks+Average, bold within
   fair-comparison brackets.
9. Add an "Effect of each [X] component" ablation + appendix sensitivity sweeps.
10. Add a qualitative case-study table with a color/italics legend exposing the mechanism on one real
    example.

## Full-text voice (section-level — from OLAPH's full LaTeX source)
Patterns visible only across the full body (OLAPH read end-to-end); quotes verbatim from
`sections/*.tex`. LaTeX formatting → `latex_style.md`.
- **Method/Data sections open with a one-sentence-per-step roadmap, each step ending
  `(Section~\ref{...})`.** *"We first train with SFT … (Section~\ref{sec:sft}). Then, we obtain $k$
  sampled predictions … Finally, we iteratively tune … (Section~\ref{sec:iterative})."*
- **Define → `(e.g., …)` in the same sentence**; restate a hard sentence with **"In other words, …"**.
- **Equations: "We compute/train … as below," + display + "where [every symbol] refers to …"** — rigid.
- **One running example threaded through everything** (a single patient drug query — Lexapro /
  white-tongue): intro, every figure caption, appendix samples.
- **Results = numbered RQs**, each under `\paragraph{RQ N.}`; **lead with the claim then point at the
  table** ("We observe/find … in Table~X"; "We depict … in Figure~X" is his figure-intro verb) — *not*
  the raw number; narrate a figure **Step 0 → Step 3**.
- **Headline result flagged with "We want to highlight that …" / "Surprisingly, …"** (not just bold).
- **Group-then-subvert:** positive generalization → **"However, [outlier]"** → re-motivate **"Thus, …"**.
- **Related Work = theme-grouped subsections + citation bundles + gap-spotting** ("there has been
  relatively little effort …"), **credit-and-build** ("Our work is based on …") — NOT "Unlike X".
- **Conclusion = "We introduce X … We also present Y …"**, thesis as **concede → However → claim**
  ("7B LLMs are not reliable enough … However, … 7B models can produce …").
- **Limitations as a chain** "One limitation could be … Also, … Finally, …", each softened by a
  trailing **"However, our approach …"**; future work as **"For future work, if …, they could …"**.
- **Stances marked explicitly:** "We agree with the notion that … / we believe … / We hypothesize that
  …"; sourcing & honesty pushed into **footnotes**.
- **Connective palette:** Thus / To this end / In detail / In other words / However / Overall / In
  summary. ⚠️ OLAPH-era does the unpacking with **colon + (i.e./e.g.) parentheticals and essentially
  NO em-dash**; the current OpenBioRQ voice uses `---` (five-moves move 1) — match the target paper.

## Could not verify
Corresponding-author status on OLAPH / SysGen / ConNER / Regularization-for-Long-NER; full
intros/figures/tables of ConNER and Transferability-NLI (read at abstract level only — the OUP full text
did not load). All quotes above are from sources actually retrieved.

## Current voice deltas — OpenBioRQ (2026-06-19, single-author)
He hand-rewrote OpenBioRQ's whole abstract + intro + Fig 1 caption and asked to internalize the deltas.
These **layer on top of** (and in two places revise) the historical corpus above; the corpus stays the
evidence basis, this is the current direction for *new* single-author papers.
- **Person = first-person singular "I/my"** (single-author). The DMIS-era "we" was multi-author;
  reader-inclusive "we" ("how do we know") survives. Harmonize stray editorial "we/our" → "I/my" when refining.
- **Precise number, not ratio-gloss** — "15.9%", not "one in six" (**revises** the 5-move move-4 "one
  concrete numeric result" toward the exact figure; drop the folksy gloss).
- **Plain words over arcane terms** — unpack or replace: "the failure is one of *provenance*" → "one of
  *linking the claim to its source*"; "capability *gradient*" → "range". Keep one term per load-bearing
  concept, though — don't half-rename a named finding.
- **Light punctuation** — cut decorative/stacked `---` and unnecessary commas; a secondary aside →
  comma clause (*"assumption---a known answer---and"* → *"assumption, a known answer, and"*) or its own
  short sentence (~1 `---` per sentence).
- **Minimal inline emphasis** — strip rhetorical `\emph`/`\textbf` (*`\emph{exists}`* → exists); reserve
  emphasis for the one key concept (`\emph{unsolved}`). Prefer the bare figure or "almost"/"roughly"
  over `$\sim$`/`$\approx$`.
- **Flowing prose, not scaffold** — the intro dropped its `\paragraph{}` subheads, bold inline leads,
  and the **contributions `itemize`** (folded to inline (1)(2)(3)). **Revises** the "~4 numbered
  contributions" convention: plan in blocks, render flowing; explicit list only if the venue expects it.
- **Soften categorical claims** — "the fourth corner is *empty*" → "*underexplored*"; "*cannot even
  arise*" → "*have no room to appear*". Defensible phrasing over absolute.
- **Fig 1 single-column** by default (`\columnwidth`); full-width (`figure*`) only when the diagram needs it.
- **Figure placement at its `\ref{}`** — a figure should appear on the same page as its first textual
  reference, or the page just before/after, never floated pages away; put `\begin{figure}` near the
  referencing paragraph and use `[t]`/`[b]`.
- **Cut redundant re-explanation** — once a point is unpacked earlier, don't restate it later (the
  rewrite deleted three sentences that re-explained the existence≠correctness / L1-vs-L2 point).
- **Hook + running example unchanged** — concrete-first PMID 34407296 (an ophthalmology paper cited for
  a COVID vaccine claim), threaded as the canonical instance.
