#!/usr/bin/env python3
"""Aggregate raw per-GSA/year/SYMB_CLASS crop acres into a tidy time series + validate.

Writes crop_acres_by_gsa.csv (dashboard-ready):
  subbasin, gsa, year, cropped_acres, idle_acres, urban_acres, other_acres,
  citrus, deciduous, field, grain, pasture, rice, truck, vineyard, young_perennial
"""
import csv, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "crop_by_gsa_raw.csv")
OUT = os.path.join(HERE, "crop_acres_by_gsa.csv")

# DWR standard SYMB_CLASS -> friendly crop category (irrigated ag classes)
CROP = {"C": "citrus", "D": "deciduous", "F": "field", "G": "grain", "P": "pasture",
        "R": "rice", "T": "truck", "V": "vineyard", "YP": "young_perennial"}
IDLE = {"I"}
URBAN = {"U"}
# everything else (native NC/NV/NW/NR/NB, semi-ag S, water, X, E) -> other/non-crop

CATS = list(CROP.values())


def main():
    agg = defaultdict(lambda: defaultdict(float))  # (sub,gsa,year) -> {cat: acres}
    meta = {}
    for r in csv.DictReader(open(RAW)):
        k = (r["subbasin"], r["gsa"], int(r["year"]))
        meta[k] = (r["subbasin"], r["gsa"], int(r["year"]))
        c = r["symb_class"]; ac = float(r["acres"])
        if c in CROP:
            agg[k]["cropped_acres"] += ac
            agg[k][CROP[c]] += ac
        elif c in IDLE:
            agg[k]["idle_acres"] += ac
        elif c in URBAN:
            agg[k]["urban_acres"] += ac
        else:
            agg[k]["other_acres"] += ac

    fields = (["subbasin", "gsa", "year", "cropped_acres", "idle_acres", "urban_acres", "other_acres"] + CATS)
    rows = []
    for k in sorted(agg, key=lambda x: (x[0], x[1], x[2])):
        d = agg[k]
        row = {"subbasin": k[0], "gsa": k[1], "year": k[2]}
        for f in fields[3:]:
            row[f] = f"{d.get(f, 0.0):.1f}"
        rows.append(row)
    with open(OUT, "w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=fields)
        w.writeheader(); w.writerows(rows)

    # validation: subbasin cropped totals per year
    sub_yr = defaultdict(lambda: defaultdict(float))
    for row in rows:
        sub_yr[row["subbasin"]][row["year"]] += float(row["cropped_acres"])
    print(f"wrote {len(rows)} rows -> {os.path.basename(OUT)}\n")
    print("Cropped acres by subbasin/year (validation):")
    yrs = sorted({row["year"] for row in rows})
    print("  subbasin        " + "".join(f"{y:>12}" for y in yrs))
    for sub in sorted(sub_yr):
        print(f"  {sub:14s}" + "".join(f"{sub_yr[sub][y]:>12,.0f}" for y in yrs))


if __name__ == "__main__":
    main()
