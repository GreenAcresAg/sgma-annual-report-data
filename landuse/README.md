# Land-use / cropped acreage (DWR i15 Statewide Crop Mapping, LandIQ)

Per-GSA cropped acres 2020–2024, computed by server-side spatial-statistics query against
DWR's i15 Statewide Crop Mapping map services (LandIQ remote-sensing crop maps), one query per
GSA per year: `sum(ACRES) group by SYMB_CLASS`, spatial filter = GSA boundary (intersects).

- **Source:** data.cnra.ca.gov "Statewide Crop Mapping" — annual ArcGIS map services (2020–2024).
- **Boundaries:** DWR SGMA GSA boundaries (subbasins_gsas.geojson).
- **cropped_acres** = sum of irrigated-ag SYMB_CLASS: C citrus, D deciduous, F field, G grain/hay,
  P pasture, R rice, T truck/nursery/berry, V vineyard, YP young perennial.
  Excludes I (idle/fallow), U (urban), native/semi-ag/water/unclassified.
- **Caveat:** intersects, not clipped — crop polygons on a GSA edge count fully; subbasin sums
  show <~2% overcount vs GSP-stated irrigated totals, acceptable for trend/comparison.
- Files: crop_by_gsa_raw.csv (per class), crop_acres_by_gsa.csv (tidy), crop_batch.py + crop_aggregate.py (repro).
