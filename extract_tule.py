#!/usr/bin/env python3
"""Clean extractor for the Tule Subbasin benchmark leveling tables.

The Tule coordinated annual report publishes its physical benchmark network per-benchmark, but the
table layout changed between report years — this handles both:

  (A) WY2024 ("Benchmark Name" table): Benchmark Name, Owner, Latitude, Longitude, per-year
      Measurement Date + Elevation (ft amsl), annual Subsidence (ft).
  (B) WY2025 detailed appendix ("RMS Benchmark" + "Ground Surface Elevation" with a 2nd header row
      of bare years 2020/2023/2024/2025) — ~19 benchmarks, parsed via find_tables.
  (C) WY2025 SMC compliance table (Site | July 2020 | July 2025 | Difference | InSAR | MO/MT).
      find_tables mangles it, so this is parsed by WORD POSITION: benchmark rows anchored by the id
      token's y, numeric tokens binned to their nearest header column by x (InSAR/MO/MT columns act
      as decoy anchors). No coordinates in WY2025 (name-match to WY2024 for those).

Usage: python3 extract_tule.py <report.pdf>[:firstpage-lastpage] [<report.pdf>[:range] ...]
The optional 1-indexed :page-range skips a full-document scan (these PDFs are 500-680 pp). Rows for
each extracted report_year REPLACE any existing Tule rows for that year; other Tule years are kept.
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


# Physical benchmark id, e.g. E0035_B_RMS / E0056_G_FKC / P0096_B_LSMA. Full-match rejects InSAR
# sites (…_InSAR) and rows where find_tables merged the whole line into the id cell.
BM_ID = re.compile(r"[A-Z]{1,2}\d{3,4}_[A-Z]_(RMS|FKC|LSMA)")


def table_benchmark_name(ex, yr):
    """Format A — WY2024 'Benchmark Name' table (with coords + per-year elevation/subsidence)."""
    hdr = [(c or "").replace("\n", " ").strip() for c in ex[0]]
    if not any("benchmark name" in h.lower() for h in hdr):
        return None

    def col(key):
        return next((i for i, h in enumerate(hdr) if key in h.lower()), None)
    ci_name, ci_own = col("benchmark name"), col("owner")
    ci_lat, ci_lon = col("latitude"), col("longitude")
    val_cols = [i for i, h in enumerate(hdr) if VAL_HDR.search(h)]
    rows = []
    for r in ex[1:]:
        r = [(c or "").replace("\n", " ").strip() for c in r]
        name = r[ci_name] if ci_name is not None and ci_name < len(r) else ""
        if not name or "benchmark" in name.lower():
            continue
        for vc in val_cols:
            rows.append({"report_year": yr, "subbasin": "Tule",
                         "GSA": r[ci_own] if ci_own is not None and ci_own < len(r) else "",
                         "station_id": name,
                         "latitude": r[ci_lat] if ci_lat is not None and ci_lat < len(r) else "",
                         "longitude": r[ci_lon] if ci_lon is not None and ci_lon < len(r) else "",
                         "station_type": "benchmark surveyed",
                         "metric": hdr[vc], "value": num(r[vc]) if vc < len(r) else None})
    return rows


def table_rms_gse(ex, yr):
    """Format B — WY2025 'RMS Benchmark' + 'Ground Surface Elevation' table, years in a 2nd header
    row (2020/2023/2024/2025). Skip the SMC/criteria variant (its year row reads '2025 Survey')."""
    row0 = " ".join((c or "") for c in ex[0]).lower()
    if "rms benchmark" not in row0 or "ground surface elevation" not in row0:
        return None
    # find the header row that lists bare years, map column -> year
    year_cols = {}
    for r in ex[:6]:
        cand = {i: c.strip() for i, c in enumerate((x or "").strip() for x in r)
                if re.fullmatch(r"20\d\d", (c or "").strip())}
        if len(cand) > len(year_cols):
            year_cols = cand
    if len(year_cols) < 2:
        return None
    rows = []
    for r in ex:
        cells = [(c or "").replace("\n", " ").strip() for c in r]
        sid = cells[0] if cells else ""
        if not BM_ID.fullmatch(sid):
            continue
        for ci, yv in year_cols.items():
            rows.append({"report_year": yr, "subbasin": "Tule", "GSA": "", "station_id": sid,
                         "latitude": "", "longitude": "", "station_type": "benchmark surveyed",
                         "metric": f"{yv} Elevation (ft amsl)",
                         "value": num(cells[ci]) if ci < len(cells) else None})
    return rows


def parse_smc_words(page, yr):
    """Word-position parser for the WY2025 SMC table — find_tables merges its rows, so instead we
    anchor each benchmark row by the id token's y and bin every numeric token to its nearest header
    column by x. We keep only the 'July 2020' / 'July 2025' benchmark-elevation and 'Difference'
    columns; the InSAR and MO/MT columns are separate anchors that harmlessly absorb their values."""
    words = page.get_text("words")   # (x0, y0, x1, y1, text, ...)
    julys = sorted((w for w in words if w[4].strip() == "July"), key=lambda w: w[0])
    diffs = [w for w in words if w[4].startswith("Difference")]
    if len(julys) < 2 or not diffs:
        return None
    x20, x25, xd = julys[0][0], julys[1][0], diffs[0][0]
    # target columns + distractor anchors (InSAR / MO / MT) so their values don't bleed in
    anchors = [(x20, "2020 Elevation (ft amsl)"), (x25, "2025 Elevation (ft amsl)"),
               (xd, "2020 to 2025 Subsidence (ft)")]
    for w in words:
        if w[1] < 200 and re.fullmatch(r"Jan|Oct|Measurable|Minimum|Allowable", w[4].strip()):
            anchors.append((w[0], None))
    rows = []
    for idw in (w for w in words if BM_ID.fullmatch(w[4])):
        yc = (idw[1] + idw[3]) / 2
        line = [w for w in words if abs((w[1] + w[3]) / 2 - yc) < 4 and NUM.match(w[4])]
        picked = {}
        for w in line:
            xc = (w[0] + w[2]) / 2
            metric = min(anchors, key=lambda a: abs(a[0] - xc))[1]
            if not metric or metric in picked:
                continue
            v = float(w[4])
            ok = (50 <= v <= 700) if "Elevation" in metric else (-6 <= v <= 20)
            if ok:                     # guard against a neighbouring column's value bleeding in
                picked[metric] = w[4]
        for metric, value in picked.items():
            rows.append({"report_year": yr, "subbasin": "Tule", "GSA": "", "station_id": idw[4],
                         "latitude": "", "longitude": "", "station_type": "benchmark surveyed",
                         "metric": metric, "value": value})
    return rows or None


def extract(pdf, page_range=None):
    doc = fitz.open(pdf)
    yr = report_year(doc)
    lo, hi = (page_range or (1, len(doc)))
    rows, nbm = [], set()
    for pg in range(lo - 1, min(hi, len(doc))):
        page = doc[pg]
        got = parse_smc_words(page, yr)      # word-based: the SMC table find_tables can't segment
        if not got:
            for tab in page.find_tables().tables:
                ex = tab.extract()
                if ex and len(ex) >= 3:
                    got = (table_benchmark_name(ex, yr) or table_rms_gse(ex, yr))
                    if got:
                        break
        if got:
            rows += got
            for r in got:
                nbm.add(r["station_id"])
            print(f"  {yr} p{pg + 1}: -> {len({r['station_id'] for r in got})} benchmarks")
    doc.close()
    print(f"  {yr}: {len(nbm)} benchmarks total")
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    new = []
    for arg in sys.argv[1:]:
        path, _, rng = arg.partition(":")
        pr = None
        if rng:
            a, _, b = rng.partition("-")
            pr = (int(a), int(b or a))
        if os.path.exists(path):
            new += extract(path, pr)
        else:
            print(f"  missing: {path}")
    seen, tule = set(), []
    for r in new:
        k = (r["report_year"], r["station_id"], r["metric"])
        if k not in seen:
            seen.add(k); tule.append(r)
    # Replace only the Tule report_years we just extracted; keep everything else (incl. other years).
    years = {r["report_year"] for r in tule}
    prev = list(csv.DictReader(open(OUT))) if os.path.exists(OUT) else []
    keep = [r for r in prev if not (r.get("subbasin") == "Tule" and r.get("report_year") in years)]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader(); w.writerows(keep + tule)
    print(f"Tule: replaced years {sorted(years)} -> {len(tule)} rows "
          f"({len({r['station_id'] for r in tule})} benchmarks). CSV total now {len(keep)+len(tule)} rows.")
