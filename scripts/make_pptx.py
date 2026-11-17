"""Build the two Review presentations from the DAI PowerPoint template.

The template's own slides, layouts and theme are reused, so the deck keeps the
department's formatting instead of an invented one.
"""

from __future__ import annotations

import shutil

from pptx import Presentation
from pptx.util import Cm, Pt

TEMPLATE = "UZ - DAI Proposal Power Point template.pptx"
PROPOSAL = "FINISHED/Proposal_Presentation_v1.pptx"
REVIEW1 = "FINISHED/Review1_Presentation_v1.pptx"

TITLE = ("Deployment-Readiness Auditing of Smallholder Maize Yield-Interval Models")
NAME = "Ian Chinyoka"
REG = "R231473B"
SUPERVISOR = "Mr Zimowa"
DEGREE = "BSc (Hons) Data Science and Informatics"
AREA = "Analytics and Informatics"

LAYOUT_TITLE = 0
LAYOUT_CONTENT = 1
LAYOUT_TWO = 3
LAYOUT_ONLY = 5


def fill_title_slide(slide):
    title = slide.shapes.title
    title.text_frame.text = TITLE
    # keep the title clear of the crest at the top right
    title.left = Cm(2.2)
    title.width = Cm(24.0)
    title.top = Cm(4.6)
    title.height = Cm(5.4)
    title.text_frame.word_wrap = True
    for p in title.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(32)
    sub = slide.placeholders[1]
    tf = sub.text_frame
    tf.text = f"Student Name: {NAME}"
    for r in tf.paragraphs[0].runs:
        r.font.size = Pt(16)
    for line in [f"Registration Number: {REG}",
                 f"Supervisor: {SUPERVISOR}",
                 f"Degree Programme: {DEGREE}",
                 f"Area of Research: {AREA}"]:
        p = tf.add_paragraph()
        p.text = line
        for r in p.runs:
            r.font.size = Pt(16)


def bullets(slide, items, size=18):
    """items: list of (level, text) or plain strings."""
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        if isinstance(item, tuple):
            level, text = item
        else:
            level, text = 0, item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        p.text = text
        p.level = level
        for r in p.runs:
            r.font.size = Pt(size if level == 0 else size - 2)
        first = False


def content_slide(prs, heading, items, size=18):
    s = prs.slides.add_slide(prs.slide_layouts[LAYOUT_CONTENT])
    s.shapes.title.text_frame.text = heading
    bullets(s, items, size)
    return s


def two_col_slide(prs, heading, left_title, left_items, right_title, right_items, size=16):
    s = prs.slides.add_slide(prs.slide_layouts[LAYOUT_TWO])
    s.shapes.title.text_frame.text = heading
    phs = [ph for ph in s.placeholders if ph.placeholder_format.idx in (1, 2)]
    for ph, label, items in ((phs[0], left_title, left_items), (phs[1], right_title, right_items)):
        tf = ph.text_frame
        tf.word_wrap = True
        tf.text = label
        for r in tf.paragraphs[0].runs:
            r.font.bold = True
            r.font.size = Pt(size)
        for it in items:
            p = tf.add_paragraph()
            p.text = it
            p.level = 0
            for r in p.runs:
                r.font.size = Pt(size - 2)
    return s


def picture_slide(prs, heading, image, caption, max_h_cm=11.4):
    from PIL import Image
    w_px, h_px = Image.open(image).size
    height = Cm(max_h_cm)
    width = int(height * w_px / h_px)
    s = prs.slides.add_slide(prs.slide_layouts[LAYOUT_ONLY])
    s.shapes.title.text_frame.text = heading
    left = int((prs.slide_width - width) / 2)
    top = Cm(3.9)
    s.shapes.add_picture(image, left, top, height=height)
    tb = s.shapes.add_textbox(left, top + height + Cm(0.3), width, Cm(1.6))
    tb.text_frame.word_wrap = True
    tb.text_frame.text = caption
    for r in tb.text_frame.paragraphs[0].runs:
        r.font.size = Pt(12)
        r.font.italic = True
    return s


def build_proposal():
    shutil.copyfile(TEMPLATE, PROPOSAL)
    prs = Presentation(PROPOSAL)
    fill_title_slide(prs.slides[0])
    # slide 2 is the template's own Overview slide and is kept as it stands

    content_slide(prs, "Introduction (Overview and Background)", [
        "Maize is the staple crop of smallholder farming in Sub-Saharan Africa; fertiliser, "
        "credit and insurance decisions all depend on a yield expectation.",
        "Yield models are now published with prediction intervals, and those intervals are "
        "used to justify decisions.",
        "An interval is only useful if it is valid where it is used \u2014 and validation in "
        "one place does not transfer to another.",
        "This project builds an auditor that tests whether such a model may be deployed in a "
        "named district.",
    ], size=17)

    content_slide(prs, "Motivation of the study", [
        "Extension advice, credit limits and insurance premiums are being set from model "
        "output, not from measured yield.",
        "A point prediction hides its own uncertainty; a decision needs the interval.",
        "The published panel is public and reused, so results are checkable and repeatable.",
        "A wrong interval is worse than no interval: it looks like knowledge.",
    ])

    content_slide(prs, "Challenges in the study", [
        "The panel is duplicated and clustered \u2014 4,764 of 14,773 rows (32.2%) are "
        "duplicates, so random splits leak.",
        "Point skill and interval calibration fail independently, and are usually reported "
        "as one number.",
        "Moving to one country changes both the covariate and the outcome distribution.",
        "The standard support check sees covariates only, so an outcome shift passes "
        "undetected.",
        "No published study costs the remedy, so the label budget is unknown.",
    ], size=17)

    two_col_slide(prs, "Pre-Literature Review", "What the literature establishes", [
        "Interval construction is mature (conformal, quantile, Bayesian).",
        "Validation design inflates reported skill on structured data.",
        "Support checks exist for covariate shift.",
        "Machine learning predicts yield well enough to deploy.",
    ], "What it does not establish", [
        "No joint audit of skill and calibration.",
        "No test of the support check against coverage loss.",
        "No label budget for the remedy.",
        "No interval evidence on a multi-country maize panel.",
    ])

    content_slide(prs, "Research Gap", [
        "G1  No study reports honest skill, separate calibration and a costed remedy for one "
        "domain in one place.",
        "G2  The support check is never compared with observed coverage loss.",
        "G3  Remedy cost, in labels required, is unquantified.",
        "G4  Agronomic panels are under-tested for transport.",
        "G5  Interval width is rarely reported beside coverage.",
    ], size=17)

    content_slide(prs, "Problem Statement", [
        "A yield model is fitted on a multi-country panel and proposed for use in one "
        "district. The deployment question is not \u201chow accurate is it?\u201d but four:",
        (1, "P1  Is the reported accuracy an artefact of the evaluation design?"),
        (1, "P2  Does the model still rank correctly in the target region?"),
        (1, "P3  Is the interval calibrated there, and would anyone notice if it were not?"),
        (1, "P4  What would repair it, and what would the repair cost?"),
        "No existing instrument answers P1 to P4 together, for one domain, with the cost "
        "stated.",
    ], size=17)

    content_slide(prs, "Research Questions", [
        "RQ1  How much of the reported skill of a maize yield model is an artefact of random "
        "validation?",
        "RQ2  Once the split is honest, how does point transfer differ from interval "
        "calibration across countries?",
        "RQ3  Which distribution shift explains a coverage failure, and can a covariate-space "
        "check detect it?",
        "RQ4  What label budget restores coverage, and what interval width does it buy?",
    ], size=17)

    content_slide(prs, "Research Objectives", [
        "Measure the inflation between random, clustered and country-holdout validation.",
        "Separate point skill from interval calibration, per country.",
        "Diagnose the responsible shift by comparing the support verdict with observed "
        "coverage loss.",
        "Produce a level-adjusted recalibration with its label-budget curve.",
        "Deliver a single readiness report for a named target domain.",
    ], size=17)

    content_slide(prs, "Methodology (Proposed)", [
        "M1  Split integrity \u2014 random vs clustered vs country-holdout audit.",
        "M2  Skill and calibration separation \u2014 R\u00b2 beside per-country coverage, "
        "with bounds.",
        "M3  Transport diagnosis \u2014 dissimilarity index against measured coverage loss.",
        "M4  Level-adjusted recalibration \u2014 coverage restored against labels required.",
        "M5  Readiness report \u2014 one verdict, with the interval width at that budget.",
    ], size=17)

    two_col_slide(prs, "Research Outline (Road map / Workplan)", "Phase II", [
        "Proposal (this document)",
        "Survey paper: 15 foundational sources",
        "Systematic review: 71 retained, 49 included",
    ], "Phase III \u2014 Review 1", [
        "Chapter 1: introduction",
        "Chapter 2: literature review + matrix",
        "Chapter 3: methodology, first draft",
        "Review 1 presentation (this deck)",
    ])

    content_slide(prs, "Conclusion", [
        "The three literatures that decide whether an interval may be trusted are mature "
        "separately and silent jointly.",
        "The panel makes the gap measurable: +0.265 random, +0.177 clustered, \u22121.943 "
        "country-holdout.",
        "The project contributes an audit, not a new learner: four answers, one verdict, one "
        "document.",
        "Success is a readiness verdict a non-specialist can act on, including what the "
        "remedy would cost.",
    ], size=17)

    prs.save(PROPOSAL)
    print(f"wrote {PROPOSAL} ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")


def build_review1():
    shutil.copyfile(TEMPLATE, REVIEW1)
    prs = Presentation(REVIEW1)
    fill_title_slide(prs.slides[0])

    content_slide(prs, "Progress since the proposal", [
        "The review has moved from a purposive reading list to a documented systematic search.",
        "The audit has a first working module: split integrity, run on the real panel.",
        "This presentation reports Chapters 1 and 2 and the first draft of Chapter 3.",
        "Nothing reported here is projected; every number came from the panel or the search log.",
    ], size=17)

    content_slide(prs, "Chapter 1 \u2014 Introduction and background", [
        "Maize dominates smallholder cropping; decisions around it are made on expected "
        "yield.",
        "Models now supply that expectation, increasingly with intervals attached.",
        "An interval carries a promise of coverage \u2014 a promise that is conditional on "
        "where it was calibrated.",
        "Deployment in a named district is therefore a statistical question, not only an "
        "agronomic one.",
    ])

    content_slide(prs, "Motivation and challenges", [
        "Motivation: advice is being issued on model output whose uncertainty is unreported.",
        "Challenge 1 \u2014 32.2% duplicate rows make random validation optimistic.",
        "Challenge 2 \u2014 skill and calibration are reported as one number.",
        "Challenge 3 \u2014 transfer changes covariates and outcomes at once.",
        "Challenge 4 \u2014 the standard support check never looks at the outcome "
        "distribution.",
    ], size=17)

    picture_slide(prs, "Chapter 2 \u2014 the systematic search",
                  "docs/figures/prisma_flow.png",
                  "491 identified, 463 screened, 329 excluded, 84 eligible, 71 retained, "
                  "49 included in the synthesis.")

    two_col_slide(prs, "Chapter 2 \u2014 what the synthesis shows", "Established", [
        "49 studies from Elsevier, Wiley, Springer, Taylor & Francis.",
        "Intervals are constructible with coverage guarantees.",
        "Spatial validation shows random validation to be optimistic.",
        "Support checks exist and are standard practice.",
    ], "Absent", [
        "No joint audit of skill and calibration.",
        "No test of the support check against coverage loss.",
        "No label budget for any remedy.",
        "No interval evidence for a multi-country maize panel.",
    ])

    content_slide(prs, "Research Gradient \u2014 the gap restated", [
        "G1  One instrument, one domain, four answers \u2014 absent from the corpus.",
        "G2  Support verdict vs measured coverage loss \u2014 absent.",
        "G3  Labels required to restore coverage \u2014 absent.",
        "G4  Interval evidence on an agronomic panel \u2014 absent.",
        "G5  Width reported beside coverage \u2014 rarely done.",
    ], size=17)

    content_slide(prs, "Chapter 3 (first draft) \u2014 method", [
        "M1  Split integrity: random, clustered (1,526 clusters) and country-holdout designs "
        "on the same learner.",
        "M2  Skill and calibration: R\u00b2 beside per-country coverage with bounds.",
        "M3  Transport diagnosis: dissimilarity index compared with coverage loss.",
        "M4  Recalibration: level offset estimated from a labelled target sample; label-budget "
        "curve.",
        "M5  Report: one readiness verdict, with width at that budget.",
    ], size=17)

    content_slide(prs, "Result so far \u2014 Module 1 on the real panel", [
        "14,773 rows, 1,526 clusters, 4,764 duplicate rows (32.2%).",
        "Random 5-fold: R\u00b2 = +0.265.",
        "Clustered hold-out: R\u00b2 = +0.177  (inflation +0.088).",
        "Country hold-out: R\u00b2 = \u22121.943  (inflation +2.208).",
        "Trace: global imputation was optimistic; fold-internal imputation gives \u22121.943.",
    ], size=17)

    two_col_slide(prs, "Next steps", "Immediate", [
        "M2 calibration on the honest split",
        "M3 support check vs coverage loss",
    ], "Before submission", [
        "M4 label-budget curve",
        "Chapter 4 results, Chapter 5 discussion",
        "Technical paper (Research Paper 2)",
    ])

    content_slide(prs, "Conclusion", [
        "The literature is strong on each of the four questions and silent when they are "
        "asked together.",
        "The panel already shows how large the artefact is: +2.208 under country hold-out.",
        "The contribution is the joint audit and its costed remedy.",
        "Review 1 delivers Chapters 1 and 2 complete, Chapter 3 drafted, and Module 1 running.",
    ], size=17)

    prs.save(REVIEW1)
    n = len(prs.slides._sldIdLst)
    print(f"wrote {REVIEW1} ({n} slides)")


build_proposal()
build_review1()
