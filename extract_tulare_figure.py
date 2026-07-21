#!/usr/bin/env python3
"""Extract per-benchmark subsidence values from the Tulare Lake annual-report FIGURE maps.

The WY2019-WY2022 Tulare Lake reports do NOT tabulate benchmark subsidence (that starts in the
WY2023 report's Fall-to-Fall Table E-1). Instead each has a "Land Subsidence Monitoring Sites"
map figure (Figure F-1 / C-x) that plots every benchmark with its measured annual value printed
as a text label next to the station id — e.g. "Subsidence Monitoring Sites (WY20 Measurements) /
Average Annual Change (ft)".

Because it's a figure, station id and value are separate positioned text tokens. We recover the
pairing geometrically: build the station x value distance matrix and solve the optimal assignment
(scipy Hungarian), keeping only tight pairs. The pairing distance is a built-in quality signal.

Metric captured = "WY20YY Average Annual Change (ft)" (a per-water-year rate — NOT the same as the
Fall-to-Fall cumulative-increment series; do not merge the two. See SURVEY_BASIS.md).

Usage:  python3 extract_tulare_figure.py WY2019=/path/2019.pdf:12 WY2020=/path/2020.pdf:502 ...
        (the :N suffixes are 1-indexed figure pages; comma-separate multiple pages)
Appends to data/benchmark_displacement_annual.csv, idempotent on (report_year,subbasin,station_id,metric).
"""
import csv, os, re, sys, math
import fitz
from scipy.optimize import linear_sum_assignment

DATA = os.path.join(os.path.dirname(__file__), "data")
OUT = os.path.join(DATA, "benchmark_displacement_annual.csv")
SUBBASIN = "Tulare Lake"
COLS = ["report_year", "subbasin", "GSA", "station_id", "latitude", "longitude",
        "station_type", "metric", "value"]
STID = re.compile(r"^(SUB\d{2,3}|CRCN|LEMA|S\d{3}P?\d?|K\d{3}|U\s?\d{3}|X\s?\d{3}|N\s?\d{3})\*?$")
VAL = re.compile(r"^-?[01]?\.\d{2,4}$")     # annual change in feet, |v| < ~2
MAX_DIST = 18.0                              # px; wider pairs are unreliable -> drop
MAX_ABS_FT = 1.5


def cen(w):
    return ((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)


def meas_year(page_text, fallback):
    m = re.search(r"WY\s?(\d\d)\s*Measurement", page_text, re.I)
    if not m:
        m = re.search(r"\(WY\s?(\d\d)\s*Measurement", page_text, re.I)
    return f"WY20{m.group(1)}" if m else fallback


def extract_page(page, report_year):
    words = page.get_text("words")
    stations = [(w[4].rstrip("*").replace(" ", ""), cen(w)) for w in words if STID.match(w[4])]
    vals = [(float(w[4]), cen(w)) for w in words if VAL.match(w[4]) and abs(float(w[4])) <= MAX_ABS_FT]
    if not stations or not vals:
        return {}, None
    # optimal station<->value assignment by euclidean distance
    cost = [[math.hypot(sc[0] - vc[0], sc[1] - vc[1]) for _, vc in vals] for _, sc in stations]
    ri, ci = linear_sum_assignment(cost)
    my = meas_year(page.get_text(), report_year)
    out = {}
    for r, c in zip(ri, ci):
        d = cost[r][c]
        sid = stations[r][0]
        if d <= MAX_DIST:                       # drop loose pairs (station w/ no nearby value)
            # keep the tightest if a station id appears twice on the page
            if sid not in out or d < out[sid][1]:
                out[sid] = (vals[c][0], d)
    return out, my


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rows = []
    for arg in sys.argv[1:]:
        year, _, rest = arg.partition("=")
        path, _, pagespec = rest.partition(":")
        if not os.path.exists(path):
            print(f"  file not found: {path}"); continue
        doc = fitz.open(path)
        pages = [int(p) - 1 for p in pagespec.split(",") if p]
        best = {}   # (metric_year, sid) -> (value, dist)
        for pn in pages:
            pairs, my = extract_page(doc[pn], year)
            print(f"  {year} p{pn + 1}: metric-year {my}, {len(pairs)} benchmarks paired")
            for sid, (v, d) in pairs.items():
                k = (my, sid)
                if k not in best or d < best[k][1]:
                    best[k] = (v, d)
        doc.close()
        for (my, sid), (v, d) in best.items():
            rows.append({"report_year": year, "subbasin": SUBBASIN, "GSA": "", "station_id": sid,
                         "latitude": "", "longitude": "", "station_type": "benchmark (figure)",
                         "metric": f"{my} Average Annual Change (ft)", "value": f"{v:.4f}"})
    os.makedirs(DATA, exist_ok=True)
    if os.path.exists(OUT):
        rows = list(csv.DictReader(open(OUT))) + rows
    seen, deduped = set(), []
    for r in rows:
        k = (r["report_year"], r.get("subbasin", ""), r["station_id"], r.get("metric", ""))
        if k not in seen:
            seen.add(k); deduped.append(r)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(deduped)
    print(f"wrote {len(deduped)} rows total -> {os.path.basename(OUT)}")
