"""Draw the UML figures for the proposal as PNGs (matplotlib, no binaries).

Four figures, matching what Review 1 and Review 2 ask for:
  1 use-case diagram    - actors and the auditor's services
  2 activity diagram    - the audit run, with its two decision points
  3 class diagram       - the five modules and their data
  4 deployment diagram  - what runs where, including the stored results

Layout rules used throughout: every connector starts and ends on a shape
boundary, labels are offset clear of lines, and boxes are sized from their text
so nothing overflows.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon

OUT = "docs/figures"
os.makedirs(OUT, exist_ok=True)

INK = "#1a1a1a"
FILL = "#ffffff"
ACCENT = "#dce6f2"
DPI = 200
FIGSIZE = (8.0, 4.8)


def canvas():
    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fill=FILL, size=8.5, bold=False, rounded=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounded}",
                                linewidth=1.1, edgecolor=INK, facecolor=fill))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
            color=INK, fontweight="bold" if bold else "normal")
    return (x, y, w, h)


def label_box(ax, x, y, w, h, name, detail, fill=ACCENT, size=7.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
                                linewidth=1.1, edgecolor=INK, facecolor=fill))
    ax.text(x + w / 2, y + h - 3.0, name, ha="center", va="center", fontsize=size + 0.4,
            fontweight="bold", color=INK)
    ax.plot([x, x + w], [y + h - 5.2, y + h - 5.2], color=INK, linewidth=0.8)
    ax.text(x + 1.4, y + h - 7.4, detail, ha="left", va="top", fontsize=size, color=INK,
            linespacing=1.45)
    return (x, y, w, h)


def oval(ax, cx, cy, w, h, text, fill=ACCENT, size=8.0):
    ax.add_patch(Ellipse((cx, cy), w, h, linewidth=1.1, edgecolor=INK, facecolor=fill))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=size, color=INK)


def diamond(ax, cx, cy, w, h, text, size=7.6):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, linewidth=1.1, edgecolor=INK, facecolor=FILL))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=size, color=INK, linespacing=1.35)


def arrow(ax, p1, p2, style="-|>", rad=0.0, dashed=False):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=10,
                                 linewidth=1.0, color=INK,
                                 connectionstyle=f"arc3,rad={rad}",
                                 shrinkA=0, shrinkB=0,
                                 linestyle="--" if dashed else "-"))


def tag(ax, x, y, text, ha="left"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=7.2, color=INK,
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none"))


def actor(ax, cx, cy, name):
    ax.add_patch(Circle((cx, cy + 7.5), 2.2, linewidth=1.1, edgecolor=INK, facecolor=FILL))
    ax.plot([cx, cx], [cy + 5.3, cy - 1.0], color=INK, linewidth=1.1)
    ax.plot([cx - 3.2, cx + 3.2], [cy + 2.6, cy + 2.6], color=INK, linewidth=1.1)
    ax.plot([cx, cx - 2.6], [cy - 1.0, cy - 5.4], color=INK, linewidth=1.1)
    ax.plot([cx, cx + 2.6], [cy - 1.0, cy - 5.4], color=INK, linewidth=1.1)
    ax.text(cx, cy - 9.4, name, ha="center", va="top", fontsize=8.2, color=INK,
            linespacing=1.3)


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.06, facecolor="white")
    plt.close(fig)
    print("wrote", path)


# ---------------------------------------------------------------- figure 1 ---
fig, ax = canvas()
ax.add_patch(FancyBboxPatch((22, 8), 56, 82, boxstyle="round,pad=0,rounding_size=1.0",
                            linewidth=1.0, edgecolor=INK, facecolor="none", linestyle="--"))
ax.text(50, 94, "AGROYIELD-ADAPT auditor", ha="center", fontsize=9.5, fontweight="bold")
ax.text(50, 88.5, "«system boundary»", ha="center", fontsize=7.4, style="italic")
uses = [
    ("Run split-integrity audit", 76),
    ("Separate skill from calibration", 61),
    ("Diagnose transport and level shift", 46),
    ("Prescribe remedy and label budget", 31),
    ("Generate readiness report", 16),
]
for text, y in uses:
    oval(ax, 50, y, 44, 11.0, text)
actor(ax, 9, 54, "Agricultural\nanalyst")
actor(ax, 94, 16, "Extension\nplanner")
for _, y in uses[:4]:
    arrow(ax, (12.5, 54), (28, y), style="-", rad=-0.04)
arrow(ax, (88.5, 16), (72.5, 16), style="-")
save(fig, "fig1_usecase.png")

# ---------------------------------------------------------------- figure 2 ---
fig, ax = canvas()
ax.add_patch(Circle((50, 95), 2.2, facecolor=INK, edgecolor=INK))
box(ax, 26, 79, 48, 10, "Load panel and record checksum", fill=ACCENT)
box(ax, 26, 65, 48, 10, "Fit model: random, cluster, LOCO", fill=ACCENT)
box(ax, 26, 51, 48, 10, "Compare intervals per domain", fill=ACCENT)
diamond(ax, 50, 41, 36, 12, "Inflation or gap\nover tolerance?")
diamond(ax, 50, 27, 36, 12, "Labels available\nfor target domain?")
box(ax, 26, 8, 48, 10, "Emit readiness report", fill=FILL)
box(ax, 78, 36, 20, 10, "Flag split risk", fill=FILL, size=8.0)
box(ax, 2, 22, 20, 10, "Request local labels", fill=FILL, size=8.0)

arrow(ax, (50, 92.8), (50, 89))
arrow(ax, (50, 79), (50, 75))
arrow(ax, (50, 65), (50, 61))
arrow(ax, (50, 51), (50, 47))
arrow(ax, (50, 35), (50, 33))
tag(ax, 52, 34, "yes")
arrow(ax, (50, 21), (50, 18))
tag(ax, 52, 19.5, "yes")
arrow(ax, (68, 41), (78, 41))
tag(ax, 71, 43, "yes")
arrow(ax, (88, 36), (88, 13), style="-")
arrow(ax, (88, 13), (74, 13), style="-")
arrow(ax, (32, 27), (22, 27), style="-")
tag(ax, 24, 29, "no")
arrow(ax, (12, 22), (12, 13), style="-")
arrow(ax, (12, 13), (26, 13), style="-")
save(fig, "fig2_activity.png")

# ---------------------------------------------------------------- figure 3 ---
fig, ax = canvas()
ax.text(50, 95, "audit pipeline and its data", ha="center", fontsize=9.5, fontweight="bold")
label_box(ax, 2, 62, 29, 30, "Panel", "path\nn_rows, n_countries\ncluster_key()\nbuild_matrix()")
label_box(ax, 35.5, 62, 29, 30, "SplitAudit", "designs\ntrees, seed\nmake_splits()\nevaluate()")
label_box(ax, 69, 62, 29, 30, "CalibrationAudit", "alpha\ndomains\ncoverage()\nwidth()")
label_box(ax, 35.5, 14, 29, 30, "TransportDiagnosis", "di, w1, ess\nlevel_offset\nout_of_area()\nflag()")
label_box(ax, 69, 14, 29, 30, "Remedy", "strategy\nlabel_budget\napply()\nexpected_width()")
label_box(ax, 2, 14, 29, 30, "ReadinessReport", "verdicts\nemit_json()\nemit_html()")

arrow(ax, (31, 77), (35.5, 77))          # Panel -> SplitAudit
arrow(ax, (64.5, 77), (69, 77))          # SplitAudit -> CalibrationAudit
arrow(ax, (50, 62), (50, 44))            # SplitAudit -> TransportDiagnosis
arrow(ax, (83.5, 62), (83.5, 44))        # CalibrationAudit -> Remedy
arrow(ax, (64.5, 29), (69, 29))          # TransportDiagnosis -> Remedy
arrow(ax, (83.5, 14), (83.5, 9), style="-")
arrow(ax, (83.5, 9), (16.5, 9), style="-")
arrow(ax, (16.5, 9), (16.5, 14))         # Remedy -> ReadinessReport
save(fig, "fig3_class.png")

# ---------------------------------------------------------------- figure 4 ---
fig, ax = canvas()
ax.add_patch(FancyBboxPatch((4, 6), 92, 88, boxstyle="round,pad=0,rounding_size=1.0",
                            linewidth=1.0, edgecolor=INK, facecolor="none", linestyle="--"))
ax.text(50, 90, "«device» analyst workstation (Windows 11, no server)", ha="center",
        fontsize=8.6)
box(ax, 8, 54, 34, 28, "Python 3.13\nagroyield_adapt\n+ pinned environment", fill=ACCENT)
box(ax, 58, 54, 34, 28, "SQLite\nresults/audit.db", fill=ACCENT)
box(ax, 8, 16, 34, 22, "Panel CSV\nSHA-256 verified", fill=FILL)
box(ax, 58, 16, 34, 22, "Report artefact\nHTML + JSON", fill=FILL)

arrow(ax, (42, 68), (58, 68))
tag(ax, 50, 71, "writes verdicts", ha="center")
arrow(ax, (25, 38), (25, 54))
tag(ax, 27, 46, "reads")
arrow(ax, (75, 54), (75, 38))
tag(ax, 77, 46, "renders")
save(fig, "fig4_deployment.png")

print("done")
