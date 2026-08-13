---
name: figure-generation
description: Generate publication-quality scientific figures using matplotlib/seaborn with a three-phase pipeline (query expansion, code generation with execution, VLM visual feedback). Handles bar charts, line plots, heatmaps, training curves, ablation plots, and more. Use when the user needs figures, plots, or visualizations for a paper.
argument-hint: [figure-description]
---

# Scientific Figure Generation

Generate publication-quality figures for research papers.
Adapted from MatPlotAgent (lingzhi227/agent-research-skills) for minstar's environment.

## Input

- `$0` — Description of the desired figure
- `$1` — (Optional) Path to data file (CSV, JSON, NPY, PKL) or results directory

## Phase 0: Dependency Precheck (DO THIS FIRST)

`matplotlib`/`seaborn` live in **base** conda env here (NOT torchtitan — that is
training-only, see [[feedback_torchtitan_env]]). `sklearn` (for t-SNE) is also in base.
Confirm before generating any code:

```bash
python -c "import matplotlib; matplotlib.use('Agg'); import seaborn, sklearn; print('ok')"
```

If it fails: `pip install -q matplotlib seaborn` (sklearn already present). Never run plot
scripts under the torchtitan env.

## Scripts

### Generate figure template
```bash
python ~/.claude/skills/figure-generation/scripts/figure_template.py --type bar --output figure_script.py --name comparison
python ~/.claude/skills/figure-generation/scripts/figure_template.py --list-types
python ~/.claude/skills/figure-generation/scripts/figure_template.py --list-venues
```

Available types: `bar`, `training-curve`, `heatmap`, `ablation`, `line`, `scatter`, `radar`, `violin`, `tsne`, `attention`, `lollipop`, `strip`

### Venue / journal presets (`--venue`)
Size the figure to the **target column** and tweak the style automatically — ask which venue
*before* generating, then pass it. Width is exposed in the script as `FIG_WIDTH` (use it as the
first `figsize` arg). Generated scripts always inherit the chosen venue's font rcParams.

| Venue | Width | Style |
|-------|-------|-------|
| `neurips` / `icml` | 3.25in | serif, 9pt (single column) |
| `acl` | 3.15in | serif, 9pt |
| `ieee` | 3.5in | serif, 8pt |
| `neurips-wide` | 6.75in | serif, 9pt (double-column span) |
| `nature` / `science` | 3.5in | **sans-serif (DejaVu Sans)**, 7pt, thin spines |
| `cell` | 3.35in | sans-serif, 7pt |
| `default` | 7.0in | serif, 11pt (slides/preview) |

```bash
# single-column NeurIPS bar chart, journal EPS+TIFF for a Nature submission
python .../figure_template.py --type bar --venue neurips --name fig1 -o fig1.py
python .../figure_template.py --type strip --venue nature --format pdf,png,eps,tiff -o fig2.py
```

### Output formats (`--format`)
Default `png,pdf`. Add `eps`/`tiff` when a journal requires them (`--format pdf,png,eps,tiff`).
The shared `save_fig(name)` helper emits every format at 300 DPI. Note: EPS can't store
transparency (alpha artists render opaque) — a benign warning, expected for `nature`/`science`.

### Significance markers
The preamble ships `sig_marker(ax, x1, x2, y, p)` — draws a bracket between two x-positions and
auto-stars the p-value (`***`≤1e-3, `**`≤1e-2, `*`≤5e-2, else `n.s.`). The `strip` template
demonstrates it. Use for any bar/box/violin comparison that needs statistical annotation.

## Three-Phase Pipeline (from MatPlotAgent)

### Phase 1: Query Expansion
Expand the user's figure description into step-by-step coding specifications using the prompts in `references/figure-prompts.md`. Determine: figure type, data mapping (x/y/color/hue), style requirements, paper conventions.

### Phase 2: Code Generation with Execution Loop (up to 4 retries)
1. Generate a self-contained Python script using the template from `scripts/figure_template.py` as a starting point
2. Write script to a temp file and execute: `python figure_script.py`
3. If error: capture traceback, feed back, regenerate (see ERROR_PROMPT in references)
4. If no `.png` produced: add explicit save instruction, retry
5. On success: report the generated figure path

### Phase 3: Visual Refinement (planner → stylist → **critic**)
Read the generated PNG file (Read tool — you ARE the VLM here, no external model call) and
visually inspect using the VLM feedback prompts from `references/figure-prompts.md`. Run two
distinct lenses (PaperBanana-style role split) rather than one pass:
- **Stylist** — Does the figure type match the request? Labels/titles/legends correct? Color
  scheme consistent and colorblind-safe? Axis scales sensible? Text readable at *print* size?
- **Critic** — Would this pass the target venue's guidelines? Specifically: width matches the
  column (`--venue`), no chartjunk, no default matplotlib title (use the LaTeX caption), error
  bars/significance present where claimed, fonts not shrunk below ~6pt at final size.

If improvements needed: generate corrective instructions and re-execute.

## References

- All MatPlotAgent prompts: `~/.claude/skills/figure-generation/references/figure-prompts.md`
- Figure templates: `~/.claude/skills/figure-generation/scripts/figure_template.py`

## Output

Both PNG (preview, 300 DPI) and PDF (vector, for paper) formats. Plus the LaTeX include code:

```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\linewidth]{figures/figure_name.pdf}
    \caption{Description. Best viewed in color.}
    \label{fig:figure_name}
\end{figure}
```

## Quality Requirements
- DPI ≥ 300, or vector PDF
- Colorblind-friendly palette (no red-green only)
- All text ≥ 8pt at print size
- Consistent styling across all paper figures
- No matplotlib default title — use LaTeX caption
- **Font: DejaVu Serif (primary).** Times New Roman is NOT installed and the tectonic build
  also cannot load it (over-estimates page count ~10-15%, see [[healthcare_paper_build_toolchain]]).
  The template already lists DejaVu Serif first so a figure's fonts match the compiled PDF.

## Integration with paper workflow (minstar)
- Figures land in the paper repo's `figures/` dir; paste the LaTeX include block into the
  section being written with [[paper-voice]].
- Build the paper with the `tex` conda env (tectonic), see [[healthcare_paper_build_toolchain]]
  and [[ko_widesearch_paper_build]]. For final page-count truth use Overleaf, not local tectonic.

## Out of scope (deliberately not internalized)
- **Mermaid / schematic-diagram tools** — papers want vector pipeline/architecture diagrams;
  for those use TikZ in the LaTeX directly, not a raster export. This skill stays matplotlib/
  seaborn statistical plots only.
- **Text→image generators (gpt-image-2, PaperBanana's Gemini image path)** — external image
  API, produces raster AI art with no reproducible data binding. Unsuitable for quantitative
  paper figures. Internalized instead: PaperBanana's venue-guideline + planner/stylist/critic
  idea, and K-Dense's journal presets / significance markers / EPS-TIFF output — all native
  matplotlib, fully reproducible.

## Related Skills
- Downstream: `paper-voice`, `paper-main-appendix`
