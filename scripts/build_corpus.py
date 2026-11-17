"""Build the systematic literature review corpus.

Searches OpenAlex (title/abstract index) for the review questions, keeps only
records published by the six publishers Dr Mhlangu named, screens them against
the published criteria, downloads the openly licensed PDFs, and writes:

  docs/litreview/corpus.json          every record with provenance
  papers/*.pdf                        downloaded open-access articles
  docs/litreview/AGROYIELD-ADAPT.ris  Mendeley import (IEEE style selectable)
  docs/litreview/corpus_xlsx.json     rows for the workbook writer
  docs/litreview/prisma_counts.json   the PRISMA numbers
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request

OUT = "docs/litreview"
PAPERS = "papers"
os.makedirs(OUT, exist_ok=True)
os.makedirs(PAPERS, exist_ok=True)
MAILTO = "chinyokaian@users.noreply.github.com"
UA = {"User-Agent": f"agroyield-litreview ({MAILTO})"}

# The six publishers named by the supervisor.
PUBLISHERS = {
    "Elsevier": re.compile(r"^elsevier", re.I),
    "Taylor & Francis": re.compile(r"taylor", re.I),
    "SAGE": re.compile(r"^sage", re.I),
    "Wiley": re.compile(r"wiley", re.I),
    "Springer": re.compile(r"springer", re.I),
    "Emerald": re.compile(r"emerald", re.I),
}

QUERIES = [
    "conformal prediction crop yield uncertainty",
    "prediction interval crop yield machine learning",
    "uncertainty quantification agricultural yield prediction",
    "quantile regression yield forecasting",
    "spatial cross-validation crop yield prediction",
    "data leakage machine learning agronomy",
    "model validation spatial prediction soil",
    "transferability crop yield model new region",
    "area of applicability spatial prediction",
    "distribution shift machine learning agriculture",
    "yield prediction smallholder maize machine learning",
    "remote sensing yield prediction uncertainty",
    "calibration uncertainty deep learning crop",
    "generalisation gap yield prediction model",
]
PER_QUERY = 100

CROP = re.compile(r"crops?|maize|corn|wheat|rice|sorghum|millet|soybean|sugarcane|"
                  r"agronom|agricultur|smallholder|soil|farmland|farms?|"
                  r"field trial|orchard|horticultur|crop yield|crop production|"
                  r"yield gap|evapotranspiration", re.I)
NON_AGRI = re.compile(r"biochar|biogas|pyrolysis|electricity|spot price|sea ice|"
                      r"occupancy|building|anaerobic digest|groundwater level", re.I)
METHOD = re.compile(r"conformal|prediction interval|quantile|uncertaint|coverage|calibrat|"
                    r"cross-validat|validation|leakage|applicabilit|transferab|"
                    r"distribution shift|covariate shift|extrapolat|generalisation|"
                    r"generalization", re.I)
PREDICT = re.compile(r"predict|forecast|estimat|model", re.I)
OUT_OF_SCOPE = re.compile(r"survival analys|hazard ratio|clinical|patient|medical|"
                          r"hospital|diagnos|image segmentation|object detection|"
                          r"sentiment|natural language|language model|alloy|battery|"
                          r"wireless|antenna|load forecast|traffic|stock price", re.I)


def fetch(query: str, per_page: int = 100) -> list[dict]:
    params = urllib.parse.urlencode({
        "search": query, "per-page": per_page, "mailto": MAILTO,
        "filter": "type:article|book-chapter",
    })
    url = f"https://api.openalex.org/works?{params}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
        data = json.load(r)
    out = []
    for w in data.get("results", []):
        pl = w.get("primary_location") or {}
        src = pl.get("source") or {}
        inv = w.get("abstract_inverted_index") or {}
        words: dict[int, str] = {}
        for word, positions in inv.items():
            for p in positions:
                words[p] = word
        authors = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])]
        out.append({
            "openalex_id": w.get("id"),
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "title": (w.get("title") or "").strip(),
            "year": w.get("publication_year"),
            "venue": src.get("display_name") or "",
            "publisher_raw": src.get("host_organization_name") or "",
            "authors": [a for a in authors if a],
            "abstract": " ".join(words[k] for k in sorted(words)),
            "volume": (w.get("biblio") or {}).get("volume") or "",
            "issue": (w.get("biblio") or {}).get("issue") or "",
            "first_page": (w.get("biblio") or {}).get("first_page") or "",
            "last_page": (w.get("biblio") or {}).get("last_page") or "",
            "is_oa": (w.get("open_access") or {}).get("is_oa"),
            "pdf_url": (w.get("best_oa_location") or {}).get("pdf_url") or "",
            "landing": pl.get("landing_page_url") or "",
            "cited_by": w.get("cited_by_count"),
        })
    return out


def publisher_of(raw: str) -> str | None:
    for name, pat in PUBLISHERS.items():
        if pat.search(raw or ""):
            return name
    return None


records: list[dict] = []
for q in QUERIES:
    try:
        got = fetch(q, PER_QUERY)
    except Exception as exc:  # noqa: BLE001
        print(f"  query failed ({exc}): {q}")
        continue
    kept = [r for r in got if publisher_of(r["publisher_raw"])]
    for r in kept:
        r["query"] = q
        r["publisher"] = publisher_of(r["publisher_raw"])
    records.extend(kept)
    print(f"  {len(got):3d} retrieved, {len(kept):3d} from the six publishers  | {q}")

identified = len(records)
seen: dict[str, dict] = {}
dupes = 0
for r in records:
    key = (r["doi"] or re.sub(r"[^a-z0-9]", "", r["title"].lower()))[:120]
    if key and key in seen:
        dupes += 1
        continue
    if key:
        seen[key] = r
unique = list(seen.values())

screened_out = []
in_scope = []
for r in unique:
    text = f"{r['title']} {r['abstract']}"
    if not r["title"]:
        screened_out.append((r, "no title"))
    elif OUT_OF_SCOPE.search(text):
        screened_out.append((r, "outside scope: outcome not a continuous agronomic quantity"))
    elif not CROP.search(text):
        screened_out.append((r, "outside scope: no agronomic outcome"))
    elif NON_AGRI.search(text) and not re.search(r"crop|maize|soil|agricultur", text, re.I):
        screened_out.append((r, "outside scope: non-agronomic outcome"))
    elif not PREDICT.search(text):
        screened_out.append((r, "no predictive model"))
    elif not METHOD.search(text):
        screened_out.append((r, "reports point accuracy only; no uncertainty, validation or transport claim"))
    else:
        in_scope.append(r)

in_scope.sort(key=lambda r: (-(r["cited_by"] or 0), -(int(r["year"] or 0))))
TARGET = 72
corpus = in_scope[:TARGET]

print(f"\nidentified {identified} | duplicates {dupes} | unique {len(unique)}")
print(f"screened out {len(screened_out)} | met criteria {len(in_scope)} | corpus kept {len(corpus)}")
from collections import Counter
print("by publisher:", dict(Counter(r["publisher"] for r in corpus)))

# ---- download the openly licensed PDFs -------------------------------------
downloaded, failed = 0, []
for r in corpus:
    if not r["pdf_url"]:
        failed.append((r, "no open-access PDF"))
        continue
    first = (r["authors"][0].split()[-1] if r["authors"] else "anon").lower()
    first = re.sub(r"[^a-z]", "", first) or "anon"
    name = f"{r['year']}_{first}_{re.sub(r'[^a-z0-9]+', '-', r['title'].lower())[:50].strip('-')}.pdf"
    path = os.path.join(PAPERS, name)
    if os.path.exists(path):
        r["pdf_file"] = name
        downloaded += 1
        continue
    try:
        req = urllib.request.Request(r["pdf_url"], headers=UA)
        with urllib.request.urlopen(req, timeout=90) as resp:
            blob = resp.read()
        if blob[:4] == b"%PDF" and len(blob) > 20000:
            open(path, "wb").write(blob)
            r["pdf_file"] = name
            downloaded += 1
        else:
            failed.append((r, "response was not a PDF"))
    except Exception as exc:  # noqa: BLE001
        failed.append((r, f"download failed: {type(exc).__name__}"))
    time.sleep(0.5)

print(f"PDFs downloaded: {downloaded} | not available: {len(failed)}")

json.dump({"corpus": corpus, "excluded": [{"title": r["title"], "reason": why}
                                          for r, why in screened_out]},
          open(f"{OUT}/corpus.json", "w", encoding="utf-8"), indent=1)

counts = {
    "executed": time.strftime("%Y-%m-%d"),
    "publishers": list(PUBLISHERS),
    "queries": QUERIES,
    "identified": identified,
    "duplicates_removed": dupes,
    "screened": len(unique),
    "excluded_screening": len(screened_out),
    "met_criteria": len(in_scope),
    "corpus": len(corpus),
    "pdfs_downloaded": downloaded,
    "pdfs_unavailable": len(failed),
    "by_publisher": dict(Counter(r["publisher"] for r in corpus)),
}
json.dump(counts, open(f"{OUT}/prisma_counts.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(counts, indent=1)[:600])
