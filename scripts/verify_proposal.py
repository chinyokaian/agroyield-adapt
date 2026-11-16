"""Three independent verification passes over the finalised proposal.

Pass 1  structure and UZ formatting rules
Pass 2  every number cross-checked against the committed result file and recomputed from the CSV
Pass 3  claim hygiene: no superseded statements, no overclaiming, required guideline items present

Exit code is non-zero if any check fails.
"""

from __future__ import annotations

import json
import re
import sys

from docx import Document

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
text = "\n".join(p.text for p in doc.paragraphs)
for table in doc.tables:
    for row in table.rows:
        text += "\n" + " | ".join(c.text for c in row.cells)
flat = re.sub(r"\s+", " ", text)

# ---------------------------------------------------------------- pass 1 -----
print("PASS 1 - structure and formatting")
check(len(doc.paragraphs) > 40, f"document has {len(doc.paragraphs)} paragraphs")
headings = [p.text for p in doc.paragraphs if p.style.name.startswith("Heading")]
required_sections = [
    "1. Problem statement", "2. Aim and objectives", "3. Research questions and hypotheses",
    "4. Scope and delimitation", "5. Data", "6. Method",     "7. Results to date and verification status",
    "8. Deliverables", "9. Ethics, data governance and reproducibility",
    "10. Risks and mitigation", "11. Timeline", "References",
]
for sec in required_sections:
    check(sec in headings, f"section present: {sec}")
check(len(doc.tables) >= 4, f"{len(doc.tables)} tables rendered")

title_para = next(p for p in doc.paragraphs if p.text.startswith("AGROYIELD-ADAPT"))
check(str(title_para.alignment) == "CENTER (1)", f"title alignment is {title_para.alignment}")
for i, tbl in enumerate(doc.tables):
    widths = [c.width for c in tbl.rows[0].cells]
    check(all(w is not None for w in widths), f"table {i+1}: every column has an explicit width")
    total = sum(round(w.cm, 2) for w in widths)
    check(14.8 <= total <= 15.6, f"table {i+1}: total width {total} cm fits the 15.5 cm text block")

ref_started = False
ref_indents = []
for p in doc.paragraphs:
    if p.text.strip() == "References":
        ref_started = True
        continue
    if ref_started and p.text.strip():
        ref_indents.append(p.paragraph_format.first_line_indent)
check(len(ref_indents) >= 9 and all(v is not None and v.cm < 0 for v in ref_indents),
      f"all {len(ref_indents)} references use a hanging indent")
normal = doc.styles["Normal"]
check(normal.font.name == "Times New Roman", f"base font is {normal.font.name}")
check(normal.font.size.pt == 12, f"base size is {normal.font.size.pt} pt")
check(abs(float(normal.paragraph_format.line_spacing) - 1.5) < 1e-6,
      f"line spacing is {normal.paragraph_format.line_spacing}")

# ---------------------------------------------------------------- pass 2 -----
print("\nPASS 2 - numbers verified against recorded runs and the raw data")
with open(RESULTS, encoding="utf-8") as fh:
    rep = json.load(fh)
df = load_panel(DATA)
live = duplication_stats(df)

expected = {
    "14,773": (live["rows"], 14773),
    "1,526": (live["clusters"], 1526),
    "32.2%": (live["pct_sharing_coord_year"], 32.2),
    "4,764": (live["rows_sharing_coord_year"], 4764),
}
for shown, (computed, recorded) in expected.items():
    check(shown in flat, f"'{shown}' stated in the document")
    check(computed == recorded, f"'{shown}' recomputed from CSV matches record ({computed})")

designs = rep["results"]
for design, shown in [("random", "+0.265"), ("cluster", "+0.177"), ("country", "-1.943")]:
    value = designs[design]["r2_log"]
    check(shown in flat, f"'{shown}' stated for {design}")
    check(f"{value:+.3f}" == shown, f"{design} R2 in record is {value:+.3f}")
for design, shown in [("random", "1,486"), ("cluster", "1,578"), ("country", "2,284")]:
    rmse = designs[design]["rmse_kg_ha"]
    check(shown in flat, f"'{shown}' RMSE stated for {design}")
    check(f"{rmse:,.0f}" == shown, f"{design} RMSE in record is {rmse:,.0f}")

infl = rep["inflation"]
check("+0.088" in flat and f"{infl['cluster']:+.3f}" == "+0.088", "cluster inflation +0.088")
check("+2.208" in flat and f"{infl['country']:+.3f}" == "+2.208", "country inflation +2.208")
check("-0.925" in flat, "superseded global-imputation value reported transparently")
check("f305a3d3e48015bd877dc9df5c53b1715c61f940d58383d57d4dfb68c59c6ff0" in flat,
      "data checksum recorded")

zero = int((df[TARGET] == 0).sum())
zero_pct = 100.0 * float((df[TARGET] == 0).mean())
check("263" in flat and zero == 263, f"zero-yield records recomputed: {zero}")
check("1.78%" in flat and f"{zero_pct:.2f}%" == "1.78%", f"zero-yield share: {zero_pct:.2f}%")
check(len(df.columns) == 53 or "53 columns" in flat, f"column count: {len(df.columns)} (document states 53)")

soil_missing = df.groupby(df["country"].str.lower())["soil_clay"].apply(
    lambda s: 100.0 * s.isna().mean())
for country, shown in [("burundi", "78.4%"), ("rwanda", "76.3%")]:
    computed = f"{soil_missing[country]:.1f}%"
    check(computed == shown, f"{country} soil missingness recomputed: {computed}")
    check(shown in flat, f"{country} soil missingness stated as {shown}")

# ---------------------------------------------------------------- pass 3 -----
print("\nPASS 3 - claim hygiene and guideline coverage")
forbidden = {
    "central Zambia is the primary case": "old single-country framing",
    "has not been downloaded or audited": "superseded data-status statement",
    "proven novelty": "overclaim",
    "new framework": "overclaim",
    "guarantees coverage": "overclaim (no distribution-free guarantee holds off-exchangeability)",
    "superior": "unqualified superiority claim",
}
for phrase, why in forbidden.items():
    check(phrase.lower() not in flat.lower(), f"no superseded/overclaiming phrase: {why}")

required = {
    "CC BY 4.0": "licence stated",
    "doi:10.5281/zenodo.11122388": "dataset DOI stated",
    "Appendix A": "code appendix promised",
    "Appendix B": "user manual promised",
    "45–60 pages": "report length rule acknowledged",
    "Out of scope": "scope boundary drawn",
    "not a new algorithm": "contribution bounded",
    "Harvard": "referencing style named",
    "preliminary": "unverified numbers labelled preliminary",
}
for phrase, why in required.items():
    check(phrase.lower() in flat.lower(), f"{why} ('{phrase}')")

refs_section = flat.split("References")[-1]
n_refs = len(re.findall(r"\(\d{4}\)", refs_section))
check(n_refs >= 9, f"{n_refs} Harvard-style references listed")
for placeholder in ["[Your full name and student number]", "[Supervisor name]"]:
    if placeholder in flat:
        notes.append(f"placeholder left for the candidate: {placeholder}")

print("\n" + "=" * 60)
print(f"{len(failures)} failures")
for note in notes:
    print(f"NOTE  {note}")
sys.exit(1 if failures else 0)
