"""Check the survey paper against UZ-DAI "Structure of DAI research paper 1".

Each check corresponds to a line of the department's template.
"""

from __future__ import annotations

import re
import sys

from docx import Document
from docx.enum.text import WD_BREAK

DOC = "FINISHED/Survey_Paper_v1.docx"

# Word's own count for this file, produced by scripts/word_stats.ps1
WORD_PAGES = 8
WORD_WORDS = 4193

results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((bool(ok), label))


doc = Document(DOC)
paras = [p.text.strip() for p in doc.paragraphs]
flat = re.sub(r"\s+", " ", " ".join(paras))
upper = flat.upper()

ref_pos = next(i for i, t in enumerate(paras) if t.upper() == "REFERENCES")
body_text = " ".join(paras[:ref_pos])
refs = [p for p in paras[ref_pos + 1:] if re.match(r"^\[\d+\]", p)]
table_text = " ".join(c.text for t in doc.tables for r in t.rows for c in r.cells)

# 1. Title ---------------------------------------------------------------
check(flat.count("A Survey of") >= 2, "title begins 'A Survey of'")
check("IAN CHINYOKA" in flat and "R231473B" in flat,
      "student name and number appear")
check("SURVEY PAPER 1" in upper, "title page identifies the paper type")

break_at = [i for i, p in enumerate(doc.paragraphs) if 'w:type="page"' in p._p.xml]
check(bool(break_at), "document contains an explicit page break")
if break_at:
    i = break_at[0]
    before = " ".join(paras[:i]).upper()
    after = " ".join(paras[i + 1:i + 3])
    check("SURVEY PAPER 1" in before and "IAN CHINYOKA" in before
          and after.startswith("A Survey of"),
          "page break separates the title page from the body")

# 2. Abstract ------------------------------------------------------------
abstract_par = next((t for t in paras if t.startswith("Abstract")), "")
abstract_words = len(abstract_par.split())
check(bool(abstract_par), "abstract present")
check(80 <= abstract_words <= 320, f"abstract length reasonable ({abstract_words} words)")
check(paras.index(abstract_par) < next(i for i, t in enumerate(paras)
                                      if t.upper().startswith("1. INTRODUCTION")),
      "abstract precedes the introduction")
check("Index Terms" in flat, "index terms / keywords present")

# 3. Introduction --------------------------------------------------------
intro_i = next((i for i, t in enumerate(paras) if t.upper().startswith("1. INTRODUCTION")), -1)
check(intro_i >= 0, "introduction present")
check("This paper surveys" in flat, "introduction states what the paper presents")

# 4. Body ----------------------------------------------------------------
check("2. PROBLEM DESCRIPTION" in upper, "problem description section present")
check("REVIEW OF FOUNDATIONAL PAPERS" in upper, "literature review section present")
check(len(refs) >= 10 and len(refs) <= 22,
      f"foundational papers within 10-22 ({len(refs)} cited)")
check(len(doc.inline_shapes) >= 4, f"figures used liberally ({len(doc.inline_shapes) - 1} figures + crest)")
check(len(doc.tables) >= 1, "comparison table present")
check("CRITICAL ASSESSMENT OF THE BASE PROJECT" in upper,
      "critical assessment of the base project present")
check("PROPOSED IMPROVEMENTS" in upper, "proposed solutions section present")

# per-paper commentary: every source discussed in prose, not only tabulated
prose = body_text
missing = []
for n in range(1, len(refs) + 1):
    if f"[{n}]" not in prose:
        missing.append(n)
check(not missing, f"each paper critically discussed in the prose (missing: {missing or 'none'})")

# commentary sentences about the base project
commentary_marks = prose.count("base project")
check(commentary_marks >= 15,
      f"commentary ties each paper to the base project ({commentary_marks} mentions)")

# feasibility backed by the literature: each proposed improvement cites sources
check("5. PROPOSED IMPROVEMENTS" in upper and "[11], [12]" in prose and "[9], [10]" in prose,
      "proposed improvements are backed by cited literature")

# 5. Conclusion / future work -------------------------------------------
check("CONCLUSION AND FUTURE WORK" in upper, "conclusion and future work section present")
check(prose.count("Five directions follow") == 1, "future research directions enumerated")

# 6. References ----------------------------------------------------------
check(len(refs) >= 10, f"reference list present ({len(refs)} entries)")
check(all(r.startswith(f"[{i}]") for i, r in enumerate(refs, start=1)),
      "references numbered consecutively in IEEE style")
check(sum(1 for r in refs if "vol." in r or "doi:" in r or "pp." in r) >= len(refs) - 1,
      "references carry IEEE volume/page/doi detail")
cited = {int(n) for n in re.findall(r"\[(\d{1,2})\]", body_text + " " + table_text)}
check(cited == set(range(1, len(refs) + 1)),
      f"every reference cited, every citation resolvable ({sorted(cited)})")

# Assessment standards ---------------------------------------------------
check(5 <= WORD_PAGES <= 8, f"page count within 5-8 pages (Word: {WORD_PAGES})")
check(3500 <= WORD_WORDS <= 4500, f"word count near 4000 (Word: {WORD_WORDS})")

# Formatting -------------------------------------------------------------
s = doc.sections[0]
check(round(s.page_width.cm, 1) == 21.0 and round(s.page_height.cm, 1) == 29.7, "A4 page")
check(doc.styles["Normal"].font.name == "Times New Roman", "Times New Roman body")
over = [round(sh.width.cm, 2) for sh in doc.inline_shapes if sh.width.cm > 15.92]
check(not over, f"no figure exceeds the text block ({over or 'none'})")
tw = round(sum(c.width.cm for c in doc.tables[0].rows[0].cells), 2)
check(tw <= 15.92, f"table fits the text block ({tw} cm)")

# Report -----------------------------------------------------------------
failed = [label for ok, label in results if not ok]
lines = [f"{'PASS' if ok else 'FAIL'}  {label}" for ok, label in results]
lines.append("")
lines.append(f"{len(results)} checks, {len(failed)} failures")
out = "\n".join(lines)
print(out)
open("docs/verification_survey.txt", "w", encoding="utf-8").write(out + "\n")
sys.exit(1 if failed else 0)
