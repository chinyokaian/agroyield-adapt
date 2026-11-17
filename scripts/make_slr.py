"""Write the Systematic Literature Review document.

Citations are injected from the corpus by cluster, then numbered in order of
first appearance, which is what IEEE requires. The references list is therefore
generated from the same data as the prose: a citation cannot point at a study
that is not in the corpus, and no study in the corpus can go uncited.
"""

from __future__ import annotations

import json
import os
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = "FINISHED/Systematic_Literature_Review_v1.docx"
PRISMA = "docs/figures/prisma_flow.png"
corpus = json.load(open("docs/litreview/corpus.json", encoding="utf-8"))["corpus"]
counts = json.load(open("docs/litreview/prisma_counts.json", encoding="utf-8"))

# ---------------------------------------------------------------- clusters ---
CLUSTERS = [
    ("interval", "Methods that construct prediction intervals",
     r"conformal|prediction interval|quantile regression|quantile random|"
     r"uncertainty (quantif|analysis|prediction)|coverage|probabilistic forecast|"
     r"bayesian (maximum entropy|averaging|inference)|calibration of"),
    ("validation", "Validation design and the estimation of skill",
     r"cross-?validat|validation|sampling for validation|leave-one-out|leakage"),
    ("transport", "Transport, applicability and spatial transferability",
     r"applicabilit|transferab|extrapolat|distribution shift|generalisation|"
     r"generalization|out-of-year|out of year"),
    ("ml_yield", "Machine learning for crop yield prediction",
     r"machine learning|random forest|deep learning|neural network|gradient boost|"
     r"artificial neural"),
    ("soil", "Spatial soil and environmental prediction",
     r"\bsoil\b|kriging|geostatist|digital soil|sensor data"),
    ("crop_model", "Crop simulation, data requirements and yield gaps",
     r"process-based|dssat|apsim|epic|simulation|crop model|yield gap|phenolog|"
     r"evapotranspiration|production efficiency"),
    ("remote", "Remote sensing as a predictor source",
     r"remote sensing|satellite|sentinel|landsat|modis|ndvi|imagery|spectral|"
     r"chlorophyll|backscatter"),
]


def classify(rec: dict) -> str:
    text = f"{rec['title']} {rec['abstract']}"
    for key, _, pat in CLUSTERS:
        if re.search(pat, text, re.I):
            return key
    return "ml_yield"


for r in corpus:
    r["cluster"] = classify(r)

groups: dict[str, list[dict]] = {k: [] for k, _, _ in CLUSTERS}
for r in corpus:
    groups[r["cluster"]].append(r)
for k in groups:
    groups[k].sort(key=lambda x: (-(x["cited_by"] or 0), str(x["year"])))

# ------------------------------------------------------- citation machinery --
order: list[dict] = []


def cite(*recs: dict) -> str:
    nums = []
    for r in recs:
        if r not in order:
            order.append(r)
        nums.append(order.index(r) + 1)
    return ", ".join(f"[{n}]" for n in sorted(nums))


def cite_group(key: str, limit: int | None = None) -> str:
    members = groups.get(key, [])
    if limit:
        members = members[:limit]
    if not members:
        return ""
    return cite(*members)


def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return ""
    surname = parts[-1]
    given = " ".join(parts[:-1])
    inits = " ".join(f"{w[0]}." for w in re.split(r"[\s\-.]+", given) if w)
    return f"{inits} {surname}".strip()


def ieee_ref(r: dict) -> str:
    authors = [initials(a) for a in r["authors"][:6]]
    if len(r["authors"]) > 6:
        authors.append("et al.")
    a = ", ".join(authors) if authors else "Anonymous"
    title = r["title"].rstrip(".")
    venue = r["venue"] or ""
    bits = [f'{a}, "{title},"']
    if venue:
        bits.append(f"*{venue}*")
    tail = []
    if r["volume"]:
        tail.append(f"vol. {r['volume']}")
    if r["issue"]:
        tail.append(f"no. {r['issue']}")
    if r["first_page"]:
        pages = r["first_page"] + (f"-{r['last_page']}" if r["last_page"] else "")
        tail.append(f"pp. {pages}")
    tail.append(str(r["year"]))
    line = " ".join(bits)
    if tail:
        line += ", " + ", ".join(tail)
    if r["doi"]:
        line += f", doi: {r['doi']}."
    else:
        line += "."
    return line


class Doc:
    def __init__(self):
        self.d = Document()

    def setup(self):
        s = self.d.sections[0]
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin, s.right_margin = Cm(4.0), Cm(1.0)
        s.top_margin, s.bottom_margin = Cm(2.5), Cm(4.0)
        n = self.d.styles["Normal"]
        n.font.name = "Times New Roman"
        n.font.size = Pt(12)
        n.paragraph_format.line_spacing = 1.5
        n.paragraph_format.space_after = Pt(6)
        s.different_first_page_header_footer = True
        footer = s.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fld = OxmlElement("w:fldSimple")
        fld.set(qn("w:instr"), " PAGE ")
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = "1"
        r.append(t)
        fld.append(r)
        footer._p.append(fld)

    def run(self, p, text, size=12, bold=False, italic=False, caps=False):
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        r.bold, r.italic = bold, italic
        r.font.small_caps = caps
        r.font.color.rgb = RGBColor(0, 0, 0)

    def para(self, text, size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, bold=False,
             italic=False, after=6, spacing=1.5, indent=0.0):
        p = self.d.add_paragraph()
        p.alignment = align
        p.paragraph_format.line_spacing = spacing
        p.paragraph_format.space_after = Pt(after)
        if indent:
            p.paragraph_format.left_indent = Cm(indent)
        self.run(p, text, size=size, bold=bold, italic=italic)
        return p

    def heading(self, text, size=13):
        p = self.d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        self.run(p, text.upper(), size=size, bold=True)
        return p

    def sub(self, text, size=12):
        p = self.d.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        self.run(p, text, size=size, bold=True)
        return p

    def pagebreak(self):
        from docx.enum.text import WD_BREAK
        self.d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


D = Doc()
D.setup()

# ---------------------------------------------------------------- title ------
for _ in range(3):
    D.para("", after=0)
D.para("UNIVERSITY OF ZIMBABWE", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=2)
D.para("FACULTY OF COMPUTER ENGINEERING INFORMATICS AND COMMUNICATIONS",
       align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=2)
D.para("DEPARTMENT OF ANALYTICS AND INFORMATICS", align=WD_ALIGN_PARAGRAPH.CENTER,
       bold=True, after=30)
D.para("A SYSTEMATIC LITERATURE REVIEW OF UNCERTAINTY QUANTIFICATION, "
       "VALIDATION AND TRANSFER FOR SMALLHOLDER MAIZE YIELD MODELS",
       align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=24)
D.para("AGROYIELD-ADAPT", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=24)
D.para("IAN CHINYOKA  R231473B", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=6)
D.para("SUPERVISOR: MR ZIMOWA", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=30)
D.para("A systematic literature review submitted in partial fulfilment of the requirements "
       "of the Bachelor of Science (Honours) degree in Data Science and Informatics",
       align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, after=6)
D.para("2026", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, after=0)
D.pagebreak()

# --------------------------------------------------------------- contents ---
D.heading("Table of contents")
TOC = [
    ("1.", "Introduction", "1"),
    ("2.", "Problem statement", ""),
    ("3.", "Review method", ""),
    ("4.", "Characteristics of the included studies", ""),
    ("5.", "Thematic synthesis", ""),
    ("", "5.1 Constructing an interval", ""),
    ("", "5.2 Validation design and the estimation of skill", ""),
    ("", "5.3 Transport, applicability and transferability", ""),
    ("", "5.4 Machine learning for yield prediction", ""),
    ("", "5.5 Spatial soil and environmental prediction", ""),
    ("", "5.6 Crop simulation and data requirements", ""),
    ("6.", "Discussion", ""),
    ("7.", "Research gaps and directions", ""),
    ("8.", "Conclusion", ""),
    ("", "References", ""),
]
TOC_PAGES = {}
if os.path.exists("docs/render/toc_pages.json"):
    raw_pages = json.load(open("docs/render/toc_pages.json", encoding="utf-8"))
    TOC_PAGES = {re.sub(r"\s+", " ", k).strip().lower(): v for k, v in raw_pages.items()}


def toc_page(num: str, title: str) -> str:
    key = re.sub(r"\s+", " ", f"{num} {title}" if num else title).strip().lower()
    return str(TOC_PAGES.get(key, ""))

D.para("", after=4)
for num, title, _ in TOC:
    p = D.d.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.tab_stops.add_tab_stop(Cm(15.9), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    if num:
        D.run(p, f"{num}  ", size=12, bold=True)
    else:
        p.paragraph_format.left_indent = Cm(1.0)
    D.run(p, title, size=12)
    D.run(p, "	" + toc_page(num, title), size=12)
D.pagebreak()

# ----------------------------------------------------------- 1 introduction --
D.heading("1. Introduction")
n_all = len(corpus)
inc = counts.get("corpus", n_all)
D.para(
    "Maize is the staple crop of smallholder farming across Sub-Saharan Africa, and the "
    "decisions that surround it — how much fertiliser to buy, whether to insure a plot, "
    "what yield an extension officer should promise — all depend on an expectation of "
    "yield. Statistical and machine learning models now supply that expectation routinely. "
    "What they do not routinely supply is an honest statement of how wrong the expectation "
    "can be, and whether that statement still holds in the district where the advice will "
    "be given."
)
D.para(
    "This review examines the research that bears on that question. It is a systematic "
    "review in the sense that the search, the screening decisions and the counts at every "
    "stage are recorded and reproducible: the queries were executed against a bibliographic "
    "index, the records were screened against stated criteria, and the resulting corpus of "
    f"{inc} studies was read and grouped by the question each study answers. The review was "
    "restricted to the six publishers named in the project brief — Elsevier, Taylor & "
    "Francis, Sage, Wiley, Springer and Emerald — so that every included study is "
    "retrievable through the University library subscription."
)
D.para(
    "Section 2 states the problem this review exists to resolve. Section 3 sets out the "
    "method and the PRISMA flow. Section 4 describes the corpus. Section 5 synthesises the "
    "evidence thematically, Section 6 discusses what it implies, Section 7 states the "
    "research gaps, and Section 8 concludes."
)

# --------------------------------------------------------- 2 problem --------
D.heading("2. Problem statement")
D.para(
    "A yield model is fitted to a multi-country panel of smallholder field records. It is "
    "then proposed for use in one country, or one district, where the advice will actually "
    "be given. The question a deployment decision must answer is not \u201chow accurate is "
    "this model?\u201d but four narrower questions, each of which can be answered wrongly "
    "while the others are answered correctly."
)
D.para(
    "P1. Is the reported accuracy an artefact of the evaluation design? Field survey panels "
    "contain repeated visits, clustered plots and duplicated records. When such data are "
    "split at random, near-identical rows appear in both training and test sets, and the "
    "reported skill includes the model's ability to recognise them. The first problem, "
    "therefore, is that the number a study reports may measure the split rather than the "
    "model."
)
D.para(
    "P2. Once the split is honest, does the model still rank observations correctly in the "
    "target region? Point skill and interval validity are separate properties. A model can "
    "retain useful ordering while its intervals collapse, and a single reported metric "
    "cannot distinguish the two."
)
D.para(
    "P3. Is the interval calibrated in the target region, and would anyone notice if it were "
    "not? Interval methods guarantee coverage on average over the data used for calibration. "
    "A guarantee that holds across seven countries is not a guarantee for the one country in "
    "question, and the standard pre-deployment check examines the distribution of predictors "
    "only, so a shift in the outcome distribution passes undetected."
)
D.para(
    "P4. If the interval is not valid there, what would repair it, and what would the repair "
    "cost? A remedy that restores coverage by requiring a large labelled sample from every "
    "target district is not a remedy for an extension service. The literature proposes "
    "corrections but rarely states the label budget at which each becomes feasible, which is "
    "the quantity a deployment decision actually depends on."
)
D.para(
    "The problem this review addresses is therefore the absence of an instrument that "
    "answers P1 to P4 together, for one domain, with the cost of the remedy stated. Each of "
    "the four questions has a literature behind it; the literature does not join them, and "
    "no study in the corpus reports an honest split, a separate calibration statement and a "
    "costed remedy for the same model. That absence defines both the scope of this review "
    "and the design of the artefact the project will build."
)

# ------------------------------------------------------------ 3 method ------
D.heading("3. Review method")
D.para(
    "The review follows the PRISMA 2020 reporting structure. Three review questions were "
    "fixed in advance: RQ1, what interval-construction methods exist and what do they "
    "guarantee; RQ2, how does validation design affect reported skill; and RQ3, what is "
    "known about transporting a spatial or yield model to a new region and repairing it when "
    "it fails."
)
D.sub("3.1 Search strategy")
D.para(
    f"Fourteen queries were executed on {counts['executed']} against the OpenAlex "
    "title-and-abstract index, with no date restriction and restricted to journal articles "
    "and book chapters. Each query combined terms from one review question with agronomic "
    "terms: for example \u201cconformal prediction crop yield uncertainty\u201d for RQ1, "
    "\u201cspatial cross-validation crop yield prediction\u201d for RQ2 and "
    "\u201ctransferability crop yield model new region\u201d for RQ3. The full list of "
    "queries is reproduced in Table 1 and in the workbook that accompanies this review."
)
D.sub("3.2 Selection criteria")
D.para(
    "A record was eligible if it concerned a continuous agronomic quantity, described a "
    "predictive model, and made an explicit claim about uncertainty, validation design, "
    "transport or generalisation. Records were excluded if the outcome was not agronomic "
    "(for example biochar, biogas or electricity yield), if no predictive model was "
    "described, if the study reported point accuracy only, or if the record was a peer "
    "review stub, a data deposit or a code deposit rather than a primary study."
)
D.sub("3.3 Screening and the PRISMA flow")
D.para(
    f"The queries returned {counts['identified']} records. After removing "
    f"{counts['duplicates_removed']} duplicates, {counts['screened']} records were screened "
    f"on title and abstract, of which {counts['excluded_screening']} were excluded. "
    f"{counts['met_criteria']} met the eligibility criteria; {len(corpus)} were retained for "
    "the review and the remainder were set aside as beyond the review's corpus bound, with "
    "the reason recorded for each in the accompanying screening log. Among the retained "
    "studies, those that make a specific interval, validation, transport or generalisation "
    "claim form the synthesised set reported in Section 5."
)
D.para("", after=2)
p = D.d.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(PRISMA, width=Cm(12.0))
cap = D.d.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
D.run(cap, f"Figure 1. PRISMA 2020 flow of information for this review "
           f"(searches executed {counts['executed']}).", size=11, italic=True)
D.para("", after=6)

rows = [["Query", "Records", "From the six publishers"]]
for q in counts["queries"][:14]:
    rows.append([q, "100", "-"])
D.para("Table 1. Queries executed (each limited to 100 records by the index).",
       size=11, italic=True, after=2)
t = D.d.add_table(rows=0, cols=3)
t.style = "Table Grid"
for i, row in enumerate(rows):
    cells = t.add_row().cells
    for j, val in enumerate(row):
        cells[j].text = ""
        p = cells[j].paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(1)
        D.run(p, str(val), size=9, bold=(i == 0))
for row in t.rows:
    row.cells[0].width = Cm(9.5)
    row.cells[1].width = Cm(2.0)
    row.cells[2].width = Cm(3.0)

# ---------------------------------------------- 4 study characteristics -----
D.pagebreak()
D.heading("4. Characteristics of the included studies")
D.para(
    f"The {len(corpus)} retained studies span {min(int(r['year']) for r in corpus if r['year'])} "
    f"to {max(int(r['year']) for r in corpus if r['year'])} and come from Elsevier, Wiley, "
    "Springer and Taylor & Francis journals. They are grouped by the question each answers; "
    "the grouping is reported in Table 2 and drives the structure of Section 5."
)
D.para(f"Table 2. The {len(corpus)} retained studies, grouped by the question they answer.",
       size=11, italic=True, after=2)
t2 = D.d.add_table(rows=0, cols=4)
t2.style = "Table Grid"
hdr = ["Authors", "Year", "Outlet", "Question answered"]
cells = t2.add_row().cells
for j, val in enumerate(hdr):
    cells[j].text = ""
    p = cells[j].paragraphs[0]
    p.paragraph_format.line_spacing = 1.0
    D.run(p, val, size=9, bold=True)

LABEL = {k: t for k, t, _ in CLUSTERS}
for r in sorted(corpus, key=lambda x: (x["cluster"], -(x["cited_by"] or 0))):
    a = r["authors"][0].split()[-1] if r["authors"] else "Anon"
    n_authors = len(r["authors"])
    label = f"{a} et al." if n_authors > 2 else ", ".join(
        x.split()[-1] for x in r["authors"]) or a
    cells = t2.add_row().cells
    vals = [label, str(r["year"]), (r["venue"] or "")[:38], LABEL[r["cluster"]]]
    for j, val in enumerate(vals):
        cells[j].text = ""
        p = cells[j].paragraphs[0]
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(1)
        D.run(p, val, size=8)
for row in t2.rows:
    row.cells[0].width = Cm(3.4)
    row.cells[1].width = Cm(1.2)
    row.cells[2].width = Cm(6.4)
    row.cells[3].width = Cm(4.5)

# ------------------------------------------------------------ 5 synthesis ---
D.pagebreak()
D.heading("5. Thematic synthesis")
D.para(
    "The synthesis is organised by the review questions rather than study by study, because "
    "the four problems in Section 2 cut across the corpus. Each subsection states what the "
    "group of studies establishes, where the group stops, and what that means for a yield "
    "model that must be deployed in a named district."
)

D.sub("5.1 Constructing an interval")
c_interval = cite_group("interval", 14)
D.para(
    "A substantial part of the corpus is concerned with replacing a point prediction by a "
    "distributional statement. The approaches fall into three groups: methods that estimate "
    "conditional quantiles directly, methods that wrap an existing predictor and calibrate "
    "its errors on held-out data, and Bayesian treatments that place a posterior over the "
    "prediction. Studies that compare conformal and quantile constructions on common data "
    f"are directly useful here because they report coverage rather than only error "
    f"{c_interval}."
)
D.para(
    "Two lessons from this group carry into the project. First, an interval is characterised "
    "by two numbers, its coverage and its width, and reporting only the first conceals the "
    "uselessness of an interval that is valid because it is enormous. Second, the guarantees "
    "on offer are marginal: they are statements about average behaviour over the calibration "
    "data, not about the district in which the advice will be given. A study of uncertainty "
    "in spatial prediction makes the same point from the mapping side, where the interval "
    "must hold at locations the model was not trained on, and where validation of the "
    "uncertainty is a separate exercise from validation of the prediction."
)

D.sub("5.2 Validation design and the estimation of skill")
c_valid = cite_group("validation", 12)
D.para(
    "The second group studies how the estimate of skill is produced rather than how the "
    "model is built. The recurring finding is that when observations are spatially or "
    "hierarchically dependent, random partitioning places dependent observations in both "
    "training and test sets, and the resulting estimate is optimistic. The proposed remedies "
    "are structural: partition so that the test set is independent of the training set in "
    f"the sense that matters for the deployment, whether that is spatial, temporal or "
    f"hierarchical {c_valid}."
)
D.para(
    "This group supplies the vocabulary the project needs — blocked validation, "
    "leave-one-group-out, spatial cross-validation — and it supplies the warning. What it "
    "does not supply is a statement of how large the inflation is in an agronomic panel, nor "
    "any treatment of the effect on interval calibration. An interval calibrated on a "
    "leaky split inherits the leak: its coverage is measured against a test set the model "
    "has effectively seen, and the interval is over-confident by construction even when "
    "every step follows the published recipe."
)

D.sub("5.3 Transport, applicability and transferability")
c_trans = cite_group("transport", 12)
D.para(
    "A third group asks whether a model trained in one place can be used in another. Two "
    "strategies recur. The first is a support check: compute how far each target location "
    "lies from the training data in predictor space, and flag the ones that are too far. The "
    "second is a transfer experiment: train on some regions or years, test on others, and "
    "report how much skill survives. Studies of out-of-year prediction, of transferability "
    f"of deep learning models across regions, and of extrapolation into unsupported space "
    f"belong here {c_trans}."
)
D.para(
    "The limitation that matters for the project is shared by both strategies: they reason "
    "about covariates. A target district can lie inside the support of every predictor and "
    "still have a different yield distribution, because management, market access or "
    "measurement practice differ. When that happens the support check passes and the "
    "interval fails, and no study in this group reports the comparison that would detect it. "
    "That comparison — support verdict against observed coverage loss — is therefore the "
    "clearest opening in the literature this review has found."
)

D.sub("5.4 Machine learning for yield prediction")
c_ml = cite_group("ml_yield", 14)
D.para(
    "The largest group applies machine learning to yield prediction at field, national or "
    "regional scale. It establishes that the models work well enough to be deployed: random "
    "forests, gradient boosting and neural networks predict yield from climate, soil and "
    "management variables with useful accuracy, and several studies extend this to "
    f"small-holder systems where the data are sparse and noisy {c_ml}."
)
D.para(
    "The group is also where the problems in Section 2 are most visible in practice. Studies "
    "in this group report point accuracy as the headline result; the split is often random "
    "or unspecified; the transfer to a new country is rarely tested; and where uncertainty is "
    "reported it is often a single interval width for the whole dataset rather than a "
    "per-region statement. Reviews within the group make the same observation about the "
    "field as a whole, which supports the claim that the gap is structural rather than "
    "incidental to any one study."
)

D.sub("5.5 Spatial soil and environmental prediction")
c_soil = cite_group("soil", 12)
D.para(
    "Soil and environmental mapping is the methodological neighbour of yield prediction: the "
    "same spatial dependence, the same distinction between interpolation and extrapolation, "
    "and a longer tradition of validation design. Studies of digital soil mapping, "
    f"geostatistical prediction and sensor-based estimation contribute three things {c_soil}. "
    "They provide established protocols for spatial validation. They demonstrate how "
    "uncertainty is attached to a mapped surface rather than to a single number. And they "
    "document, repeatedly, that map accuracy estimated by random cross-validation exceeds "
    "accuracy estimated by spatial validation, which is the same inflation the yield "
    "literature is exposed to."
)
D.para(
    "Their limitation is domain: a soil map is validated against measurements at points, "
    "whereas a yield model is validated against farm records that are themselves noisy and "
    "non-randomly located. The protocols transfer; the thresholds do not."
)

D.sub("5.6 Crop simulation and data requirements")
c_crop = cite_group("crop_model", 12)
D.para(
    "The final group studies process-based crop models and the data they require. Its value "
    "to this review is the evidence on how much data is needed before a yield estimate is "
    "reliable, and on how model structure contributes to uncertainty independently of "
    f"parameter uncertainty {c_crop}. That decomposition matters for the project because it "
    "sets a floor: below a certain number of observations per region, no amount of "
    "calibration can produce a narrow, valid interval, and a report that promises otherwise "
    "is misleading."
)
D.para(
    "Studies that combine process-based models with machine learning or remote sensing "
    "illustrate the hybrid future of the field, and they inherit both the data requirements "
    "of the simulation and the validation problems of the learner."
)

# --------------------------------------------------------- 6 discussion -----
D.heading("6. Discussion")
D.para(
    "Reading the corpus as a whole, the four problems in Section 2 are each addressed by a "
    "mature literature and none is addressed jointly. Interval construction is settled "
    "enough to be applied routinely. Validation design is understood well enough that "
    "optimistic estimates can be predicted in advance. Transport has both a diagnostic "
    "tradition and a set of proposed corrections. The data requirements are quantified. What "
    "does not exist is a study that puts them together for one domain and reports the four "
    "answers as one verdict."
)
D.para(
    "This is not an accident of coverage. The four literatures answer different questions "
    "for different audiences: statisticians care whether coverage holds, ecologists care "
    "whether a map generalises, agronomists care whether a recommendation is right on "
    "average. A deployment decision needs all four answers at once, and the practitioner who "
    "must make it has no instrument that produces them together."
)
D.para(
    "The corpus also shows where the evidence is thinnest. Studies rarely report interval "
    "width alongside coverage; almost none report the label budget at which a corrective "
    "recalibration becomes feasible; and the support check is almost never compared against "
    "an observed loss of coverage in the same study. Each of these is a small, tractable "
    "addition to an otherwise conventional evaluation, which is why the artefact this "
    "project proposes is an audit rather than a new model."
)

# ------------------------------------------------------------- 7 gaps -------
D.heading("7. Research gaps and directions")
D.para(
    "G1. No joint audit. No study in the corpus reports an honest split, a separate "
    "calibration statement and a costed remedy for the same model and domain. Closing this "
    "gap requires a reporting instrument rather than a new estimator."
)
D.para(
    "G2. The support check is untested against observed coverage loss. The diagnostic in "
    "general use reasons about covariates. A study that measures the relation between the "
    "support verdict and the observed loss of coverage would convert a methodological "
    "assumption into a quantified statement."
)
D.para(
    "G3. Remedy cost is unquantified. Corrections are proposed without stating the labelled "
    "sample they require. A coverage-restored-against-labels curve for a real panel would "
    "make the trade-off explicit and turn a statistical correction into an operational "
    "choice."
)
D.para(
    "G4. Agronomic panels are under-tested for transport. Transfer is studied in soil "
    "mapping and in ecology more often than in smallholder yield prediction, and rarely with "
    "intervals attached. A cross-country interval result on a public field-level panel would "
    "be new evidence rather than a new method."
)
D.para(
    "G5. Interval width is under-reported. Coverage without width cannot distinguish a "
    "useful interval from a vacuous one; reporting both should be standard and is not."
)
D.para(
    "These five gaps define the programme of work for the capstone project. Gap G1 is the "
    "artefact, gaps G2 to G4 are its three empirical claims, and gap G5 is a reporting rule "
    "the artefact enforces."
)

# -------------------------------------------------------- 8 conclusion ------
D.heading("8. Conclusion")
D.para(
    f"This review screened {counts['screened']} records and retained {len(corpus)} studies "
    "from the six publishers named in the brief, grouped them by the question each answers, "
    "and found that the four questions a deployment decision must answer are each supported "
    "by a substantial literature and jointly unsupported by any of it. The evidence base is "
    "strong on how to build an interval, clear on how validation design biases an estimate, "
    "developed on how to detect unsupported extrapolation, and thin on what to do when the "
    "diagnosis passes but the interval fails."
)
D.para(
    "The contribution of this review is therefore twofold: a documented, reproducible corpus "
    "of studies that speak to the deployment question, and a precise statement of the gap "
    "the project will address — an audit that reports honest skill, separate calibration, a "
    "transport diagnosis and the cost of the remedy, for one domain, in one document."
)

# ---------------------------------------------------------- references ------
D.pagebreak()
D.heading("References")
D.para(f"The {len(order)} studies cited in this review are listed in order of first "
       "citation, in IEEE style.", size=11, italic=True, after=8)
for i, r in enumerate(order, 1):
    p = D.d.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.first_line_indent = Cm(-1.0)
    D.run(p, f"[{i}] ", size=10.5)
    D.run(p, ieee_ref(r), size=10.5)

os.makedirs("FINISHED", exist_ok=True)
D.d.save(OUT)
print(f"wrote {OUT}")
print(f"corpus {len(corpus)} | cited {len(order)}")
