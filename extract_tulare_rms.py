#!/usr/bin/env python3
"""Targeted extractor for the Tulare Lake subsidence RMS "Fall-to-Fall" benchmark table.

Precision-focused companion to extract_ar_benchmarks.py. The generic extractor over-captures
(any subsidence/RMS/elevation table), so for the Tulare Lake annual reports we target the ONE
clean table whose header carries a `Subsidence RMS Station ID` column plus one or more
`Fall <yr> to Fall <yr> (feet)` annual-displacement columns (Appendix "Table E-1" style).

Confirmed layouts:
  WY2023 p199: GSA | Subsidence RMS Station ID | Latitude | Longitude | Station Type | 2 Fall cols
  WY2024      : same family (already in the CSV, 38 stations)
  WY2025 p235: GSA | Subsidence RMS Station ID | Latitude | Longitude | 3 Fall cols (no Type col)

Usage:  python3 extract_tulare_rms.py WY2023=/path/2023.pdf WY2025=/path/2025.pdf
Writes/append-dedups into data/benchmark_displacement_annual.csv (same schema/keys as the
generic extractor: report_year, subbasin, GSA, station_id, latitude, longitude, station_type,
metric, value). Idempotent on (report_year, subbasin, station_id, metric).
"""
import csv, os, re, sys
import fitz  # PyMuPDF

DATA = os.path.join(os.path.dirname(__file__), "data")
OUT = os.path.join(DATA, "benchmark_displacement_annual.csv")
SUBBASIN = "Tulare Lake"
FALL = re.compile(r"fall\s*20\d\d\s*to\s*fall\s*20\d\d", re.I)
STID = re.compile(r"subsidence\s*rms\s*station|station\s*id|rms\s*station", re.I)
NUM = re.compile(r"^[+-]?\d+(\.\d+)?$")
COLS = ["report_year", "subbasin", "GSA", "station_id", "latitude", "longitude",
        "station_type", "metric", "value"]


# Annual Fall-to-Fall vertical displacement is realistically within a few feet; anything larger
# is a source typo (e.g. WY2023 S222R prints "-2838") — keep the station row but drop the value.
MAX_ABS_FT = 5.0


def num_or_none(v):
    v = (v or "").strip().replace("+", "")
    if not NUM.match(v):
        return None            # "Missing data" etc.
    return v if abs(float(v)) <= MAX_ABS_FT else None


def find_col(hdr, rx):
    for i, h in enumerate(hdr):
        if rx.search(h):
            return i
    return None


def extract(report_year, pdf_path):
    doc = fitz.open(pdf_path)
    rows, tables = [], 0
    for page in doc:
        for tab in page.find_tables().tables:
            d = tab.extract()
            if not d or len(d) < 3:
                continue
            hdr = [(c or "").replace("\n", " ").strip() for c in d[0]]
            fall_cols = [i for i, h in enumerate(hdr) if FALL.search(h)]
            ci_id = find_col(hdr, STID)
            if not fall_cols or ci_id is None:
                continue  # not THE table
            ci_lat = find_col(hdr, re.compile(r"lat", re.I))
            ci_lon = find_col(hdr, re.compile(r"lon", re.I))
            ci_type = find_col(hdr, re.compile(r"type", re.I))
            ci_gsa = find_col(hdr, re.compile(r"gsa|agency", re.I))
            tables += 1
            gsa, n = "", 0
            for r in d[1:]:
                r = [(c or "").replace("\n", " ").strip() for c in r]
                if ci_gsa is not None and ci_gsa < len(r) and r[ci_gsa]:
                    gsa = r[ci_gsa]
                sid = r[ci_id] if ci_id < len(r) else ""
                if not sid or STID.search(sid) or len(sid) > 22 or len(sid.split()) > 3:
                    continue
                n += 1
                for vc in fall_cols:
                    rows.append({
                        "report_year": report_year, "subbasin": SUBBASIN, "GSA": gsa,
                        "station_id": sid,
                        "latitude": r[ci_lat] if ci_lat is not None and ci_lat < len(r) else "",
                        "longitude": r[ci_lon] if ci_lon is not None and ci_lon < len(r) else "",
                        "station_type": r[ci_type] if ci_type is not None and ci_type < len(r) else "",
                        "metric": hdr[vc] + (" (feet)" if "feet" not in hdr[vc].lower() else ""),
                        "value": num_or_none(r[vc]) if vc < len(r) else None,
                    })
            print(f"  {report_year} p{page.number + 1}: RMS Fall-to-Fall table -> "
                  f"{n} stations x {len(fall_cols)} year-col(s)")
    doc.close()
    if not tables:
        print(f"  {report_year}: no Fall-to-Fall RMS table found")
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    all_rows = []
    for arg in sys.argv[1:]:
        year, _, path = arg.partition("=")
        if not os.path.exists(path):
            print(f"  file not found: {path}"); continue
        all_rows += extract(year, path)
    os.makedirs(DATA, exist_ok=True)
    if os.path.exists(OUT):
        all_rows = list(csv.DictReader(open(OUT))) + all_rows
    seen, deduped = set(), []
    for r in all_rows:
        k = (r["report_year"], r.get("subbasin", ""), r["station_id"], r.get("metric", ""))
        if k not in seen:
            seen.add(k); deduped.append(r)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader(); w.writerows(deduped)  # run stamp_sources.py after to (re)apply provenance
    wv = sum(1 for r in deduped if r.get("value") not in (None, "", "None"))
    print(f"wrote {len(deduped)} rows ({wv} with a value) -> {os.path.basename(OUT)}")
