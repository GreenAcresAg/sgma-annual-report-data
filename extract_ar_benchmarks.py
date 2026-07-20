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
# A table is a subsidence table if any header cell looks subsidence-related.
SUBS_HDR = re.compile(r"subsid|displacement|rms|benchmark", re.I)
# A value column: header names a year, or subsidence/displacement/elevation/cumulative.
VALUE_COL = re.compile(r"\b(19|20)\d\d\b|subsid|displacement|elevation|cumulative|feet|fall", re.I)
# ...but NOT a threshold/criteria/target column (those aren't measurements).
NOISE_COL = re.compile(r"allowable|threshold|minimum|maximum|criteria|objective|measurable|"
                       r"target|interim|\bMT\b|\bMO\b|undesirable", re.I)
# Reject junk station ids (sentence fragments captured as rows).
JUNK_ID = re.compile(r"\b(the|interim|table|figure|note|between|report|see|total|average)\b", re.I)
# Columns that identify the monitoring station.
STATION_COL = re.compile(r"station|site|benchmark|monitor|well|rms\s*id", re.I)
LAT_COL = re.compile(r"lat", re.I); LON_COL = re.compile(r"lon", re.I)
TYPE_COL = re.compile(r"type", re.I); AGENCY_COL = re.compile(r"gsa|agency|responsible", re.I)
SKIP_COL = re.compile(r"responsible|agency|county|comment|note", re.I)
NUM = re.compile(r"^[+-]?\d+(\.\d+)?$")


def num_or_none(v):
    v = (v or "").strip().replace("+", "")
    return v if NUM.match(v) else None   # keep as string; "Missing data" -> None


def detect_year_and_basin(doc):
    """Read the report's water year and subbasin from its first pages."""
    head = re.sub(r"\s+", " ", " ".join(doc[i].get_text() for i in range(min(4, len(doc)))))
    ym = re.search(r"water\s*year\s*(20\d\d)|\bWY[\s-]?(20\d\d)", head, re.I)
    year = "WY" + (ym.group(1) or ym.group(2)) if ym else ""
    bm = re.search(r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,2})\s+Subbasin", head, re.I)
    basin = bm.group(1).strip().title() if bm else ""
    return year, basin


def extract_report(report_year, pdf_path):
    doc = fitz.open(pdf_path)
    auto_year, auto_basin = detect_year_and_basin(doc)
    report_year = report_year or auto_year or "unknown"
    rows = []
    for page in doc:
        for tab in page.find_tables().tables:
            data = tab.extract()
            if not data or len(data) < 3:
                continue
            hdr = [(c or "").replace("\n", " ").strip() for c in data[0]]
            if not any(SUBS_HDR.search(h) for h in hdr):
                continue

            def find(rx):
                for i, h in enumerate(hdr):
                    if rx.search(h):
                        return i
                return None
            # station column = a station-named col, else the first mostly-text column
            ci_id = find(STATION_COL)
            if ci_id is None:
                for i, h in enumerate(hdr):
                    if not SKIP_COL.search(h) and not VALUE_COL.search(h) and not LAT_COL.search(h) and not LON_COL.search(h):
                        ci_id = i; break
            ci_lat = find(LAT_COL); ci_lon = find(LON_COL)
            ci_type = find(TYPE_COL); ci_gsa = find(AGENCY_COL)
            # value columns = header names a metric AND the column actually holds numbers
            value_cols = []
            for i, h in enumerate(hdr):
                if i in (ci_id, ci_lat, ci_lon, ci_type, ci_gsa) or not VALUE_COL.search(h) or NOISE_COL.search(h):
                    continue
                nums = sum(1 for r in data[1:] if i < len(r) and NUM.match((r[i] or "").replace("+", "").strip()))
                if nums >= 2:
                    value_cols.append(i)
            if ci_id is None or not value_cols:
                continue
            gsa = ""
            n_st = 0
            for r in data[1:]:
                r = [(c or "").replace("\n", " ").strip() for c in r]
                if ci_gsa is not None and ci_gsa < len(r) and r[ci_gsa]:
                    gsa = r[ci_gsa]
                sid = r[ci_id] if ci_id < len(r) else ""
                if (not sid or SUBS_HDR.search(sid) or sid.lower() in ("station", "site", "id")
                        or len(sid) > 22 or len(sid.split()) > 3 or JUNK_ID.search(sid)):
                    continue
                n_st += 1
                for vc in value_cols:
                    rows.append({
                        "report_year": report_year, "subbasin": auto_basin, "GSA": gsa, "station_id": sid,
                        "latitude": r[ci_lat] if ci_lat is not None and ci_lat < len(r) else "",
                        "longitude": r[ci_lon] if ci_lon is not None and ci_lon < len(r) else "",
                        "station_type": r[ci_type] if ci_type is not None and ci_type < len(r) else "",
                        "metric": hdr[vc], "value": num_or_none(r[vc]) if vc < len(r) else None,
                    })
            print(f"  {report_year} ({auto_basin}) p{page.number}: subsidence table -> "
                  f"{n_st} stations x {len(value_cols)} metric col(s)")
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    all_rows = []
    # Args: "<year>=<pdf>" (explicit year) or just "<pdf>" (auto-detect year+basin).
    for arg in sys.argv[1:]:
        if "=" in arg and not os.path.exists(arg):
            year, _, path = arg.partition("=")
        else:
            year, path = "", arg
        if not os.path.exists(path):
            print(f"  file not found: {path}"); continue
        all_rows += extract_report(year, path)
    # Append to any existing output so multiple runs accumulate.
    os.makedirs(DATA, exist_ok=True)
    cols = ["report_year", "subbasin", "GSA", "station_id", "latitude", "longitude",
            "station_type", "metric", "value"]
    if os.path.exists(OUT):
        prev = list(csv.DictReader(open(OUT)))
        all_rows = prev + all_rows
    # De-duplicate on (report_year, subbasin, station_id, metric) so re-runs are idempotent.
    seen, deduped = set(), []
    for r in all_rows:
        k = (r["report_year"], r.get("subbasin", ""), r["station_id"], r.get("metric", ""))
        if k not in seen:
            seen.add(k); deduped.append(r)
    all_rows = deduped
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(all_rows)
    with_val = sum(1 for r in all_rows if r.get("value") is not None)
    print(f"wrote {len(all_rows)} rows ({with_val} with a value) -> {os.path.basename(OUT)}")
