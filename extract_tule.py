#!/usr/bin/env python3
"""Clean extractor for the Tule Subbasin benchmark leveling table.

The Tule coordinated annual report (Tule Subbasin TAC) publishes its physical benchmark network
as one well-structured table headed "Benchmark Name" — Benchmark Name, Owner, Latitude, Longitude,
per-year Measurement Date + Elevation (ft amsl), and annual Subsidence (ft). This targets ONLY
that table (ignoring the report's InSAR/threshold summary tables, which are noise for a physical-
benchmark dataset).

Usage: python3 extract_tule.py <tule_report.pdf> [<older_report.pdf> ...]
Replaces existing Tule rows in data/benchmark_displacement_annual.csv with the clean extraction.
"""
import csv, os, re, sys
import fitz

DATA = os.path.join(os.path.dirname(__file__), "data")
OUT = os.path.join(DATA, "benchmark_displacement_annual.csv")
COLS = ["report_year", "subbasin", "GSA", "station_id", "latitude", "longitude",
        "station_type", "metric", "value"]
NUM = re.compile(r"^[+-]?\d+(\.\d+)?$")
VAL_HDR = re.compile(r"elevation|subsidence", re.I)


def num(v):
    v = (v or "").strip().replace("+", "")
    return v if NUM.match(v) else None


def report_year(doc):
    """Tule titles read like 'Tule Subbasin 2023/24 Annual Report' — use the later water year."""
    head = re.sub(r"\s+", " ", " ".join(doc[i].get_text() for i in range(min(3, len(doc)))))
    yy = re.findall(r"20\d\d\s*/\s*(\d\d)\s*Annual Report", head)
    if yy:
        return "WY20" + max(yy)
    m = re.search(r"water\s*year\s*(20\d\d)", head, re.I)
    return "WY" + m.group(1) if m else "WY?"


def extract(pdf):
    doc = fitz.open(pdf)
    yr = report_year(doc)
    rows = []
    for pg in range(len(doc)):
        for tab in doc[pg].find_tables().tables:
            ex = tab.extract()
            if not ex:
                continue
            hdr = [(c or "").replace("\n", " ").strip() for c in ex[0]]
            if not any("benchmark name" in h.lower() for h in hdr):
                continue

            def col(key):
                for i, h in enumerate(hdr):
                    if key in h.lower():
                        return i
                return None
            ci_name, ci_own = col("benchmark name"), col("owner")
            ci_lat, ci_lon = col("latitude"), col("longitude")
            val_cols = [i for i, h in enumerate(hdr) if VAL_HDR.search(h)]
            for r in ex[1:]:
                r = [(c or "").replace("\n", " ").strip() for c in r]
                name = r[ci_name] if ci_name is not None and ci_name < len(r) else ""
                if not name or "benchmark" in name.lower():
                    continue
                for vc in val_cols:
                    rows.append({
                        "report_year": yr, "subbasin": "Tule",
                        "GSA": r[ci_own] if ci_own is not None and ci_own < len(r) else "",
                        "station_id": name,
                        "latitude": r[ci_lat] if ci_lat is not None and ci_lat < len(r) else "",
                        "longitude": r[ci_lon] if ci_lon is not None and ci_lon < len(r) else "",
                        "station_type": "benchmark surveyed",
                        "metric": hdr[vc], "value": num(r[vc]) if vc < len(r) else None,
                    })
            print(f"  {yr} p{pg}: Tule benchmark table -> {len(ex)-1} benchmarks x {len(val_cols)} metrics")
    doc.close()
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    new = []
    for p in sys.argv[1:]:
        if os.path.exists(p):
            new += extract(p)
        else:
            print(f"  missing: {p}")
    # Keep non-Tule rows; replace Tule with the clean extraction (dedup on year+station+metric).
    prev = list(csv.DictReader(open(OUT))) if os.path.exists(OUT) else []
    keep = [r for r in prev if r.get("subbasin") != "Tule"]
    seen, tule = set(), []
    for r in new:
        k = (r["report_year"], r["station_id"], r["metric"])
        if k not in seen:
            seen.add(k); tule.append(r)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader(); w.writerows(keep + tule)
    print(f"Tule: {len(tule)} clean rows ({len({r['station_id'] for r in tule})} benchmarks). "
          f"CSV total now {len(keep)+len(tule)} rows.")
