#!/usr/bin/env python3
"""Generate publication-quality figure templates for academic papers.

Outputs a self-contained Python script ready to be customized.

Supported figure types:
    bar, training-curve, heatmap, ablation, line, scatter,
    radar, violin, tsne, attention, lollipop, strip

Usage:
    python figure_template.py --type bar --output figure_script.py
    python figure_template.py --type lollipop --output figure_script.py
    python figure_template.py --type strip --output figure_script.py
    # Venue presets size the figure to the target column + tweak the style:
    python figure_template.py --type bar --venue neurips --output fig.py    # single col (3.25in)
    python figure_template.py --type bar --venue nature --output fig.py     # journal style (7pt, narrow)
    # Extra output formats (journals often require EPS or TIFF):
    python figure_template.py --type bar --format pdf,png,eps --output fig.py
    python figure_template.py --list-types
    python figure_template.py --list-venues
"""

import argparse
import sys

PREAMBLE = '''import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Publication-quality styling
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['DejaVu Serif', 'Times New Roman'],  # DejaVu primary: Times not installed & tectonic can't load it
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'axes.spines.top': False,
    'axes.spines.right': False,
})
__VENUE_OVERRIDE__

# Colorblind-friendly palette (Wong/Okabe-Ito + ColorBrewer-safe extras)
COLORS = ['#2196F3', '#FF5722', '#4CAF50', '#FFC107', '#9C27B0', '#607D8B', '#E91E63', '#00BCD4']

# Target figure width for the chosen venue (inches). Use as the first figsize arg.
FIG_WIDTH = __FIG_WIDTH__
# Output formats to emit; journals often require eps or tiff in addition to pdf.
SAVE_FORMATS = __SAVE_FORMATS__


def save_fig(name):
    """Save the current figure to every requested format at publication DPI."""
    for fmt in SAVE_FORMATS:
        kw = dict(bbox_inches='tight')
        if fmt in ('png', 'tiff', 'tif'):
            kw['dpi'] = 300
        plt.savefig(f'{name}.{fmt}', **kw)
    print('Figure saved:', ', '.join(f'{name}.{f}' for f in SAVE_FORMATS))


def sig_marker(ax, x1, x2, y, p, h=None):
    """Draw a significance bracket between x1 and x2 at height y.

    p -> stars: <=1e-3 '***', <=1e-2 '**', <=5e-2 '*', else 'n.s.'
    """
    s = '***' if p <= 1e-3 else '**' if p <= 1e-2 else '*' if p <= 5e-2 else 'n.s.'
    h = h if h is not None else (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.02
    ax.plot([x1, x1, x2, x2], [y, y + h, y + h, y], lw=1.0, c='black')
    ax.text((x1 + x2) / 2, y + h, s, ha='center', va='bottom', fontsize=10)
'''

TEMPLATES = {
    "bar": PREAMBLE + '''
# === Baseline Comparison Bar Chart ===
fig, ax = plt.subplots(figsize=(7, 4.5))

methods = ['Ours', 'Baseline A', 'Baseline B', 'Baseline C']
scores = [92.3, 88.1, 85.7, 83.2]
errors = [0.5, 0.8, 1.2, 0.9]

bars = ax.bar(methods, scores, yerr=errors, capsize=5,
              color=[COLORS[0]] + [COLORS[5]] * 3,
              edgecolor='white', linewidth=0.5)
ax.set_ylabel('Accuracy (%)')

for bar, score in zip(bars, scores):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.8,
            f'{score:.1f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "training-curve": PREAMBLE + '''
# === Training Curves (Loss + Accuracy) ===
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

epochs = np.arange(1, 51)
# Replace with actual data
train_loss = 2.0 * np.exp(-0.05 * epochs) + 0.3 + np.random.normal(0, 0.02, len(epochs))
val_loss = 2.2 * np.exp(-0.04 * epochs) + 0.4 + np.random.normal(0, 0.03, len(epochs))
train_acc = 100 * (1 - np.exp(-0.06 * epochs)) + np.random.normal(0, 0.5, len(epochs))
val_acc = 95 * (1 - np.exp(-0.05 * epochs)) + np.random.normal(0, 0.8, len(epochs))

ax1.plot(epochs, train_loss, label='Train', color=COLORS[0], linewidth=1.5)
ax1.plot(epochs, val_loss, label='Validation', color=COLORS[1], linewidth=1.5, linestyle='--')
ax1.set_xlabel('Epoch')
ax1.set_ylabel('Loss')
ax1.legend()
ax1.set_title('Training Loss')

ax2.plot(epochs, train_acc, label='Train', color=COLORS[0], linewidth=1.5)
ax2.plot(epochs, val_acc, label='Validation', color=COLORS[1], linewidth=1.5, linestyle='--')
ax2.set_xlabel('Epoch')
ax2.set_ylabel('Accuracy (%)')
ax2.legend()
ax2.set_title('Accuracy')

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "heatmap": PREAMBLE + '''
import seaborn as sns

# === Heatmap / Confusion Matrix ===
fig, ax = plt.subplots(figsize=(6, 5))

# Replace with actual data
class_names = ['Cat', 'Dog', 'Bird', 'Fish']
data = np.array([[45, 3, 2, 0], [4, 42, 1, 3], [1, 2, 44, 3], [0, 1, 2, 47]])

sns.heatmap(data, annot=True, fmt='d', cmap='Blues',
            xticklabels=class_names, yticklabels=class_names,
            ax=ax, square=True, linewidths=0.5)
ax.set_xlabel('Predicted')
ax.set_ylabel('True')
ax.set_title('Confusion Matrix')

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "ablation": PREAMBLE + '''
# === Ablation Study Grouped Bar Chart ===
fig, ax = plt.subplots(figsize=(8, 4.5))

datasets = ['Dataset A', 'Dataset B', 'Dataset C']
ablation_results = {
    'Full Model': [92.3, 89.1, 91.5],
    'w/o Component A': [88.7, 85.3, 87.2],
    'w/o Component B': [90.1, 87.5, 89.8],
    'w/o Component C': [86.4, 83.1, 85.0],
}

x = np.arange(len(datasets))
width = 0.18
for i, (method, scores) in enumerate(ablation_results.items()):
    offset = (i - len(ablation_results) / 2 + 0.5) * width
    bars = ax.bar(x + offset, scores, width, label=method, color=COLORS[i])

ax.set_ylabel('Accuracy (%)')
ax.set_xticks(x)
ax.set_xticklabels(datasets)
ax.legend(loc='upper right', fontsize=9)
ax.set_ylim(80, 95)

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "line": PREAMBLE + '''
# === Multi-Line Comparison Plot ===
fig, ax = plt.subplots(figsize=(7, 4.5))

x = np.linspace(0, 10, 50)
methods = {
    'Ours': np.sin(x) * 0.9 + 0.1,
    'Baseline A': np.sin(x) * 0.7 + 0.1,
    'Baseline B': np.sin(x) * 0.5 + 0.1,
}
markers = ['o', 's', '^']

for (name, y), color, marker in zip(methods.items(), COLORS, markers):
    ax.plot(x, y, label=name, color=color, linewidth=1.5,
            marker=marker, markevery=5, markersize=5)

ax.set_xlabel('X Axis Label')
ax.set_ylabel('Y Axis Label')
ax.legend()

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "scatter": PREAMBLE + '''
# === Scatter Plot with Regression Line ===
fig, ax = plt.subplots(figsize=(6, 5))

np.random.seed(42)
x = np.random.randn(100)
y = 0.8 * x + 0.3 + np.random.randn(100) * 0.3

ax.scatter(x, y, c=COLORS[0], alpha=0.6, s=30, edgecolors='white', linewidth=0.5)

# Regression line
m, b = np.polyfit(x, y, 1)
ax.plot(x, m*x + b, color=COLORS[1], linewidth=2, linestyle='--', label=f'y = {m:.2f}x + {b:.2f}')

ax.set_xlabel('X Variable')
ax.set_ylabel('Y Variable')
ax.legend()

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "radar": PREAMBLE + '''
# === Radar / Spider Chart (Multi-Metric Comparison) ===
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

categories = ['Accuracy', 'Precision', 'Recall', 'F1', 'Speed', 'Memory']
N = len(categories)

methods = {
    'Ours': [92, 91, 93, 92, 85, 78],
    'Baseline A': [88, 85, 90, 87, 90, 85],
    'Baseline B': [85, 82, 88, 84, 95, 92],
}

angles = [n / float(N) * 2 * np.pi for n in range(N)]
angles += angles[:1]

for i, (name, values) in enumerate(methods.items()):
    values += values[:1]
    ax.plot(angles, values, 'o-', linewidth=1.5, label=name, color=COLORS[i])
    ax.fill(angles, values, alpha=0.1, color=COLORS[i])

ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, size=10)
ax.set_ylim(70, 100)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "violin": PREAMBLE + '''
# === Violin Plot (Distribution Comparison) ===
fig, ax = plt.subplots(figsize=(8, 5))

np.random.seed(42)
data = {
    'Ours': np.random.normal(92, 2, 100),
    'Baseline A': np.random.normal(88, 3, 100),
    'Baseline B': np.random.normal(85, 4, 100),
}

positions = range(len(data))
parts = ax.violinplot([v for v in data.values()], positions=positions,
                       showmeans=True, showmedians=True)

for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(COLORS[i])
    pc.set_alpha(0.7)
parts['cmeans'].set_color('black')
parts['cmedians'].set_color('red')

ax.set_xticks(positions)
ax.set_xticklabels(list(data.keys()))
ax.set_ylabel('Accuracy (%)')

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "tsne": PREAMBLE + '''
from sklearn.manifold import TSNE

# === t-SNE Embedding Visualization ===
fig, ax = plt.subplots(figsize=(7, 6))

np.random.seed(42)
n_samples = 200
n_classes = 4
class_names = ['Class A', 'Class B', 'Class C', 'Class D']

# Generate sample embeddings (replace with your actual embeddings)
embeddings = np.vstack([
    np.random.randn(n_samples, 64) + i * 2 for i in range(n_classes)
])
labels = np.repeat(range(n_classes), n_samples)

tsne = TSNE(n_components=2, random_state=42, perplexity=30)
coords = tsne.fit_transform(embeddings)

for i in range(n_classes):
    mask = labels == i
    ax.scatter(coords[mask, 0], coords[mask, 1], c=COLORS[i],
              label=class_names[i], alpha=0.6, s=15, edgecolors='white', linewidth=0.3)

ax.set_xlabel('t-SNE dim 1')
ax.set_ylabel('t-SNE dim 2')
ax.legend(markerscale=2)

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "attention": PREAMBLE + '''
import seaborn as sns

# === Attention Heatmap ===
fig, ax = plt.subplots(figsize=(8, 6))

np.random.seed(42)
tokens_x = ['The', 'cat', 'sat', 'on', 'the', 'mat', '.']
tokens_y = ['The', 'cat', 'sat', 'on', 'the', 'mat', '.']

# Generate sample attention weights (replace with actual weights)
attention = np.random.dirichlet(np.ones(len(tokens_x)), size=len(tokens_y))

sns.heatmap(attention, annot=True, fmt='.2f', cmap='Blues',
            xticklabels=tokens_x, yticklabels=tokens_y,
            ax=ax, square=True, linewidths=0.5,
            cbar_kws={'label': 'Attention Weight'})
ax.set_xlabel('Key tokens')
ax.set_ylabel('Query tokens')
ax.set_title('Attention Weights')

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "lollipop": PREAMBLE + '''
# === Lollipop Chart (ranked comparison, less ink than bars) ===
fig, ax = plt.subplots(figsize=(FIG_WIDTH, 4.5))

methods = ['Ours', 'Baseline A', 'Baseline B', 'Baseline C', 'Baseline D']
scores = [92.3, 88.1, 85.7, 83.2, 79.4]

order = np.argsort(scores)             # ascending -> best on top
methods = [methods[i] for i in order]
scores = [scores[i] for i in order]
y = np.arange(len(methods))

ax.hlines(y, 0, scores, color=COLORS[5], linewidth=1.5, alpha=0.7)
ax.plot(scores, y, 'o', color=COLORS[0], markersize=8)
for yi, s in zip(y, scores):
    ax.text(s + 0.6, yi, f'{s:.1f}', va='center', fontsize=9)

ax.set_yticks(y)
ax.set_yticklabels(methods)
ax.set_xlabel('Accuracy (%)')
ax.set_xlim(left=min(scores) - 8)
ax.grid(axis='y', visible=False)

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',

    "strip": PREAMBLE + '''
import seaborn as sns

# === Violin + Strip (distribution + raw points; shows per-seed spread) ===
fig, ax = plt.subplots(figsize=(FIG_WIDTH, 5))

np.random.seed(42)
groups = ['Ours', 'Baseline A', 'Baseline B']
data = {g: np.random.normal(m, sd, 20)
        for g, m, sd in zip(groups, [92, 88, 85], [1.5, 2.5, 3.0])}

vals = [data[g] for g in groups]
parts = ax.violinplot(vals, positions=range(len(groups)),
                      showextrema=False, widths=0.7)
for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(COLORS[i]); pc.set_alpha(0.25)

for i, g in enumerate(groups):                # jittered raw points on top
    xj = np.random.normal(i, 0.05, len(data[g]))
    ax.scatter(xj, data[g], color=COLORS[i], s=14, alpha=0.8,
               edgecolors='white', linewidth=0.3, zorder=3)

ax.set_xticks(range(len(groups)))
ax.set_xticklabels(groups)
ax.set_ylabel('Accuracy (%)')
# Significance bracket example: sig_marker(ax, 0, 1, y=max top, p=0.003)
sig_marker(ax, 0, 1, y=float(np.max(np.concatenate(vals))) + 1, p=0.003)

plt.tight_layout()
save_fig('OUTPUT_NAME')
''',
}

# Venue/journal presets: (figure width in inches, rcParams override block).
# Width = single-column unless noted; pass figsize=(FIG_WIDTH, h) in the template.
VENUES = {
    "default":  (7.0,  ""),
    "neurips":  (3.25, "plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'legend.fontsize': 8})"),
    "icml":     (3.25, "plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'legend.fontsize': 8})"),
    "acl":      (3.15, "plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9, 'legend.fontsize': 8})"),
    "ieee":     (3.5,  "plt.rcParams.update({'font.size': 8, 'axes.labelsize': 8, 'legend.fontsize': 7})"),
    "neurips-wide": (6.75, "plt.rcParams.update({'font.size': 9, 'axes.labelsize': 9})"),  # double-column span
    # Nature/Science/Cell: sans-serif, ~7pt, single-column ~3.5in, thin spines.
    "nature":   (3.5, "plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans', 'Arial'], 'font.size': 7, 'axes.labelsize': 7, 'xtick.labelsize': 6, 'ytick.labelsize': 6, 'legend.fontsize': 6, 'axes.linewidth': 0.6})"),
    "science":  (3.5, "plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans', 'Arial'], 'font.size': 7, 'axes.labelsize': 7, 'xtick.labelsize': 6, 'ytick.labelsize': 6, 'legend.fontsize': 6, 'axes.linewidth': 0.6})"),
    "cell":     (3.35, "plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans', 'Arial'], 'font.size': 7, 'axes.labelsize': 7, 'xtick.labelsize': 6, 'ytick.labelsize': 6, 'legend.fontsize': 6, 'axes.linewidth': 0.6})"),
}


def main():
    if "--list-types" in sys.argv:
        print("Available figure types:")
        for name in sorted(TEMPLATES.keys()):
            print(f"  {name}")
        sys.exit(0)
    if "--list-venues" in sys.argv:
        print("Available venues (width in inches):")
        for name in VENUES:
            print(f"  {name:14s} {VENUES[name][0]}in")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Generate figure script templates")
    parser.add_argument("--type", required=True, choices=list(TEMPLATES.keys()),
                        help="Figure type")
    parser.add_argument("--output", "-o", default="figure_script.py",
                        help="Output script file")
    parser.add_argument("--name", default="figure", help="Output figure filename (without extension)")
    parser.add_argument("--venue", default="default", choices=list(VENUES.keys()),
                        help="Venue/journal preset (sizes the figure + tweaks style)")
    parser.add_argument("--format", default="png,pdf",
                        help="Comma-separated output formats, e.g. png,pdf,eps,tiff")
    parser.add_argument("--list-types", action="store_true")
    parser.add_argument("--list-venues", action="store_true")
    args = parser.parse_args()

    fig_width, venue_override = VENUES[args.venue]
    formats = [f.strip() for f in args.format.split(",") if f.strip()]

    script = (TEMPLATES[args.type]
              .replace("__VENUE_OVERRIDE__", venue_override)
              .replace("__FIG_WIDTH__", repr(fig_width))
              .replace("__SAVE_FORMATS__", repr(formats))
              .replace("OUTPUT_NAME", args.name))

    with open(args.output, "w") as f:
        f.write(script)

    print(f"Template written to {args.output} (venue={args.venue}, formats={formats})", file=sys.stderr)
    print(f"Run: python {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
