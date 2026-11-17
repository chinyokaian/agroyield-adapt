"""Write the literature workbook, the Mendeley RIS and the PRISMA figure.

All three are generated from docs/litreview/corpus.json so the counts in the
diagram, the workbook and the reference file cannot drift apart.
"""

from __future__ import annotations

import json
import os
import re

import matplotlib
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = "docs/litreview"
XLSX = "Literature_review_AGROYIELD-ADAPT.xlsx"
FIG = "docs/figures/prisma_flow.png"

data = json.load(open(f"{OUT}/corpus.json", encoding="utf-8"))
corpus = data["corpus"]
counts = json.load(open(f"{OUT}/prisma_counts.json", encoding="utf-8"))

# ---- eligibility split -----------------------------------------------------
SPECIFIC = re.compile(
    r"conformal|prediction interval|interval forecast|coverage|quantile regression|"
    r"uncertainty quantif|calibrat|spatial cross-valid|cross-validat|leakage|"
    r"applicabilit|transferab|distribution shift|covariate shift|"
    r"model evaluation|prediction error|accuracy assessment|robustness|"
    r"extrapolat|generalisa|generaliza", re.I)

cited = set()
if os.path.exists(f"{OUT}/cited_keys.json"):
    cited = set(json.load(open(f"{OUT}/cited_keys.json", encoding="utf-8")))

included, background = [], []
for r in corpus:
    key = r["doi"] or r["title"]
    is_in = key in cited if cited else bool(SPECIFIC.search(f"{r['title']} {r['abstract']}"))
    (included if is_in else background).append(r)

print(f"corpus {len(corpus)} | included in synthesis {len(included)} | background {len(background)}")

# ---- derived columns -------------------------------------------------------
METHOD_RULES = [
    ("conformal prediction", r"conformal"),
    ("quantile regression", r"quantile regression|quantile forest"),
    ("random forest", r"random forest"),
    ("gradient boosting", r"xgboost|boost(ed|ing) (tree|regress)|lightgbm|catboost"),
    ("deep learning", r"deep (learning|neural)|neural network|cnn|lstm|transformer"),
    ("remote sensing", r"remote sensing|satellite|sentinel|landsat|modis|ndvi"),
    ("process-based crop model", r"process-based|dssat|apsim|ceres|simulation model"),
    ("spatial statistics", r"kriging|geostatist|spatial autocorrelat|variogram"),
    ("Bayesian inference", r"bayesian"),
    ("meta-analysis", r"meta-analys"),
    ("field experiment", r"field experiment|trial data|plot trial|on-farm trial"),
    ("systematic review", r"systematic (literature )?review|scoping review"),
    ("survey data", r"household survey|farm survey|questionnaire|panel data"),
    ("statistical regression", r"regression|econometric|mixed[- ]effects"),
]


FALLBACK = [
    ("review or synthesis", r"we review|this review|we synthesi|literature"),
    ("comparative evaluation", r"we (assess|evaluate|compare|test|benchmark)"),
    ("data-driven modelling", r"data-driven|machine learning|statistical model"),
    ("simulation", r"simulat"),
]


def methodology(text: str) -> str:
    hits = [name for name, pat in METHOD_RULES if re.search(pat, text, re.I)]
    if hits:
        return "; ".join(hits[:3])
    soft = [name for name, pat in FALLBACK if re.search(pat, text, re.I)]
    return "; ".join(soft[:2]) if soft else "state method from the full text"


def first_sentence(text: str, limit: int = 190) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return "Abstract not available in the index; summarise from the full text."
    m = re.match(r"(.+?[.!?])\s", text + " ")
    sentence = (m.group(1) if m else text)[:limit].strip()
    return sentence


def gap(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    m = re.search(r"(however[, ]|future (work|research)|remains? (unclear|unknown|limited)|"
                  r"limited to|has not been|yet to be|little is known|"
                  r"not (yet )?(been )?(addressed|examined|evaluated))[^.]{0,160}\.", text, re.I)
    if m:
        return m.group(0).strip()[:200]
    return ("No limitation stated in the abstract; record it from the full text."
            if text else "Confirm from the full text.")


# ---- workbook --------------------------------------------------------------
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Literature Review"
HEAD = ["Authors", "Year", "Journal/Conference", "Title", "Methodology", "Remark",
        "Research Gap", "Publisher", "DOI", "In review"]
ws.append(HEAD)

thin = Side(style="thin", color="BFBFBF")
for c in range(1, len(HEAD) + 1):
    cell = ws.cell(row=1, column=c)
    cell.font = Font(bold=True, size=10, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F3864")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = Border(bottom=thin)

rows = included + background
for r in rows:
    authors = r["authors"]
    a = ", ".join(authors[:4]) + (", et al." if len(authors) > 4 else "")
    text = f"{r['title']} {r['abstract']}"
    ws.append([a, r["year"], r["venue"], r["title"], methodology(text),
               first_sentence(r["abstract"]), gap(r["abstract"]),
               r["publisher"], r["doi"], "Yes" if r in included else "No (background)"])

widths = [30, 7, 30, 52, 26, 55, 45, 14, 26, 15]
for i, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    for cell in row:
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        cell.font = Font(size=9)

# a second sheet documenting the derivation, so nothing looks hand-waved
ws2 = wb.create_sheet("Method and counts")
notes = [
    ["Systematic literature review — method and counts"],
    [""],
    ["Search executed", counts["executed"]],
    ["Index", "OpenAlex (title and abstract), no date restriction"],
    ["Publishers kept", ", ".join(counts["publishers"])],
    ["Records identified", counts["identified"]],
    ["Duplicates removed", counts["duplicates_removed"]],
    ["Records screened", counts["screened"]],
    ["Excluded at screening", counts["excluded_screening"]],
    ["Records meeting criteria", counts["met_criteria"]],
    ["Corpus in Mendeley library", len(corpus)],
    ["Included in the review synthesis", len(included)],
    ["Background only (in library, not synthesised)", len(background)],
    ["Open-access PDFs downloaded", counts["pdfs_downloaded"]],
    [""],
    ["Queries"],
]
for q in counts["queries"]:
    notes.append(["", q])
notes += [
    [""],
    ["Column derivation"],
    ["Methodology", "Detected from method terms in the title and abstract"],
    ["Remark", "First sentence of the abstract"],
    ["Research Gap", "Limitation sentence found in the abstract; otherwise flagged for full-text reading"],
    ["Action required", "Confirm Methodology, Remark and Research Gap against the PDF for every row"],
]
for row in notes:
    ws2.append(row)
ws2.column_dimensions["A"].width = 34
ws2.column_dimensions["B"].width = 95
for row in ws2.iter_rows():
    for cell in row:
        cell.alignment = Alignment(vertical="top", wrap_text=True)
ws2["A1"].font = Font(bold=True, size=12)

wb.save(XLSX)
print(f"wrote {XLSX} with {len(rows)} rows")

# ---- RIS for Mendeley ------------------------------------------------------
def ris_escape(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


lines: list[str] = []
for r in rows:
    lines.append("TY  - JOUR")
    for a in r["authors"]:
        lines.append(f"AU  - {ris_escape(a)}")
    lines.append(f"TI  - {ris_escape(r['title'])}")
    lines.append(f"PY  - {r['year']}")
    lines.append(f"JO  - {ris_escape(r['venue'])}")
    lines.append(f"PB  - {ris_escape(r['publisher'])}")
    if r["volume"]:
        lines.append(f"VL  - {r['volume']}")
    if r["issue"]:
        lines.append(f"IS  - {r['issue']}")
    if r["first_page"]:
        lines.append(f"SP  - {r['first_page']}")
    if r["last_page"]:
        lines.append(f"EP  - {r['last_page']}")
    if r["doi"]:
        lines.append(f"DO  - {r['doi']}")
    if r["landing"]:
        lines.append(f"UR  - {r['landing']}")
    if r["abstract"]:
        lines.append(f"AB  - {ris_escape(r['abstract'])[:1200]}")
    lines.append("ER  - ")
    lines.append("")
open(f"{OUT}/AGROYIELD-ADAPT.ris", "w", encoding="utf-8").write("\n".join(lines))
print(f"wrote {OUT}/AGROYIELD-ADAPT.ris with {len(rows)} records")

# ---- PRISMA diagram --------------------------------------------------------
INK = "#1a1a1a"
fig, ax = plt.subplots(figsize=(6.3, 7.4), dpi=200)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")


def box(x, y, w, h, text, fill="#ffffff", size=7.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8",
                                linewidth=1.0, edgecolor=INK, facecolor=fill))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
            color=INK, linespacing=1.45)


def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=INK, linewidth=1.0))


ax.text(50, 97, "PRISMA 2020 flow of information", ha="center", fontsize=8.6, fontweight="bold")

ax.text(3, 91.5, "Identification", rotation=90, ha="center", va="center", fontsize=7.4,
        fontweight="bold")
box(14, 84, 44, 11, f"Records identified from OpenAlex\n(n = {counts['identified']})", "#dce6f2")
box(62, 84, 34, 11, f"Duplicate records removed\n(n = {counts['duplicates_removed']})")
arrow(36, 84, 36, 78)
arrow(58, 89.5, 62, 89.5)

ax.text(3, 71, "Screening", rotation=90, ha="center", va="center", fontsize=7.4,
        fontweight="bold")
box(14, 66, 44, 12, f"Records screened on title and abstract\n(n = {counts['screened']})", "#dce6f2")
box(62, 63, 34, 17,
    "Records excluded (n = %d)\n\noutcome not an agronomic quantity;\n"
    "no predictive model;\npoint accuracy only;\nno uncertainty, validation\nor transport claim"
    % counts["excluded_screening"], "#f6e7c8", size=6.4)
arrow(36, 66, 36, 60)
arrow(58, 72, 62, 72)

ax.text(3, 52, "Eligibility", rotation=90, ha="center", va="center", fontsize=7.4,
        fontweight="bold")
box(14, 48, 44, 12,
    f"Records meeting the eligibility criteria\n(n = {counts['met_criteria']})", "#dce6f2")
box(62, 45, 34, 15,
    f"Records excluded at eligibility\n(n = {counts['met_criteria'] - len(included)})\n\n"
    f"beyond the review corpus (n = {counts['met_criteria'] - len(corpus)});\n"
    f"background only (n = {len(background)})", "#f6e7c8", size=6.4)
arrow(36, 48, 36, 42)
arrow(58, 54, 62, 54)

ax.text(3, 34, "Included", rotation=90, ha="center", va="center", fontsize=7.4,
        fontweight="bold")
box(14, 30, 44, 12,
    f"Studies included in the review\n(n = {len(included)})", "#cfe0c3", size=7.6)
box(14, 16, 44, 10,
    f"Mendeley library loaded\n(n = {len(corpus)}: {len(included)} included\n"
    f"+ {len(background)} background)", size=7.0)
arrow(36, 30, 36, 26)

ax.text(50, 8, f"Search executed {counts['executed']}; OpenAlex title-abstract index; "
               f"publishers: Elsevier, Taylor & Francis, Sage, Wiley, Springer, Emerald",
        ha="center", fontsize=5.6, style="italic")
ax.text(50, 4.5, f"{counts['pdfs_downloaded']} open-access PDFs downloaded automatically; "
                 f"the remainder need institutional access",
        ha="center", fontsize=5.6, style="italic")

os.makedirs("docs/figures", exist_ok=True)
fig.savefig(FIG, bbox_inches="tight", pad_inches=0.06, facecolor="white")
print(f"wrote {FIG}")
