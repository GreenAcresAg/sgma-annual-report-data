#!/usr/bin/env python3
"""Per-GSA per-year cropped-acre time series from DWR i15 Statewide Crop Mapping (LandIQ).

For each GSA polygon in our 6 subbasins, POST a spatial statistics query to each year's
crop map service summing ACRES grouped by SYMB_CLASS (DWR standard crop class). Cached to
crop_by_gsa_raw.csv so reruns skip completed (GSA,year) pairs.

NOTE: intersects (not clipped) — boundary crop polygons count fully. Validated by summing
GSAs to subbasin totals; boundary error is small vs GSA size.
"""
import json, urllib.request, urllib.parse, os, csv, time

HERE = os.path.dirname(os.path.abspath(__file__))
GEO = "/Users/natalie/sgma-dashboard/data/subbasins_gsas.geojson"
RAW = os.path.join(HERE, "crop_by_gsa_raw.csv")
OURS = {"Kings", "Westside", "Kaweah", "Tulare Lake", "Tule", "Kern", "Kern County"}
SUBNORM = {"Kern County": "Kern"}

YEAR_ITEM = {2024: "39b63601dfb34274899d15a13465644e", 2023: "d94e891e00364e49a2ed9e9e2e27837d",
             2022: "8b0555ad7cb14dcab66901925427228a", 2021: "5fe15fbb9296403eb4ea91e3d031619d",
             2020: "576e483b63334c4886a0e535584c4570"}


def resolve_urls():
    urls = {}
    for yr, iid in YEAR_ITEM.items():
        m = json.load(urllib.request.urlopen(
            f"https://www.arcgis.com/sharing/rest/content/items/{iid}?f=json", timeout=45))
        urls[yr] = m["url"] + "/0/query"
    return urls


def gsa_rings(f):
    g = f["geometry"]
    return g["coordinates"] if g["type"] == "Polygon" else [r for p in g["coordinates"] for r in p]


def query(url, rings, tries=3):
    esri = {"rings": rings, "spatialReference": {"wkid": 4326}}
    params = {"f": "json", "geometry": json.dumps(esri), "geometryType": "esriGeometryPolygon",
              "inSR": "4326", "spatialRel": "esriSpatialRelIntersects", "where": "1=1",
              "outStatistics": json.dumps([{"statisticType": "sum", "onStatisticField": "ACRES",
                                            "outStatisticFieldName": "ac"}]),
              "groupByFieldsForStatistics": "SYMB_CLASS"}
    data = urllib.parse.urlencode(params).encode()
    for t in range(tries):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=120))
            if "features" in r:
                return {(feat["attributes"]["SYMB_CLASS"] or "").strip(): feat["attributes"]["ac"]
                        for feat in r["features"]}
            raise RuntimeError(json.dumps(r)[:200])
        except Exception as e:
            if t == tries - 1:
                raise
            time.sleep(3 * (t + 1))


def main():
    geo = json.load(open(GEO))
    gsas = [(SUBNORM.get(f["properties"]["subbasin"], f["properties"]["subbasin"]),
             f["properties"]["GSA_Name"], gsa_rings(f))
            for f in geo["features"] if f["properties"].get("subbasin") in OURS]
    done = set()
    rows = []
    if os.path.exists(RAW):
        for r in csv.DictReader(open(RAW)):
            done.add((r["gsa"], int(r["year"])))
            rows.append(r)
    urls = resolve_urls()
    print(f"{len(gsas)} GSAs x {len(urls)} years; {len(done)} already cached", flush=True)
    for sub, name, rings in gsas:
        for yr, url in sorted(urls.items()):
            if (name, yr) in done:
                continue
            try:
                cls = query(url, rings)
                for c, ac in cls.items():
                    rows.append({"subbasin": sub, "gsa": name, "year": yr, "symb_class": c, "acres": f"{ac:.1f}"})
                print(f"  OK {yr} {name:44s} {sum(cls.values()):>9,.0f} ac ({len(cls)} classes)", flush=True)
            except Exception as e:
                print(f"  ERR {yr} {name}: {e}", flush=True)
            with open(RAW, "w", newline="") as fp:
                w = csv.DictWriter(fp, fieldnames=["subbasin", "gsa", "year", "symb_class", "acres"])
                w.writeheader(); w.writerows(rows)
    print(f"DONE. {len(rows)} rows -> {RAW}", flush=True)


if __name__ == "__main__":
    main()
