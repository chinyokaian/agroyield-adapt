"""Write the Literature Matrix CSV required for Review 1."""

from __future__ import annotations

import csv
import json
import re

OUT = "FINISHED/Literature_Matrix.csv"
corpus = json.load(open("docs/litreview/corpus.json", encoding="utf-8"))["corpus"]
cited = set(json.load(open("docs/litreview/cited_keys.json", encoding="utf-8")))

RULES = [
    ("Interval construction",
     r"conformal|prediction interval|quantile regression|quantile random|uncertainty|"
     r"coverage|probabilistic forecast|bayesian"),
    ("Validation design",
     r"cross-?validat|validation|leave-one-out|leakage|sampling for validation"),
    ("Transport and applicability",
     r"applicabilit|transferab|extrapolat|distribution shift|generalisa|generaliza|out-of-year"),
    ("Machine learning yield prediction",
     r"machine learning|random forest|deep learning|neural network|gradient boost"),
    ("Spatial soil prediction",
     r"\bsoil\b|kriging|geostatist|digital soil|sensor data"),
    ("Crop simulation",
     r"process-based|dssat|apsim|epic|simulation|crop model|yield gap|phenolog|"
     r"evapotranspiration|production efficiency"),
    ("Remote sensing",
     r"remote sensing|satellite|sentinel|landsat|modis|ndvi|imagery|spectral|chlorophyll"),
]


def focus(rec: dict) -> str:
    text = f"{rec['title']} {rec['abstract']}"
    for name, pat in RULES:
        if re.search(pat, text, re.I):
            return name
    return "Machine learning yield prediction"


def method(rec: dict) -> str:
    text = f"{rec['title']} {rec['abstract']}"
    found = []
    for name, pat in [("conformal prediction", r"conformal"),
                      ("quantile regression", r"quantile"),
                      ("random forest", r"random forest"),
                      ("gradient boosting", r"xgboost|boosted|boosting"),
                      ("deep learning", r"deep learning|neural network|cnn|lstm"),
                      ("remote sensing data", r"satellite|sentinel|landsat|modis|ndvi|imagery"),
                      ("process-based model", r"dssat|apsim|epic|process-based|simulation"),
                      ("geostatistics", r"kriging|geostatist|variogram"),
                      ("Bayesian inference", r"bayesian"),
                      ("field or survey data", r"field experiment|survey|plot data|panel data")]:
        if re.search(pat, text, re.I):
            found.append(name)
    return "; ".join(found[:3]) if found else "state from full text"


rows = sorted(corpus, key=lambda x: (int(x["year"] or 0), x["title"]))
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Matrix ID", "Authors", "Year", "Title", "Outlet", "Publisher", "DOI",
                "Method", "Thematic focus", "Included in synthesis"])
    for i, r in enumerate(rows, 1):
        key = r["doi"] or r["title"]
        authors = "; ".join(r["authors"][:4]) + (" et al." if len(r["authors"]) > 4 else "")
        w.writerow([f"LM{i:03d}", authors, r["year"], r["title"], r["venue"], r["publisher"],
                    r["doi"], method(r), focus(r), "Yes" if key in cited else "No"])

print(f"wrote {OUT} with {len(rows)} rows; "
      f"{sum(1 for r in rows if (r['doi'] or r['title']) in cited)} marked included")
