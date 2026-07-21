# Annual-report benchmark extraction — status & data quality

`data/benchmark_displacement_annual.csv` is a **best-effort, mixed-quality** extraction of
subsidence data from SGMA annual report PDFs. **Each subbasin's report uses a different
consultant and table schema**, so a single extractor cannot cleanly parse all of them. The
`metric` column preserves each value's meaning — **do not mix metrics blindly** (see
[../SURVEY_BASIS.md](../SURVEY_BASIS.md)). Values include *both* displacement (≈ ±1 ft) and
absolute elevations (≈ hundreds of ft amsl) — filter by `metric`.

## Per-subbasin status (WY2024 reports, first pass)

| Subbasin | Status | Notes |
|---|---|---|
| **Tulare Lake** (WY2020–WY2025) | ✅ clean | Full multi-year, two metrics — see below. Verified/cross-validated. |
| **Kaweah** (WY2023–WY2025) | ✅ clean | `extract_kaweah.py` (P&P "Subsidence Monitoring Station" table): per-year elevations + annual + cumulative subsidence (ft). MT/MO criteria excluded; column-map by header (generic extractor mangled it). Cross-validated: 2020 baseline identical across 3 reports. |
| **Tule** (WY2024) | ✅ clean | Dedicated `extract_tule.py` targets the "Benchmark Name" leveling table (69 benchmarks, coords, 2023 & 2024 elevations + 2023→2024 subsidence). InSAR/threshold tables excluded. |
| **Westside** | ⚠️ partial | Only 1 row captured — subsidence is mostly in figures, not tables. |
| **Delta-Mendota** | ❌ none | No parsable subsidence table (figures / different layout). |

## Tulare Lake — full water-year coverage (WY2019–WY2025)

Two *different* metrics, kept in separate `metric` labels — **do not concatenate them into one
series** (a Fall-to-Fall cumulative increment ≠ a per-WY average annual rate):

| Report | Metric (`metric` value) | Source in report | # benchmarks | Extractor |
|---|---|---|---:|---|
| WY2019 | — | narrative + InSAR figure only; network not yet reporting per-benchmark | 0 | n/a |
| WY2020 | `WY2020 Average Annual Change (ft)` | Figure F-1 map labels (p502) | 23 | `extract_tulare_figure.py` |
| WY2021 | `WY2021 Average Annual Change (ft)` | "WY21 Measurement" figures (p463–465) | 28 | `extract_tulare_figure.py` |
| WY2022 | `WY2022 Average Annual Change (ft)` + `WY2021 …` | "WY22/WY21 Measurement" figures (p57–59) | 26 + 22 | `extract_tulare_figure.py` |
| WY2023 | `Fall 2021 to Fall 2022 (feet)`, `Fall 2022 to Fall 2023 (feet)` | Table E-1 (p199) | 32 | `extract_tulare_rms.py` |
| WY2024 | `Fall 2022→2023`, `Fall 2023→2024 (feet)` | Table E-1 | 38 | `extract_ar_benchmarks.py` |
| WY2025 | `Fall 2022→2023`, `2023→2024`, `2024→2025 (feet)` | Table E-1 (p235) | 55 | `extract_tulare_rms.py` |

Notes / QC:
- **WY2019–WY2022 have no benchmark *table*** — the measured values are printed as text labels on
  the "Land Subsidence Monitoring Sites" map figures. `extract_tulare_figure.py` recovers each
  station↔value pair geometrically (scipy Hungarian assignment on the label positions); the pairing
  distance is a quality signal and loose pairs (>18 px) are dropped.
- **Cross-validated:** WY2021 values appear in *both* the WY2021 and WY2022 reports and agree to a
  mean of 0.001 ft (max 0.029) across 22 shared stations. The `report_year` column keeps provenance;
  use `report_year == WY2021` as the primary WY2021 record.
- **Source typo caught:** WY2023 S222R printed `-2838` ft (impossible); `extract_tulare_rms.py` now
  drops Fall values with |v| > 5 ft.
- **Excluded (not measurements):** WY2022 Table C-1 "Baseline / With GSP Implementation" columns are
  *modeled projection scenarios*, not survey data, and are intentionally not extracted.

## Why this is hard
Consultants report subsidence as: annual increments (Tulare Lake), per-year elevations (Kaweah),
InSAR summaries (Tule), or figures/charts (Westside, Delta-Mendota). Reliable coverage needs a
**per-subbasin (per-format) extractor + QC**, not one generic parser. `extract_ar_benchmarks.py`
is generic (good recall, imperfect precision) and filters obvious noise (threshold/criteria
columns, junk station ids), but curation is still required.

## Backlog
- Per-format extractors / cleanup for Tule, Westside, Delta-Mendota (and the other SJV subbasins).
- Fix `report_year` auto-detect for the Tule/Westside title formats.
- Earlier years (WY2019–WY2022) — reports cluster at lower submittal-id ranges on the SGMA portal.
- Separate physical-benchmark rows from InSAR-derived rows via `station_type` / station-id suffix.
