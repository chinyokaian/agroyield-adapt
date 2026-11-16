"""Build the finalised proposal document for the AGROYIELD-ADAPT capstone.

Every quantitative statement here is taken from a run recorded in this
repository (results/split_audit.json, diag_label_free.csv, pilot_onboard_results.csv).
Statements that are not yet reproduced under the auditor's own preprocessing are
marked preliminary in the text itself.
"""

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, Cm

OUT = "FINISHED/Proposal_AGROYIELD-ADAPT_v2.docx"

doc = Document()

# --- page and base style: TNR 12, 1.5 spacing (UZ-DAI formatting rules) -------
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.54)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(6)


def h(text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.name = "Times New Roman"
    return p


def para(text, bold=False, style=None):
    p = doc.add_paragraph(style=style)
    run = p.add_run(text)
    run.bold = bold
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)
    p.paragraph_format.line_spacing = 1.5
    return p


def bullet(text):
    return para(text, style="List Bullet")


def table(rows, widths=None):
    t = doc.add_table(rows=0, cols=len(rows[0]))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = ""
            if widths:
                cells[i].width = Cm(widths[i])
            p = cells[i].paragraphs[0]
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(str(v))
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
    doc.add_paragraph()


# --- title block -------------------------------------------------------------
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("AGROYIELD-ADAPT: A DEPLOYMENT-READINESS AUDITOR FOR\n"
              "SMALLHOLDER MAIZE YIELD-INTERVAL MODELS")
r.bold = True
r.font.size = Pt(16)
r.font.name = "Times New Roman"

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = sub.add_run("Capstone Project Proposal (v2)")
rs.italic = True
rs.font.size = Pt(13)
rs.font.name = "Times New Roman"

table([
    ["Candidate", "[Your full name and student number]"],
    ["Programme", "BSc Data Science and Informatics"],
    ["Department", "Analytics and Informatics, Faculty of Engineering, Informatics and Communications"],
    ["Supervisor", "[Supervisor name]"],
    ["Date", "November 2026"],
    ["Status", "Final draft for supervisor sign-off; supersedes proposal v1"],
], widths=[4.2, 11.2])

# --- 1 -----------------------------------------------------------------------
h("1. Problem statement", 1)
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

# --- 2 -----------------------------------------------------------------------
h("2. Aim and objectives", 1)
para("Aim: to develop and reproducibly evaluate a deployment-readiness auditor that diagnoses "
     "split inflation and interval miscalibration in maize yield models, and prescribes a "
     "calibration remedy with its label and interval-width cost.", bold=True)
para("Objectives:", bold=True)
bullet("O1. Establish how much reported skill is an artefact of validation design for a "
       "multinational smallholder maize panel, using random, spatially clustered and "
       "leave-one-country-out validation with identical features and model.")
bullet("O2. Separate model skill from interval validity: report point-transfer accuracy and "
       "empirical coverage per domain as independent verdicts.")
bullet("O3. Identify which measurable properties of a target domain predict coverage loss, and "
       "test whether the field's standard applicability diagnostic detects it.")
bullet("O4. Implement a level-adjusted calibration procedure with a label-budget rule, and "
       "evaluate it against pooled, per-domain and label-free weighting baselines.")
bullet("O5. Deliver the auditor as documented, tested software with a reproducibility record, "
       "and evaluate its warning behaviour.")

# --- 3 -----------------------------------------------------------------------
h("3. Research questions and hypotheses", 1)
para("RQ1. How large is the inflation in reported predictive skill when spatial and national "
     "structure are respected?")
para("RQ2. Do intervals calibrated on a multi-country pool retain nominal coverage in a held-out "
     "country, and does point-model skill predict whether they will?")
para("RQ3. Is coverage loss predictable from observable properties of the target domain, and "
     "does the dissimilarity-index applicability check detect it?")
para("RQ4. What label budget and interval-width cost does restoring coverage require?")
para("Four pre-declared hypotheses follow, each falsifiable and each reported whichever way it "
     "falls: H1 inflation exceeds 0.05 R-squared on the clustered design; H2 pooled calibration "
     "does not reach nominal coverage in at least one domain and coverage is not monotone in "
     "point-model skill; H3 coverage loss is associated with the target domain's yield level "
     "rather than with covariate-space dissimilarity alone; H4 local recalibration restores "
     "coverage at no more than a stated width penalty.")

# --- 4 -----------------------------------------------------------------------
h("4. Scope and delimitation", 1)
para("In scope: a Python command-line auditor with five modules (split integrity, skill and "
     "calibration separation, transport diagnosis, level-adjusted recalibration, report "
     "generation), evaluated on one public panel.")
para("Out of scope, and not claimed: a new theory of conformal prediction; live data ingestion; a "
     "mobile application; a commercial backend; causal effects of changing agronomic practice; "
     "farmer income or insurance outcomes; national representativeness; and validity for "
     "Zimbabwe, which the dataset does not cover. The contribution is an instrument plus measured "
     "evidence, not a new algorithm.")

# --- 5 -----------------------------------------------------------------------
h("5. Data", 1)
para("The study uses the One Acre Fund smallholder maize panel (Aramburu Merlos et al., 2024), "
     "deposited on Zenodo (doi:10.5281/zenodo.11122388) under CC BY 4.0 and used in the "
     "dataset's own source publication (Aramburu-Merlos et al., 2024). The local copy has been "
     "audited and fingerprinted: 14,773 field-season records, 53 columns, seven countries "
     "(Kenya 7,258; Tanzania 3,710; Rwanda 2,080; Zambia 861; Burundi 640; Nigeria 115; "
     "Uganda 109), survey years 2016–2020 and 2022, 263 zero-yield records (1.78%), 1,526 "
     "spatial-temporal clusters at 0.1 degree plus year, and 4,764 records (32.2%) sharing a "
     "cluster with another record. Soil covariates are missing for 78.4% of Burundi records and "
     "76.3% of Rwandan records, a limitation carried forward to the analysis.")
hash_p = doc.add_paragraph()
hash_p.paragraph_format.line_spacing = 1.5
hash_run = hash_p.add_run("SHA-256 of the analysed file: ")
hash_run.font.name = "Times New Roman"
hash_run.font.size = Pt(12)
hash_val = hash_p.add_run("f305a3d3e48015bd877dc9df5c53b1715c61f940d58383d57d4dfb68c59c6ff0")
hash_val.font.name = "Consolas"
hash_val.font.size = Pt(9.5)

# --- 6 -----------------------------------------------------------------------
h("6. Method", 1)
para("The artefact is developed as five modules, each independently testable:", bold=True)
bullet("M1 Split integrity. Fits one model under random, cluster-grouped and "
       "leave-one-country-out validation and reports the resulting inflation.")
bullet("M2 Skill and calibration separation. Reports point-transfer accuracy and empirical "
       "interval coverage per domain as separate verdicts.")
bullet("M3 Transport diagnosis. Computes dissimilarity index and out-of-area share, "
       "prediction-distribution distance, effective sample size of density-ratio weights, and the "
       "target domain's yield-level offset, then issues a pass/warn/fail flag.")
bullet("M4 Level-adjusted recalibration. Corrects the score quantile for the target domain's "
       "level offset from a small labelled sample and reports the label budget required.")
bullet("M5 Report generation. Produces a machine-readable and human-readable readiness report.")
para("Evaluation uses three validation designs, three seeds and a second model family; the "
     "auditor's own warning behaviour is assessed against observed coverage loss, so the tool is "
     "evaluated as software as well as used as an instrument. All preprocessing is fold-internal, "
     "and every run is recorded with seeds, fold assignments and a data fingerprint.")

# --- 7 -----------------------------------------------------------------------
h("7. Results to date and verification status", 1)
para("Module 1 is implemented, unit-tested and run on the full panel. The table reports the same "
     "random forest and features under three validation designs.", bold=False)
table([
    ["Validation design", "Folds", "R-squared (log yield)", "RMSE (kg/ha)"],
    ["Random 5-fold", "5", "+0.265", "1,486"],
    ["Cluster-grouped 5-fold (0.1 deg + year)", "5", "+0.177", "1,578"],
    ["Leave-one-country-out", "7", "-1.943", "2,284"],
], widths=[6.6, 1.6, 4.2, 3.0])
para("Inflation relative to the random design is +0.088 R-squared when cluster structure is "
     "ignored and +2.208 when national structure is ignored. An earlier run that imputed missing "
     "values once, globally, before splitting produced -0.925 for the cross-country design; "
     "imputing inside each fold moves it to -1.943. The earlier figure was therefore optimistic, "
     "because global imputation uses test-set statistics.")
para("Preliminary work from the development pilot, not yet recomputed under the auditor's "
     "preprocessing, suggests the calibration picture: pooled calibration at nominal 0.90 gives "
     "empirical coverage between 0.574 and 1.000 across the seven countries; per-domain "
     "calibration gives 0.852 to 0.930 at a median width of 0.95 times pooled; label-free "
     "density-ratio weighting does not improve on pooled calibration and retains an effective "
     "sample size of only 0.09 to 0.17. Across the seven domains the signed coverage error is "
     "monotone in the domain's median yield (Spearman rho = +0.96, n = 7) and uncorrelated with "
     "the dissimilarity index (rho = 0.00). With seven domains this is suggestive, not "
     "conclusive; replicating it at stratum level is an objective of this project, and it is "
     "reported as a hypothesis under test, not as a finding.")

# --- 8 -----------------------------------------------------------------------
h("8. Deliverables", 1)
table([
    ["Deliverable", "Guideline basis", "Review"],
    ["This proposal, finalised", "Project proposal", "Review 1"],
    ["Development and test environment specification", "Review 1 objective: tools, environment, test procedures", "Review 1"],
    ["First draft of test procedures", "Review 1 objective", "Review 1"],
    ["Initial UML analysis of the formulated solution", "Review 1 objective", "Review 1"],
    ["Final design: algorithm, UML set, database and interface design", "Review 2 objective", "Review 2"],
    ["Implemented and evaluated auditor (M1-M5), with test suite", "Prototype development and evaluation", "Review 3"],
    ["Project demonstration with before/after readiness report", "Final oral presentation", "Review 4"],
    ["Final report, 45–60 pages, Harvard referencing", "Report format rules", "Final"],
    ["Appendix A: source code repository; Appendix B: user manual", "Report appendices", "Final"],
    ["Systematic review and survey paper; technical paper", "Literature and presentation criteria", "Final"],
], widths=[6.4, 6.0, 3.0])

# --- 9 -----------------------------------------------------------------------
h("9. Ethics, data governance and reproducibility", 1)
para("The analysis uses an already-published, fully anonymised dataset under CC BY 4.0; no new "
     "field data and no personal data are collected. A short structured walkthrough with three to "
     "five professional users will be conducted to evaluate the report as a decision aid; it "
     "collects no personal data, uses a one-page information sheet and consent note, and requires "
     "supervisor approval before it begins. Code, seeds, fold assignments and result files are "
     "versioned in a public repository; the data file is fingerprinted by checksum.")

# --- 10 ----------------------------------------------------------------------
h("10. Risks and mitigation", 1)
table([
    ["Risk", "Mitigation"],
    ["Reframing not accepted by supervisor", "Proposal v2 is submitted for sign-off before any further build; Module 1 is independent of the framing"],
    ["Seven country domains give low statistical power", "Replicate at stratum level (25 strata) and across seeds; report effect sizes with uncertainty, and never treat fold-seeds as independent"],
    ["Auditor judged not to be a prototype", "Ship command-line tool, interface, report, user manual and test suite; seek written confirmation at Review 1"],
    ["Soil missingness confounds the diagnosis", "Optional iSDAsoil covariate layer; otherwise report the confound explicitly as a limitation"],
    ["Scope creep beyond a 45–60 page report", "Five fixed modules; no live service, no accounts, no mobile client"],
], widths=[5.0, 10.4])

# --- 11 ----------------------------------------------------------------------
h("11. Timeline", 1)
table([
    ["Period", "Work"],
    ["By Review 1 (1–4 December 2026)", "Proposal v2, environment specification, test procedures draft, initial UML, Module 1 running"],
    ["December 2026 – January 2027", "Modules 2 and 3, systematic review, survey paper"],
    ["February 2027", "Module 4 and label-budget evaluation; robustness runs"],
    ["March 2027", "Report drafting, technical paper, user manual, demonstration preparation"],
], widths=[4.4, 11.0])

# --- references --------------------------------------------------------------
h("References", 1)
refs = [
    "Angelopoulos, A. N. and Bates, S. (2023) 'Conformal prediction: a gentle introduction', "
    "Foundations and Trends in Machine Learning, 16(4), pp. 494-591.",
    "Aramburu Merlos, F., Tenorio, F. A., Mashingaidze, N., Sananka, A., Aston, S. and Grassini, P. "
    "(2024) Maize management and yield of smallholder farmers in Sub-Saharan Africa between 2016 "
    "and 2022. Zenodo. doi:10.5281/zenodo.11122388.",
    "Aramburu-Merlos, F., Tenorio, F. A. M., Mashingaidze, N., Sananka, A., Aston, S., Ojeda, J. J. "
    "and Grassini, P. (2024) 'Adopting yield-improving practices to meet maize demand in "
    "Sub-Saharan Africa without cropland expansion', Nature Communications, 15. "
    "doi:10.1038/s41467-024-48859-0.",
    "Barber, R. F., Candes, E. J., Ramdas, A. and Tibshirani, R. J. (2023) 'Conformal prediction "
    "beyond exchangeability', The Annals of Statistics, 51(2).",
    "Kapoor, S. and Narayanan, A. (2023) 'Leakage and the reproducibility crisis in "
    "machine-learning-based science', Patterns, 4(9).",
    "Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J. and Wasserman, L. (2018) "
    "'Distribution-free predictive inference for regression', Journal of the American "
    "Statistical Association, 113(523), pp. 1094-1111.",
    "Meyer, H. and Pebesma, E. (2021) 'Predicting into unknown space? Estimating the area of "
    "applicability of spatial prediction models', Methods in Ecology and Evolution, 12(9), "
    "pp. 1620-1633.",
    "Podkopaev, A. and Ramdas, A. (2021) 'Tracking the risk of a deployed model and detecting "
    "harmful distribution shifts', Proceedings of the 24th International Conference on Artificial "
    "Intelligence and Statistics.",
    "Tibshirani, R. J., Barber, R. F., Candes, E. J. and Ramdas, A. (2019) 'Conformal prediction "
    "under covariate shift', Advances in Neural Information Processing Systems, 32.",
    "Vovk, V., Gammerman, A. and Shafer, G. (2005) Algorithmic Learning in a Random World. "
    "New York: Springer.",
]
for ref in refs:
    p = doc.add_paragraph(ref)
    p.paragraph_format.first_line_indent = Cm(-1.0)
    p.paragraph_format.left_indent = Cm(1.0)
    p.paragraph_format.line_spacing = 1.5
    for run in p.runs:
        run.font.size = Pt(11)

doc.save(OUT)
print(f"wrote {OUT}")
