#!/usr/bin/env python3
"""Westside subbasin subsidence benchmarks — coordinates (GSP Table 3-15) + leveling (annual-report
Table 5-5), joined by benchmark id.

Westside's annual report tabulates per-benchmark subsidence as "BM #1–26" (Table 5-5: annual rates
2020→ + cumulative) but with NO coordinates. The coordinates live in the 2025 Westside Subbasin
Amended GSP (LSCE), Table 3-15 "Proposed Monitoring Network for Subsidence" — Site Name / Site Type /
Monitoring Agency / Latitude (NAD83) / Longitude (NAD83) for the whole network (WWD GPS benchmarks,
USBR, DWR/CASP aqueduct benchmarks, UNAVCO CGPS, USGS extensometers).

Usage:
    python3 extract_westside.py "<GSP.pdf>" "<annual_report.pdf>"
Writes:
    data/westside_subsidence_network.csv   — every site: name, site_type, agency, lat, lon
    (Table 5-5 leveling join is added by the annual-report arg when present)
"""
import csv, os, re, sys
import fitz

DATA = os.path.join(os.path.dirname(__file__), "data")
NETCSV = os.path.join(DATA, "westside_subsidence_network.csv")
LAT = re.compile(r"^3[567]\.\d{3,}$")
LON = re.compile(r"^-1(19|20)\.\d{3,}$")


def clean_id(name):
    return re.sub(r"[¹²³\d]$", "", name).strip() if name.endswith(("¹", "²", "³")) else name.strip()


def extract_network(gsp_pdf):
    """Table 3-15 in the GSP: the full subsidence monitoring network with NAD83 coordinates."""
    doc = fitz.open(gsp_pdf)
    rows = []
    for page in doc:
        t = page.get_text()
        if "Proposed Monitoring Network for Subsidence" not in t:
            continue
        for tab in page.find_tables().tables:
            d = tab.extract()
            hdr = " | ".join((c or "") for c in d[0]).lower()
            if "latitude" not in hdr or "site" not in hdr:
                continue
            for r in d[1:]:
                c = [(x or "").replace("\n", " ").strip() for x in r]
                if len(c) < 5:
                    continue
                name, stype, agency, lat, lon = c[0], c[1], c[2], c[3], c[4]
                if not (LAT.match(lat) and LON.match(lon)):
                    continue
                rows.append({"site_name": clean_id(name), "site_type": stype, "agency": agency,
                             "latitude": lat, "longitude": lon,
                             "source_doc": "Westside Subbasin GSP — Amended (LSCE, 2025)",
                             "source_page": "Table 3-15 p361"})
    doc.close()
    return rows


OUT = os.path.join(DATA, "benchmark_displacement_annual.csv")
COLS = ["report_year", "subbasin", "GSA", "station_id", "latitude", "longitude",
        "station_type", "metric", "value"]
NUM = re.compile(r"^-?\d+\.\d+$")


def norm(name):
    return re.sub(r"\s+", " ", (name or "").replace("#", "").replace("¹", "").replace("²", "")).strip().upper()


def extract_leveling(report_pdf):
    """Table 5-5 in the annual report: per-benchmark annual subsidence rate by year (2020→) — the
    'Location' column is the benchmark name (matches Table 3-15). Positive = subsidence."""
    doc = fitz.open(report_pdf)
    rows = {}
    for page in doc:
        if "Annual Rates of Measured Winter/Spring Subsidence" not in page.get_text():
            continue
        for tab in page.find_tables().tables:
            d = tab.extract()
            # year-header row: cells that are a 4-digit year (strip footnote superscript digit)
            year_cols = {}
            for r in d[:6]:
                cand = {}
                for i, c in enumerate((x or "").strip() for x in r):
                    m = re.match(r"^(20\d\d)\d?$", c)
                    if m:
                        cand[i] = int(m.group(1))
                if len(cand) > len(year_cols):
                    year_cols = cand
            if len(year_cols) < 3:
                continue
            for r in d:
                c = [(x or "").replace("\n", " ").strip() for x in r]
                name = c[1] if len(c) > 1 else ""
                if not name or name.lower() in ("location", "") or "subsidence" in name.lower():
                    continue
                rates = {y: c[i] for i, y in year_cols.items() if i < len(c) and NUM.match(c[i])}
                if rates:
                    rows.setdefault(norm(name), (name, {}))[1].update(rates)
    doc.close()
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    net = extract_network(sys.argv[1])
    from collections import Counter
    os.makedirs(DATA, exist_ok=True)
    with open(NETCSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["site_name", "site_type", "agency", "latitude", "longitude",
                                          "source_doc", "source_page"])
        w.writeheader(); w.writerows(net)
    print(f"wrote {len(net)} sites -> {os.path.basename(NETCSV)}")
    print("  by agency:", dict(Counter(r["agency"] for r in net)))

    if len(sys.argv) < 3:
        sys.exit(0)
    lev = extract_leveling(sys.argv[2])
    coords = {norm(r["site_name"]): r for r in net}
    yr = re.search(r"WY_?(\d{4})", sys.argv[2])
    report_year = "WY" + (yr.group(1) if yr else "2025")
    new = []
    joined = 0
    for key, (name, rates) in lev.items():
        c = coords.get(key)
        if not c:
            continue
        joined += 1
        for y, v in sorted(rates.items()):
            new.append({"report_year": report_year, "subbasin": "Westside",
                        "GSA": "Westlands Water District", "station_id": name,
                        "latitude": c["latitude"], "longitude": c["longitude"],
                        "station_type": "benchmark surveyed (GPS)",
                        "metric": f"WY{y} Subsidence Rate (ft)", "value": v})
    prev = [r for r in csv.DictReader(open(OUT))] if os.path.exists(OUT) else []
    keep = [r for r in prev if not (r.get("subbasin") == "Westside" and "Subsidence Rate" in r.get("metric", ""))]
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader(); w.writerows(keep + new)
    print(f"leveling: {len(lev)} benchmarks in Table 5-5, {joined} joined to coordinates "
          f"-> {len(new)} Westside rate rows written.")
