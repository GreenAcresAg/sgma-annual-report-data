#!/usr/bin/env python3
"""Extract subsidence benchmark data from GSA annual report PDFs (Appendix E, Table E-1).

DWR's central export has no benchmark measurements for several subbasins (e.g. Tulare Lake).
The values live only inside each annual report's "Land Subsidence RMS Monitoring Network" table
(Appendix E, Table E-1), which gives per-benchmark **annual Fall-to-Fall displacement (feet)**.
This script pulls that table out of each report PDF (structured table extraction) and consolidates
it long-format across reporting years.

Usage: download the annual report PDFs from the SGMA portal
  (https://sgma.water.ca.gov/portal/service/gspar/document/<id>), then:
    python3 extract_ar_benchmarks.py <report_year>=<file.pdf> [<report_year>=<file.pdf> ...]
  e.g.  python3 extract_ar_benchmarks.py WY2024=/tmp/ar477docs/4886.bin

Writes:
  data/benchmark_displacement_annual.csv  — long: report_year, GSA, station_id, lat, lon,
                                            station_type, period, displacement_ft
Survey basis: values are ANNUAL Fall-to-Fall vertical displacement (feet); benchmark = releveling
to a survey monument, "Continuous GPS" = CGPS-derived. See SURVEY_BASIS.md.
"""
import csv, os, re, sys
import fitz  # PyMuPDF

DATA = os.path.join(os.path.dirname(__file__), "data")
OUT = os.path.join(DATA, "benchmark_displacement_annual.csv")
# Header signature that identifies the Land Subsidence RMS table (Table E-1).
HDR = re.compile(r"subsidence\s*rms|land subsidence rms", re.I)
PERIOD_COL = re.compile(r"fall\s*\d{4}.*fall\s*\d{4}|20\d\d.*20\d\d", re.I)
NUM = re.compile(r"^[+-]?\d+(\.\d+)?$")


def num_or_none(v):
    v = (v or "").strip().replace("+", "")
    return v if NUM.match(v) else None   # keep as string; "Missing data" -> None


def extract_report(report_year, pdf_path):
    doc = fitz.open(pdf_path)
    rows = []
    for page in doc:
        for tab in page.find_tables().tables:
            data = tab.extract()
            if not data or len(data) < 2:
                continue
            hdr = [(c or "").replace("\n", " ").strip() for c in data[0]]
            if not any(HDR.search(h) for h in hdr):
                continue
            # locate columns
            def find(*keys):
                for i, h in enumerate(hdr):
                    if any(k in h.lower() for k in keys):
                        return i
                return None
            ci_gsa = find("gsa")
            ci_id = find("station id", "rms station", "station")
            ci_lat = find("latitude"); ci_lon = find("longitude")
            ci_type = find("station type", "type")
            # value (period) columns = any header naming two years / "fall .. fall"
            period_cols = [i for i, h in enumerate(hdr) if PERIOD_COL.search(h)]
            if ci_id is None or not period_cols:
                continue
            gsa = ""
            for r in data[1:]:
                r = [(c or "").replace("\n", " ").strip() for c in r]
                if ci_gsa is not None and r[ci_gsa]:
                    gsa = r[ci_gsa]            # GSA cells are merged; carry down
                sid = r[ci_id] if ci_id < len(r) else ""
                if not sid or sid.lower().startswith(("subsidence", "station")):
                    continue
                for pc in period_cols:
                    val = num_or_none(r[pc]) if pc < len(r) else None
                    rows.append({
                        "report_year": report_year, "GSA": gsa, "station_id": sid,
                        "latitude": r[ci_lat] if ci_lat is not None and ci_lat < len(r) else "",
                        "longitude": r[ci_lon] if ci_lon is not None and ci_lon < len(r) else "",
                        "station_type": r[ci_type] if ci_type is not None and ci_type < len(r) else "",
                        "period": hdr[pc], "displacement_ft": val,
                    })
            print(f"  {report_year} p{page.number}: Table E-1 -> {len(data)-1} stations, "
                  f"{len(period_cols)} period column(s)")
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    all_rows = []
    for arg in sys.argv[1:]:
        year, _, path = arg.partition("=")
        if not os.path.exists(path):
            print(f"  {year}: file not found: {path}"); continue
        all_rows += extract_report(year, path)
    os.makedirs(DATA, exist_ok=True)
    cols = ["report_year", "GSA", "station_id", "latitude", "longitude",
            "station_type", "period", "displacement_ft"]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(all_rows)
    with_val = sum(1 for r in all_rows if r["displacement_ft"] is not None)
    print(f"wrote {len(all_rows)} rows ({with_val} with a value) -> {os.path.basename(OUT)}")
