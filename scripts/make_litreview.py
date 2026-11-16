"""Fill the DAI literature-review workbook for this project.

Keeps the template's seven columns (Authors, Year, Journal/Conference, Title,
Methodology, Remark, Research Gap) and replaces the sample rows - which were
about security-requirement classification, not maize - with sources that this
project actually relies on.

Only entries whose bibliographic details are verifiable are included; the
2026 preprints still to be confirmed are listed on a second sheet rather than
given invented authors.
"""

from __future__ import annotations

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

OUT = "Literature_review_AGROYIELD-ADAPT.xlsx"

TITLE = ("AGROYIELD-ADAPT: A DEPLOYMENT-READINESS AUDITOR FOR SMALLHOLDER "
         "MAIZE YIELD-INTERVAL MODELS")

HEADERS = ["Authors", "Year", "Journal/Conference", "Title", "Methodology",
           "Remark", "Research Gap"]

ROWS = [
    ["Breiman, L.", 2001, "Machine Learning, 45(1), 5-32",
     "Random forests",
     "Ensembles of decision trees with bootstrap aggregation and random feature "
     "subsetting; regression by averaging.",
     "The workhorse regressor used throughout this project as the point predictor.",
     "Produces point predictions only; no predictive interval and no coverage guarantee."],

    ["Meinshausen, N.", 2006, "Journal of Machine Learning Research, 7, 983-999",
     "Quantile regression forests",
     "Stores the full conditional distribution of tree leaves and reads off "
     "conditional quantiles from forest weights.",
     "Conditional quantile alternative to conformal intervals; used as a baseline.",
     "Estimated quantiles are not finite-sample valid and carry no coverage guarantee."],

    ["Vovk, V., Gammerman, A. and Shafer, G.", 2005, "Springer (book)",
     "Algorithmic learning in a random world",
     "Develops conformal prediction as an online learning framework with "
     "exchangeability-based validity.",
     "Founding statement of marginal coverage under exchangeability.",
     "No treatment of spatially clustered or cross-country data; no notion of a "
     "target-domain label budget."],

    ["Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J. and Wasserman, L.", 2018,
     "Journal of the American Statistical Association, 113(523), 1094-1111",
     "Distribution-free predictive inference for regression",
     "Split conformal plus locally weighted and jackknife+ variants for "
     "regression with finite-sample guarantees.",
     "Supplies the split-conformal machinery and the local-weighting idea behind "
     "per-domain recalibration.",
     "Coverage is marginal, not conditional on region or country; shift is not "
     "diagnosed."],

    ["Tibshirani, R. J., Barber, R. F., Candes, E. J. and Ramdas, A.", 2019,
     "Advances in Neural Information Processing Systems, 32",
     "Conformal prediction under covariate shift",
     "Reweights calibration scores by an estimated likelihood ratio between "
     "target and calibration covariates.",
     "The label-free remedy evaluated and rejected in this project (effective "
     "sample size collapsed to 0.09-0.17).",
     "Requires an accurate density ratio and a support overlap that smallholder "
     "panels do not provide across countries."],

    ["Romano, Y., Patterson, E. and Candes, E. J.", 2019,
     "Advances in Neural Information Processing Systems, 32",
     "Conformalized quantile regression",
     "Uses conditional quantile estimates as the conformity score to obtain "
     "adaptive-width intervals.",
     "Shows how interval width can adapt to difficulty; relevant to the width-cost "
     "reporting this project requires.",
     "Still assumes exchangeability and is not tested across national domains in "
     "agronomy."],

    ["Angelopoulos, A. N. and Bates, S.", 2023,
     "Foundations and Trends in Machine Learning, 16(4), 494-591",
     "Conformal prediction: a gentle introduction",
     "Tutorial and synthesis of split, full and Mondrian conformal prediction with "
     "practical recipes.",
     "Source for the pooled and Mondrian baselines implemented in the auditor.",
     "States that conditional coverage is hard and offers no transfer protocol for "
     "panel data or any warning instrument."],

    ["Barber, R. F., Candes, E. J., Ramdas, A. and Tibshirani, R. J.", 2023,
     "The Annals of Statistics, 51(2)",
     "Conformal prediction beyond exchangeability",
     "Derives coverage-gap bounds that hold under distribution drift rather than "
     "assuming exchangeability.",
     "Theoretical basis for reporting a measured coverage gap instead of an "
     "assumed guarantee.",
     "The bound is expressed through a shift measure that no agronomic study "
     "computes; not operationalised as a tool."],

    ["Podkopaev, A. and Ramdas, A.", 2021,
     "Proceedings of the 24th International Conference on Artificial Intelligence "
     "and Statistics (AISTATS)",
     "Tracking the risk of a deployed model and detecting harmful distribution shifts",
     "Monitors deployed-model risk under label shift and triggers adaptation when "
     "the shift is detected.",
     "Antecedent for the level-adjusted (label-shift) recalibration this project "
     "implements.",
     "Focuses on monitoring a deployed classifier; does not cost the labels needed "
     "or address regression intervals over yield."],

    ["Meyer, H. and Pebesma, E.", 2021,
     "Methods in Ecology and Evolution, 12(9), 1620-1633",
     "Predicting into unknown space? Estimating the area of applicability of "
     "spatial prediction models",
     "Computes a dissimilarity index from scaled predictor-space distance to the "
     "training data and flags out-of-area predictions.",
     "The incumbent pre-deployment check; this project measures its correlation "
     "with actual coverage loss (rho = 0.00).",
     "Reasons about covariates only, so it is structurally blind to a shift in the "
     "outcome distribution."],

    ["Roberts, D. R. et al.", 2017, "Ecography, 40(8), 913-929",
     "Cross-validation strategies for data with temporal, spatial, hierarchical or "
     "phylogenetic structure",
     "Compares random, spatial, temporal and hierarchical cross-validation designs "
     "on structured ecological data.",
     "Justifies the cluster-grouped validation design used in Module 1.",
     "Ecological focus, point accuracy only; no interval audit and no prescription."],

    ["Ploton, P. et al.", 2020, "Nature Communications, 11",
     "Spatial validation reveals poor predictive performance of large-scale "
     "ecological mapping models",
     "Contrasts random and spatial cross-validation on large-scale mapping models.",
     "Independent evidence that random validation inflates reported skill, which "
     "Module 1 reproduces on the maize panel.",
     "Does not examine interval coverage, nor offer a repair or its cost."],

    ["Kapoor, S. and Narayanan, A.", 2023, "Patterns, 4(9)",
     "Leakage and the reproducibility crisis in machine-learning-based science",
     "Taxonomy of data leakage across modelling fields, with a survey of affected "
     "published results.",
     "Provides the vocabulary and the leakage typology used by the split-integrity "
     "module.",
     "Descriptive; no executable check that a given model or pipeline is leaking."],

    ["Aramburu Merlos, F., Tenorio, F. A., Mashingaidze, N., Sananka, A., Aston, S. "
     "and Grassini, P.", 2024, "Zenodo, doi:10.5281/zenodo.11122388 (CC BY 4.0)",
     "Maize management and yield of smallholder farmers in Sub-Saharan Africa "
     "between 2016 and 2022",
     "Field-level survey of 14,773 maize records across seven countries, with "
     "coordinates, management and biophysical covariates.",
     "The dataset this project audits; fingerprinted by SHA-256 and used unchanged.",
     "Published as a data resource with no analysis of predictive uncertainty or "
     "interval validity."],

    ["Aramburu-Merlos, F. et al.", 2024, "Nature Communications, 15",
     "Adopting yield-improving practices to meet maize demand in Sub-Saharan Africa "
     "without cropland expansion",
     "Random-forest analysis of management versus environment effects on yield, "
     "with a CAST applicability assessment.",
     "The source publication of the panel; establishes the agronomic framing and "
     "the applicability practice this project tests.",
     "Reports point predictions and a support check, but no intervals, no calibration "
     "audit and no transfer cost."],
]

PENDING = [
    ["DriftGuard (preprint)", 2026, "arXiv preprint, August 2026",
     "Label-free drift audit with prospective label-budget design",
     "Two-stage audit: label-free stage plus a labelled stage using a probability "
     "sample of target labels.",
     "Closest prior art to Modules 3-4; must be cited as the generic ancestor and "
     "distinguished from the agronomic instantiation.",
     "Not applied to agronomic panels; does not separate point skill from interval "
     "validity."],
    ["Uganda ZARDI study", 2026, "Journal article (metadata to confirm)",
     "Pooled conformal yield intervals for Ugandan maize",
     "Pooled split-conformal intervals evaluated within one country.",
     "Single-country precedent for conformal yield intervals; shows pooled "
     "calibration works in-domain.",
     "No cross-country transport, no diagnosis, no remedy costing."],
    ["Frontiers in Plant Science", 2026, "Frontiers in Plant Science (metadata to confirm)",
     "Conformal profit bounds with abstention for nitrogen recommendation",
     "Risk-controlled interval estimates used to support or abstain from an N "
     "recommendation.",
     "Demonstrates the decision value of calibrated intervals in agronomy.",
     "Single setting; does not test transport or prescribe a label budget."],
    ["SSRN working paper", 2026, "SSRN (metadata to confirm)",
     "Dissimilarity-index-conditioned conformal prediction",
     "Conditions conformal calibration on the applicability index.",
     "Directly overlaps Module 3; must be cited and differentiated.",
     "Conditions on covariates only, so cannot detect an outcome-level shift."],
    ["COPA 2025", 2025, "Proceedings of COPA (metadata to confirm)",
     "Empirical assessment of importance weighting for conformal prediction",
     "Benchmarks weighted conformal under estimated density ratios.",
     "Supports this project's negative result on label-free weighting.",
     "General benchmark; no agronomic or cross-country application."],
]


def build():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Literature Review"

    ws["A1"] = TITLE
    ws["A1"].font = Font(bold=True, size=12)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(HEADERS))

    for col, header in enumerate(HEADERS, start=1):
        c = ws.cell(row=2, column=col, value=header)
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DCE6F2")
        c.alignment = Alignment(vertical="top", wrap_text=True)

    for r, row in enumerate(ROWS, start=3):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=value)
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    widths = [34, 7, 30, 44, 44, 44, 44]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A3"

    ws2 = wb.create_sheet("To verify before submission")
    ws2["A1"] = ("These sources are known to exist and are relied on in the text, but their "
                 "authors and DOIs must be confirmed from the publisher record before the "
                 "survey paper is submitted. They are listed here rather than given invented "
                 "metadata.")
    ws2["A1"].alignment = Alignment(wrap_text=True, vertical="top")
    ws2.merge_cells("A1:G1")
    for col, header in enumerate(HEADERS, start=1):
        c = ws2.cell(row=2, column=col, value=header)
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="F2DCDB")
        c.alignment = Alignment(vertical="top", wrap_text=True)
    for r, row in enumerate(PENDING, start=3):
        for c, value in enumerate(row, start=1):
            cell = ws2.cell(row=r, column=c, value=value)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    for i, w in enumerate(widths, start=1):
        ws2.column_dimensions[get_column_letter(i)].width = w
    ws2.freeze_panes = "A3"

    wb.save(OUT)
    print(f"wrote {OUT}: {len(ROWS)} verified sources, {len(PENDING)} to verify")


if __name__ == "__main__":
    build()
