"""Try every available open-access location for each corpus record."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request

OUT = "docs/litreview"
PAPERS = "papers"
os.makedirs(PAPERS, exist_ok=True)
UA = {"User-Agent": "agroyield-litreview (chinyokaian@users.noreply.github.com)"}

data = json.load(open(f"{OUT}/corpus.json", encoding="utf-8"))
corpus = data["corpus"]


def locations(record: dict) -> list[str]:
    urls = []
    if record.get("pdf_url"):
        urls.append(record["pdf_url"])
    oa = record.get("oa_url") or ""
    if oa:
        urls.append(oa)
    # OpenAlex keeps an alternative list per work; re-fetch it for this id.
    try:
        url = f"https://api.openalex.org/works/{record['openalex_id'].split('/')[-1]}?mailto=chinyokaian@users.noreply.github.com"
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            w = json.load(r)
        for loc in w.get("locations") or []:
            if loc.get("pdf_url"):
                urls.append(loc["pdf_url"])
    except Exception:
        pass
    seen, clean = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            clean.append(u)
    return clean


def slug(record: dict) -> str:
    first = (record["authors"][0].split()[-1] if record["authors"] else "anon").lower()
    first = re.sub(r"[^a-z]", "", first) or "anon"
    title = re.sub(r"[^a-z0-9]+", "-", record["title"].lower())[:50].strip("-")
    return f"{record['year']}_{first}_{title}.pdf"


got, missed = [], []
for i, rec in enumerate(corpus, 1):
    path = os.path.join(PAPERS, slug(rec))
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        got.append(rec["title"])
        rec["pdf_file"] = os.path.basename(path)
        continue
    saved = False
    for url in locations(rec):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as resp:
                ctype = resp.headers.get("Content-Type", "")
                blob = resp.read(6_000_000)
            if blob[:4] == b"%PDF" or "pdf" in ctype.lower():
                if blob[:4] != b"%PDF":
                    continue
                open(path, "wb").write(blob)
                rec["pdf_file"] = os.path.basename(path)
                got.append(rec["title"])
                saved = True
                break
        except Exception:
            continue
    if not saved:
        missed.append(rec)
    if i % 10 == 0:
        print(f"  {i}/{len(corpus)} processed, {len(got)} PDFs so far")

json.dump({"corpus": corpus, "excluded": data.get("excluded", [])},
          open(f"{OUT}/corpus.json", "w", encoding="utf-8"), indent=1)

print(f"\nPDFs on disk: {len(got)}")
print(f"no open-access copy: {len(missed)}")
for rec in missed[:8]:
    print("   -", rec["title"][:70], "|", rec["publisher"])
