"""Build the survey paper (IEEE conventions, A4, single column).

Content is drawn only from the sources recorded in
Literature_review_AGROYIELD-ADAPT.xlsx, and the review protocol section states
plainly that screening is ongoing rather than inventing database counts.
"""

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = "FINISHED/Survey_Paper_v1.docx"

AUTHOR = "[Student name] [Registration number]"
SUPERVISOR = "[Supervisor name]"
TITLE = ("Uncertainty Quantification and Transfer Validation for Crop Yield "
         "Prediction: A Structured Review")

doc = Document()


def page_setup():
    for s in doc.sections:
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin = s.right_margin = Cm(2.54)
        s.top_margin = s.bottom_margin = Cm(2.54)


def base_style():
    n = doc.styles["Normal"]
    n.font.name = "Times New Roman"
    n.font.size = Pt(10.5)
    n.paragraph_format.line_spacing = 1.15
    n.paragraph_format.space_after = Pt(5)


def run_in(p, text, size=10.5, bold=False, italic=False):
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    r.bold, r.italic = bold, italic
    r.font.color.rgb = RGBColor(0, 0, 0)
    return r


def para(text, size=10.5, italic=False, bold=False, align=None, spacing=1.15,
         after=5, first_indent=0.0):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = spacing
    p.paragraph_format.space_after = Pt(after)
    if align is not None:
        p.alignment = align
    if first_indent:
        p.paragraph_format.first_line_indent = Cm(first_indent)
    run_in(p, text, size=size, italic=italic, bold=bold)
    return p


def heading(number, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run_in(p, f"{number}. {text.upper()}", size=10.5)
    for r in p.runs:
        r.font.small_caps = True
    return p


def subheading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run_in(p, text, size=10.5, italic=True)
    return p


def table_caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = True
    run_in(p, text, size=9.0)
    return p


def table(rows, widths, header=True):
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
            run_in(p, str(value), size=8.5, bold=(header and i == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_page_field():
    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), " PAGE ")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    footer._p.append(fld)


page_setup()
base_style()
add_page_field()

# ---------------------------------------------------------------- title block ---
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run_in(p, TITLE, size=16, bold=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
run_in(p, AUTHOR, size=11)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
run_in(p, "Department of Analytics and Informatics, Faculty of Computer Engineering "
          "Informatics and Communications", size=9.5, italic=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(10)
run_in(p, f"Supervisor: {SUPERVISOR}", size=9.5, italic=True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p.paragraph_format.space_after = Pt(4)
run_in(p, "Abstract—", size=9.5, bold=True)
run_in(p, "Models that predict crop yield are increasingly published with prediction "
          "intervals, and those intervals are increasingly used to support fertiliser, credit "
          "and insurance decisions. Three research strands bear on whether such an interval can "
          "be trusted in a new region: how the interval is constructed, how the evaluation is "
          "designed, and how the model is transported. Reviews normally treat these strands "
          "separately. This paper synthesises fifteen primary sources along those three axes and "
          "reports four findings. Interval construction is mature, with finite-sample guarantees "
          "available under stated assumptions. Evaluation design materially inflates reported "
          "skill when spatial or hierarchical structure is ignored, and that inflation is "
          "documented but seldom audited in agronomic studies. The standard pre-deployment "
          "support check reasons about covariates only and therefore cannot detect a shift in "
          "the outcome distribution. Finally, no source reports construction, evaluation and "
          "transport for one domain in one place, and none costs the remedy. The review "
          "concludes that the missing artefact is a joint audit that separates skill from "
          "calibration, diagnoses which shift is responsible, and states the label budget "
          "required to restore coverage. Five research gaps follow from the synthesis.",
       size=9.5)

p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(8)
run_in(p, "Keywords—", size=9.5, bold=True)
run_in(p, "conformal prediction; uncertainty quantification; crop yield; distribution shift; "
          "spatial cross-validation; data leakage", size=9.5, italic=True)

# --------------------------------------------------------------------- I -----
heading("I", "Introduction")
para(
    "Yield prediction models built on field-level survey data are now common in agronomic "
    "research, and they are increasingly reported with prediction intervals rather than point "
    "estimates alone. The reason is practical: an interval can be attached to a decision. A "
    "fertiliser recommendation, a credit limit or an insurance premium needs to know how "
    "uncertain a prediction is, not merely what the prediction is."
)
para(
    "An interval is useful only if it is valid where it is used. Validity here has a precise "
    "meaning: over repeated draws, the interval should contain the true value at the stated "
    "rate. Conformal prediction supplies that property under an assumption of exchangeability, "
    "and the framework has become the default way to attach a guarantee to an arbitrary point "
    "predictor [1], [2]. The guarantee, however, is marginal: it holds on average over the "
    "data used, not for each region or each subgroup, and it can fail when the target data are "
    "not exchangeable with the calibration data."
)
para(
    "That failure mode matters in agronomy because models are routinely fitted on a "
    "multi-country panel and then applied to one country. Three literatures touch this problem "
    "without meeting. The conformal literature studies how to construct intervals and what "
    "they guarantee [1]–[5]. The validation literature studies how evaluation design inflates "
    "reported skill when data are spatially or hierarchically structured [11]–[13]. The "
    "spatial-prediction literature studies whether a target location lies inside the "
    "predictor's support [10]. A practitioner holding a model therefore has three separate "
    "answers and no single verdict."
)
para(
    "This paper reviews those strands together. Its contribution is a synthesis organised by "
    "three questions: how intervals are constructed, how their validity is evaluated, and how "
    "they behave when transported. Section II states the review protocol. Sections III to V "
    "treat the three strands in turn. Section VI synthesises them in one table, Section VII "
    "states the research gaps that follow, and Section VIII concludes."
)

# -------------------------------------------------------------------- II -----
heading("II", "Review protocol")
subheading("A. Review questions")
para(
    "The review addresses three questions. RQ1: what guarantees do the main interval-"
    "construction methods provide, and under which assumptions? RQ2: how do evaluation designs "
    "affect reported predictive skill, and are interval studies designed to avoid that effect? "
    "RQ3: what evidence exists on the behaviour of intervals when a model is moved to a new "
    "region, and what remedies are proposed?"
)
subheading("B. Sources and search strategy")
para(
    "Searches cover Scopus, Web of Science, Google Scholar and arXiv, supplemented by the "
    "Zenodo record for the dataset used in the associated project. The search combines three "
    "term groups: interval and uncertainty terms (conformal prediction, quantile regression, "
    "prediction interval, coverage), crop terms (maize, yield, smallholder, agronomic), and "
    "transfer terms (distribution shift, covariate shift, applicability, spatial "
    "cross-validation, transferability). Reference lists of retained papers are screened for "
    "further sources."
)
subheading("C. Inclusion and exclusion")
para(
    "Studies are included when they propose or evaluate a method for predictive uncertainty, "
    "or quantify the effect of validation design on reported skill, or assess the "
    "transportability of a spatial prediction model. Studies are excluded when they report "
    "point accuracy only and make no claim about uncertainty or transport, when the outcome is "
    "not a continuous agronomic quantity, and when no method or evaluation is described. No "
    "date restriction is applied; the corpus spans 2001 to 2024."
)
subheading("D. Corpus status and data extraction")
para(
    "Fifteen sources are retained for synthesis at the time of writing, and they are the "
    "sources cited in this paper; screening against the protocol above is continuing and the "
    "final screening counts will be reported in the submitted version rather than estimated "
    "here. For each source the following are extracted: the method, the guarantee claimed, the "
    "assumption the guarantee rests on, the evaluation design used, whether any distribution "
    "shift is handled, and whether a remedy and its cost are stated. These six fields are what "
    "Table I reports."
)
subheading("E. Limitations of the review")
para(
    "The review is purposive rather than exhaustive at this stage, it covers one crop, and it "
    "relies on the assumptions stated by each source rather than re-deriving them. Where a "
    "source is known to exist but its bibliographic details could not be confirmed, it is not "
    "cited; the associated workbook records those separately. This is a deliberate choice: an "
    "unverified citation is worse than an absent one."
)

# ------------------------------------------------------------------- III -----
heading("III", "Constructing an interval")
para(
    "Two families dominate. The first estimates conditional quantiles directly, either by "
    "quantile regression forests, which read quantiles from the empirical distribution held in "
    "the leaves of an ensemble [5], so that the point predictor and the interval come from one "
    "model, or by conformalised quantile regression, which uses estimated quantiles as a "
    "conformity score and then calibrates the score on held-out data [4]. The second family "
    "wraps an arbitrary point predictor, such as a random forest [6]. Split conformal prediction "
    "fits the model on one part of the data, computes nonconformity scores on a second part, and "
    "takes a quantile of those "
    "scores as the interval half-width [3]. Its appeal is that the guarantee does not depend on "
    "the model being correct, only on the calibration and test data being exchangeable [1], "
    "[2]."
)
para(
    "The guarantee is the crux. Split conformal gives marginal coverage: averaged over the "
    "test distribution, the interval contains the truth at the nominal rate. It does not give "
    "coverage conditional on a region, a country or a covariate value, and the difference "
    "between those two statements is exactly the difference between a model that is valid on "
    "average across a seven-country panel and one that is valid in the country where it will be "
    "used. Group-conditional variants relax the assumption by calibrating within groups, at the "
    "cost of needing enough data in each group; the tutorial treatment in [1] is explicit that "
    "conditional coverage is hard in general."
)
para(
    "Under distribution shift the guarantee degrades, and the degradation is quantifiable: "
    "coverage-gap bounds are available once the shift is expressed through an appropriate "
    "measure [7]. That result is important for practice because it converts an assumed "
    "guarantee into a measurable quantity, which is the first step towards reporting a gap "
    "rather than asserting a property. What the literature does not supply is a routine way to "
    "compute that measure for an agronomic panel, which is why the applied studies in this "
    "corpus report nominal coverage and stop there."
)

# -------------------------------------------------------------------- IV -----
heading("IV", "Evaluating the interval: design and leakage")
para(
    "An interval is only as credible as the evaluation that produced it. When observations are "
    "spatially or hierarchically structured, random cross-validation places near-duplicate "
    "records in both training and test sets, and the model's apparent skill includes its "
    "ability to recognise those duplicates. The validation literature documents this for "
    "ecological and spatial data and prescribes blocked designs instead [11]. The effect is not "
    "small: a comparison of random and spatial validation on large-scale mapping models found "
    "that spatial validation revealed markedly poorer performance than random validation had "
    "suggested [12]."
)
para(
    "The same problem has a name and a taxonomy. Leakage is the use, during training or "
    "evaluation, of information that would not be available at prediction time; a survey across "
    "modelling fields catalogues the recurring forms, including duplicate records, temporal "
    "leakage and the reuse of test data for model selection [13]. This matters for interval "
    "work specifically, because the calibration set is part of the evaluation. If the "
    "calibration set shares clusters with the test set, the scores are computed on data the "
    "model has effectively seen, and the resulting interval is over-confident by construction — "
    "even when every individual step follows the conformal recipe correctly."
)
para(
    "The literature reviewed here is uneven on this point. Method papers are careful about "
    "exchangeability in principle [1], [3], [7] but do not audit the evaluation design of the "
    "applications they motivate; application papers report random or unspecified splits and "
    "treat the guarantee as inherited. No source in this corpus reports both a leakage-aware "
    "evaluation design and an interval-validity result for the same model, which is the "
    "observation that motivates gap G1 in Section VII."
)

# --------------------------------------------------------------------- V -----
heading("V", "Transport: applicability, shift and remedy")
para(
    "Three remedies appear in the corpus, and they answer different questions. The first asks "
    "whether the target is inside the predictor's support. The dissimilarity index computes a "
    "scaled distance in predictor space from each target location to the training data and "
    "flags those beyond a threshold, giving an area of applicability [10]. In agronomic "
    "practice this is the standard pre-deployment check, and the source publication of the "
    "public field-level panel used in the associated project applies a check of this kind on "
    "that panel [14], [15]. Its limitation is "
    "structural: it measures the covariates only. A target region can sit comfortably inside "
    "the covariate support and still have a different yield distribution, because management, "
    "market access or measurement practice differ."
)
para(
    "The second remedy reweights the calibration set towards the target distribution. Under "
    "covariate shift, weighting the conformity scores by an estimated likelihood ratio restores "
    "validity [8]. The method is principled and its failure mode is well understood: the "
    "weights concentrate on few calibration points, the effective sample size falls, and the "
    "resulting interval becomes unstable. This is not a hypothetical concern in a "
    "seven-country panel, where one country can be an outlier in several covariates at once."
)
para(
    "The third remedy assumes the shift is in the outcome distribution rather than the "
    "covariates, and adapts the threshold accordingly. Methods for tracking a deployed model's "
    "risk under label shift establish the principle that the score distribution, not only the "
    "covariate distribution, carries the information needed to correct coverage [9]. Applied to "
    "yield, this suggests that a small labelled sample from the target region, used to estimate "
    "the level offset, may be more informative than a large unlabelled sample and a covariate "
    "diagnostic. The corpus does not test that proposition, and it does not quantify how many "
    "labels such a correction needs — the quantity a deployment decision actually depends on."
)

# -------------------------------------------------------------------- VI -----
heading("VI", "Synthesis")
table_caption("Table I. What each family of methods guarantees, what it assumes, and what it "
              "leaves untested")
table([
    ["Family", "Guarantee claimed", "Assumption", "Not addressed"],
    ["Split conformal [1], [3]", "Marginal coverage at nominal rate",
     "Exchangeability of calibration and test data", "Conditional coverage by region; shift"],
    ["Group-conditional [1]", "Coverage within each group",
     "Enough data per group; group known at test time", "Cost of labels per group"],
    ["Weighted conformal [8]", "Coverage under covariate shift",
     "Accurate density ratio; overlap", "Weight collapse; effective sample size"],
    ["Quantile-based [4], [5]", "Adaptive interval width",
     "Model estimates quantiles well; exchangeability", "Finite-sample validity off-exchangeability"],
    ["Label-shift adaptation [9]", "Risk control under outcome shift",
     "Access to a labelled target sample", "Label budget; regression intervals"],
    ["Applicability index [10]", "Flags unsupported locations",
     "Covariates carry the relevant shift", "Any outcome-level shift"],
    ["Blocked validation [11], [12]", "Honest estimate of skill",
     "Blocks match the deployment structure", "Interval validity; the remedy"],
    ["Leakage taxonomy [13]", "Diagnosis of inflation",
     "The reviewer knows the pipeline", "Executable audit of a given model"],
], widths=[4.0, 4.4, 4.2, 3.3])
para(
    "Read across Table I, the pattern is not a gap in any single row but a gap between rows. "
    "Each family answers its own question correctly. None of them reports, for one domain, "
    "both the honest point skill and the interval validity, and none states what it would cost "
    "to repair the interval. The practitioner's question — is this model safe here, and what "
    "would make it safe — falls between the columns."
)

# ------------------------------------------------------------------- VII -----
heading("VII", "Research gaps")
para("Five gaps follow directly from the synthesis.", first_indent=0.0)
table_caption("Table II. Gaps, the evidence that they exist, and the evidence that would close "
              "them")
table([
    ["Gap", "Why it exists", "Evidence that would close it"],
    ["G1 No joint audit of skill and calibration",
     "Method papers assume a design; application papers assume a guarantee [1], [13]",
     "One report per domain giving point skill, coverage and the design that produced them"],
    ["G2 Support checks are blind to outcome shift",
     "The index is computed in covariate space [10]",
     "A measured relation between a covariate diagnostic and observed coverage loss"],
    ["G3 Remedy cost is unquantified",
     "Remedies are proposed without a label budget [8], [9]",
     "Coverage restored against labels required, per domain"],
    ["G4 Agronomic panels are untested for transport",
     "Yield studies report point accuracy; the panel's own source does not report intervals [14], [15]",
     "Cross-country interval results on a public field-level panel"],
    ["G5 Leakage rarely audited in interval studies",
     "Calibration is treated as part of the method, not the evaluation [13]",
     "Interval results reported under blocked and unblocked designs for the same model"],
], widths=[4.4, 5.9, 5.6])
para(
    "Gap G3 deserves emphasis because it is the one a deployment decision turns on. A remedy "
    "that restores coverage by demanding two thousand labelled observations in every target "
    "region is not a remedy for a smallholder extension service. Stating the budget turns a "
    "statistical correction into an operational choice, and no source in this corpus states it."
)

# ------------------------------------------------------------------ VIII -----
heading("VIII", "Conclusion")
para(
    "The three strands reviewed here are individually mature and jointly incomplete. Interval "
    "construction is settled enough to be applied routinely; evaluation design is known to "
    "inflate reported skill when structure is ignored; and transport is handled either by a "
    "covariate-space support check or by a reweighting scheme whose failure mode is known. What "
    "does not exist in the corpus is an instrument that puts the three together for one domain, "
    "states which of them is failing, and costs the repair. That absence is the gap this "
    "review identifies, and it is the gap the associated capstone project addresses by building "
    "and evaluating a deployment-readiness auditor for smallholder maize yield models."
)

# ---------------------------------------------------------------- references ---
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.LEFT
p.paragraph_format.space_before = Pt(10)
p.paragraph_format.space_after = Pt(4)
run_in(p, "REFERENCES", size=10.5)

refs = [
    "A. N. Angelopoulos and S. Bates, “Conformal prediction: a gentle introduction,” "
    "Foundations and Trends in Machine Learning, vol. 16, no. 4, pp. 494–591, 2023.",
    "V. Vovk, A. Gammerman and G. Shafer, Algorithmic Learning in a Random World. New York: "
    "Springer, 2005.",
    "J. Lei, M. G’Sell, A. Rinaldo, R. J. Tibshirani and L. Wasserman, “Distribution-free "
    "predictive inference for regression,” Journal of the American Statistical Association, "
    "vol. 113, no. 523, pp. 1094–1111, 2018.",
    "Y. Romano, E. Patterson and E. J. Candès, “Conformalized quantile regression,” in Advances "
    "in Neural Information Processing Systems, vol. 32, 2019.",
    "N. Meinshausen, “Quantile regression forests,” Journal of Machine Learning Research, "
    "vol. 7, pp. 983–999, 2006.",
    "L. Breiman, “Random forests,” Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.",
    "R. F. Barber, E. J. Candès, A. Ramdas and R. J. Tibshirani, “Conformal prediction beyond "
    "exchangeability,” The Annals of Statistics, vol. 51, no. 2, 2023.",
    "R. J. Tibshirani, R. F. Barber, E. J. Candès and A. Ramdas, “Conformal prediction under "
    "covariate shift,” in Advances in Neural Information Processing Systems, vol. 32, 2019.",
    "A. Podkopaev and A. Ramdas, “Tracking the risk of a deployed model and detecting harmful "
    "distribution shifts,” in Proc. 24th Int. Conf. Artificial Intelligence and Statistics "
    "(AISTATS), 2021.",
    "H. Meyer and E. Pebesma, “Predicting into unknown space? Estimating the area of "
    "applicability of spatial prediction models,” Methods in Ecology and Evolution, vol. 12, "
    "no. 9, pp. 1620–1633, 2021.",
    "D. R. Roberts et al., “Cross-validation strategies for data with temporal, spatial, "
    "hierarchical or phylogenetic structure,” Ecography, vol. 40, no. 8, pp. 913–929, 2017.",
    "P. Ploton et al., “Spatial validation reveals poor predictive performance of large-scale "
    "ecological mapping models,” Nature Communications, vol. 11, 2020.",
    "S. Kapoor and A. Narayanan, “Leakage and the reproducibility crisis in machine-learning-"
    "based science,” Patterns, vol. 4, no. 9, 2023.",
    "F. Aramburu Merlos, F. A. Tenorio, N. Mashingaidze, A. Sananka, S. Aston and P. Grassini, "
    "“Maize management and yield of smallholder farmers in Sub-Saharan Africa between 2016 and "
    "2022,” Zenodo, 2024, doi: 10.5281/zenodo.11122388.",
    "F. Aramburu-Merlos et al., “Adopting yield-improving practices to meet maize demand in "
    "Sub-Saharan Africa without cropland expansion,” Nature Communications, vol. 15, 2024.",
]
for i, ref in enumerate(refs, start=1):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.9)
    p.paragraph_format.first_line_indent = Cm(-0.9)
    run_in(p, f"[{i}] {ref}", size=9.0)

doc.save(OUT)
print(f"wrote {OUT}")
