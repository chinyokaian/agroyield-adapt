"""Remove records that the agronomic rule should have caught, and correct the counts.

The first screen keyed on the word "yield", which let through biochar, biogas,
electricity and sea-ice studies. This applies the corrected rule to the saved
corpus and records the correction, rather than leaving inflated counts in place.
"""

from __future__ import annotations

import json
import re

OUT = "docs/litreview"
OFF_TOPIC = re.compile(
    r"biochar|pyrolysis|electricity|spot price|biogas|anaerobic digest|sea ice|"
    r"occupanc|building|land-?use transitions|mesoscale carbon dioxide", re.I)

data = json.load(open(f"{OUT}/corpus.json", encoding="utf-8"))
counts = json.load(open(f"{OUT}/prisma_counts.json", encoding="utf-8"))

kept, dropped = [], []
for r in data["corpus"]:
    if OFF_TOPIC.search(r["title"]):
        dropped.append(r)
    else:
        kept.append(r)

data["corpus"] = kept
existing = data.get("excluded") or []
existing += [{"title": r["title"], "reason": "outside scope: non-agronomic outcome (rule corrected)"}
             for r in dropped]
data["excluded"] = existing
json.dump(data, open(f"{OUT}/corpus.json", "w", encoding="utf-8"), indent=1)

counts["excluded_screening"] = counts["excluded_screening"] + len(dropped)
counts["met_criteria"] = counts["met_criteria"] - len(dropped)
counts["corpus"] = len(kept)
counts["correction"] = (f"{len(dropped)} records removed after re-applying the agronomic "
                        "criterion; the first screen keyed on the word 'yield'")
json.dump(counts, open(f"{OUT}/prisma_counts.json", "w", encoding="utf-8"), indent=1)

print(f"dropped {len(dropped)} off-topic records:")
for r in dropped:
    print("   -", r["title"].encode("ascii", "replace").decode()[:80])
print(f"corpus now {len(kept)}; screened-out now {counts['excluded_screening']}; "
      f"met criteria now {counts['met_criteria']}")
