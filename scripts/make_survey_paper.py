"""Build the survey paper to the UZ-DAI Survey Paper 1 structure.

Template requirements implemented here:
  * separate title page carrying the student's name and number
  * "A Survey of ..." title
  * sections: Abstract, Introduction, Body (problem + critical review of each
    foundational paper + figures), Conclusion / future work, References
  * 10-22 foundational papers (15 are cited), IEEE reference style
  * 5-8 pages / approximately 4000 words
"""

import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

OUT = "FINISHED/Survey_Paper_v1.docx"

TITLE = ("A Survey of Uncertainty Quantification and Transfer Validation for "
         "Smallholder Crop Yield Prediction")
AUTHOR = "IAN CHINYOKA  R231473B"
SUPERVISOR = "MR ZIMOWA"
DEPT = ("Department of Analytics and Informatics, Faculty of Computer Engineering "
        "Informatics and Communications")
UNIV = "University of Zimbabwe"
YEAR = "2026"

FIG1 = "docs/figures/survey_fig1_taxonomy.png"
FIG2 = "docs/figures/survey_fig2_coverage.png"
FIG3 = "docs/figures/survey_fig3_pipeline.png"

doc = Document()


# ----------------------------------------------------------------- helpers ---
def run_in(p, text, size=10, bold=False, italic=False, small_caps=False):
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    r.bold, r.italic, r.font.small_caps = bold, italic, small_caps
    r.font.color.rgb = RGBColor(0, 0, 0)
    return r


def para(text, size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY, spacing=1.15, after=5,
         indent=0.0, first=0.0, bold=False, italic=False):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = spacing
    p.paragraph_format.space_after = Pt(after)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    if first:
        p.paragraph_format.first_line_indent = Cm(first)
    run_in(p, text, size=size, bold=bold, italic=italic)
    return p


def heading(number, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run_in(p, f"{number}. {text.upper()}", size=10.5, small_caps=True)
    return p


def subheading(label, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run_in(p, f"{label} {text}", size=10.5, italic=True)
    return p


def figure(path, caption, width_cm=14.6):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Cm(width_cm))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.line_spacing = 1.0
    c.paragraph_format.space_after = Pt(9)
    run_in(c, caption, size=9.0)


def table_caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = True
    run_in(p, text, size=9.0)


def table(rows, widths, head_size=8.5, body_size=8.2):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, row in enumerate(rows):
        cells = t.add_row().cells
        for j, value in enumerate(row):
            cells[j].text = ""
            cells[j].width = Cm(widths[j])
            p = cells[j].paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(1)
            run_in(p, str(value), size=head_size if i == 0 else body_size, bold=(i == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def setup(section):
    section.page_width, section.page_height = Cm(21.0), Cm(29.7)
    section.left_margin = section.right_margin = Cm(2.54)
    section.top_margin = section.bottom_margin = Cm(2.54)


def add_page_field(section):
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), " PAGE ")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    footer._p.append(fld)


setup(doc.sections[0])
n = doc.styles["Normal"]
n.font.name = "Times New Roman"
n.font.size = Pt(10)
n.paragraph_format.line_spacing = 1.15
n.paragraph_format.space_after = Pt(5)
add_page_field(doc.sections[0])

# ------------------------------------------------------------- title page ---
logo = doc.add_paragraph()
logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
logo.paragraph_format.space_before = Pt(24)
logo.paragraph_format.space_after = Pt(10)
if os.path.exists("docs/assets/uz_logo.jpg"):
    logo.add_run().add_picture("docs/assets/uz_logo.jpg", width=Cm(2.6))

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_in(p, UNIV.upper(), size=16, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
run_in(p, "FACULTY OF COMPUTER ENGINEERING INFORMATICS AND COMMUNICATIONS", size=10.5,
       bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(50)
run_in(p, "DEPARTMENT OF ANALYTICS AND INFORMATICS", size=10.5, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(6)
run_in(p, "SURVEY PAPER 1", size=11, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(24)
run_in(p, TITLE, size=15, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
run_in(p, "BY", size=10.5, bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(20)
run_in(p, AUTHOR, size=12, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
run_in(p, "SUPERVISOR", size=10.5, bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(50)
run_in(p, SUPERVISOR, size=11.5, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(40)
run_in(p, "A survey paper submitted in partial fulfilment of the requirements of the "
          "Bachelor of Science (Honours) degree in Data Science and Informatics", size=10,
       italic=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_in(p, YEAR, size=11, bold=True)

doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ------------------------------------------------------------- abstract -----
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
run_in(p, TITLE, size=13, bold=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(1)
run_in(p, AUTHOR, size=10.5)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(1)
run_in(p, DEPT, size=9, italic=True)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(10)
run_in(p, f"Supervisor: {SUPERVISOR}", size=9, italic=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p.paragraph_format.space_after = Pt(4)
run_in(p, "Abstract—", size=9.5, bold=True)
run_in(p, "Yield prediction models built on smallholder survey data are increasingly "
          "published with prediction intervals, and those intervals increasingly inform "
          "fertiliser, credit and insurance decisions. Whether an interval can be trusted in "
          "a region it was not calibrated for depends on three separate bodies of work: how "
          "the interval is constructed, how the fit is judged, and how the model is moved. "
          "This paper surveys fifteen foundational works across those three strands and "
          "assesses them against the needs of the base project, a deployment-readiness "
          "auditor for smallholder maize yield models. Four findings emerge. Interval "
          "construction is mature, with finite-sample guarantees available under stated "
          "assumptions. Evaluation design materially inflates reported skill when spatial or "
          "hierarchical structure is ignored, and interval studies seldom audit this. The "
          "standard pre-deployment support check reasons about covariates only and therefore "
          "cannot detect a shift in the outcome distribution. No surveyed work reports "
          "construction, honest evaluation and transport for one domain together, and none "
          "costs the remedy. The paper concludes that the missing artefact is a joint audit "
          "that separates skill from calibration, diagnoses which shift is responsible and "
          "states the label budget required to restore coverage, and it sets out five "
          "research directions that follow.", size=9.5)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(10)
run_in(p, "Index Terms—", size=9.5, bold=True)
run_in(p, "conformal prediction; uncertainty quantification; crop yield; distribution shift; "
          "spatial cross-validation; data leakage", size=9.5, italic=True)

# --------------------------------------------------------------------- 1 ----
heading("1", "Introduction")
para(
    "Yield prediction models fitted to field-level survey data are now common in agronomic "
    "research, and they are increasingly reported with prediction intervals rather than point "
    "estimates alone. The reason is practical: an interval can be attached to a decision. A "
    "fertiliser recommendation, a credit limit or an insurance premium needs to know how "
    "uncertain a prediction is, not only what the prediction is."
)
para(
    "An interval is useful only if it is valid where it is used. Validity has a precise "
    "meaning: over repeated draws the interval should contain the true value at the stated "
    "rate. Conformal prediction supplies that property under an assumption of exchangeability, "
    "and the framework has become the standard way to attach a guarantee to an arbitrary point "
    "predictor [1], [2]. The guarantee is marginal, however: it holds on average over the data "
    "used, not for each region or each subgroup, and it fails when target data are not "
    "exchangeable with calibration data."
)
para(
    "That failure mode matters in agronomy because models are routinely fitted on a "
    "multi-country panel and then applied to one country. Three literatures bear on the "
    "problem without meeting. The conformal literature studies how to construct intervals and "
    "what they guarantee [1]–[5]. The validation literature studies how evaluation design "
    "inflates reported skill when data are spatially or hierarchically structured [11]–[13]. "
    "The spatial-prediction literature studies whether a target location lies inside the "
    "predictor's support [10]. A practitioner holding a model therefore has three separate "
    "answers and no single verdict."
)
para(
    "This paper surveys those strands together and assesses each source against the "
    "requirements of the base project, AGROYIELD-ADAPT, a deployment-readiness auditor that "
    "must decide whether a smallholder maize yield-interval model is safe to deploy in a "
    "particular country. Section 2 states the problem and the base project. Section 3 reviews "
    "the fifteen foundational papers, groups them by the question each answers, gives a "
    "critical commentary on each, and tabulates what each contributes and what it leaves "
    "undone. Section 4 assesses the base project critically. Section 5 sets out the "
    "improvements the survey supports and their feasibility. Section 6 concludes and states "
    "future directions."
)

# --------------------------------------------------------------------- 2 ----
heading("2", "Problem description and the base project")
para(
    "The base project addresses a specific and common situation. A model is fitted to the "
    "One Acre Fund smallholder maize panel, a public field-level dataset of 14,773 season "
    "records from seven Sub-Saharan African countries covering 2016 to 2022 [14]. The panel "
    "is observational, unbalanced across countries and years, and contains 4,764 duplicate "
    "rows, 32.2 per cent of the file. The model is a random forest [6] fitted to predict "
    "maize yield from management and environment variables. The question the project must "
    "answer is not how accurate that model is on the panel, but whether an interval produced "
    "from it can be trusted when the model is applied to one country, and what it would cost "
    "to make it trustworthy."
)
para(
    "Three difficulties make that question hard, and each has a literature behind it. First, "
    "the dataset is duplicated and clustered, so a random split lets the model see near-copies "
    "of test rows during training; the reported accuracy is then partly a measure of "
    "duplicate recognition [11], [12]. Second, once the split is honest, the point model's "
    "skill and the interval's calibration become two distinct quantities that can fail "
    "independently; a model can transfer its ranking ability to a new country while its "
    "intervals collapse, and reporting a single number hides that [1], [3]. Third, moving to "
    "one country changes both the covariate distribution and the outcome distribution, and "
    "the usual pre-deployment check measures only the first [10]."
)
para(
    "The base project's own preliminary result shows why this matters. The same random forest "
    "scores an R-squared of +0.265 under random five-fold validation, +0.177 when "
    "spatial-temporal clusters are held out, and −1.943 when whole countries are held out — an "
    "inflation of +0.088 and +2.208 respectively. A practitioner who validated the model "
    "randomly would conclude it transfers; the honest design says it does not. Because each "
    "of the fifteen sources below addresses one part of this picture, reviewing them together "
    "is the only way to see which part the base project is missing."
)
figure(FIG1, "Fig. 1. The three literatures that bear on the base project, and the verdict "
             "none of them delivers alone.")

# --------------------------------------------------------------------- 3 ----
heading("3", "Review of foundational papers")
para(
    "The fifteen sources are grouped by the question each answers. For every paper the "
    "commentary states what the approach guarantees, why it matters to the base project, and "
    "where it stops. Table I summarises the same judgement in comparable form, and Fig. 2 "
    "shows the distribution of concerns across the corpus."
)

subheading("3.1", "Constructing an interval and what the guarantee means")
para(
    "Vovk, Gammerman and Shafer [2] established the framework on which everything here rests: "
    "a prediction set is valid if, over repeated draws, it fails to contain the truth at most "
    "a known rate, and that property follows from the exchangeability of the data rather than "
    "from the correctness of the model. For the base project this is the single most useful "
    "idea in the corpus, because it explains why an interval can be attached to a random "
    "forest whose functional form nobody believes. The limitation is equally important: a "
    "textbook treatment assumes exchangeability and offers no guidance for a panel whose rows "
    "are grouped by country and year, which is exactly the base project's situation."
)
para(
    "Angelopoulos and Bates [1] turn that framework into a recipe. Split conformal prediction "
    "fits the model on one part of the data, computes nonconformity scores on a second part "
    "and takes a quantile of those scores as the interval half-width. The survey is valuable "
    "to the base project for two reasons: it states the recipe precisely enough to implement, "
    "and it is candid that conditional coverage — coverage for a given region or covariate "
    "value — is hard in general. That candour is the gap the base project must measure rather "
    "than assume away: a marginal guarantee across seven countries says nothing about the one "
    "country where a recommendation will be issued."
)
para(
    "Lei et al. [3] give the finite-sample justification for the split construction in "
    "regression, with an explicit marginal coverage statement. Its significance for the base "
    "project is procedural: it settles that calibration must be done on data held out from "
    "fitting, which rules out the resubstitution habit of quoting in-sample residuals as "
    "uncertainty. The assumption is independent and identically distributed sampling, and the "
    "paper does not examine what happens when rows are clustered, so the base project cannot "
    "inherit the guarantee merely by citing it."
)
para(
    "Romano, Patterson and Candès [4] replace the constant-width interval with a "
    "conformalised quantile regression, calibrating estimated conditional quantiles so that "
    "the interval adapts to heteroscedasticity. Maize yield is strongly heteroscedastic — "
    "high-input plots vary more than low-input plots — so an adaptive width is not a luxury "
    "here but a requirement if the interval is to be useful at both ends of the management "
    "range. The approach still delivers marginal coverage, and it depends on the quantile "
    "model being adequate, which is a real constraint on a panel with seven countries."
)
para(
    "Meinshausen [5] offers the alternative route: quantile regression forests read quantiles "
    "from the empirical distribution held in the leaves of an ensemble, so one model produces "
    "both the prediction and the interval. For the base project the attraction is economy — "
    "no separate calibration set is needed, which matters when a target country contributes "
    "few rows — but there is no finite-sample coverage guarantee, only an approximation that "
    "improves with the number of trees. Choosing between [4] and [5] is therefore a choice "
    "between a guarantee that needs data and an approximation that needs none."
)
para(
    "Breiman [6] is included because it defines the object whose uncertainty is being "
    "quantified. The random forest is the point learner in the base project, and the paper's "
    "contribution to this survey is negative but essential: it makes no uncertainty statement "
    "at all. Every later step in the base project exists to supply the statement that the "
    "point model cannot give."
)
para(
    "Barber et al. [7] move beyond exchangeability and give coverage-gap bounds that hold "
    "under a measurable distribution shift. This is the theoretical hinge of the survey. It "
    "converts the question “does our guarantee survive the move to one country?” from a matter "
    "of assertion into a quantity that can in principle be computed and reported. The "
    "limitation is practical: the bound requires a shift measure that applied studies rarely "
    "have, which is why the applied papers in this corpus report nominal coverage and stop."
)

subheading("3.2", "Judging the fit: validation design and leakage")
para(
    "Roberts et al. [11] catalogue cross-validation strategies for data with temporal, "
    "spatial, hierarchical or phylogenetic structure, and prescribe blocking that mirrors the "
    "structure of the prediction task. This is the design the base project's first module "
    "implements: hold out whole clusters for the clustered design and whole countries for the "
    "transfer design. The paper is about estimating skill honestly, not about intervals, and "
    "that limit is precisely why it cannot be the whole answer — an honest split still leaves "
    "the calibration question open."
)
para(
    "Ploton et al. [12] supply the evidence that the design matters in practice. Comparing "
    "random and spatial validation on large-scale mapping models, they find that spatial "
    "validation reveals markedly poorer performance than random validation had suggested. For "
    "the base project this is the published precedent for the inflation it measures, and the "
    "magnitude reported there is consistent with the +0.088 clustered and +2.208 "
    "country-holdout inflation observed on the maize panel. The study concerns ecological "
    "mapping rather than yield, so it motivates the audit without supplying its thresholds."
)
para(
    "Kapoor and Narayanan [13] name the underlying problem and give it a taxonomy: leakage is "
    "the use, during training or evaluation, of information unavailable at prediction time, "
    "and its recurring forms include duplicate records, temporal leakage and the reuse of test "
    "data for model selection. The survey's value to the base project is vocabulary and a "
    "checklist, and its relevance to intervals is direct: the calibration set is part of the "
    "evaluation. If calibration rows share clusters with test rows, the scores are computed on "
    "data the model has effectively seen and the interval is over-confident by construction, "
    "even when every individual step follows the recipe correctly. The paper diagnoses; it "
    "does not provide an executable audit of a given pipeline, which is what the base project "
    "must build."
)

subheading("3.3", "Moving the model: applicability, shift and remedy")
para(
    "Meyer and Pebesma [10] propose the dissimilarity index, a scaled distance in predictor "
    "space from each target location to the training data, with a threshold beyond which "
    "predictions are flagged as outside the area of applicability. It is the standard "
    "pre-deployment check in spatial prediction and the one the base project's domain already "
    "uses [15]. Its limitation is structural rather than incidental: the index is computed in "
    "covariate space, so a target region can sit comfortably inside the support and still have "
    "a different yield distribution because management, market access or measurement practice "
    "differ. Demonstrating that blind spot is one of the base project's contributions."
)
para(
    "Tibshirani et al. [8] provide the first remedy: under covariate shift, weighting the "
    "conformity scores by an estimated likelihood ratio restores validity. The method is "
    "principled and its failure mode is well understood — the weights concentrate on few "
    "calibration points, the effective sample size collapses and the interval becomes unstable. "
    "In a seven-country panel, where one country can be an outlier in several covariates at "
    "once, this is a live concern rather than a footnote, and the paper does not quantify the "
    "stability cost."
)
para(
    "Podkopaev and Ramdas [9] treat the complementary case, where the shift is in the outcome "
    "distribution, and show that tracking the risk of a deployed model requires watching the "
    "score distribution rather than only the covariates. Translated to yield, the implication "
    "is that a small labelled sample from the target country, used to estimate a level offset, "
    "may be worth more than a large unlabelled sample and a covariate diagnostic. The paper "
    "works in a classification and risk-control setting and does not produce regression "
    "intervals, but it supplies the hypothesis the base project's fourth module tests."
)

subheading("3.4", "The agronomic base")
para(
    "Aramburu Merlos et al. [14] publish the panel itself: 14,773 georeferenced field records "
    "of maize management and yield from smallholder farms in seven countries, licensed CC BY "
    "4.0. Its significance is that the base project's claims are tied to a public, "
    "reproducible dataset rather than to a private extract, and its limitation is equally "
    "relevant: it is observational, unbalanced across countries and years, and duplicated. The "
    "duplicates are not a defect of the release but a property of the survey design that any "
    "honest audit must handle explicitly."
)
para(
    "Aramburu-Merlos et al. [15] analyse the same panel and show how much of the yield gap "
    "could be closed by adopting yield-improving practices, applying an area-of-applicability "
    "check of the kind proposed in [10]. The paper is the clearest statement of what the "
    "domain currently does: a support check before extrapolation, and point accuracy as the "
    "measure of success. It reports no prediction intervals and no leakage audit, which is "
    "precisely the gap the base project occupies — the domain already accepts that "
    "extrapolation must be checked, but checks it only in covariate space and only for the "
    "point prediction."
)

subheading("3.5", "Comparative assessment")
table_caption("TABLE I. Critical assessment of the fifteen foundational papers")
table([
    ["Source", "Contribution", "Significance to the base project", "Limitation"],
    ["[1] Angelopoulos & Bates, 2023", "Tutorial and recipe for split conformal prediction",
     "Supplies the calibration step the auditor implements",
     "Marginal guarantee only; conditional coverage left open"],
    ["[2] Vovk et al., 2005", "The conformal framework and its validity argument",
     "Explains why an interval can wrap a random forest at all",
     "Assumes exchangeability; no guidance for grouped panels"],
    ["[3] Lei et al., 2018", "Finite-sample marginal coverage for split conformal regression",
     "Rules out resubstitution; calibration must be held out",
     "i.i.d. sampling assumed; clustering untreated"],
    ["[4] Romano et al., 2019", "Conformalised quantile regression with adaptive width",
     "Motivates reporting interval width beside coverage",
     "Needs an adequate quantile model; still marginal"],
    ["[5] Meinshausen, 2006", "Quantile regression forests",
     "One-model route to intervals when a country has few rows",
     "No finite-sample guarantee; approximation only"],
    ["[6] Breiman, 2001", "Random forests",
     "Defines the point learner whose uncertainty is audited",
     "Makes no uncertainty statement at all"],
    ["[7] Barber et al., 2023", "Coverage-gap bounds beyond exchangeability",
     "Turns the transfer question into a measurable gap",
     "Requires a shift measure practitioners rarely have"],
    ["[8] Tibshirani et al., 2019", "Weighted conformal prediction under covariate shift",
     "Candidate remedy when the shift is covariate",
     "Weight collapse; effective sample size unaddressed"],
    ["[9] Podkopaev & Ramdas, 2021", "Risk tracking and detection under distribution shift",
     "Supports the level-offset hypothesis for yield",
     "Classification framing; no regression intervals"],
    ["[10] Meyer & Pebesma, 2021", "Dissimilarity index and area of applicability",
     "The standard check whose blind spot the auditor exposes",
     "Covariate space only; outcome shift invisible"],
    ["[11] Roberts et al., 2017", "Cross-validation strategies for structured data",
     "Grounds the auditor's clustered and country-holdout designs",
     "Concerns skill, not interval validity"],
    ["[12] Ploton et al., 2020", "Spatial validation exposes inflated skill",
     "Published precedent for the inflation the auditor measures",
     "Ecological mapping; no thresholds for yield"],
    ["[13] Kapoor & Narayanan, 2023", "Leakage taxonomy across modelling fields",
     "Gives the auditor its checklist and vocabulary",
     "Diagnosis, not an executable audit"],
    ["[14] Aramburu Merlos et al., 2024", "The open smallholder maize panel",
     "Empirical vehicle; public and reproducible",
     "Observational, unbalanced, 32.2% duplicated rows"],
    ["[15] Aramburu-Merlos et al., 2024", "Yield-gap analysis with an applicability check",
     "Shows what the domain does and what it omits",
     "No intervals, no leakage audit"],
], widths=[3.5, 4.2, 4.4, 3.7], head_size=8.4, body_size=7.8)
figure(FIG2, "Fig. 2. Which of four concerns each source addresses. No source fills the "
             "fourth column: none states what the remedy costs.", width_cm=12.8)
para(
    "Read across Table I, the pattern is not a gap in any single row but a gap between rows. "
    "Each family answers its own question correctly. None reports, for one domain, both the "
    "honest point skill and the interval validity, and none states what it would cost to "
    "repair the interval. The practitioner's question — is this model safe here, and what "
    "would make it safe — falls between the columns, and Fig. 2 makes the omission visible: "
    "the fourth column is empty for every source in the corpus."
)

# --------------------------------------------------------------------- 4 ----
heading("4", "Critical assessment of the base project")
para(
    "Three strengths hold up under review. The project takes a public dataset rather than a "
    "private extract, so its claims are checkable. It separates the two failures that the "
    "corpus usually reports together, which is the specific contribution Table I shows to be "
    "missing. And it costs the remedy, reporting the labels and interval width required, "
    "which is the concern no surveyed source addresses."
)
para(
    "Four weaknesses follow from the same review. First, breadth: the project audits one "
    "learner on one panel, so its thresholds are calibrated to maize and cannot be claimed "
    "portable. Second, the audit inherits the guarantee of whichever construction it wraps; "
    "if it uses split conformal it inherits marginal coverage, and reporting a single "
    "per-country coverage figure without interval bounds would overstate precision [1], [3]. "
    "Third, the project's diagnosis depends on a covariate-space support check whose "
    "insufficiency it asserts; asserting it is weaker than measuring the relation between "
    "that check and observed coverage loss, which is what [10] and [7] together would allow. "
    "Fourth, the project reports no external validation: every number in it comes from one "
    "panel, so the claim that the auditor generalises is a design argument, not a result."
)
para(
    "The literature makes each weakness addressable rather than fatal. Blocking is standard "
    "[11]; coverage-gap bounds give the language for bounded claims [7]; label-shift "
    "reasoning gives a defensible diagnosis when covariates fail to explain the loss [9]; and "
    "the comparative framing in [12] gives a precedent for reporting inflation as a measured "
    "quantity rather than an assertion."
)

# --------------------------------------------------------------------- 5 ----
heading("5", "Proposed improvements and their feasibility")
para(
    "The survey supports four improvements, shown in Fig. 3 as an audit that reports its four "
    "steps together for one domain. Each is feasible with the corpus already reviewed, and "
    "each is scoped so that a negative result is still informative."
)
para(
    "Check the split before anything else. The auditor should report the inflation between "
    "random and blocked designs as its first output, because a model that fails here cannot "
    "be salvaged by any interval method [11], [12]. This is already implemented and produces "
    "the +0.088 and +2.208 figures quoted in Section 2."
)
para(
    "Separate skill from calibration. Report point transfer and per-country coverage as two "
    "numbers, with the coverage figure accompanied by an interval so that the reader can see "
    "how much evidence stands behind it [1], [3]. Reporting coverage alone invites the "
    "over-reading that a single number prevents."
)
para(
    "Diagnose which shift is responsible. Compare the covariate-space support verdict with the "
    "observed coverage loss; where the support check passes and coverage fails, the shift is "
    "in the outcome distribution and a level-adjusted calibration is indicated [9], [10]. This "
    "comparison is the project's sharpest claim because it tests the domain's standard practice "
    "rather than merely applying it."
)
para(
    "Prescribe and cost the remedy. For a level-adjusted recalibration, report the labels "
    "required in the target country and the interval width obtained at that budget [4], [9]. "
    "A remedy costing two thousand labels per country is not a remedy for an extension "
    "service, and stating the number converts a statistical correction into an operational "
    "choice. Feasibility here is bounded by the panel: a country with few rows can support the "
    "estimate but not a tight one, and the report must say so."
)
figure(FIG3, "Fig. 3. The audit the base project proposes, with the surveyed evidence behind "
             "each step. The addition is that the four steps are reported together, for one "
             "domain, with a cost.")

# --------------------------------------------------------------------- 6 ----
heading("6", "Conclusion and future work")
para(
    "The three strands surveyed here are individually mature and jointly incomplete. Interval "
    "construction is settled enough to apply routinely; evaluation design is known to inflate "
    "reported skill when structure is ignored; and transport is handled either by a "
    "covariate-space support check or by a reweighting scheme whose failure mode is known. "
    "What the corpus does not contain is an instrument that puts the three together for one "
    "domain, states which is failing, and costs the repair. That absence is the gap the base "
    "project addresses."
)
para(
    "Five directions follow, in order of tractability. First, measure the relation between a "
    "covariate-space support check and observed coverage loss, so that the diagnostic blind "
    "spot becomes a quantified statement rather than an assertion. Second, report coverage "
    "with interval bounds for every country, so that small-sample country results are read "
    "correctly. Third, establish the label budget curve — coverage restored against labels "
    "required — for level-adjusted recalibration on this panel. Fourth, extend the audit to a "
    "second crop or a second panel to test whether its thresholds are portable. Fifth, "
    "integrate the audit into a reporting artefact that a non-specialist can act on, since the "
    "value of a readiness verdict lies in its being read."
)
para(
    "Each direction is modest on its own. Together they convert a literature of separate "
    "guarantees into a single defensible statement about whether a yield-interval model may "
    "be deployed in a given region, which is the question the base project exists to answer."
)

# ---------------------------------------------------------------- refs ------
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.space_after = Pt(4)
run_in(p, "REFERENCES", size=10.5, small_caps=True)

refs = [
    "A. N. Angelopoulos and S. Bates, “Conformal prediction: a gentle introduction,” "
    "Foundations and Trends in Machine Learning, vol. 16, no. 4, pp. 494–591, 2023.",
    "V. Vovk, A. Gammerman and G. Shafer, Algorithmic Learning in a Random World. New York, "
    "NY, USA: Springer, 2005.",
    "J. Lei, M. G’Sell, A. Rinaldo, R. J. Tibshirani and L. Wasserman, “Distribution-free "
    "predictive inference for regression,” Journal of the American Statistical Association, "
    "vol. 113, no. 523, pp. 1094–1111, 2018.",
    "Y. Romano, E. Patterson and E. J. Candès, “Conformalized quantile regression,” in "
    "Advances in Neural Information Processing Systems, vol. 32, 2019, pp. 3543–3553.",
    "N. Meinshausen, “Quantile regression forests,” Journal of Machine Learning Research, "
    "vol. 7, pp. 983–999, 2006.",
    "L. Breiman, “Random forests,” Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.",
    "R. F. Barber, E. J. Candès, A. Ramdas and R. J. Tibshirani, “Conformal prediction beyond "
    "exchangeability,” The Annals of Statistics, vol. 51, no. 2, pp. 816–845, 2023.",
    "R. J. Tibshirani, R. F. Barber, E. J. Candès and A. Ramdas, “Conformal prediction under "
    "covariate shift,” in Advances in Neural Information Processing Systems, vol. 32, 2019, "
    "pp. 2530–2540.",
    "A. Podkopaev and A. Ramdas, “Tracking the risk of a deployed model and detecting harmful "
    "distribution shifts,” in Proc. 24th Int. Conf. Artificial Intelligence and Statistics "
    "(AISTATS), 2021, pp. 2140–2148.",
    "H. Meyer and E. Pebesma, “Predicting into unknown space? Estimating the area of "
    "applicability of spatial prediction models,” Methods in Ecology and Evolution, vol. 12, "
    "no. 9, pp. 1620–1633, 2021.",
    "D. R. Roberts et al., “Cross-validation strategies for data with temporal, spatial, "
    "hierarchical or phylogenetic structure,” Ecography, vol. 40, no. 8, pp. 913–929, 2017.",
    "P. Ploton et al., “Spatial validation reveals poor predictive performance of large-scale "
    "ecological mapping models,” Nature Communications, vol. 11, art. 4540, 2020.",
    "S. Kapoor and A. Narayanan, “Leakage and the reproducibility crisis in machine-learning-"
    "based science,” Patterns, vol. 4, no. 9, art. 100804, 2023.",
    "F. Aramburu Merlos, F. A. Tenorio, N. Mashingaidze, A. Sananka, S. Aston and P. Grassini, "
    "“Maize management and yield of smallholder farmers in Sub-Saharan Africa between 2016 and "
    "2022,” Zenodo, 2024, doi: 10.5281/zenodo.11122388.",
    "F. Aramburu-Merlos et al., “Adopting yield-improving practices to meet maize demand in "
    "Sub-Saharan Africa without cropland expansion,” Nature Communications, vol. 15, art. "
    "5598, 2024.",
]
for i, ref in enumerate(refs, start=1):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.85)
    p.paragraph_format.first_line_indent = Cm(-0.85)
    run_in(p, f"[{i}] {ref}", size=9.0)

doc.save(OUT)
print(f"wrote {OUT}")
