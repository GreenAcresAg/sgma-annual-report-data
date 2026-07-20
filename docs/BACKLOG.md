# Backlog

## Extract subsidence benchmark history from individual GSA annual reports
DWR's central export lacks the pre-2019 / annual-since-2000 benchmark leveling for several
subbasins (notably **Tulare Lake, 5-022.12**). Fill it by pulling each GSA's annual-report
submittal from the SGMA portal and extracting the subsidence tables, then normalizing to the
survey basis in SURVEY_BASIS.md and appending to `data/subsidence_data.csv`.

Tulare Lake GSAs to source: North Fork Kings, South Fork Kings, Southwest Kings,
Mid-Kings River, El Rico, Tri-County WA.

Feasibility depends on whether each report has a machine-readable data upload vs. PDF tables.

## Add PDF URLs to annual_report_catalog.csv
The catalog currently lists which reports exist (subbasin × area × year). Add direct PDF links
once a reliable SGMA-portal document endpoint is identified.

## DONE (partial): benchmark extraction from annual report PDFs
- Cracked it: Appendix E **Table E-1** in each Tulare Lake annual report holds per-benchmark
  annual Fall-to-Fall displacement (feet). `extract_ar_benchmarks.py` pulls it via structured
  table extraction. WY2024 (portal submittal 477 / doc 4886) extracted -> 38 stations,
  `data/benchmark_displacement_annual.csv`.
- The SGMA-portal machine-readable export (`SgmaWell/service/monitoring/exportgeneralsites?
  basinId=507&reportYearId=1..9`) returns **empty for Tulare Lake every year** — confirming the
  values are PDF-only.

## TODO: prior-year Tulare Lake reports (WY2020–2023)
Need each year's report PDF (submittal/doc ids) to build the full 2019→2024 annual series. Run:
`python3 extract_ar_benchmarks.py WY2023=<pdf> WY2022=<pdf> WY2021=<pdf> WY2020=<pdf>`.
Then extend to other subbasins (each has its own basinId; Table E-1 layout may differ per author).
