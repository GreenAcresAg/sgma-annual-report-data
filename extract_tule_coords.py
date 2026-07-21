#!/usr/bin/env python3
"""Harvest Tule benchmark coordinates from a member-GSA GSP's subsidence RMS table.

The Tule *coordinated* annual report tabulates benchmark subsidence but publishes coordinates only
for the E/P/D series. The individual GSA GSPs carry the rest: e.g. the Lower Tule River ID GSP has
"Table 4-4: RMS for Monitoring Land Subsidence" (RMS ID | Management Area | GPS Latitude | Longitude)
with the L-series coordinates. This finds any such table (RMS id + lat + lon per row, matched by
cell pattern so the messy spacer columns don't matter) and accumulates into a coordinate reference
file the map join reads.

Usage:  python3 extract_tule_coords.py "<GSA_GSP.pdf>" [more GSPs...]
Writes/updates: data/tule_benchmark_coords.csv  (station_id, latitude, longitude, area)
"""
import csv, os, re, sys
import fitz

DATA = os.path.join(os.path.dirname(__file__), "data")
OUT = os.path.join(DATA, "tule_benchmark_coords.csv")
BM = re.compile(r"[A-Z]{1,2}\d{3,4}_[A-Z]_(?:RMS|FKC|LSMA)")
LAT = re.compile(r"^3[56]\.\d{3,}$")
LON = re.compile(r"^-119\.\d{3,}$|^-120\.\d{3,}$")


def harvest(pdf):
    doc = fitz.open(pdf)
    out = {}
    for page in doc:
        t = page.get_text()
        if not (BM.search(t) and re.search(r"3[56]\.\d{3,}", t) and re.search(r"Subsidence|RMS", t, re.I)):
            continue
        for tab in page.find_tables().tables:
            d = tab.extract()
            for r in d:
                cells = [(c or "").replace("\n", " ").strip() for c in r]
                sid = next((c for c in cells if BM.fullmatch(c)), None)
                lat = next((c for c in cells if LAT.match(c)), None)
                lon = next((c for c in cells if LON.match(c)), None)
                area = next((c for c in cells if "Area" in c or "Service" in c or "GSA" in c), "")
                if sid and lat and lon:
                    out[sid] = (lat, lon, area)
    doc.close()
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    coords = {}
    if os.path.exists(OUT):
        for r in csv.DictReader(open(OUT)):
            coords[r["station_id"]] = (r["latitude"], r["longitude"], r.get("area", ""))
    for pdf in sys.argv[1:]:
        if not os.path.exists(pdf):
            print(f"  missing: {pdf}"); continue
        got = harvest(pdf)
        coords.update(got)
        print(f"  {os.path.basename(pdf)[:40]}: {len(got)} benchmark coords "
              f"(prefixes {sorted({k[0] for k in got})})")
    os.makedirs(DATA, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["station_id", "latitude", "longitude", "area"])
        for sid in sorted(coords):
            w.writerow([sid, *coords[sid]])
    print(f"wrote {len(coords)} total benchmark coords -> {os.path.basename(OUT)}")
