#!/usr/bin/env python3
"""Catalogue each GSA's total plan area + irrigated acreage from its GSP (page-referenced).

For every GSA-level GSP in the registry (docs/source_documents.csv), pull the GSA's total area and
irrigated acreage with the page they appear on, so the dashboard can normalize metrics by BOTH
total and irrigated acres. Writes gsp/gsa_acreage.csv:
  subbasin, gsa, metric(total_area|irrigated_area), value(acres), page, source_doc, snippet

Usage: python3 extract_gsa_acreage.py <docs_dir_with_pdfs>   (e.g. ~/Downloads)
"""
import csv, os, re, sys
import fitz

HERE = os.path.dirname(__file__)
REG = os.path.join(HERE, "docs", "source_documents.csv")
OUT = os.path.join(HERE, "gsp", "gsa_acreage.csv")

# total plan area: "The X GSA area is 14,491 acres", "encompasses ~/approximately N acres", etc.
TOTAL = re.compile(r"(?:GSA area is|GSA (?:area )?(?:is )?approximately|encompasses|covers(?: approximately)?|"
                   r"plan area (?:is |of )?(?:approximately )?|area of (?:approximately )?)"
                   r"[^.\n]{0,40}?([\d,]{3,7})\s*acres", re.I)
# irrigated acreage: "N acres of irrigated", "irrigated ... N acres", "N irrigated acres"
IRRIG = re.compile(r"([\d,]{3,7})\s*(?:acres of irrigated|irrigated acres)|"
                   r"irrigated[^.\n]{0,40}?([\d,]{3,7})\s*acres", re.I)


def acres(s):
    return int(s.replace(",", ""))


def find(doc, rx, lo=50000, hi=2000000):
    for pg in range(len(doc)):
        t = doc[pg].get_text()
        for m in rx.finditer(t):
            v = next(g for g in m.groups() if g)
            if lo <= acres(v) <= hi:
                snip = re.sub(r"\s+", " ", t[max(0, m.start() - 40):m.end() + 10]).strip()
                return acres(v), pg + 1, snip
    return None, None, None


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads")
    gsps = [r for r in csv.DictReader(open(REG))
            if r["doc_type"] == "GSP" and "Subbasin" not in r["gsa_or_area"]]
    rows = []
    for r in gsps:
        p = os.path.join(src, r["local_filename"])
        if not os.path.exists(p):
            print(f"  missing: {r['local_filename']}"); continue
        doc = fitz.open(p)
        # GSA plan areas are typically a few thousand to ~350k acres
        tot, tpg, tsnip = find(doc, TOTAL, 1000, 400000)
        irr, ipg, isnip = find(doc, IRRIG, 500, 400000)
        doc.close()
        for metric, val, pg, snip in [("total_area", tot, tpg, tsnip), ("irrigated_area", irr, ipg, isnip)]:
            if val:
                rows.append({"subbasin": r["subbasin"], "gsa": r["gsa_or_area"], "metric": metric,
                             "value": val, "page": pg, "source_doc": r["canonical_name"], "snippet": snip})
        print(f"  {r['gsa_or_area']:42s} total={tot} (p{tpg})  irrigated={irr} (p{ipg})")
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["subbasin", "gsa", "metric", "value", "page", "source_doc", "snippet"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote {len(rows)} acreage rows -> {os.path.basename(OUT)}")
