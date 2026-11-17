"""Assemble the Concept Development and Evaluation Report, Draft 1.

Chapter 1 and Chapter 3 are written here; Chapter 2 is the systematic review,
copied element by element from its own document and renumbered into 2.x.
Citations are renumbered afterwards so the whole report satisfies IEEE's
first-appearance rule and carries a single reference list.
"""

from __future__ import annotations

import copy
import json
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SLR = "FINISHED/Systematic_Literature_Review_v1.docx"
OUT = "FINISHED/Concept_Development_Report_Draft1.docx"
PRISMA = "docs/figures/prisma_flow.png"

doc = Document()


def setup():
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.left_margin, s.right_margin = Cm(4.0), Cm(1.0)
    s.top_margin, s.bottom_margin = Cm(3.0), Cm(2.5)
    n = doc.styles["Normal"]
    n.font.name = "Times New Roman"
    n.font.size = Pt(12)
    n.paragraph_format.line_spacing = 1.5
    n.paragraph_format.space_after = Pt(6)


def run(p, text, size=12, bold=False, italic=False):
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    r.bold, r.italic = bold, italic
    r.font.color.rgb = RGBColor(0, 0, 0)
    return r


def para(text, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False, italic=False,
         after=6, spacing=1.5):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = spacing
    p.paragraph_format.space_after = Pt(after)
    run(p, text, size=size, bold=bold, italic=italic)
    return p


def chapter(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.keep_with_next = True
    run(p, text, size=14, bold=True)


def section(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run(p, text, size=12, bold=True)


setup()
footer = doc.sections[0].footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.sections[0].different_first_page_header_footer = True
fld = OxmlElement("w:fldSimple")
fld.set(qn("w:instr"), " PAGE ")
r = OxmlElement("w:r")
t = OxmlElement("w:t")
t.text = "1"
r.append(t)
fld.append(r)
footer._p.append(fld)

# ------------------------------------------------------------- title page ---
for _ in range(2):
    para("", after=0)
logo = doc.add_paragraph()
logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
if os.path.exists("docs/assets/uz_logo.jpg"):
    logo.add_run().add_picture("docs/assets/uz_logo.jpg", width=Cm(3.0))
para("UNIVERSITY OF ZIMBABWE", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=2)
para("FACULTY OF COMPUTER ENGINEERING INFORMATICS AND COMMUNICATIONS",
     align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=2)
para("DEPARTMENT OF ANALYTICS AND INFORMATICS", align=WD_ALIGN_PARAGRAPH.CENTER,
     bold=True, after=28)
para("CONCEPT DEVELOPMENT AND EVALUATION REPORT", align=WD_ALIGN_PARAGRAPH.CENTER,
     bold=True, after=4)
para("DRAFT 1 \u2014 REVIEW 1", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=20)
para("AGROYIELD-ADAPT: A DEPLOYMENT-READINESS AUDITOR FOR SMALLHOLDER MAIZE "
     "YIELD-INTERVAL MODELS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=24)
para("IAN CHINYOKA  R231473B", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=4)
para("SUPERVISOR: MR ZIMOWA", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=28)
para("Submitted in partial fulfilment of the requirements of the Bachelor of Science "
     "(Honours) degree in Data Science and Informatics", align=WD_ALIGN_PARAGRAPH.CENTER,
     italic=True, after=6)
para("2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=0)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ------------------------------------------------------------------ TOC ----
TOC_ENTRIES = [
    ("1.", "CHAPTER 1: INTRODUCTION"),
    ("1.1", "Background"),
    ("1.2", "Motivation"),
    ("1.3", "Problem statement"),
    ("1.4", "Research questions"),
    ("1.5", "Research objectives"),
    ("1.6", "Scope and significance"),
    ("1.7", "Structure of the report"),
    ("2.", "CHAPTER 2: LITERATURE REVIEW"),
    ("2.1", "Introduction"),
    ("2.2", "Problem statement"),
    ("2.3", "Review method"),
    ("2.4", "Characteristics of the included studies"),
    ("2.5", "Thematic synthesis"),
    ("2.6", "Discussion"),
    ("2.7", "Research gaps and directions"),
    ("2.8", "Summary"),
    ("3.", "CHAPTER 3: METHODOLOGY (FIRST DRAFT)"),
    ("3.1", "Research design"),
    ("3.2", "Data"),
    ("3.3", "The audit modules"),
    ("3.4", "Evaluation measures"),
    ("3.5", "Ethical considerations"),
    ("3.6", "Limitations of the design"),
    ("", "REFERENCES"),
]
TOC_PAGES = {}
if os.path.exists("docs/render/report_toc_pages.json"):
    TOC_PAGES = json.load(open("docs/render/report_toc_pages.json", encoding="utf-8"))

para("TABLE OF CONTENTS", bold=True, after=10)
for num, title in TOC_ENTRIES:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.tab_stops.add_tab_stop(Cm(15.9), WD_TAB_ALIGNMENT.RIGHT,
                                              WD_TAB_LEADER.DOTS)
    if num and "." == num[-1]:
        run(p, f"{num}  ", bold=True)
    elif num:
        p.paragraph_format.left_indent = Cm(1.2)
        run(p, f"{num}  ")
    run(p, title)
    key = title if (num.endswith(".") or not num) else f"{num} {title}"
    run(p, "	" + str(TOC_PAGES.get(key.strip(), "")))
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ------------------------------------------------------- chapter 1 ---------
chapter("CHAPTER 1: INTRODUCTION")
section("1.1 Background")
para(
    "Maize is the staple crop of smallholder farming across Sub-Saharan Africa, and the "
    "decisions that surround it \u2014 how much fertiliser to buy, whether to insure a plot, "
    "what yield an extension officer should promise \u2014 all rest on an expectation of "
    "yield. Statistical and machine learning models now supply that expectation routinely, "
    "and increasingly they supply it as an interval rather than a single number, because an "
    "interval is the form in which a prediction can be attached to a decision."
)
para(
    "An interval carries a promise: over repeated draws, the true yield should fall inside "
    "it at the stated rate. That promise is conditional in a way that is easy to overlook. "
    "It holds on average over the data used to calibrate it, not in the district where the "
    "advice will be given, and it degrades when the target data are not exchangeable with "
    "the calibration data. A model can therefore be published with a valid interval and "
    "still mislead the extension service that uses it."
)
section("1.2 Motivation")
para(
    "The motivation is practical. Credit limits, insurance premiums and fertiliser "
    "recommendations are being set from model output, and the people setting them are not in "
    "a position to check the interval themselves. A point prediction at least looks like an "
    "estimate; an interval that is wrong looks like knowledge, which is worse. The evidence "
    "base for judging such an interval exists, but it is split across three literatures that "
    "do not cite one another, as Chapter 2 shows."
)
section("1.3 Problem statement")
para(
    "A yield model is fitted to a multi-country panel of smallholder field records and then "
    "proposed for use in one country or district. The deployment question is not how "
    "accurate the model is, but four narrower questions, each of which can be answered "
    "wrongly while the others are answered correctly."
)
para(
    "P1. Is the reported accuracy an artefact of the evaluation design? Field panels contain "
    "repeated visits, clustered plots and duplicated records; when such data are split at "
    "random, the reported skill measures the split as much as the model."
)
para(
    "P2. Once the split is honest, does the model still rank observations correctly in the "
    "target region? Point skill and interval validity are separate properties and a single "
    "metric cannot distinguish them."
)
para(
    "P3. Is the interval calibrated there, and would anyone notice if it were not? The "
    "standard pre-deployment check examines the distribution of predictors only, so a shift "
    "in the outcome distribution passes undetected."
)
para(
    "P4. What would repair it, and what would the repair cost? A correction that restores "
    "coverage at the price of a large labelled sample in every district is not a remedy for "
    "an extension service."
)
para(
    "No existing instrument answers P1 to P4 together, for one domain, with the cost of the "
    "remedy stated. That absence is the problem this project addresses."
)
section("1.4 Research questions")
para("RQ1. How much of the reported skill of a maize yield model is an artefact of random "
     "validation?")
para("RQ2. Once the split is honest, how does point transfer differ from interval "
     "calibration across countries?")
para("RQ3. Which distribution shift explains a coverage failure, and can a covariate-space "
     "support check detect it?")
para("RQ4. What label budget restores coverage, and what interval width does it buy?")
section("1.5 Research objectives")
para("To measure the inflation between random, clustered and country-holdout validation on "
     "the same learner and panel.")
para("To separate point skill from interval calibration, reporting both per country with "
     "bounds.")
para("To diagnose the responsible shift by comparing the support verdict with the observed "
     "loss of coverage.")
para("To produce a level-adjusted recalibration together with its label-budget curve.")
para("To deliver a single readiness report for a named target domain.")
section("1.6 Scope and significance")
para(
    "The scope is one crop, one public panel and one learner, so the thresholds reported are "
    "calibrated to maize and are not claimed to be portable. The significance lies in the "
    "reporting instrument rather than in a new estimator: the audit states what is wrong, "
    "which shift is responsible and what the repair would cost, and it does so in a form a "
    "non-specialist can act on."
)
section("1.7 Structure of the report")
para(
    "Chapter 1 states the problem, questions and objectives. Chapter 2 reports the systematic "
    "review of the literature and the gap it establishes. Chapter 3 sets out the methodology "
    "in its first draft, including the audit modules and the measures by which each will be "
    "judged. Later chapters will report results, discussion and conclusions."
)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ------------------------------------------------------- chapter 2 ---------
chapter("CHAPTER 2: LITERATURE REVIEW")
para("This chapter is the systematic review reported in full in the accompanying review "
     "document; the section numbering here follows the report.", italic=True, after=8)

slr = Document(SLR)
src = [p for p in slr.paragraphs]
texts = [p.text.strip() for p in src]
start = next(i for i, t in enumerate(texts) if t.upper() == "1. INTRODUCTION")
end = max(i for i, t in enumerate(texts) if t.upper() == "REFERENCES")

RENAME = {
    "1. INTRODUCTION": "2.1 Introduction",
    "2. PROBLEM STATEMENT": "2.2 Problem statement",
    "3. REVIEW METHOD": "2.3 Review method",
    "4. CHARACTERISTICS OF THE INCLUDED STUDIES": "2.4 Characteristics of the included studies",
    "5. THEMATIC SYNTHESIS": "2.5 Thematic synthesis",
    "6. DISCUSSION": "2.6 Discussion",
    "7. RESEARCH GAPS AND DIRECTIONS": "2.7 Research gaps and directions",
    "8. CONCLUSION": "2.8 Summary",
}

body_children = list(slr.element.body)
# locate the range using python-docx's own paragraph text, then map to elements
start_el = body_children.index(slr.paragraphs[start]._p)
end_el = body_children.index(slr.paragraphs[end]._p)

copied = 0
skipped_figs = 0
for el in body_children[start_el:end_el]:
    if not el.tag.endswith("}p") and not el.tag.endswith("}tbl"):
        continue
    if el.tag.endswith("}p") and "w:drawing" in el.xml:
        skipped_figs += 1
        continue
    new_el = copy.deepcopy(el)
    doc.element.body.sectPr.addprevious(new_el)
    copied += 1

# rename headings inside the copied range, and renumber figures and tables
for p in doc.paragraphs:
    txt = p.text.strip()
    if txt in RENAME:
        new = RENAME[txt]
        for r in p.runs:
            r.text = ""
        p.runs[0].text = new.upper() if txt.startswith(("1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ")) else new
    elif re.match(r"^5\.\d ", txt):
        n = txt[2]
        for r in p.runs:
            r.text = ""
        p.runs[0].text = f"2.5.{n} " + txt[4:]

for p in doc.paragraphs:
    if p.text.startswith("Figure 1."):
        for r in p.runs:
            r.text = ""
        p.runs[0].text = p.text.replace("Figure 1.", "Figure 2.1.") if p.runs else ""
    if p.text.startswith("Table 1."):
        for r in p.runs:
            r.text = ""
        p.runs[0].text = "Table 2.1." + p.text[len("Table 1."):]
    elif p.text.startswith("Table 2."):
        for r in p.runs:
            r.text = ""
        p.runs[0].text = "Table 2.2." + p.text[len("Table 2."):]

# the PRISMA figure was skipped; place it after the method section
fig_p = doc.add_paragraph()
fig_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
fig_p.add_run().add_picture(PRISMA, width=Cm(12.0))
cap = doc.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(cap, "Figure 2.1. PRISMA 2020 flow of information for this review.", size=11,
    italic=True)

# ------------------------------------------------------- chapter 3 ---------
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
chapter("CHAPTER 3: METHODOLOGY (FIRST DRAFT)")
section("3.1 Research design")
para(
    "The project is a design-science study with an empirical core. The artefact is a "
    "deployment-readiness auditor; the empirical work is the measurement it performs on a "
    "real panel. Each module is built so that a negative result is still informative: an "
    "audit that finds no inflation, no coverage loss and no benefit from recalibration is a "
    "result about the domain, not a failure of the instrument."
)
section("3.2 Data")
para(
    "The data are the public One Acre Fund smallholder maize panel: 14,773 field records from "
    "seven countries, 2016 to 2022, licensed CC BY 4.0. The panel is observational and "
    "unbalanced, and it contains 4,764 duplicate rows (32.2%) across 1,526 spatial-temporal "
    "clusters. Duplication is treated as a property of the survey design to be handled "
    "explicitly rather than as a defect to be deleted silently, because deleting it changes "
    "the population being described."
)
section("3.3 The audit modules")
para(
    "The auditor is organised into five modules, each answering one of the four problems in "
    "Section 1.3 plus a reporting layer."
)
rows = [
    ["Module", "Question", "Output"],
    ["M1 Split integrity", "P1", "R\u00b2 under random, clustered and country-holdout "
                                        "designs; inflation in R\u00b2"],
    ["M2 Skill and calibration", "P2", "Point transfer beside per-country coverage with "
                                       "bounds"],
    ["M3 Transport diagnosis", "P3", "Support verdict compared with observed coverage loss"],
    ["M4 Recalibration", "P4", "Labels required against coverage restored; interval width"],
    ["M5 Readiness report", "All", "One verdict for a named target domain"],
]
tbl = doc.add_table(rows=0, cols=3)
tbl.style = "Table Grid"
for i, row in enumerate(rows):
    cells = tbl.add_row().cells
    for j, val in enumerate(row):
        cells[j].text = ""
        p = cells[j].paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(1)
        run(p, val, size=10, bold=(i == 0))
for row in tbl.rows:
    row.cells[0].width = Cm(4.2)
    row.cells[1].width = Cm(1.6)
    row.cells[2].width = Cm(9.2)
para("Table 3.1. The five audit modules and the question each answers.", size=11,
     italic=True, after=8)
section("3.4 Evaluation measures")
para(
    "Module 1 is judged on the difference in R\u00b2 between designs. Module 2 on coverage "
    "relative to the nominal level, reported with its own interval so that small-country "
    "results are read correctly. Module 3 on whether the support verdict and the coverage "
    "loss agree. Module 4 on the shape of the label-budget curve and the interval width at a "
    "stated budget. Module 5 on whether a reader who is not a statistician can act on the "
    "verdict."
)
section("3.5 Ethical considerations")
para(
    "The data are secondary, public and licensed for reuse, and contain no personal "
    "identifiers beyond farm-level geography; no new human subjects data will be collected. "
    "The ethical risk is therefore one of interpretation rather than collection: a readiness "
    "verdict must not be presented as advice to a specific farmer, and the report states the "
    "domain and the budget to which each verdict applies."
)
section("3.6 Limitations of the design")
para(
    "Three limitations are accepted at the outset. The audit covers one crop and one panel, "
    "so its thresholds are not portable without re-running it. Its claims inherit the "
    "guarantees of whichever interval construction it wraps. And it reports no externally "
    "validated second panel, so the generalisation claim is a design argument rather than a "
    "result."
)

# ------------------------------------------------------- references --------
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
para("REFERENCES", bold=True, after=8)
slr_refs = [p.text.strip() for p in slr.paragraphs[start:]]
refs = [t for t in slr_refs if re.match(r"^\[\d+\]", t)]
ref_texts = [re.sub(r"^\[\d+\]\s*", "", r) for r in refs]

for i, rtxt in enumerate(ref_texts, 1):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.first_line_indent = Cm(-1.0)
    run(p, f"[{i}] ", size=10.5)
    run(p, rtxt, size=10.5)

doc.save(OUT)
print(f"wrote {OUT}")
print(f"copied {copied} elements from the review; {skipped_figs} figure placeholders; "
      f"{len(ref_texts)} references")
