---
name: concept-infographic
description: Turn a research hypothesis, equation, or role decomposition into a clean academic-style infographic via an image-generation prompt recipe + a consistent design system (green="ours", blue=policy, orange=world-model). Use for hero-equation + role-card layouts, probabilistic factorizations, or per-domain role-comparison graphics for papers/slides/READMEs. For data-driven charts (bar/line/heatmap from raw numbers) use the figure-generation skill instead.
argument-hint: [hypothesis-or-equation]
---

# Research-Hypothesis Infographic Generator

A reusable skill for producing **clean, academic-style infographics** that visualize
ML/agent research concepts — especially **probabilistic factorizations** and
**role-decomposition diagrams** (e.g., Policy / World-Model / Prior).

Built from the "AgentPlanet" and "Qwen-AgentWorld" infographic series.

## Input

- `$0` — The hypothesis / equation / role split to visualize (free text).
- This skill produces an **image-generation prompt** (and design spec). For pixel-perfect
  math or data-driven charts, fall back to matplotlib (see §6) or the
  [[figure-generation]] skill.

---

## 1. When to use this skill

Trigger this skill when a user asks to:

- Turn a **research hypothesis / equation** into a presentable figure.
- Visualize a **role split** (e.g., `policy` vs `world model` vs `our method`).
- Create a **per-domain comparison table** as a graphic (rows = domains, columns = roles).
- Produce a **"hero equation + supporting cards"** layout for a paper, slide, or README.

Do **not** use it for photo-realistic images, charts from raw data (use the
**figure-generation** skill / matplotlib), or pixel-accurate math typesetting
(use LaTeX/matplotlib instead — see §6).

---

## 2. Core design system (keep these constant for a consistent series)

| Token            | Value                                  | Meaning                          |
|------------------|----------------------------------------|----------------------------------|
| Background       | light off-white (`#F8F8F6`-ish)         | clean, paper-like                |
| Policy color     | **blue** `#2563EB`                      | `policy / π / states → actions`  |
| World-model color| **orange** `#F59E0B`                    | `world model / W / (s,a) → s'`   |
| "Ours" color     | **green** `#16A34A`                     | the proposed method (emphasis)   |
| Typography       | clean **sans-serif**, high legibility   | -                                |
| Cards            | rounded rectangles + subtle drop shadow | modular blocks                   |
| Layout           | aligned grid, generous whitespace       | presentation-ready               |

**Convention:** the user's *own* contribution ("ours") is always the **green**, largest,
most-emphasized card. Baselines are blue/orange.

---

## 3. Two reusable layout templates

### Template A — "Role Decomposition" (per-domain table)
Rows = domains; each row card is split LEFT (policy/blue) vs RIGHT (world-model/orange),
with a domain pill on the far left and a capability tag.

Use when comparing **how two roles behave across N domains**.

### Template B — "Factorization Hero" (equation + 3 role cards)
Top: one large **hero equation** in a rounded panel + a one-line caption.
Middle: 2–4 **vertical role cards**, each with icon + math signature + subtitle + footer pill.
Bottom: a small banner clarifying the key insight; optional hierarchy visual.

Use when presenting a **probabilistic factorization** and naming each factor.

---

## 4. The prompt recipe (image-generation)

Build the generation prompt by filling this skeleton. Order matters:

```
A clean, modern academic infographic titled "<TITLE>".

TOP SECTION — a hero equation in a soft rounded panel, large math typography:
"<EQUATION>"
Below it a small caption: "<ONE-LINE INSIGHT>".

MIDDLE SECTION — <N> vertical role cards side by side, each rounded with a distinct color + icon:

CARD k (<COLOR>, labeled "<ROLE LABEL>"):
Icon: <SIMPLE LINE ICON>.
Title: "<MATH SIGNATURE, e.g. π : s → a>"
Subtitle: "<PLAIN-LANGUAGE MEANING>"
Footer pill: "<METHOD NAME>"
(repeat for each role; make the "ours" card GREEN, biggest, most emphasized)

BOTTOM SECTION — a small horizontal banner note: "<KEY DISTINCTION>".
(optional) hierarchy visual: <e.g. a planet sphere containing s0,s1,s2 nodes
connected by action arrows a0,a1>.

Style: minimalist tech/academic infographic, soft rounded cards, subtle drop shadows,
clean sans-serif typography, color scheme green (#16A34A) emphasis, blue (#2563EB),
orange (#F59E0B), light off-white background. Clear math notation, well-aligned,
balanced whitespace, presentation-ready, high quality.
```

**Aspect ratio:** use `portrait` for stacked cards / tables; `landscape` for 3 cards in a row.

---

## 5. Worked example (the AgentPlanet figure)

- **TITLE:** `AgentPlanet: Factorizing a World and the Actions Within It`
- **EQUATION:**
  `p(world, trajectory) = planet(s0, R) . PROD_t pi(a_t | s_t, R) . W(s_{t+1} | s_t, a_t, R)`
- **INSIGHT:** `Factorizing the full probability of a world + its trajectory yields exactly three roles.`
- **CARDS:**
  1. GREEN / **OURS — AgentPlanet** — `planet : empty -> (s0, R)` — "Generates the WORLD ITSELF — the PRIOR"
  2. BLUE / **Policy — Agent-World** — `pi : s -> a` — "ACT within the world (per-step conditional)"
  3. ORANGE / **World Model — Qwen-AgentWorld** — `W : (s,a) -> s'` — "DYNAMICS (per-step conditional)"
- **KEY DISTINCTION:** `pi and W are per-step conditionals; planet is the PRIOR over an entire world (s0 + R).`
- **HIERARCHY VISUAL:** a large planet sphere containing orbiting nodes s0,s1,s2 linked by action arrows a0,a1.

---

## 6. Quality notes & fallbacks

- **Generative text drift:** image models may mis-render subscripts/symbols. Keep equations
  SHORT; spell ambiguous glyphs (e.g., write "s0" not "s_0", "->" not arrows) in the prompt.
- **Need pixel-perfect math?** Render with matplotlib + LaTeX instead of an image model.
  For a full data/figure pipeline use the [[figure-generation]] skill; for a one-off
  equation panel, this minimal snippet (base conda env — NOT torchtitan) suffices:

```python
import matplotlib.pyplot as plt
plt.rcParams["text.usetex"] = False  # or True if a TeX install is available
fig, ax = plt.subplots(figsize=(10, 2)); ax.axis("off")
ax.text(0.5, 0.5,
        r"$p(\mathrm{world},\tau)=\mathrm{planet}(s_0,R)\prod_t \pi(a_t\mid s_t,R)\,W(s_{t+1}\mid s_t,a_t,R)$",
        ha="center", va="center", fontsize=18)
fig.savefig("equation.png", dpi=300, bbox_inches="tight")
```

- **Series consistency:** reuse the exact color hex codes and the green="ours" convention
  across every figure so a paper/deck looks unified.
- **Editing an existing figure:** prefer an image-edit call with the previous image as
  reference rather than regenerating from scratch.

---

## 7. Minimal checklist before delivering

- [ ] Title present and specific
- [ ] Hero equation short, glyphs spelled out
- [ ] "Ours" card is green + largest
- [ ] Baselines mapped to blue/orange consistently
- [ ] One-line insight + bottom key-distinction banner
- [ ] Correct aspect ratio (portrait for stacks, landscape for rows)
- [ ] Note to user: generative text may need a matplotlib fallback for precision
