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

## DONE: all Tulare Lake water years (WY2019–WY2025)
Extracted from the local report PDFs (~/Downloads/5-022.12_*_WY_*.pdf). Two metrics, two
extractors — full detail in [EXTRACTION_STATUS.md](EXTRACTION_STATUS.md):
- `extract_tulare_rms.py` — Fall-to-Fall Table E-1 for WY2023 (32 stations) + WY2025 (55). Added a
  ±5 ft plausibility guard (WY2023 S222R prints an impossible `-2838`).
- `extract_tulare_figure.py` — the WY2020–WY2022 reports have NO table; per-benchmark values are
  map-figure labels. Recovered via geometric (Hungarian) station↔value pairing. WY2020 (23),
  WY2021 (28), WY2022 (26). Cross-validated WY2021 across two reports (mean Δ 0.001 ft).
- WY2019: no per-benchmark data exists (narrative + InSAR figure only).

## TODO: extend the figure/table extractors to other subbasins
Each subbasin's reports use their own author/layout; Kaweah/Tule already have dedicated scripts.
Westside & Delta-Mendota still need per-format extractors (their subsidence is figure-only).
