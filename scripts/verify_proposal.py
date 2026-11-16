"""Four-pass verification of the proposal.

Pass 1  UZ-DAI §3.2 compliance: page setup, typography, front matter order,
        preliminary numbering, chapter casing, fields and captions
Pass 2  every number re-derived from the committed run and the raw CSV
Pass 3  claim hygiene and guideline coverage
Pass 4  layout: table widths inside the text block, hanging indents, logo embedded

Exit code is non-zero if any check fails.
"""

from __future__ import annotations

import json
import re
import sys

from docx import Document
from docx.oxml.ns import qn

from agroyield_adapt.checks.splits import duplication_stats
from agroyield_adapt.schema import TARGET, load_panel

DOC = "FINISHED/Proposal_AGROYIELD-ADAPT_v2.docx"
DATA = "One_Acre_Fund_MEL_maize_survey_data_2016-2022.csv"
RESULTS = "results/split_audit.json"

failures: list[str] = []
notes: list[str] = []


def check(condition: bool, label: str) -> None:
    print(f"  {'PASS' if condition else 'FAIL'}  {label}")
    if not condition:
        failures.append(label)


doc = Document(DOC)
paragraphs = [p for p in doc.paragraphs]
text = "\n".join(p.text for p in paragraphs)
for t in doc.tables:
    for row in t.rows:
        text += "\n" + " | ".join(c.text for c in row.cells)
flat = re.sub(r"\s+", " ", text)

# ---------------------------------------------------------------- pass 1 -----
print("PASS 1 - UZ-DAI §3.2 compliance")

s = doc.sections[0]
check(abs(s.page_width.cm - 21.0) < 0.05 and abs(s.page_height.cm - 29.7) < 0.05,
      f"page size A4 ({s.page_width.cm:.1f} x {s.page_height.cm:.1f} cm)")
check(abs(s.left_margin.cm - 4.0) < 0.05, f"left margin {s.left_margin.cm:.2f} cm (required 4.0)")
check(abs(s.right_margin.cm - 1.0) < 0.05, f"right margin {s.right_margin.cm:.2f} cm (required 1.0)")
check(abs(s.top_margin.cm - 2.5) < 0.05, f"top margin {s.top_margin.cm:.2f} cm (required 2.5)")
check(abs(s.bottom_margin.cm - 4.0) < 0.05,
      f"bottom margin {s.bottom_margin.cm:.2f} cm (required 4.0)")

normal = doc.styles["Normal"]
check(normal.font.name == "Times New Roman", f"base font {normal.font.name} (required Times New Roman)")
check(normal.font.size.pt == 12, f"base size {normal.font.size.pt} pt (required 12)")
check(abs(float(normal.paragraph_format.line_spacing) - 1.5) < 1e-6,
      f"line spacing {normal.paragraph_format.line_spacing} (required 1.5)")

front = ["ABSTRACT", "DECLARATION", "COPYRIGHT", "DEDICATION", "ACKNOWLEDGEMENTS",
         "ABBREVIATIONS", "TABLE OF CONTENTS", "LIST OF TABLES", "LIST OF FIGURES",
         "LIST OF APPENDICES"]
positions = []
for name in front:
    hit = next((i for i, p in enumerate(paragraphs) if p.text.strip() == name), None)
    check(hit is not None, f"preliminary page present: {name}")
    if hit is not None:
        positions.append(hit)
check(positions == sorted(positions), "preliminary pages are in the prescribed order")

title_text = flat[:1200]
for item in ["UNIVERSITY OF ZIMBABWE", "FACULTY OF COMPUTER ENGINEERING",
             "DEPARTMENT OF ANALYTICS AND INFORMATICS", "AGROYIELD-ADAPT", "BY",
             "SUPERVISED BY", "PARTIAL FULFILMENT", "2026"]:
    check(item in title_text, f"title page shows: {item}")
check(len(doc.inline_shapes) >= 5,
      f"{len(doc.inline_shapes)} images embedded (logo + four UML figures)")
check('TOC \\h \\z \\c &quot;Figure&quot;' in doc.element.xml
      or 'TOC \\h \\z \\c "Figure"' in doc.element.xml, "list of figures field present")
fig_captions = ["".join(n.text or "" for n in p._p.iter(qn("w:t"))).strip()
                for p in paragraphs]
fig_captions = [c for c in fig_captions if c.startswith("Figure ")]
check(len(fig_captions) == 4, f"{len(fig_captions)} figure captions found")
for i, cap in enumerate(fig_captions, start=1):
    check(cap.startswith(f"Figure {i}:"), f"caption {i} reads correctly: {cap[:45]}")
check(doc.element.xml.count("SEQ Figure") == 4, "four figure captions carry SEQ fields")
check("UZ LOGO" not in flat, "no unresolved logo placeholder")
check("no figures are included" not in flat.lower(), "list of figures is a field, not a disclaimer")

chapters = [p.text.strip() for p in paragraphs if p.text.strip().startswith("CHAPTER ")]
check(len(chapters) >= 5, f"{len(chapters)} chapter headings found")
for c in chapters:
    check(c == c.upper(), f"chapter heading is upper case: {c[:40]}")

subs = [p.text.strip() for p in paragraphs if re.match(r"^\d\.\d ", p.text.strip())]
check(len(subs) >= 12, f"{len(subs)} numbered sub-headings found")
check(all(not s.isupper() for s in subs), "sub-headings are not in upper case")

sect_xml = s._sectPr.xml
check('w:fmt="lowerRoman"' in sect_xml, "preliminaries use roman numerals")
body_sect = doc.sections[1]._sectPr.xml
check('w:start="1"' in body_sect and "lowerRoman" not in body_sect,
      "main body restarts numbering at 1 in arabic numerals")
check("PAGE" in s.footer.paragraphs[0]._p.xml, "page number field in the footer")
check(s.footer.paragraphs[0].alignment is not None
      and "CENTER" in str(s.footer.paragraphs[0].alignment),
      "page number is centred at the bottom edge")

full_xml = doc.element.xml
check(full_xml.count('TOC \\o') >= 1, "table of contents field present")
check('TOC \\h \\z \\c &quot;Table&quot;' in full_xml or 'TOC \\h \\z \\c "Table"' in full_xml,
      "list of tables field present")
check(full_xml.count("SEQ Table") == len(doc.tables),
      f"{full_xml.count('SEQ Table')} table captions carry SEQ fields for {len(doc.tables)} tables")

caption_texts = []
for p in paragraphs:
    joined = "".join(node.text or "" for node in p._p.iter(qn("w:t"))).strip()
    if joined.startswith("Table "):
        caption_texts.append(joined)
check(len(caption_texts) == len(doc.tables),
      f"{len(caption_texts)} captions for {len(doc.tables)} tables")
for i, cap in enumerate(caption_texts, start=1):
    check(cap.startswith(f"Table {i}:"), f"caption {i} reads correctly before field update: {cap[:45]}")
check("updateFields" in doc.settings.element.xml, "fields refresh when the document is opened")

# ---------------------------------------------------------------- pass 2 -----
print("\nPASS 2 - numbers verified against recorded runs and the raw data")
with open(RESULTS, encoding="utf-8") as fh:
    rep = json.load(fh)
df = load_panel(DATA)
live = duplication_stats(df)

for shown, computed, recorded in [
    ("14,773", live["rows"], 14773),
    ("1,526", live["clusters"], 1526),
    ("32.2%", live["pct_sharing_coord_year"], 32.2),
    ("4,764", live["rows_sharing_coord_year"], 4764),
]:
    check(shown in flat, f"'{shown}' stated in the document")
    check(computed == recorded, f"'{shown}' recomputed from CSV matches record ({computed})")

zero = int((df[TARGET] == 0).sum())
zero_pct = 100.0 * float((df[TARGET] == 0).mean())
check(zero == 263 and "263" in flat, f"zero-yield records: {zero}")
check(f"{zero_pct:.2f}%" == "1.78%" and "1.78%" in flat, f"zero-yield share {zero_pct:.2f}%")
check(len(df.columns) == 53 and "53 columns" in flat, f"column count {len(df.columns)}")

soil = df.groupby(df["country"].str.lower())["soil_clay"].apply(lambda v: 100.0 * v.isna().mean())
for country, shown in [("burundi", "78.4%"), ("rwanda", "76.3%")]:
    check(f"{soil[country]:.1f}%" == shown, f"{country} soil missingness {soil[country]:.1f}%")
    check(shown in flat, f"{country} soil missingness stated as {shown}")

for design, r2, rmse in [("random", "+0.265", "1,486"), ("cluster", "+0.177", "1,578"),
                         ("country", "-1.943", "2,284")]:
    check(f"{rep['results'][design]['r2_log']:+.3f}" == r2, f"{design} R2 matches record ({r2})")
    check(f"{rep['results'][design]['rmse_kg_ha']:,.0f}" == rmse, f"{design} RMSE matches record ({rmse})")
    check(r2 in flat and rmse in flat, f"{design} figures appear in the document")

check(f"{rep['inflation']['cluster']:+.3f}" == "+0.088" and "+0.088" in flat, "cluster inflation +0.088")
check(f"{rep['inflation']['country']:+.3f}" == "+2.208" and "+2.208" in flat, "country inflation +2.208")
check("-0.925" in flat, "superseded global-imputation value reported transparently")
check("f305a3d3e48015bd877dc9df5c53b1715c61f940d58383d57d4dfb68c59c6ff0" in flat,
      "data checksum recorded")

# ---------------------------------------------------------------- pass 3 -----
print("\nPASS 3 - claim hygiene and guideline coverage")
for phrase, why in {
    "central zambia is the primary case": "old single-country framing",
    "has not been downloaded or audited": "superseded data-status statement",
    "proven novelty": "overclaim",
    "new framework": "overclaim",
    "guarantees coverage": "overclaim",
    "superior": "unqualified superiority claim",
}.items():
    check(phrase not in flat.lower(), f"no superseded/overclaiming phrase: {why}")

for phrase, why in {
    "cc by 4.0": "licence stated",
    "doi:10.5281/zenodo.11122388": "dataset DOI stated",
    "appendix a": "code appendix promised",
    "appendix b": "user manual promised",
    "45–60 pages": "report length rule acknowledged",
    "out of scope": "scope boundary drawn",
    "not a new algorithm": "contribution bounded",
    "harvard": "referencing style named",
    "preliminary": "unverified numbers labelled preliminary",
    "moderation": "",
}.items():
    if phrase == "moderation":
        continue
    check(phrase in flat.lower(), f"{why} ('{phrase}')")

refs = [p for p in paragraphs if re.match(r"^[A-Z][\w'\-]+,\s", p.text.strip())
        and "(20" in p.text]
check(len(refs) >= 9, f"{len(refs)} Harvard-style references listed")

# ---------------------------------------------------------------- pass 4 -----
print("\nPASS 4 - layout")
for i, tbl in enumerate(doc.tables):
    widths = [c.width for c in tbl.rows[0].cells]
    check(all(w is not None for w in widths), f"table {i+1}: explicit column widths")
    total = sum(w.cm for w in widths)
    check(total <= 16.05, f"table {i+1}: total width {total:.2f} cm fits the 16.0 cm text block")

hanging = [p for p in refs if p.paragraph_format.first_line_indent is not None
           and p.paragraph_format.first_line_indent.cm < 0]
check(len(hanging) == len(refs), f"all {len(refs)} references use a hanging indent")

for placeholder in ["[Student name] [Registration number]", "[Supervisor name]",
                    "[To be completed by the candidate"]:
    if placeholder in flat:
        notes.append(f"placeholder left for the candidate: {placeholder}")

print("\n" + "=" * 60)
print(f"{len(failures)} failures")
for note in notes:
    print(f"NOTE  {note}")
sys.exit(1 if failures else 0)
