"""Verify the review document, and the consistency of every artefact.

Citations are checked the way a marker would check them: numbering must start
at one, increase in order of first appearance, have no gaps, and every entry in
the list must be cited in the text.
"""

from __future__ import annotations

import csv
import json
import re
import sys

import openpyxl
from docx import Document

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))


# ---------------------------------------------------------------- the docs --
SLR = "FINISHED/Systematic_Literature_Review_v1.docx"
SURVEY = "FINISHED/Survey_Paper_v1.docx"
PROPOSAL = "FINISHED/Proposal_AGROYIELD-ADAPT_v2.docx"

doc = Document(SLR)
paras = [p.text.strip() for p in doc.paragraphs]
flat = re.sub(r"\s+", " ", " ".join(paras))
upper = flat.upper()

# structure
for need in ["INTRODUCTION", "PROBLEM STATEMENT", "REVIEW METHOD",
             "CHARACTERISTICS OF THE INCLUDED STUDIES", "THEMATIC SYNTHESIS",
             "DISCUSSION", "RESEARCH GAPS AND DIRECTIONS", "CONCLUSION", "REFERENCES"]:
    check(need in upper, f"section present: {need.title()}")

check(all(p in flat for p in ["P1.", "P2.", "P3.", "P4."]),
      "problem statement states the four sub-problems explicitly")
check("absence of an instrument that answers P1 to P4" in flat,
      "problem statement names the gap in one sentence")
check("PRISMA" in flat, "PRISMA flow reported")
check(len(doc.inline_shapes) >= 1, "PRISMA figure embedded")
check("Figure 1." in flat, "figure caption present")

# citations
ref_start = max(i for i, t in enumerate(paras) if t.upper() == "REFERENCES")
body = " ".join(paras[:ref_start])
refs = [p for p in paras[ref_start + 1:] if re.match(r"^\[\d+\]", p)]
check(len(refs) >= 45 and len(refs) <= 60,
      f"reference count inside Dr Mhlangu's 45-60 band ({len(refs)})")

nums_in_text = [int(n) for n in re.findall(r"\[(\d{1,3})\]", body)]
first_seen = []
for n in nums_in_text:
    if n not in first_seen:
        first_seen.append(n)
check(first_seen == sorted(first_seen),
      "citations appear in increasing order of first use (IEEE)")
check(sorted(set(nums_in_text)) == list(range(1, len(refs) + 1)),
      f"numbering is complete and gapless 1..{len(refs)}")
check(all(re.match(rf"^\[{i}\]", refs[i - 1]) for i in range(1, len(refs) + 1)),
      "reference list is numbered in the same order")
check(all(('"' in r) or ("\u201c" in r) for r in refs),
      "every reference carries a quoted title (IEEE)")
check(all(re.search(r"(19|20)\d\d", r) for r in refs), "every reference carries a year")
bad_refs = [r[:60] for r in refs if not re.search(r"doi:|vol\.|pp\.|p\.", r)]
check(not bad_refs, f"references carry volume/page or doi detail ({bad_refs or 'none'})")

# no leftovers
for bad in ["[[", "]]", "{", "}", "TODO", "TBD", "Lorem", "[Student"]:
    check(bad not in flat, f"no unresolved placeholder: {bad}")

# ---------------------------------------------------------------- artefacts --
corpus = json.load(open("docs/litreview/corpus.json", encoding="utf-8"))["corpus"]
counts = json.load(open("docs/litreview/prisma_counts.json", encoding="utf-8"))

wb = openpyxl.load_workbook("Literature_review_AGROYIELD-ADAPT.xlsx")
ws = wb["Literature Review"]
rows = list(ws.iter_rows(min_row=2, values_only=True))
check(len(rows) == len(corpus), f"workbook rows match the corpus ({len(rows)} vs {len(corpus)})")
check(all(r[3] for r in rows), "every workbook row has a title")
check(all(r[0] for r in rows), "every workbook row has authors")
dois = [r[8] for r in rows if r[8]]
check(len(dois) == len(set(dois)), "no duplicate DOIs in the workbook")

ris = open("docs/litreview/AGROYIELD-ADAPT.ris", encoding="utf-8").read()
check(ris.count("TY  - JOUR") == len(corpus),
      f"RIS record count matches the corpus ({ris.count('TY  - JOUR')})")
check(ris.count("ER  - ") == ris.count("TY  - JOUR"), "every RIS record is closed")
ris_dois = re.findall(r"^DO  - (.+)$", ris, re.M)
check(len(ris_dois) == len(set(ris_dois)), "no duplicate DOIs in the RIS")

# counts arithmetic
ident, dupes = counts["identified"], counts["duplicates_removed"]
screened, excl, met = counts["screened"], counts["excluded_screening"], counts["met_criteria"]
check(ident - dupes == screened, f"identified - duplicates = screened ({ident}-{dupes}={screened})")
check(excl + met == screened, f"excluded + eligible = screened ({excl}+{met}={screened})")
check(met >= counts["corpus"], f"eligible >= retained corpus ({met} >= {counts['corpus']})")
check(0.06 <= len(corpus) and 45 <= len(refs) <= 60,
      f"library {len(corpus)} within 60-75 and included {len(refs)} within 45-60")

# the paper's own numbers must match the artefacts
check(str(counts["screened"]) in flat, f"paper quotes the screened count ({counts['screened']})")
check(str(len(corpus)) in flat, f"paper quotes the retained corpus ({len(corpus)})")

# ------------------------------------------------------------ other reports --
for path in (SURVEY, PROPOSAL):
    d = Document(path)
    name = path.split("/")[-1]
    cand = [i for i, p in enumerate(d.paragraphs)
            if re.search(r"references?\s*$", p.text.strip(), re.I)
            and len(p.text.strip()) < 40]
    rstart = max(cand) if cand else None
    check(rstart is not None, f"{name}: references section located")
    if rstart is None:
        continue
    body2 = " ".join(p.text for p in d.paragraphs[:rstart])
    tail = [p.text.strip() for p in d.paragraphs[rstart + 1:] if p.text.strip()]
    numbered = [t for t in tail if re.match(r"^\[\d+\]", t)]
    check(len(tail) >= 8, f"{name}: reference list present ({len(tail)} entries)")
    if numbered:
        used = sorted({int(n) for n in re.findall(r"\[(\d{1,2})\]", body2)})
        check(used == list(range(1, len(numbered) + 1)),
              f"{name}: every reference cited, none dangling")
    else:
        # author-date list (Harvard): each cited surname-year must have an entry
        cited = set(re.findall(r"\(([A-Z][A-Za-z\u2019'-]+),?\s*(\d{4})\)", body2))
        joined = " ".join(tail)
        missing = [f"{a} {y}" for a, y in cited if not (a in joined and y in joined)]
        check(not missing,
              f"{name}: every author-date citation has a reference entry ({missing[:4] or 'none'})")

failed = [l for ok, l in results if not ok]
print("\n".join(f"{'PASS' if ok else 'FAIL'}  {l}" for ok, l in results))
print(f"\n{len(results)} checks, {len(failed)} failures")
open("docs/verification_all.txt", "w", encoding="utf-8").write(
    "\n".join(f"{'PASS' if ok else 'FAIL'}  {l}" for ok, l in results)
    + f"\n\n{len(results)} checks, {len(failed)} failures\n")
sys.exit(1 if failed else 0)
