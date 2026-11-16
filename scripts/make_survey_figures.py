"""Figures for the survey paper.

Figure 1  the three literatures that bear on the base project
Figure 2  which of four concerns each of the fifteen sources addresses
Figure 3  the audit the base project proposes, with the evidence behind each step
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = "docs/figures"
os.makedirs(OUT, exist_ok=True)

INK = "#1a1a1a"
FILL = "#ffffff"
ACCENT = "#dce6f2"
WARM = "#f6e7c8"
DPI = 200


def canvas(w=6.2, h=4.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=DPI)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fill=FILL, size=6.6, bold=False, align="center"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.0",
                                linewidth=1.0, edgecolor=INK, facecolor=fill))
    if align == "center":
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
                color=INK, fontweight="bold" if bold else "normal", linespacing=1.4)
    else:
        ax.text(x + 2, y + h / 2, text, ha="left", va="center", fontsize=size,
                color=INK, fontweight="bold" if bold else "normal", linespacing=1.4)


def arrow(ax, p1, p2):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=10,
                                 linewidth=1.0, color=INK, shrinkA=0, shrinkB=0))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.06, facecolor="white")
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------- figure 1 ---
fig, ax = canvas(6.2, 3.5)
ax.text(50, 95, "Three literatures, one question", ha="center", fontsize=7.0, fontweight="bold")

colours = [ACCENT, ACCENT, ACCENT]
titles = ["Making the interval", "Judging the fit", "Moving the model"]
items = [
    ["split conformal [1], [3]", "group-conditional [1]", "quantile-based [4], [5]"],
    ["random cross-validation", "blocked / spatial CV [11]", "leakage audit [12], [13]"],
    ["support check [10]", "reweighting [8]", "label-shift correction [9]"],
]
for i, (title, rows) in enumerate(zip(titles, items)):
    x = 3 + i * 32.5
    ax.add_patch(FancyBboxPatch((x, 58), 29, 26, boxstyle="round,pad=0,rounding_size=1.0",
                                linewidth=1.1, edgecolor=INK, facecolor=colours[i]))
    ax.text(x + 14.5, 78.5, title, ha="center", fontsize=7.2, fontweight="bold")
    for j, row in enumerate(rows):
        ax.text(x + 14.5, 71.5 - j * 4.6, row, ha="center", fontsize=6.4)
    arrow(ax, (x + 14.5, 58), (50, 44))

box(ax, 17, 30, 66, 12,
    "One domain: skill, coverage and the cost of repair", fill=WARM, size=6.4, bold=True)
ax.text(50, 24, "no single source delivers this verdict", ha="center", fontsize=5.6,
        style="italic")
ax.text(50, 12, "base project: smallholder maize yield-interval models", ha="center",
        fontsize=5.6)
arrow(ax, (50, 30), (50, 17))
save(fig, "survey_fig1_taxonomy.png")

# ---------------------------------------------------------------- figure 2 ---
fig, ax = canvas(6.4, 5.2)
sources = [
    ("[1] Angelopoulos & Bates 2023", [1, 0, 0, 0]),
    ("[2] Vovk et al. 2005", [1, 0, 0, 0]),
    ("[3] Lei et al. 2018", [1, 0, 0, 0]),
    ("[4] Romano et al. 2019", [1, 0, 0, 0]),
    ("[5] Meinshausen 2006", [1, 0, 0, 0]),
    ("[6] Breiman 2001", [0, 0, 0, 0]),
    ("[7] Barber et al. 2023", [1, 0, 1, 0]),
    ("[8] Tibshirani et al. 2019", [1, 0, 1, 0]),
    ("[9] Podkopaev & Ramdas 2021", [0, 0, 1, 0]),
    ("[10] Meyer & Pebesma 2021", [0, 0, 1, 0]),
    ("[11] Roberts et al. 2017", [0, 1, 0, 0]),
    ("[12] Ploton et al. 2020", [0, 1, 0, 0]),
    ("[13] Kapoor & Narayanan 2023", [0, 1, 0, 0]),
    ("[14] Aramburu Merlos et al. 2024", [0, 0, 0, 0]),
    ("[15] Aramburu-Merlos et al. 2024", [0, 0, 1, 0]),
]
ax.text(50, 98, "Which concerns the fifteen sources address", ha="center", fontsize=7.0,
        fontweight="bold")
cols = ["interval\nbuilt", "evaluation\nhonest", "shift\nfound", "remedy\ncosted"]
for j, c in enumerate(cols):
    ax.text(58 + j * 10, 88.5, c, ha="center", va="center", fontsize=5.8, fontweight="bold", linespacing=1.35)
for i, (label, flags) in enumerate(sources):
    y = 82 - i * 4.6
    ax.text(54, y, label, ha="right", va="center", fontsize=6.0)
    for j, f in enumerate(flags):
        x = 55 + j * 10
        ax.add_patch(Rectangle((x, y - 1.7), 5.6, 3.6, linewidth=0.9, edgecolor=INK,
                               facecolor="#8fb3d9" if f else "white"))
ax.text(77, 8.5, "filled = addressed      empty = not addressed", ha="center", fontsize=6.0,
        style="italic")
ax.text(77, 3.5, "no source fills the fourth column", ha="center", fontsize=6.2,
        fontweight="bold")
save(fig, "survey_fig2_coverage.png")

# ---------------------------------------------------------------- figure 3 ---
fig, ax = canvas(6.2, 3.3)
ax.text(50, 95, "Audit proposed for the base project", ha="center", fontsize=7.0,
        fontweight="bold")
steps = [
    ("1. Check the split", "blocked design;\nreport inflation", "evidence: [11]-[13]"),
    ("2. Separate skill\nfrom calibration", "point transfer vs\ncoverage per domain", "evidence: [1], [3], [7]"),
    ("3. Diagnose the shift", "support, reweighting,\nlevel offset", "evidence: [8]-[10]"),
    ("4. Prescribe and cost", "remedy + labels\nrequired + width", "evidence: [9], [4]"),
]
centres = []
for i, (head, body_text, ev) in enumerate(steps):
    x = 2 + i * 24.5
    ax.add_patch(FancyBboxPatch((x, 50), 22, 34, boxstyle="round,pad=0,rounding_size=1.0",
                                linewidth=1.1, edgecolor=INK, facecolor=ACCENT))
    ax.text(x + 11, 73, head, ha="center", va="center", fontsize=5.6, fontweight="bold",
            linespacing=1.4)
    ax.text(x + 11, 61, body_text, ha="center", va="center", fontsize=6.2, linespacing=1.5)
    ax.text(x + 11, 53, ev, ha="center", va="center", fontsize=5.8, style="italic")
    centres.append(x + 11)
    if i < 3:
        arrow(ax, (x + 22, 67), (x + 24.5, 67))
box(ax, 20, 24, 60, 10, "readiness verdict for one target domain", fill=WARM, size=7.0,
    bold=True)
ax.plot([centres[0], centres[-1]], [44, 44], color=INK, linewidth=1.0)
for c in centres:
    ax.plot([c, c], [50, 44], color=INK, linewidth=1.0)
arrow(ax, (50, 44), (50, 34))
ax.text(50, 14, "what the base project adds: the four steps are reported together, "
                "for one domain, with a cost", ha="center", fontsize=5.6, style="italic")
save(fig, "survey_fig3_pipeline.png")

print("done")
