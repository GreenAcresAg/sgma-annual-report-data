#!/usr/bin/env python3
"""Stamp source_doc + source_ref (canonical GSP/report name + page) onto the benchmark dataset.

Every value must be human-verifiable: which document (name + version) and page it came from — the
documents live in the shared Drive (see docs/SOURCE_REFERENCING.md). The benchmark extractors write
only the raw columns, so run this AFTER any extraction to (re)apply provenance from the
(subbasin, report_year) mapping below. Keep this mapping in sync with docs/source_documents.csv.
"""
import csv, os

DATA = os.path.join(os.path.dirname(__file__), "data")
OUT = os.path.join(DATA, "benchmark_displacement_annual.csv")

# subbasin -> canonical annual-report name template (%s = report_year)
DOC = {"Tulare Lake": "Tulare Lake Subbasin Annual Report %s",
       "Kaweah": "Kaweah Subbasin Annual Report %s",
       "Tule": "Tule Subbasin Annual Report %s",
       "Westside": "Westside Subbasin Annual Report %s"}

# (subbasin, report_year) -> where in that document (table + page)
REF = {
    ("Tulare Lake", "WY2020"): "Fig F-1 subsidence map p502",
    ("Tulare Lake", "WY2021"): "WY21 measurement figs pp463-465",
    ("Tulare Lake", "WY2022"): "WY22/WY21 measurement figs pp57-59",
    ("Tulare Lake", "WY2023"): "Fall-to-Fall Table E-1 p199",
    ("Tulare Lake", "WY2024"): "Fall-to-Fall Table E-1",
    ("Tulare Lake", "WY2025"): "Fall-to-Fall Table E-1 p235",
    ("Kaweah", "WY2023"): "subsidence table pp54-56",
    ("Kaweah", "WY2024"): "subsidence table pp54-56",
    ("Kaweah", "WY2025"): "subsidence table pp45-47",
    ("Tule", "WY2024"): "Benchmark Name table p430",
    ("Tule", "WY2025"): "SMC table pp61-70; RMS GSE appendix p510; "
                        "L-coords via Tule Subbasin GSP LTRID Table 4-4 p278",
    ("Westside", "WY2025"): "Annual Report Table 5-5 pp52-53 (rates); "
                           "coords via Westside Subbasin GSP Table 3-15 p361",
}


def main():
    rows = list(csv.DictReader(open(OUT)))
    cols = [c for c in rows[0] if c not in ("source_doc", "source_ref")] + ["source_doc", "source_ref"]
    n = 0
    for r in rows:
        sub, yr = r["subbasin"], r["report_year"]
        r["source_doc"] = (DOC[sub] % yr) if sub in DOC else yr
        r["source_ref"] = REF.get((sub, yr), "")
        if r["source_ref"]:
            n += 1
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"stamped source_doc + source_ref on {len(rows)} rows ({n} with a page ref).")


if __name__ == "__main__":
    main()
