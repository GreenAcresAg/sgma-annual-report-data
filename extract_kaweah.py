#!/usr/bin/env python3
"""Clean, targeted extractor for the Kaweah Subbasin annual-report subsidence table.

The Kaweah annual reports (Provost & Pritchard) tabulate subsidence in Chapter 5 as:

  Subsidence Monitoring Station | Responsible Agency | MT | MO | 20YY Elevation (x3) |
  WYYYYY Subsidence (ft) | Cumulative Subsidence (ft)

- Per-benchmark ground-surface **elevations** at ~3 epochs (ft), an **annual** subsidence and a
  **cumulative** subsidence (both feet, POSITIVE = subsidence / elevation loss).
- MT / MO are Sustainable Management Criteria (minimum threshold / measurable objective), NOT
  measurements — excluded.

The generic extract_ar_benchmarks.py mangled this table (grabbed MT/MO, bled elevations into the
lat column). This script maps columns by header name so the values stay put, and REPLACES any
existing Kaweah rows in the consolidated CSV.

Usage:  python3 extract_kaweah.py WY2023=/path/50221_WY_2023.pdf WY2024=/path/502211_WY_2024.pdf ...
Writes data/benchmark_displacement_annual.csv (schema shared with the other extractors). No
coordinates (the report has none) — the map sources them by name-match.
"""
import csv, os, re, sys
import fitz

DATA = os.path.join(os.path.dirname(__file__), "data")
OUT = os.path.join(DATA, "benchmark_displacement_annual.csv")
SUBBASIN = "Kaweah"
COLS = ["report_year", "subbasin", "GSA", "station_id", "latitude", "longitude",
        "station_type", "metric", "value"]
NUM = re.compile(r"^-?\d+(\.\d+)?$")
STATION_HDR = re.compile(r"subsidence\s+monitoring\s+station", re.I)
ELEV_HDR = re.compile(r"(20\d\d)\s*Elevation", re.I)
ANN_HDR = re.compile(r"WY\s*(20\d\d)\s*Subsidence", re.I)
CUM_HDR = re.compile(r"Cumulative\s*Subsidence", re.I)
STATION_ID = re.compile(r"^[A-Z]{1,3}\s?\d{1,4}[A-Z]?\d?$|^[A-Za-z].*(Check|Bridge|Well)", re.I)


def val_at(row, i):
    """Value at header column i, tolerating one-cell spacer drift; '-' / '' -> None."""
    for j in (i, i + 1):
        if 0 <= j < len(row):
            c = (row[j] or "").replace("\n", " ").strip()
            if c and c != "-":
                return c if NUM.match(c) else (None if c in ("-", "") else c)
    return None


def extract(report_year, pdf_path):
    doc = fitz.open(pdf_path)
    rows, seen_station = [], set()
    for page in doc:
        for tab in page.find_tables().tables:
            d = tab.extract()
            if not d or len(d) < 3:
                continue
            hdr = [(c or "").replace("\n", " ").strip() for c in d[0]]
            ci_station = next((i for i, h in enumerate(hdr) if STATION_HDR.search(h)), None)
            if ci_station is None:
                continue
            elev_cols = [(i, ELEV_HDR.search(h).group(1)) for i, h in enumerate(hdr) if ELEV_HDR.search(h)]
            ann = next(((i, ANN_HDR.search(h).group(1)) for i, h in enumerate(hdr) if ANN_HDR.search(h)), None)
            cum = next((i for i, h in enumerate(hdr) if CUM_HDR.search(h)), None)
            if not elev_cols and ann is None and cum is None:
                continue
            n = 0
            for r in d[1:]:
                r = [(c or "").replace("\n", " ").strip() for c in r]
                sid = next((r[j] for j in (ci_station, ci_station + 1)
                            if j < len(r) and r[j]), "")
                if not sid or not STATION_ID.match(sid) or sid in seen_station:
                    continue
                seen_station.add(sid); n += 1
                out = []
                for ci, yr in elev_cols:
                    out.append((f"{yr} Elevation (ft)", val_at(r, ci)))
                if ann is not None:
                    out.append((f"WY{ann[1]} Subsidence (ft)", val_at(r, ann[0])))
                if cum is not None:
                    out.append(("Cumulative Subsidence (ft)", val_at(r, cum)))
                for metric, value in out:
                    v = value if (value and NUM.match(str(value))) else ""
                    # subsidence/cumulative are a few feet at most; a large value is an elevation
                    # that drifted into the cell (irregular rows) — drop it.
                    if v and "Subsidence" in metric and abs(float(v)) > 10:
                        v = ""
                    rows.append({"report_year": report_year, "subbasin": SUBBASIN, "GSA": "",
                                 "station_id": sid, "latitude": "", "longitude": "",
                                 "station_type": "benchmark surveyed", "metric": metric, "value": v})
            print(f"  {report_year} p{page.number + 1}: {n} stations "
                  f"({len(elev_cols)} elev cols, ann={'Y' if ann else 'N'}, cum={'Y' if cum is not None else 'N'})")
    doc.close()
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    new = []
    for arg in sys.argv[1:]:
        year, _, path = arg.partition("=")
        if not os.path.exists(path):
            print(f"  file not found: {path}"); continue
        new += extract(year, path)
    # Replace existing Kaweah rows; keep everyone else, then append clean Kaweah.
    keep = [r for r in csv.DictReader(open(OUT))] if os.path.exists(OUT) else []
    keep = [r for r in keep if r["subbasin"] != SUBBASIN]
    all_rows = keep + new
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader(); w.writerows(all_rows)  # run stamp_sources.py after to (re)apply provenance
    wv = sum(1 for r in new if r["value"] not in ("", None))
    print(f"replaced Kaweah: {len(new)} rows ({wv} with a value); CSV now {len(all_rows)} rows.")
