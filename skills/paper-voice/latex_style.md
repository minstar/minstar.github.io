# minstar's LaTeX formatting house style — reference for `/paper-voice`

Concrete, reusable LaTeX conventions extracted **verbatim from his real OLAPH source** (ICLR 2025; he
is 1st author). Most are venue-agnostic house style; where the active **AAAI OpenBioRQ** paper differs,
it's tagged `[venue]`. Companions: `authored_corpus_style.md` (writing voice), `SKILL.md` (the five
moves). Faithful — every recipe is how he actually wrote it.

## Package stack (his real preamble)
`booktabs` (the only table-rule commands he uses), `multirow`, `array`, `tabularx`, `adjustbox`,
`graphicx`, `amsmath`/`amssymb`/`amsfonts`/`bm`/`upgreek`/`mathtools`/`nicefrac`, `xcolor`+`color`+
`soul`, `caption`, `hyperref`+`cleveref`, `natbib`, `pifont`, `algorithm2e`, `subfigure`+`subcaption`,
`wrapfig`, `makecell`, `diagbox`, `arydshln`, `scalerel`+`xparse`.
**Loaded-but-UNUSED — do not assume them:** `makecell`, `subcaption`/`subfigure`, `cleveref` (`\cref`),
`soul` (`\hl`/`\ul`), `diagbox`, `arydshln` (`\hdashline`), `algorithm2e` — all loaded yet **never
invoked in the body**. His real toolkit is a narrow subset of the preamble.

## Custom macros (his own)
- `\cmark`=`\ding{51}` (✓), `\xmark`=`\ding{55}` (✗) — used in *figure captions* as a legend symbol,
  not in table cells.
- Color-text shorthands `\red{}` `\blue{}` `\cyan{}` `\yellow{}` `\black{}` `\dandelion{}`; palette
  `greencolor`#8CD0A4, `yellowcolor`#F9D17C (muted; in OLAPH used only in one annotated equation).
- `\emojione`/`\emojitwo` via `scalerel` = inline GitHub / HuggingFace icons — placed in the **abstract
  footnotes** linking code/data (`\href` to github.com/dmis-lab/… and huggingface.co/datasets/…).
- Drafting: `\fix`/`\new` = `\marginpar{FIX|NEW}`.

## Tables — the dominant recipe (used ~10× identically)
`\caption` ABOVE → `\centering` → `{\resizebox{1.0\textwidth}{!}{ booktabs tabular }}{}` → `\label` →
`\vspace{-10pt}`. **Width control is always `\resizebox`, never `\small`/`\adjustbox`.** booktabs only
(`\toprule/\midrule/\cmidrule{a-b}/\bottomrule`) — **no vertical rules, no `\hline`, no dashed lines,
no `\diagbox`, no cell color.** Two-row headers = stacked
`\multirow{2}{*}{\begin{tabular}[c]{@{}c@{}}\textbf{..}\\\textbf{..}\end{tabular}}` + a spanning
`\multicolumn{N}{c}{\textbf{..}}` over a `\cmidrule`. In-cell line breaks / `\pm` stats = nested
`\begin{tabular}[c]{@{}c@{}}..\\..\end{tabular}` (**not `\makecell`**); std as `22.3~$\pm$~6.5`.

**Result-cell emphasis — two documented modes (pick one, don't mix):**
- **(OLAPH)** baseline value + improvement as `(+0.33)`/`(-1.9)` delta in parens; **best is NOT bolded.**
- **(Self-BioRAG)** `\textbf{}` the best within a fair-comparison bracket (e.g. per param-size).
Only **headers** are bolded in both.

Canonical template (trimmed, `6.Experimental.tex`):
```latex
\begin{table*}[]
\caption{We use \textbf{MedLFQA} to evaluate five open-foundation models. ... numbers in parentheses
represent the improvement when applying our \textbf{\textsc{Olaph}} framework for one step.}
\vspace{-0.1cm}
\centering
{\resizebox{1.0\textwidth}{!}{
\begin{tabular}{l l lllll }
\toprule
\multicolumn{1}{c}{\multirow{2}{*}{\begin{tabular}[c]{@{}c@{}}\textbf{MedLFQA}\\ \textbf{Dataset}\end{tabular}}} & ... & \multicolumn{5}{c}{\textbf{Open LM (+\textsc{Olaph} Step-1)}} \\ \cmidrule{3-7}
 & & \multicolumn{1}{c}{\textbf{LLaMA2}} & ... & \textbf{BioMistral} \\ \midrule
\multirow{3}{*}{LiveQA} & Words Composition & 7.4 (+0.33) & ... \\
 & Semantic Similarity & 64.7 (+2.3) & ... \\
 & Factuality & 16.1 (+26.2) & ... \\ \midrule
... \bottomrule
\end{tabular}}}{}
\label{tab:main}
\vspace{-10pt}
\end{table*}
```
Single-column prompt/example boxes: one-col `{ l }` tabular, centered bold title row, content via
explicit `\\`, `\resizebox{0.98\textwidth}`, caption BELOW. `\resizebox` widths actually used: `1.0`
(default), `0.98` (text boxes), `0.85`/`0.8`, `0.65\columnwidth` (a boxed equation).

## Figures — two real modes
**(a) Multi-panel `figure*[t]`:** bare `\includegraphics[width=.48\columnwidth]{...}` side by side,
` \\` to start a new row, `\vspace{-0.3cm}` before caption. **He does NOT use real `\begin{subfigure}`**
— panels are juxtaposed includegraphics sharing ONE caption that names positions ("Top Left", "Bottom
Right").
**(b) `wrapfigure{R}{0.45\textwidth}`** in-flow side figure, image ~`0.43\textwidth`, `\vspace{-0.25cm}`
to pull up. Full-width architecture fig = `\includegraphics[width=\textwidth]{...model_figure.pdf}` in
`figure*[t!]`. Placement almost always `[t]`/`[t!]`.

## Captions
Caption ABOVE tables, BELOW figures. **Long & explanatory: 3–6 sentences** — restate the setup, name
every panel, and usually END ON THE TAKEAWAY ("We observe that starting with SFT shows degradation, but
… highest effectiveness with iterative alignment tuning."). Bold the **system/dataset name
mid-sentence** (`\textbf{MedLFQA}`), not a `\textbf{Lead-in:}` prefix.

## Equations / notation
Numbered `\begin{equation}` + inline `\label{eq:..}`, preceded by `\vspace{5pt}`, introduced by **"We
compute/train … as below,"** and followed by a **"where $x$ refers to …, $D_*$ refers to …"** gloss
defining *every* symbol. Multi-line (e.g. a DPO loss) = unnumbered `\begin{align*}`. Operators as
upright `\text{max}`/`\text{log}`/`\text{contradicts}` (not `\max`). Metric names small-caps even in
math: `\textsc{Hallucination}`. The eval-metric eq is the ONLY colored object —
`\underbrace{..}_{\parbox{62pt}{\scriptsize\centering Words\\Composition}}` term annotations via
`\red/\blue/\black`.
```latex
\vspace{5pt}
\begin{equation}
    \pi_{SFT} = \underset{\pi}{\text{max}} \mathbb{E}_{(x, a^*) \sim D_*} ~\text{log}~ \pi(a^* | x)
\end{equation}
where $\pi$ refers to the large language model, $x$ refers to the question, $a^*$ ... and $D_*$ refers to ...
```

## Citations  [venue-dependent]
- **OLAPH/ICLR:** 100% `\citep` (natbib author-year), attached with a `~` non-breaking space; **stacks
  many keys in one** `\citep{a,b,c,d}`; even when the author is the grammatical subject he keeps
  `\citep` ("the authors from~\citep{manes2024k} provide …") — never `\citet`/`\citealp`/`\cite`.
- **OpenBioRQ/AAAI:** `\cite` numeric, **no space after comma**, year-ordered (see SKILL.md Citations);
  `\citep` is undefined there.

## In-text emphasis  (counts in OLAPH: `\textbf`×181, `\textsc`×70, `\textit`×3, `\paragraph`×8; `\texttt`/`\emph`/soul = 0)
- **`\textsc{SystemName}` is the signature** — the framework is *always* `\textsc{Olaph}`, doubled at
  definition `\textbf{\textsc{Olaph}}`; metrics `\textsc{FActScore}`/`\textsc{Hallucination}`.
  [OpenBioRQ uses an `\openbiorq{}` macro for the same role.]
- `\textbf` for dataset/system names on important mention, the **backronym** (`\textbf{O}ptimizing
  \textbf{L}arge …`), and labels inside example boxes (`\textbf{Question}:`).
- `\paragraph{Title-Case Lead.}` (period INSIDE braces) as lightweight finding/setup headers —
  `\paragraph{RQ 1.}`, `\paragraph{Training Setup.}`, `\paragraph{Sensitivity Analysis of $\alpha_3$.}`.
- `\textit` reserved for quoted example questions only. **`\texttt`, `\emph`, soul `\hl`/`\ul` never
  used** in OLAPH. [Contrast: OpenBioRQ DOES use `\texttt{}` for field/tool names and `\emph{}` — era
  difference.]

## Cross-refs
`Table~\ref{tab:..}` / `Figure~\ref{fig:..}` / `Equation~\ref{eq:..}` / `Section~\ref{sec:..}` /
`Appendix~\ref{app:..}` — type word written manually with `~` (cleveref loaded but `\cref` unused).
Label prefixes strict: `tab:`/`fig:`/`eq:`/`sec:`/`app:`.

## Venue/era divergences (OLAPH 2024 ↔ OpenBioRQ 2026)
| | OLAPH (ICLR, DMIS-era) | OpenBioRQ (AAAI, current) |
|---|---|---|
| citations | `\citep` natbib author-year | `\cite` numeric, no-space-after-comma |
| em-dash | **avoided** (colon-unpack + (e.g.)) | **used** heavily (`---`) |
| `\texttt`/`\emph` | never | used (field/tool names, emphasis) |
| intro open | broad ("In the medical domain…") | concrete-first hook |
Pick per the target paper; for the active OpenBioRQ follow the right column.
