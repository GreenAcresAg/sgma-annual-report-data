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
| **Tulare Lake** (WY2024) | ✅ clean | Geosyntec "Table E-1", annual Fall-to-Fall displacement (ft). Verified. |
| **Kaweah** (WY2023, WY2024) | ✅ clean | Per-year elevations (amsl) + WY subsidence (ft). |
| **Tule** | ⚠️ mixed / raw | Report mixes InSAR-derived points, elevations, and annual subsidence; `report_year` not auto-detected ("unknown"); needs per-format cleanup + station-type separation. |
| **Westside** | ⚠️ partial | Only 1 row captured — subsidence is mostly in figures, not tables. |
| **Delta-Mendota** | ❌ none | No parsable subsidence table (figures / different layout). |

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
