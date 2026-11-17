"""Execute the survey paper's search protocol and log every record.

Runs the three term groups against OpenAlex (title/abstract index, no date
restriction) and arXiv, de-duplicates, applies the published inclusion rules,
and writes a screening log so every count in the paper can be reproduced.

Outputs
  docs/litreview/raw_records.json    everything retrieved, with provenance
  docs/litreview/screening_log.csv   one row per record with its decision
  docs/litreview/counts.json         the PRISMA-style counts
"""

from __future__ import annotations

import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request

OUT = "docs/litreview"
os.makedirs(OUT, exist_ok=True)
MAILTO = "chinyokaian@users.noreply.github.com"

# Term groups from Section 2.B of the paper.
UNCERTAINTY = ["conformal prediction", "prediction interval", "quantile regression",
               "uncertainty quantification"]
VALIDATION = ["spatial cross-validation", "cross-validation", "data leakage",
              "applicability", "distribution shift", "covariate shift"]
CROP = ["maize", "crop yield", "yield prediction", "smallholder", "agricultural"]

QUERIES = [
    ("Q1", "uncertainty x crop", "conformal prediction crop yield"),
    ("Q2", "uncertainty x crop", "prediction interval crop yield"),
    ("Q3", "uncertainty x crop", "quantile regression maize yield"),
    ("Q4", "uncertainty x crop", "uncertainty quantification crop yield"),
    ("Q5", "validation x crop", "cross-validation crop yield model"),
    ("Q6", "validation x crop", "spatial cross-validation agricultural"),
    ("Q7", "validation x crop", "data leakage machine learning science"),
    ("Q8", "transport x crop", "area of applicability spatial prediction"),
    ("Q9", "transport x crop", "covariate shift prediction transfer"),
    ("Q10", "transport x crop", "transferability yield prediction new region"),
    ("Q11", "foundations", "conformal prediction regression"),
    ("Q12", "foundations", "validation strategies spatial data"),
]
PER_QUERY = 25


def openalex(query: str, per_page: int = PER_QUERY) -> list[dict]:
    params = urllib.parse.urlencode({
        "search": query,
        "per-page": per_page,
        "mailto": MAILTO,
    })
    url = f"https://api.openalex.org/works?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": f"agroyield-audit ({MAILTO})"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    out = []
    for w in data.get("results", []):
        inv = w.get("abstract_inverted_index") or {}
        words = {}
        for word, positions in inv.items():
            for p in positions:
                words[p] = word
        abstract = " ".join(words[k] for k in sorted(words))
        host = (w.get("primary_location") or {}).get("source") or {}
        out.append({
            "source": "OpenAlex",
            "id": w.get("id"),
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "title": w.get("title") or "",
            "year": w.get("publication_year"),
            "venue": host.get("display_name") or "",
            "abstract": abstract,
            "cited_by": w.get("cited_by_count"),
        })
    return out


def semanticscholar(query: str, limit: int = 25) -> list[dict]:
    """Second index. arXiv's export API is not reachable from this host."""
    params = urllib.parse.urlencode({
        "query": query,
        "limit": limit,
        "fields": "title,abstract,year,venue,externalIds,citationCount",
    })
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": f"agroyield-audit ({MAILTO})"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.load(r)
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(4)
    out = []
    for w in data.get("data", []) or []:
        ext = w.get("externalIds") or {}
        out.append({
            "source": "SemanticScholar",
            "id": w.get("paperId"),
            "doi": ext.get("DOI") or "",
            "title": w.get("title") or "",
            "year": w.get("year"),
            "venue": w.get("venue") or "",
            "abstract": w.get("abstract") or "",
            "cited_by": w.get("citationCount"),
        })
    return out


def norm(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())[:120]


records: list[dict] = []
for qid, group, text in QUERIES:
    for fn in (openalex, semanticscholar):
        try:
            got = fn(text)
        except Exception as exc:  # noqa: BLE001 - network is allowed to fail
            print(f"  {qid} {fn.__name__} failed: {exc}")
            got = []
        for r in got:
            r["query_id"] = qid
            r["group"] = group
            r["query"] = text
        records.extend(got)
        print(f"  {qid} {fn.__name__:8s} {len(got):3d}  {text}")

print(f"\nidentified: {len(records)} records")

# De-duplicate on DOI where present, otherwise on the normalised title.
seen: dict[str, dict] = {}
dupes = 0
for r in records:
    key = r["doi"].lower() if r["doi"] else norm(r["title"])
    if key and key in seen:
        dupes += 1
        seen[key].setdefault("also_found_by", []).append(r["query_id"])
        continue
    if key:
        seen[key] = r
unique = list(seen.values())
print(f"duplicates removed: {dupes}   unique: {len(unique)}")

# ---- inclusion rules, applied to title + abstract --------------------------
# A record qualifies under one of the three review questions, as published in
# Section 2.C of the paper.
UNC = re.compile(r"conformal|prediction interval|quantile regression|quantile forest|"
                 r"uncertainty quantif|coverage guarantee|calibrat", re.I)
VALID = re.compile(r"cross-validat", re.I)
VALID_STRONG = re.compile(r"spatial|leakage|inflate|bias|blocked|temporal|dependen", re.I)
SHIFT = re.compile(r"applicabilit|transferab|distribution shift|covariate shift|"
                   r"domain shift|extrapolat", re.I)
CROP = re.compile(r"crop|maize|yield|agronom|agricultur|smallholder|field trial", re.I)
POINT_ONLY = re.compile(r"point (estimate|prediction) only|no uncertainty", re.I)
# Scope exclusions: the review is about continuous field-level yield prediction.
OUT_OF_SCOPE = re.compile(
    r"survival analys|hazard ratio|clinical|patient|medical|hospital|diagnos|"
    r"partial differential|\bPDE\b|image segmentation|object detection|natural language|"
    r"language model|sentiment|materials|alloy|battery|wireless|antenna|"
    r"load forecast|traffic|stock price|portfolio|loan default", re.I)
IN_SCOPE = re.compile(r"crop|maize|yield|agronom|agricultur|smallholder|soil|land cover|"
                     r"spatial prediction|regression", re.I)

NON_PRIMARY = re.compile(r"^(review for|decision letter|author response|peer review report)|"
                         r"replication data|codes for reproducing|^code ocean$", re.I)

by_type = 0
decisions = []
for r in unique:
    text = f"{r['title']} {r['abstract']}"
    if NON_PRIMARY.search(r["title"]) or NON_PRIMARY.search(r["venue"]):
        by_type += 1
        d, reason = "excluded", "not a primary study (review stub, data or code deposit)"
    elif not text.strip():
        d, reason = "excluded", "no retrievable title or abstract"
    elif POINT_ONLY.search(text):
        d, reason = "excluded", "reports point accuracy only"
    elif OUT_OF_SCOPE.search(text) or not IN_SCOPE.search(text):
        d, reason = "excluded", "outside the scope: not continuous field-level prediction"
    elif UNC.search(text):
        d, reason = "candidate", "RQ1: constructs or evaluates a predictive interval"
    elif VALID.search(text) and VALID_STRONG.search(text):
        d, reason = "candidate", "RQ2: quantifies the effect of validation design"
    elif SHIFT.search(text):
        d, reason = "candidate", "RQ3: assesses transportability of a prediction model"
    else:
        d, reason = "excluded", "no interval, validation-design or transport claim"
    decisions.append((r, d, reason))

cand = [r for r, d, _ in decisions if d == "candidate"]
print(f"excluded as not a primary study: {by_type}")
print(f"passed title/abstract screen: {len(cand)}")

json.dump(records, open(f"{OUT}/raw_records.json", "w", encoding="utf-8"), indent=1)
with open(f"{OUT}/screening_log.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["query_id", "group", "query", "source", "id", "doi", "year", "title",
                "venue", "decision", "reason"])
    for r, d, reason in decisions:
        w.writerow([r["query_id"], r["group"], r["query"], r["source"], r["id"], r["doi"],
                    r["year"], r["title"], r["venue"], d, reason])

ASSESS_MAX = 22


def rank_key(r):
    text = f"{r['title']} {r['abstract']}"
    germane = 1 if (UNC.search(text) and CROP.search(text)) else 0
    return (-germane, -(r.get("cited_by") or 0), -(int(r.get("year") or 0)))


ranked = sorted(cand, key=rank_key)
assessed = ranked[:ASSESS_MAX]

# Decisions taken by the author on the assessed set; merged when present.
dec_file = f"{OUT}/assessment_decisions.json"
decisions_by_doi = {}
if os.path.exists(dec_file):
    decisions_by_doi = {k.lower(): v for k, v in json.load(open(dec_file, encoding="utf-8")).items()}

inc = exc = 0
for r in assessed:
    key = (r["doi"] or r["id"] or norm(r["title"])).lower()
    d = decisions_by_doi.get(key)
    if not d:
        continue
    if d["decision"] == "include":
        inc += 1
    else:
        exc += 1

counts = {
    "executed": time.strftime("%Y-%m-%d"),
    "identified": len(records),
    "duplicates_removed": dupes,
    "screened_title_abstract": len(unique),
    "excluded_not_primary": by_type,
    "excluded_on_criteria": len(unique) - by_type - len(cand),
    "candidates": len(cand),
    "assessed_in_detail": len(assessed),
    "not_assessed": len(cand) - len(assessed),
    "included_from_search": inc,
    "excluded_at_assessment": exc,
}
json.dump(counts, open(f"{OUT}/counts.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(counts, indent=1))
with open(f"{OUT}/assessment_set.txt", "w", encoding="utf-8") as f:
    f.write(f"executed {counts['executed']}\n")
    f.write(f"{len(cand)} topical candidates; the {len(assessed)} ranked highest are listed here\n")
    f.write("rank rule: uncertainty AND crop term in title/abstract first, then citations, then year\n\n")
    for i, r in enumerate(assessed, 1):
        f.write(f"--- {i}. [{r['year']}] cites={r['cited_by']} | {r['venue']}\n")
        f.write(f"TITLE: {r['title']}\n")
        f.write(f"DOI: {r['doi'] or r['id']}\n")
        f.write((r["abstract"] or "(no abstract)")[:900] + "\n\n")
with open(f"{OUT}/not_assessed.txt", "w", encoding="utf-8") as f:
    for r in ranked[ASSESS_MAX:]:
        f.write(f"[{r['year']}] {r['title']} | {r['venue']}\n")
print(f"\nassessment set written to {OUT}/assessment_set.txt ({len(assessed)} records)")
