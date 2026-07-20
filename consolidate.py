#!/usr/bin/env python3
"""Consolidate DWR SGMA GSP Annual Report + Monitoring data for the San Joaquin Valley.

DWR aggregates GSA annual-report submittals into two open datasets on data.cnra.ca.gov:
  gspar  — GSP Annual Report Data (change in storage, extraction, surface supply, total use)
  gspmd  — GSP Monitoring Data (groundwater level, subsidence, stream gage sites + measurements)

This script pulls both, filters to the San Joaquin Valley (Bulletin 118 basin 5-022) subbasins,
cleans/dedupes, joins monitoring measurements to their sites, and writes tidy per-dataset CSVs
plus a per-site "survey basis" table so series can be stitched on a common reference.

Scope is controlled by BASINS below — widen to statewide by clearing the filter.
"""
import csv, io, json, os, subprocess
from collections import defaultdict

DATA = os.path.join(os.path.dirname(__file__), "data")
# San Joaquin Valley subbasins (Bulletin 118 basin 5-022). Filter matches the BASIN_NAME prefix.
BASINS_PREFIX = "5-022"

GSPMD = "https://data.cnra.ca.gov/dataset/536dc423-01b3-4094-bdcd-903df84f6768/resource"
GSPAR = "https://data.cnra.ca.gov/dataset/05041838-896f-4d1a-beff-0fd43b5a3e0f/resource"

# name -> download URL. Basin field is auto-detected per file (schemas differ across datasets).
SOURCES = {
    # Monitoring — sites (carry the survey basis) + measurements
    "groundwater_level_sites":  f"{GSPMD}/38dc5a77-0428-4d8b-970a-51797ed2cd36/download/groundwater_level_sites.csv",
    "groundwater_level_data":   f"{GSPMD}/d6317634-7489-4dc9-8d05-cc939e109f4a/download/groundwater_level_data.csv",
    "subsidence_sites":         f"{GSPMD}/8405de2b-a4bb-4ffd-a9bc-b65e96bc2735/download/subsidence_sites.csv",
    "subsidence_data":          f"{GSPMD}/a79c5e73-2a52-4aa7-affa-5d5fecb94cc3/download/subsidence_data.csv",
    "stream_gage_sites":        f"{GSPMD}/a7967b41-2619-4805-b7b8-f6ac0ee058c0/download/stream_gage_sites.csv",
    "stream_gage_data":         f"{GSPMD}/e65b8d20-5b52-4a13-9273-c0715d6715af/download/stream_gage_data.csv",
    # Annual report data
    "change_in_storage":        f"{GSPAR}/fdfe614a-aef2-482f-b63e-59699b7dcaf2/download/change_in_storage.csv",
    "change_in_storage_basin":  f"{GSPAR}/0f1896cd-b366-46bf-81ef-ecbfcf4b0584/download/change_in_storage_totals.csv",
    "groundwater_extraction":   f"{GSPAR}/f5d850d2-8cc1-41de-9df1-0dfdf7b6ce8b/download/groundwater_extraction.csv",
    "groundwater_extraction_methods": f"{GSPAR}/6dd66e18-7e6a-4440-96f2-334f3d0e29a4/download/groundwater_extraction_methods.csv",
    "surface_water_supply":     f"{GSPAR}/153a3415-c0a3-4d5e-81ca-a7569514a487/download/surface_water_supply.csv",
    "total_water_use":          f"{GSPAR}/0860c5f6-90e5-426f-b274-58c4bc72c2af/download/total_water_use.csv",
}

# Fields that define a subsidence/GW site's "survey basis" (kept in the basis table).
BASIS_FIELDS = ["GENERAL_SITE_ID", "LOCAL_SITE_NAME", "SITE_TYPE", "BASIN_NAME", "GSA_NAME",
                "GSP_NAME", "MONITORING_NETWORK_TYPE", "SUSTAINABILITY_INDICATORS",
                "RP_ELEVATION", "RP_DESCRIPTION", "GS_ELEVATION", "MEAS_METHOD", "MEAS_ACC",
                "LATITUDE", "LONGITUDE", "COUNTY"]


def fetch_rows(url, tries=3):
    import time
    for i in range(tries):
        out = subprocess.run(["curl", "-sL", "--max-time", "180", url],
                             capture_output=True, text=True)
        if out.returncode == 0 and out.stdout and not out.stdout.lstrip().startswith("<"):
            return list(csv.DictReader(io.StringIO(out.stdout)))
        time.sleep(3 * (i + 1))
    return None


def basin_fields(cols):
    """All columns that could carry the Bulletin-118 basin name/number.
    Different DWR tables use BASIN_NAME (name only), SUBBASIN_NUMBER, etc."""
    return [c for c in cols if "basin" in c.lower()]


def in_scope(row, fields):
    if not fields:
        return True
    return any(BASINS_PREFIX in (row.get(f, "") or "") for f in fields)


def write_csv(name, rows, cols=None):
    if not rows:
        print(f"  {name}: 0 rows (skipped)")
        return 0
    cols = cols or list(rows[0].keys())
    path = os.path.join(DATA, name + ".csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"  {name}: {len(rows)} rows -> {name}.csv ({os.path.getsize(path)//1024} KB)")
    return len(rows)


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    manifest = {"scope": f"San Joaquin Valley (Bulletin 118 basin {BASINS_PREFIX})", "datasets": {}}

    for name, url in SOURCES.items():
        rows = fetch_rows(url)
        if rows is None:
            print(f"  {name}: FETCH FAILED ({url.split('/')[-1]})")
            manifest["datasets"][name] = {"status": "fetch_failed"}
            continue
        bf = basin_fields(rows[0].keys()) if rows else []
        scoped = [r for r in rows if in_scope(r, bf)]
        n = write_csv(name, scoped)
        manifest["datasets"][name] = {"rows_total": len(rows), "rows_in_scope": n,
                                      "basin_fields": bf, "columns": list(rows[0].keys()) if rows else []}

    # ── Survey-basis table (subsidence + GW level sites) ──
    basis = []
    for site_file in ("subsidence_sites", "groundwater_level_sites"):
        p = os.path.join(DATA, site_file + ".csv")
        if not os.path.exists(p):
            continue
        seen = set()
        for r in csv.DictReader(open(p)):
            sid = r.get("GENERAL_SITE_ID")
            key = (site_file, sid)
            if sid in ("", None) or key in seen:
                continue
            seen.add(key)
            row = {k: r.get(k, "") for k in BASIS_FIELDS}
            row["DATASET"] = site_file.replace("_sites", "")
            basis.append(row)
    write_csv("survey_basis", basis, cols=["DATASET"] + BASIS_FIELDS)

    # ── Annual-report catalog (which reports exist: subbasin × area × year) ──
    cat = {}
    cis = os.path.join(DATA, "change_in_storage.csv")
    if os.path.exists(cis):
        for r in csv.DictReader(open(cis)):
            key = (r.get("SUBBASIN_NUMBER", ""), r.get("BASIN_NAME", ""),
                   r.get("ANNUAL_REPORT_AREA", ""), r.get("REPORT_YEAR", ""))
            cat.setdefault(key, r.get("SINGLE_MULTIPLE_AR", ""))
        catalog = [{"SUBBASIN_NUMBER": k[0], "BASIN_NAME": k[1], "ANNUAL_REPORT_AREA": k[2],
                    "REPORT_YEAR": k[3], "SINGLE_MULTIPLE_AR": v}
                   for k, v in sorted(cat.items())]
        write_csv("annual_report_catalog", catalog,
                  cols=["SUBBASIN_NUMBER", "BASIN_NAME", "ANNUAL_REPORT_AREA", "REPORT_YEAR", "SINGLE_MULTIPLE_AR"])
        manifest["annual_reports"] = {"reporting_areas": len({(k[0], k[2]) for k in cat}),
                                      "rows": len(catalog),
                                      "years": sorted({k[3] for k in cat if k[3]})}

    json.dump(manifest, open(os.path.join(DATA, "manifest.json"), "w"), indent=2)
    print("wrote manifest.json")
