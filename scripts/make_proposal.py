"""Build the proposal document to the letter of UZ-DAI Guidelines 2026, §3.2.

Compliance targets taken from the guideline text:
  * A4, margins 4.0 cm left / 1.0 cm right / 2.5 cm top / 4.0 cm bottom
  * Times New Roman 12 pt, one-and-a-half spacing in the body
  * page numbers centred at the bottom edge; roman numerals for preliminaries
  * title page per Appendix I (logo, faculty, department, uppercase title, name,
    purpose statement, year), single spaced, unnumbered
  * preliminary pages in order: abstract, declaration, copyright, dedication,
    acknowledgements, abbreviations, table of contents, list of tables,
    list of figures, list of appendices
  * chapter titles and numbers in upper case; sub-headings lower case
  * table captions with SEQ fields so the list of tables can be generated
"""

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = "FINISHED/Proposal_AGROYIELD-ADAPT_v2.docx"
LOGO = "docs/assets/uz_logo.jpg"
CONTENT_CM = 16.0  # A4 (21.0) minus 4.0 left and 1.0 right

YEAR = "2026"
CANDIDATE = "[Student name] [Registration number]"
SUPERVISOR = "[Supervisor name]"
DEGREE = ("BACHELOR OF SCIENCE (HONOURS) DEGREE IN "
          "DATA SCIENCE AND INFORMATICS")
TITLE = ("AGROYIELD-ADAPT: A DEPLOYMENT-READINESS AUDITOR FOR SMALLHOLDER "
         "MAIZE YIELD-INTERVAL MODELS")

doc = Document()
body = doc.element.body


# ----------------------------------------------------------------- helpers ---
def setup_page(section):
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(4.0)
    section.right_margin = Cm(1.0)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(4.0)


def set_page_numbering(section, fmt=None, start=None):
    sectPr = section._sectPr
    for el in sectPr.findall(qn("w:pgNumType")):
        sectPr.remove(el)
    node = OxmlElement("w:pgNumType")
    if fmt:
        node.set(qn("w:fmt"), fmt)
    if start is not None:
        node.set(qn("w:start"), str(start))
    sectPr.append(node)


def add_field(paragraph, instruction, placeholder=""):
    """Insert a Word field (TOC, SEQ, PAGE) at the end of a paragraph."""
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), instruction)
    run = OxmlElement("w:r")
    text = OxmlElement("w:t")
    text.text = placeholder
    run.append(text)
    fld.append(run)
    paragraph._p.append(fld)


def update_fields_on_open():
    settings = doc.settings.element
    node = OxmlElement("w:updateFields")
    node.set(qn("w:val"), "true")
    settings.append(node)


def base_style():
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)


def run_in(p, text, size=12, bold=False, italic=False, caps=False, font="Times New Roman"):
    r = p.add_run(text)
    r.font.name = font
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    r.font.color.rgb = RGBColor(0, 0, 0)
    if caps:
        r.font.all_caps = True
    return r


def para(text, size=12, bold=False, italic=False, align=None, spacing=1.5,
         space_after=6, indent_hang=False):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = spacing
    p.paragraph_format.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    if indent_hang:
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)
    run_in(p, text, size=size, bold=bold, italic=italic)
    return p


def front_heading(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing = 1.0
    run_in(p, text, size=14, bold=True)
    return p


def chapter_heading(number, title):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = True
    run_in(p, f"CHAPTER {number}: {title.upper()}", size=14, bold=True)
    return p


def sub_heading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = True
    run_in(p, text, size=12, bold=True)
    return p


def caption(number, title):
    """Table caption carrying a SEQ field so the list of tables can be built.

    The field's placeholder holds the correct number as well, so the caption is
    right even before Word next recalculates fields.
    """
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run_in(p, "Table ", size=11, bold=True)
    add_field(p, " SEQ Table \\* ARABIC ", str(number))
    run_in(p, f": {title}", size=11, bold=True)
    return p


def fig_caption(number, title):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(12)
    run_in(p, "Figure ", size=11, bold=True)
    add_field(p, " SEQ Figure \\* ARABIC ", str(number))
    run_in(p, f": {title}", size=11, bold=True)
    return p


def figure(path, number, title, width_cm=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width_cm))
    fig_caption(number, title)


def table(rows, widths):
    assert abs(sum(widths) - CONTENT_CM) < 0.35, f"widths sum to {sum(widths)} cm"
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = ""
            cells[i].width = Cm(widths[i])
            p = cells[i].paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            run_in(p, str(value), size=11)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def page_break():
    doc.add_page_break()


# ------------------------------------------------------------------ page 1 ---
base_style()
s_front = doc.sections[0]
setup_page(s_front)
s_front.different_first_page_header_footer = True   # title page unnumbered
set_page_numbering(s_front, fmt="lowerRoman", start=1)

footer_p = s_front.footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_field(footer_p, " PAGE ", "i")

logo_p = doc.add_paragraph()
logo_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
logo_p.paragraph_format.space_after = Pt(18)
logo_p.add_run().add_picture(LOGO, width=Cm(6.5))

# the logo carries the university wordmark, so it is not repeated as text
for line, size, bold in [
    ("FACULTY OF COMPUTER ENGINEERING INFORMATICS AND COMMUNICATIONS", 12, True),
    ("DEPARTMENT OF ANALYTICS AND INFORMATICS", 12, True),
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(10)
    run_in(p, line, size=size, bold=bold)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.line_spacing = 1.0
p.paragraph_format.space_before = Pt(30)
p.paragraph_format.space_after = Pt(24)
run_in(p, TITLE, size=14, bold=True)

for line, size in [("BY", 12), (CANDIDATE, 13), ("", 10), ("SUPERVISED BY", 12),
                   (SUPERVISOR, 13)]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(8)
    if line:
        run_in(p, line, size=size, bold=(line in ("BY", "SUPERVISED BY")))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.line_spacing = 1.0
p.paragraph_format.space_before = Pt(26)
p.paragraph_format.space_after = Pt(14)
run_in(p, "THIS CAPSTONE RESEARCH PROJECT WAS SUBMITTED TO THE UNIVERSITY OF "
          "ZIMBABWE IN PARTIAL FULFILMENT OF THE " + DEGREE, size=11)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.line_spacing = 1.0
run_in(p, YEAR, size=13, bold=True)

# ---------------------------------------------------------------- abstract ---
page_break()
front_heading("ABSTRACT")
para(
    "Smallholder maize yield models are increasingly published with prediction intervals, and "
    "those intervals are used to justify fertiliser, credit and crop-insurance decisions. Two "
    "failures recur in this literature and are usually reported separately: reported point "
    "accuracy is inflated by the design used to evaluate it, and interval coverage collapses "
    "when a model is applied to a region it was not calibrated on. This project develops "
    "AGROYIELD-ADAPT, a deployment-readiness auditor that reports both failures together, "
    "identifies which region is unsafe, and prescribes a calibration remedy together with the "
    "label and interval-width cost of that remedy. The artefact is a tested Python tool with "
    "five modules: split integrity, skill and calibration separation, transport diagnosis, "
    "level-adjusted recalibration, and report generation. It is evaluated on the One Acre Fund "
    "smallholder maize panel, a public dataset of 14,773 field-season records from seven "
    "countries covering 2016 to 2022, licensed CC BY 4.0, using random, spatially clustered and "
    "leave-one-country-out validation against pooled, per-domain and label-free calibration "
    "baselines. The first module is complete and unit-tested: the same random forest scores an "
    "R-squared of +0.265 under random five-fold validation, +0.177 when spatial-temporal "
    "clusters are held out, and -1.943 when whole countries are held out, an inflation of "
    "+0.088 and +2.208 R-squared respectively. Preliminary results indicate that coverage "
    "error is monotone in the target domain's yield level while the standard dissimilarity-index "
    "check is uncorrelated with it, a hypothesis the remaining modules will test at stratum "
    "level. The auditor is intended for analysts who must decide whether a yield model is safe "
    "to deploy in a particular region."
)
p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.0
p.paragraph_format.space_before = Pt(10)
run_in(p, "Keywords: ", size=11, bold=True)
run_in(p, "conformal prediction; interval calibration; distribution shift; "
          "smallholder maize; model auditing; data leakage", size=11)

# ------------------------------------------------------------- declaration ---
page_break()
front_heading("DECLARATION")
para("I, " + CANDIDATE + ", hereby declare that this work has not previously been accepted in "
     "substance for any degree and is not being concurrently submitted in candidature for any "
     "degree.")
para("")
para("Student's Signature: ....................................................."
     "  Date ...............................", spacing=1.0)
para("(" + CANDIDATE + ")", spacing=1.0)
para("")
para("Supervisor's Signature: ................................................."
     "  Date ...............................", spacing=1.0)
para("(" + SUPERVISOR + ")", spacing=1.0)

# --------------------------------------------------------------- copyright ---
page_break()
front_heading("COPYRIGHT")
para("All rights reserved. No part of this capstone design project may be reproduced, stored in "
     "any retrieval system, or transmitted in any form or by any means, electronic, mechanical, "
     "photocopying, recording or otherwise for scholarly purpose, without the prior written "
     "permission of the author or of University of Zimbabwe on behalf of the author.")

# --------------------------------------------------------------- dedication ---
page_break()
front_heading("DEDICATION")
para("[To be completed by the candidate: a short personal dedication, or this page may be "
     "removed. It is not part of the assessed contribution.]", italic=True)

# ----------------------------------------------------------- acknowledgements ---
page_break()
front_heading("ACKNOWLEDGEMENTS")
para("I wish to record my gratitude to my supervisor, " + SUPERVISOR + ", for guidance on "
     "framing the contribution and for insisting that every claim be evidenced.")
para("I thank the Department of Analytics and Informatics for the use of its computing facilities "
     "and the Faculty of Computer Engineering Informatics and Communications for the review "
     "process that shaped this proposal.")
para("I acknowledge One Acre Fund and the University of Nebraska-Lincoln for publishing the field "
     "data on which this study depends under an open licence, and the authors of the open-source "
     "scientific Python stack without which the analysis could not be reproduced.")

# ------------------------------------------------------------- abbreviations ---
page_break()
front_heading("ABBREVIATIONS")
abbrev = [
    ("AOA", "area of applicability"),
    ("CP", "conformal prediction"),
    ("DI", "dissimilarity index"),
    ("ESS", "effective sample size"),
    ("LOCO", "leave-one-country-out validation"),
    ("R-squared", "coefficient of determination on log-transformed yield"),
    ("RMSE", "root mean squared error, in kilograms per hectare"),
    ("SSA", "Sub-Saharan Africa"),
    ("UML", "Unified Modelling Language"),
    ("UZ", "University of Zimbabwe"),
]
for short, long_form in abbrev:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Cm(1.6)
    p.paragraph_format.first_line_indent = Cm(-1.6)
    run_in(p, f"{short}\t", size=12, bold=True)
    run_in(p, long_form, size=12)

# ----------------------------------------------------------- table of contents ---
page_break()
front_heading("TABLE OF CONTENTS")
p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.0
add_field(p, ' TOC \\o "1-3" \\h \\z \\u ',
          "Right-click here and choose Update Field to build the table of contents.")

page_break()
front_heading("LIST OF TABLES")
p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.0
add_field(p, ' TOC \\h \\z \\c "Table" ',
          "Right-click here and choose Update Field to build the list of tables.")

page_break()
front_heading("LIST OF FIGURES")
p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.0
add_field(p, ' TOC \\h \\z \\c "Figure" ',
          "Right-click here and choose Update Field to build the list of figures.")

page_break()
front_heading("LIST OF APPENDICES")
for label, title in [("A", "Project plan, deliverables and risk register")]:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    run_in(p, f"APPENDIX {label}: {title.upper()}", size=12)

# ================================================================== body =====
s_body = doc.add_section(WD_SECTION.NEW_PAGE)
setup_page(s_body)
set_page_numbering(s_body, fmt="decimal", start=1)
s_body.footer.is_linked_to_previous = True

# ---------------------------------------------------------------- chapter 1 ---
chapter_heading(1, "Introduction")
sub_heading("1.1 Background and problem statement")
para(
    "Models that predict smallholder maize yield are increasingly reported with prediction "
    "intervals, and those intervals are increasingly used to justify decisions about fertiliser "
    "recommendation, credit and crop insurance. Two failures recur in this literature and are "
    "usually reported separately: reported point accuracy is inflated by evaluation design, and "
    "interval coverage collapses when a model is moved to a new region. A practitioner receiving "
    "such a model today has no instrument that reports both problems together, states which "
    "region is unsafe, and costs the remedy."
)
para(
    "This project addresses that gap by building, testing and evaluating a software artefact – a "
    "deployment-readiness auditor – and by using it to measure how far common calibration "
    "strategies actually travel across smallholder maize domains in Sub-Saharan Africa."
)

sub_heading("1.2 Aim")
para("The aim is to develop and reproducibly evaluate a deployment-readiness auditor that "
     "diagnoses split inflation and interval miscalibration in maize yield models, and prescribes "
     "a calibration remedy with its label and interval-width cost.")

sub_heading("1.3 Objectives")
for obj in [
    "O1. Establish how much reported skill is an artefact of validation design for a "
    "multinational smallholder maize panel, using random, spatially clustered and "
    "leave-one-country-out validation with identical features and model.",
    "O2. Separate model skill from interval validity: report point-transfer accuracy and "
    "empirical coverage per domain as independent verdicts.",
    "O3. Identify which measurable properties of a target domain predict coverage loss, and test "
    "whether the field's standard applicability diagnostic detects it.",
    "O4. Implement a level-adjusted calibration procedure with a label-budget rule, and evaluate "
    "it against pooled, per-domain and label-free weighting baselines.",
    "O5. Deliver the auditor as documented, tested software with a reproducibility record, and "
    "evaluate its warning behaviour.",
]:
    para(obj)

sub_heading("1.4 Research questions and hypotheses")
for rq in [
    "RQ1. How large is the inflation in reported predictive skill when spatial and national "
    "structure are respected?",
    "RQ2. Do intervals calibrated on a multi-country pool retain nominal coverage in a held-out "
    "country, and does point-model skill predict whether they will?",
    "RQ3. Is coverage loss predictable from observable properties of the target domain, and does "
    "the dissimilarity-index applicability check detect it?",
    "RQ4. What label budget and interval-width cost does restoring coverage require?",
]:
    para(rq)
para(
    "Four pre-declared hypotheses follow, each falsifiable and each reported whichever way it "
    "falls: H1 inflation exceeds 0.05 R-squared on the clustered design; H2 pooled calibration "
    "does not reach nominal coverage in at least one domain and coverage is not monotone in "
    "point-model skill; H3 coverage loss is associated with the target domain's yield level "
    "rather than with covariate-space dissimilarity alone; H4 local recalibration restores "
    "coverage at no more than a stated width penalty."
)

sub_heading("1.5 Scope and delimitation")
para(
    "In scope: a Python command-line auditor with five modules (split integrity, skill and "
    "calibration separation, transport diagnosis, level-adjusted recalibration, report "
    "generation), evaluated on one public panel."
)
para(
    "Out of scope, and not claimed: a new theory of conformal prediction; live data ingestion; a "
    "mobile application; a commercial backend; causal effects of changing agronomic practice; "
    "farmer income or insurance outcomes; national representativeness; and validity for Zimbabwe, "
    "which the dataset does not cover. The contribution is an instrument plus measured evidence, "
    "not a new algorithm."
)

# ---------------------------------------------------------------- chapter 2 ---
chapter_heading(2, "Literature review and evidence base")
sub_heading("2.1 The dataset and its provenance")
para(
    "The study uses the One Acre Fund smallholder maize panel (Aramburu Merlos et al., 2024), "
    "deposited on Zenodo (doi:10.5281/zenodo.11122388) under CC BY 4.0 and used in the dataset's "
    "own source publication (Aramburu-Merlos et al., 2024). The local copy has been audited and "
    "fingerprinted: 14,773 field-season records, 53 columns, seven countries (Kenya 7,258; "
    "Tanzania 3,710; Rwanda 2,080; Zambia 861; Burundi 640; Nigeria 115; Uganda 109), survey "
    "years 2016–2020 and 2022, 263 zero-yield records (1.78%), 1,526 spatial-temporal clusters "
    "at 0.1 degree plus year, and 4,764 records (32.2%) sharing a cluster with another record. "
    "Soil covariates are missing for 78.4% of Burundi records and 76.3% of Rwandan records, a "
    "limitation carried forward to the analysis."
)
p = doc.add_paragraph()
p.paragraph_format.line_spacing = 1.5
run_in(p, "SHA-256 of the analysed file: ", size=12)
run_in(p, "f305a3d3e48015bd877dc9df5c53b1715c61f940d58383d57d4dfb68c59c6ff0",
       size=9.5, font="Consolas")

sub_heading("2.2 Related work and positioning")
para(
    "Split conformal prediction gives marginal coverage under exchangeability (Vovk, Gammerman "
    "and Shafer, 2005; Angelopoulos and Bates, 2023), and its coverage guarantee is known to "
    "degrade under distribution shift, with bounds available once the shift is quantified "
    "(Barber et al., 2023). Conditioning coverage on a domain, as Mondrian conformal prediction "
    "does, restores validity at the cost of wider intervals. Two families of remedy appear in the "
    "literature: reweighting the calibration set towards the target distribution (Tibshirani et "
    "al., 2019) and recalibrating locally on labelled target data (Lei et al., 2018; Podkopaev "
    "and Ramdas, 2021)."
)
para(
    "Separately, the spatial-prediction literature offers the dissimilarity index and area of "
    "applicability as a pre-deployment check on whether a target location is inside the "
    "predictor's support (Meyer and Pebesma, 2021). That check reasons about covariates only. "
    "Finally, a substantial methodological literature documents how evaluation design inflates "
    "reported skill through leakage (Kapoor and Narayanan, 2023), which is directly relevant to "
    "a panel in which 32.2% of records share a location and year with another record."
)
para(
    "The gap this project addresses is that these three strands are reported separately: point "
    "accuracy, interval validity and applicability are rarely presented as one verdict for one "
    "domain, and the cost of the remedy is almost never stated. The contribution is therefore an "
    "instrument that joins them and measures the cost, not a new theory."
)

# ---------------------------------------------------------------- chapter 3 ---
chapter_heading(3, "Research methodology")
sub_heading("3.1 System analysis and design")
para(
    "The formulated solution is modelled before it is built. Figure 1 shows the actors and the "
    "services the auditor exposes; Figure 2 shows the audit run with its two decision points, "
    "which is where the readiness verdict is produced; Figure 3 shows the five modules and the "
    "data each holds; and Figure 4 shows what runs where, given that the tool is deliberately "
    "single-machine and needs no server."
)
figure("docs/figures/fig1_usecase.png", 1,
       "Use-case diagram of the deployment-readiness auditor")
figure("docs/figures/fig2_activity.png", 2,
       "Activity diagram of an audit run")
figure("docs/figures/fig3_class.png", 3,
       "Class diagram of the five auditor modules")
figure("docs/figures/fig4_deployment.png", 4,
       "Deployment diagram: components on the analyst's workstation")

sub_heading("3.2 Artefact design")
para("Each module is independently testable, and each maps to one objective in Section 1.3:")
for mod in [
    "M1 Split integrity. Fits one model under random, cluster-grouped and leave-one-country-out "
    "validation and reports the resulting inflation.",
    "M2 Skill and calibration separation. Reports point-transfer accuracy and empirical interval "
    "coverage per domain as separate verdicts.",
    "M3 Transport diagnosis. Computes dissimilarity index and out-of-area share, "
    "prediction-distribution distance, effective sample size of density-ratio weights, and the "
    "target domain's yield-level offset, then issues a pass, warn or fail flag.",
    "M4 Level-adjusted recalibration. Corrects the score quantile for the target domain's level "
    "offset from a small labelled sample and reports the label budget required.",
    "M5 Report generation. Produces a machine-readable and human-readable readiness report.",
]:
    para(mod)

sub_heading("3.3 Evaluation design")
para(
    "Evaluation uses three validation designs, three seeds and a second model family. Pooled "
    "calibration is compared with per-domain (Mondrian) calibration, label-free density-ratio "
    "weighting and the level-adjusted procedure of M4, at a nominal coverage of 0.90. The "
    "auditor's own warning behaviour is assessed against observed coverage loss, so the tool is "
    "evaluated as software as well as used as an instrument. Effect sizes are reported with their "
    "uncertainty, and fold-seeds are never treated as independent observations."
)

sub_heading("3.4 Reproducibility and data handling")
para(
    "All preprocessing is fold-internal: imputation statistics are estimated on training folds "
    "only, because global imputation silently uses test-set statistics. Every run is recorded "
    "with its seeds, fold assignments and a checksum of the data file, and code is versioned in a "
    "public repository. An earlier run that imputed globally is retained as a documented "
    "sensitivity case rather than discarded."
)

# ---------------------------------------------------------------- chapter 4 ---
chapter_heading(4, "Preliminary results and discussion")
sub_heading("4.1 Split integrity")
para(
    "Module 1 is implemented, unit-tested and run on the full panel. Table 1 reports the same "
    "random forest and features under three validation designs."
)
caption(1, "Validation design versus reported skill for the full panel")
table([
    ["Validation design", "Folds", "R-squared (log yield)", "RMSE (kg/ha)"],
    ["Random 5-fold", "5", "+0.265", "1,486"],
    ["Cluster-grouped 5-fold (0.1 degree + year)", "5", "+0.177", "1,578"],
    ["Leave-one-country-out", "7", "-1.943", "2,284"],
], widths=[7.0, 1.8, 4.4, 2.8])
para(
    "Inflation relative to the random design is +0.088 R-squared when cluster structure is "
    "ignored and +2.208 when national structure is ignored. An earlier run that imputed missing "
    "values once, globally, before splitting produced -0.925 for the cross-country design; "
    "imputing inside each fold moves it to -1.943. The earlier figure was therefore optimistic, "
    "because global imputation uses test-set statistics."
)

sub_heading("4.2 Calibration pilot")
para(
    "Preliminary work from the development pilot, not yet recomputed under the auditor's "
    "preprocessing, suggests the calibration picture: pooled calibration at nominal 0.90 gives "
    "empirical coverage between 0.574 and 1.000 across the seven countries; per-domain "
    "calibration gives 0.852 to 0.930 at a median width of 0.95 times pooled; label-free "
    "density-ratio weighting does not improve on pooled calibration and retains an effective "
    "sample size of only 0.09 to 0.17. Across the seven domains the signed coverage error is "
    "monotone in the domain's median yield (Spearman rho = +0.96, n = 7) and uncorrelated with "
    "the dissimilarity index (rho = 0.00)."
)

sub_heading("4.3 Discussion")
para(
    "With seven domains this evidence is suggestive, not conclusive, and it is reported as a "
    "hypothesis under test rather than as a finding. If it survives replication at stratum level "
    "it would imply that pre-deployment support checks based on covariates cannot detect the "
    "failure that matters for intervals, and that a small labelled sample from the target domain "
    "is the only reliable remedy — which is precisely the cost the auditor is designed to state."
)

# ---------------------------------------------------------------- chapter 5 ---
chapter_heading(5, "Conclusion and recommendations")
sub_heading("5.1 Summary")
para(
    "The project delivers an instrument and a body of measured evidence about how maize "
    "yield-interval models fail when moved between regions, and what repairing them costs."
)
sub_heading("5.2 Contribution")
para(
    "The contribution is threefold: an executable audit that joins split integrity, skill and "
    "calibration; measured evidence on the size of both failures in a seven-country panel; and a "
    "recalibration procedure with an explicit label budget. It is an instrument plus evidence, "
    "not a new algorithm, and it is presented as such."
)
sub_heading("5.3 Limitations")
para(
    "Seven country domains give limited statistical power; a single model family would leave the "
    "diagnosis open to a configuration objection; and soil covariates are missing for most "
    "records in two countries. Each limitation is addressed by the evaluation design rather than "
    "argued away."
)
sub_heading("5.4 Recommendations and further work")
para(
    "Further work should replicate the diagnosis at stratum level, extend the auditor to a "
    "second crop and to seasonal forecast covariates, and test whether the label budget it "
    "prescribes is affordable in an extension setting."
)

# ------------------------------------------------------------- references ----
chapter_heading(6, "References")
refs = [
    "Angelopoulos, A. N. and Bates, S. (2023) 'Conformal prediction: a gentle introduction', "
    "Foundations and Trends in Machine Learning, 16(4), pp. 494–591.",
    "Aramburu Merlos, F., Tenorio, F. A., Mashingaidze, N., Sananka, A., Aston, S. and Grassini, "
    "P. (2024) Maize management and yield of smallholder farmers in Sub-Saharan Africa between "
    "2016 and 2022. Zenodo. doi:10.5281/zenodo.11122388.",
    "Aramburu-Merlos, F., Tenorio, F. A. M., Mashingaidze, N., Sananka, A., Aston, S., Ojeda, "
    "J. J. and Grassini, P. (2024) 'Adopting yield-improving practices to meet maize demand in "
    "Sub-Saharan Africa without cropland expansion', Nature Communications, 15. "
    "doi:10.1038/s41467-024-48859-0.",
    "Barber, R. F., Candes, E. J., Ramdas, A. and Tibshirani, R. J. (2023) 'Conformal prediction "
    "beyond exchangeability', The Annals of Statistics, 51(2).",
    "Kapoor, S. and Narayanan, A. (2023) 'Leakage and the reproducibility crisis in "
    "machine-learning-based science', Patterns, 4(9).",
    "Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J. and Wasserman, L. (2018) "
    "'Distribution-free predictive inference for regression', Journal of the American "
    "Statistical Association, 113(523), pp. 1094–1111.",
    "Meyer, H. and Pebesma, E. (2021) 'Predicting into unknown space? Estimating the area of "
    "applicability of spatial prediction models', Methods in Ecology and Evolution, 12(9), "
    "pp. 1620–1633.",
    "Podkopaev, A. and Ramdas, A. (2021) 'Tracking the risk of a deployed model and detecting "
    "harmful distribution shifts', Proceedings of the 24th International Conference on Artificial "
    "Intelligence and Statistics.",
    "Tibshirani, R. J., Barber, R. F., Candes, E. J. and Ramdas, A. (2019) 'Conformal prediction "
    "under covariate shift', Advances in Neural Information Processing Systems, 32.",
    "Vovk, V., Gammerman, A. and Shafer, G. (2005) Algorithmic Learning in a Random World. "
    "New York: Springer.",
]
for ref in refs:
    para(ref, size=11, spacing=1.5, indent_hang=True)

# ------------------------------------------------------------- appendix A ----
page_break()
front_heading("APPENDIX A: PROJECT PLAN, DELIVERABLES AND RISK REGISTER")
para("A.1 Deliverables and review mapping")
caption(2, "Deliverables mapped to guideline review objectives")
table([
    ["Deliverable", "Guideline basis", "Review"],
    ["This proposal, finalised", "Project proposal", "Review 1"],
    ["Development and test environment specification",
     "Review 1: tools, environment, test procedures", "Review 1"],
    ["First draft of test procedures", "Review 1 objective", "Review 1"],
    ["Initial UML analysis of the formulated solution", "Review 1 objective", "Review 1"],
    ["Final design: algorithm, UML set, database and interface design",
     "Review 2 objective", "Review 2"],
    ["Implemented and evaluated auditor (M1–M5), with test suite",
     "Prototype development and evaluation", "Review 3"],
    ["Project demonstration with before/after readiness report",
     "Final oral presentation", "Review 4"],
    ["Final report, 45–60 pages, Harvard referencing", "Report format rules", "Final"],
    ["Appendix A: source code repository; Appendix B: user manual",
     "Report appendices", "Final"],
    ["Systematic review and survey paper; technical paper",
     "Literature and presentation criteria", "Final"],
], widths=[7.0, 6.0, 3.0])

para("A.2 Timeline")
caption(3, "Work plan to the final review")
table([
    ["Period", "Work"],
    ["By Review 1 (1–4 December 2026)",
     "Proposal, environment specification, test procedures draft, initial UML, Module 1 running"],
    ["December 2026 – January 2027", "Modules 2 and 3, systematic review, survey paper"],
    ["February 2027", "Module 4 and label-budget evaluation; robustness runs"],
    ["March 2027", "Report drafting, technical paper, user manual, demonstration preparation"],
], widths=[4.8, 11.2])

para("A.3 Risk register")
caption(4, "Project risks and their mitigation")
table([
    ["Risk", "Mitigation"],
    ["Reframing not accepted by supervisor",
     "Proposal submitted for sign-off before further build; Module 1 is independent of framing"],
    ["Seven country domains give low statistical power",
     "Replicate at stratum level (25 strata) and across seeds; report effect sizes with "
     "uncertainty"],
    ["Auditor judged not to be a prototype",
     "Ship command-line tool, interface, report, user manual and test suite; seek written "
     "confirmation at Review 1"],
    ["Soil missingness confounds the diagnosis",
     "Optional iSDAsoil covariate layer; otherwise report the confound explicitly"],
    ["Scope creep beyond a 45–60 page report",
     "Five fixed modules; no live service, no accounts, no mobile client"],
], widths=[5.2, 10.8])

update_fields_on_open()
doc.save(OUT)
print(f"wrote {OUT}")
