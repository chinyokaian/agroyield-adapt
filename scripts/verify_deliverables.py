"""Verify the Review 1 deliverables: report, both decks and the literature matrix."""

from __future__ import annotations

import csv
import json
import re
import sys

from docx import Document
from pptx import Presentation

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))


# ------------------------------------------------------------ the report ---
doc = Document("FINISHED/Concept_Development_Report_Draft1.docx")
paras = [p.text.strip() for p in doc.paragraphs]
flat = re.sub(r"\s+", " ", " ".join(paras))

for ch in ["CHAPTER 1: INTRODUCTION", "CHAPTER 2: LITERATURE REVIEW",
           "CHAPTER 3: METHODOLOGY (FIRST DRAFT)"]:
    check(ch in flat, f"chapter present: {ch}")

for s in ["1.1 Background", "1.2 Motivation", "1.3 Problem statement", "1.4 Research questions",
          "1.5 Research objectives", "1.6 Scope and significance", "1.7 Structure of the report"]:
    check(s in flat, f"chapter 1 section: {s}")

for s in ["2.1 Introduction", "2.2 Problem statement", "2.3 Review method",
          "2.4 Characteristics of the included studies", "2.5 Thematic synthesis",
          "2.6 Discussion", "2.7 Research gaps and directions", "2.8 Summary"]:
    check(s in flat, f"chapter 2 section: {s}")

check(all(f"2.5.{i}" in flat for i in range(1, 7)), "chapter 2 subsections 2.5.1-2.5.6 present")

for s in ["3.1 Research design", "3.2 Data", "3.3 The audit modules", "3.4 Evaluation measures",
          "3.5 Ethical considerations", "3.6 Limitations of the design"]:
    check(s in flat, f"chapter 3 section: {s}")

check("P1." in flat and "P4." in flat, "problem statement keeps its four sub-problems")
check(all(f"RQ{i}." in flat for i in range(1, 5)), "four research questions present")

# citations and references
ref_start = max(i for i, t in enumerate(paras) if t.upper() == "REFERENCES")
body = " ".join(paras[:ref_start])
refs = [p for p in paras[ref_start + 1:] if re.match(r"^\[\d+\]", p)]
nums = [int(n) for n in re.findall(r"\[(\d{1,3})\]", body)]
first = []
for n in nums:
    if n not in first:
        first.append(n)
check(len(refs) == 49, f"single reference list carries the 49 sources ({len(refs)})")
check(sorted(set(nums)) == list(range(1, len(refs) + 1)),
      "citation numbering is complete and gapless")
check(first == sorted(first), "citations appear in increasing order of first use (IEEE)")

# numbering of floats
check("Figure 2.1." in flat, "figure numbered within the chapter (Figure 2.1)")
check("Table 2.1." in flat and "Table 2.2." in flat and "Table 3.1." in flat,
      "tables numbered within their chapters")
check("Figure 1." not in flat and "Table 1." not in flat and "Table 2." not in flat.replace("Table 2.1.", "").replace("Table 2.2.", ""),
      "no chapter-less float numbers left over")
check(bool(re.search(r"(?<!2\.)5\.1 Constructing", flat)) is False,
      "review sub-numbering fully remapped (no bare 5.x headings)")

# table of contents
toc = [p for p in paras if "\t" in p]
check(len(toc) == 25, f"table of contents lists every heading ({len(toc)})")
check(all(t.rstrip()[-1:].isdigit() for t in toc), "every contents entry carries a page number")

# floats
check(len(doc.inline_shapes) >= 2, "crest and PRISMA figure embedded")
check(len(doc.tables) == 3, f"three tables present ({len(doc.tables)})")

# --------------------------------------------------------------- the decks --
for path, expected_min in (("FINISHED/Proposal_Presentation_v1.pptx", 12),
                           ("FINISHED/Review1_Presentation_v1.pptx", 11)):
    prs = Presentation(path)
    name = path.split("/")[-1]
    slides = list(prs.slides)
    check(len(slides) >= expected_min, f"{name}: {len(slides)} slides")
    text0 = " ".join(shp.text_frame.text for shp in slides[0].shapes if shp.has_text_frame)
    check("Ian Chinyoka" in text0 and "R231473B" in text0 and "Zimowa" in text0,
          f"{name}: title slide carries the candidate and supervisor")
    check("Degree Programme" in text0 and "Area of Research" in text0,
          f"{name}: title slide keeps the template's fields")
    all_text = " ".join(shp.text_frame.text for s in slides for shp in s.shapes
                        if shp.has_text_frame)
    check("Title goes here" not in all_text, f"{name}: title placeholder replaced")
    check("Student Name: Ian Chinyoka" in all_text,
          f"{name}: name field filled rather than left blank")
    check(slides[1].shapes.title.text_frame.text.strip() == "Overview",
          f"{name}: template overview slide retained")
    check(all_text.count("Conclusion") >= 1, f"{name}: closes with a conclusion")
    bullets = [shp.text_frame.text for s in slides for shp in s.shapes
               if shp.has_text_frame and len(shp.text_frame.text) > 120]
    check(len(bullets) >= 6, f"{name}: content slides carry argument, not headings only")

# ------------------------------------------------------------- the matrix ---
rows = list(csv.reader(open("FINISHED/Literature_Matrix.csv", encoding="utf-8-sig")))
head, body_rows = rows[0], rows[1:]
check(len(body_rows) == 71, f"matrix rows match the corpus ({len(body_rows)})")
check(len(head) == 10, f"matrix columns ({len(head)})")
check(all(r[3] and r[1] for r in body_rows), "every matrix row has authors and a title")
check(sum(1 for r in body_rows if r[9] == "Yes") == 49,
      "matrix marks the 49 synthesised studies")
check(len({r[6] for r in body_rows if r[6]}) == len([r for r in body_rows if r[6]]),
      "no duplicate DOIs in the matrix")

# ----------------------------------------------------- consistency across ---
counts = json.load(open("docs/litreview/prisma_counts.json", encoding="utf-8"))
check(str(counts["corpus"]) in flat, f"report states the corpus size ({counts['corpus']})")
check(str(counts["screened"]) in flat, f"report states the screened count ({counts['screened']})")

failed = [l for ok, l in results if not ok]
print("\n".join(f"{'PASS' if ok else 'FAIL'}  {l}" for ok, l in results))
print(f"\n{len(results)} checks, {len(failed)} failures")
open("docs/verification_deliverables.txt", "w", encoding="utf-8").write(
    "\n".join(f"{'PASS' if ok else 'FAIL'}  {l}" for ok, l in results)
    + f"\n\n{len(results)} checks, {len(failed)} failures\n")
sys.exit(1 if failed else 0)
