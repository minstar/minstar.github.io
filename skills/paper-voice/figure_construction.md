# minstar's figure-construction method — reference for `/paper-voice`

How minstar actually BUILDS a paper figure (in PowerPoint), reverse-engineered from two real editable
decks he uses: the **SysGen** pipeline figure (`reference/figures.pptx`, 7 construction stages) and the
**Self-BioRAG** figures (`reference/figure.pptx`, 23 stages). Both decks independently converge on the
same method. Visual-design companion to `latex_style.md` (how figures are *placed* in LaTeX) and the
"Fig 1 = one concrete worked example" rule in `authored_corpus_style.md`. Faithful — distilled from what
the decks actually show.

## Build order (the sequence he draws in)
1. **Concept/teaser sketch first.** The core idea as a minimal diagram + a formal definition box —
   SysGen: `{Q, A} → {System (S), Q, Newly-Generated A'}`; Self-BioRAG: the 3-column
   `Generation / RAG / Ours` contrast. Nail *the one thing the figure must say* before any polish.
2. **Scaffold the grid + phase headers — empty.** Lay the panel structure and drop in named/numbered
   phase headers BEFORE content: a **2×2 quadrant** (P1–P4 "System Message Generation / Filtering /
   Verification / Assistant Response", or `[1] Generation … [4] Self-BioRAG`), **columns with dashed
   vertical dividers**, or **banner swimlanes** ("Data Construction & Training | Inference"). Dashed
   dividers/cross separate stages.
3. **Fill ONE panel as the exemplar**, leave the rest as stubs (SysGen: only P1 filled; Self-BioRAG:
   empty labelled grid).
4. **Block in monochrome line-art primitives, then skin.** Place plain glyphs (NN-graph, magnifier,
   doc-stack, cylinder, globe) in position first; add color fills, borders, labels in a later pass.
5. **Fill all panels from the SAME template — each baseline = the template minus one capability**, so
   the reader reads across (column→column / quadrant→quadrant) as "what does *Ours* add" (retrieval
   gate → self-reflection critic → biomedical corpus).
6. **Iterate labels / icons / wording in many near-identical passes — NOT the layout.** Once structure
   is set he refines only text & motifs: "select best evidence" → "Best evidence is selected with score
   of reflection tokens"; "Open-source LLM" → "License-Free LMM"; "Refined System" → "Filtered System";
   "Filter & Train" → "Train"; add a GPT icon; recolor a highlight. Many slide copies differ only in
   labels.

## Visual grammar
**Icon vocabulary (one icon = one fixed meaning, reused everywhere):**
- **Neural-net node-graph** = a language model (Generator / Instruction-tuned / Critic / Self-Reflection
  LM) — the universal "this is an LLM" mark. Plain head silhouette = base LLM; brain-with-circuit =
  trained / "with system role".
- **Magnifier** = retriever/retrieval · **database cylinder** = a dataset · **Erlenmeyer flask** = the
  raw instruction corpus · **document stack** = retrieved evidence.
- **Corpus logos carry the domain contrast:** **PMC building** = biomedical corpus vs **Wikipedia
  puzzle-globe** = general corpus.
- **ChatGPT/OpenAI swirl** = proprietary-API call / judge · **Python logo** = a code/filtering step.

**Fixed color-per-concept (identical across every panel — never recolor a concept):**
- **yellow/amber** = model boxes · **blue** = retriever/retrieval · **gray** = Query/Answer/data
  endpoints · **green** = self-reflection / reflection-tokens / the focal "ours" box.
- In worked-example text: **green highlight = special/reflection tokens, blue highlight = retrieved
  evidence, bold = salient facts.**
- In SysGen each of the 8 system-message components (Role/Content/Task/Action/Style/Background/Tool/
  Format) gets a fixed color, shown BOTH as nodes on a neural-net graph AND as the colored `<<Tag>>`
  markers in the example text.

**Domain variant by overlay, not redraw:** stamp a stethoscope / red medical-cross onto the generic
LM/retriever icon to mark the "Bio" version; swap the corpus logo (globe ↔ PMC) for general ↔ biomedical.

**Flow / shape conventions:** thin solid arrows for the main flow (**L→R across the pipeline, top→bottom
within a column**); **thick gray block arrows** between icons (SysGen); **dashed lines** = fan-out /
grouping (PMC → ①②③ candidates); **dashed curved arrows** = an iterative loop; **decision diamond**
with Yes/No exits for a gate; **circled ①②③** for parallel candidates.

**Embed the real worked example, color-coded — in every panel.** Not abstract boxes: paste an ACTUAL
artifact (a real `<<Role>>You are an AI code analysis assistant.<<Role>>` system message; a real MedQA
PCOS vignette with 4 options; a BRCA1/BRCA2 retrieval case) into rounded-rectangle cards, highlighted by
token/evidence/fact. Keep the verbatim full text on a **separate asset slide** and hand-truncate it into
the box. (This is the visual half of the writing rule "Fig 1 = one concrete worked example".)

**Typography:** **bold, often 2-line, centered label INSIDE** the colored box with the icon inline; a
**white title chip** on the box's top edge ("Case of [No Retrieval]", "MedQA"); phase names in **blue
title bars / slanted ribbon tabs**; system/dataset names (Self-BioRAG, PMC, MedQA) as prominent headers;
reflection tokens as **`[bracketed]`** chips.

**Layout structures (3 recurring):** (i) **column-per-method** with dashed vertical dividers;
(ii) **2×2 quadrant** with a dashed cross; (iii) **two-lane banner** = icon-flow column on the left +
worked-example cards stacked on the right.

## Apply-it checklist
1. Sketch the **concept + a formal `{before}→{after}` definition box** first; decide the single message.
2. **Scaffold empty panels + phase headers** (quadrant / dashed columns / banner swimlanes) before content.
3. **One fixed icon per role, one fixed color per concept**, identical across all panels.
4. **Same template per baseline panel, minus one capability** — the figure teaches one axis, read L→R.
5. **Embed a real, color-coded worked example** in every panel; keep verbatim text on a side slide, truncate in.
6. **Domain/variant = overlay a motif or swap the corpus logo**, don't redraw the icon.
7. Encode control flow by **shape**: diamond = gate, dashed fan-out = candidates, curved-dashed = loop, solid = main flow.
8. Lock the layout, then **iterate only labels/wording/icons** across copies — never re-lay-out late.

Source decks: `…/healthcare-research/paper_writing/reference/figures.pptx` (SysGen) + `figure.pptx` (Self-BioRAG).
