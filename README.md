# SGMA Annual Report & Monitoring Data — San Joaquin Valley (consolidated)

A tidy, reproducible consolidation of the data California GSAs submit to DWR in their
**Groundwater Sustainability Plan (GSP) annual reports** and monitoring networks, for the
**San Joaquin Valley** (Bulletin 118 basin **5-022**, all subbasins). Built as a shared
reference for other Green Acres projects (e.g. the InSAR subsidence map).

> **Scope:** San Joaquin Valley subbasins (`5-022.*`). Widen to statewide by changing
> `BASINS_PREFIX` in `consolidate.py` and re-running.

## Sources (all public, DWR)

DWR aggregates GSA annual-report submittals into two open datasets on data.cnra.ca.gov, which
this repo pulls, filters to the SJV, cleans, and re-publishes together:

- **GSP Annual Report Data** (`gspar`) — change in storage, groundwater extraction, surface-water
  supply, total water use.
- **GSP Monitoring Data** (`gspmd`) — groundwater level, subsidence, and stream-gage **sites**
  (which carry the survey basis) and their **measurements**.

Regenerate everything with:
```bash
python3 consolidate.py     # curl + clean -> data/*.csv + manifest.json
```

## What's in `data/`

| File | Rows (SJV) | What |
|---|---:|---|
| `annual_report_catalog.csv` | 151 | Which annual reports exist: subbasin × reporting area × year (2019–2025) |
| `change_in_storage.csv` / `_basin.csv` | 251 / 151 | Annual change in groundwater storage (by aquifer / basin total) |
| `groundwater_extraction.csv` / `_methods.csv` | 111 / 111 | Annual extraction by water-use sector + methods |
| `surface_water_supply.csv` | 111 | Annual surface-water supply |
| `total_water_use.csv` | 111 | Annual total water use |
| `groundwater_level_sites.csv` | 1,785 | GW-level monitoring sites |
| `groundwater_level_data.csv` | 123,439 | GW-level measurements |
| `subsidence_sites.csv` | 281 | Subsidence monitoring sites (benchmarks, extensometers, CGPS, InSAR points) |
| `subsidence_data.csv` | 25,316 | Subsidence measurements (`CUM_DISPLACE_ELEV` over time) |
| `stream_gage_sites.csv` | 12 | Stream-gage sites |
| `survey_basis.csv` | 207 | Per-site **survey basis** for subsidence + GW-level sites (see below) |
| `manifest.json` | — | Per-dataset row counts, columns, basin fields, catalog summary |

Column definitions: **[DATA_DICTIONARY.md](DATA_DICTIONARY.md)**.

## Survey basis — read before stitching series

Subsidence and groundwater-level series are only comparable if they share the same **basis**
(baseline date, vertical datum, and reference point). This is tracked so you don't accidentally
combine incompatible series. **[SURVEY_BASIS.md](SURVEY_BASIS.md)** has the full guidance; in short:

- Subsidence `CUM_DISPLACE_ELEV` is **cumulative displacement relative to `DATE_OF_DISPLACE_START`**
  — that baseline varies by site/GSA. Never merge two series without aligning baselines.
- `survey_basis.csv` carries each site's `MEAS_METHOD`, `RP_ELEVATION`, `GS_ELEVATION`,
  `RP_DESCRIPTION`, `SITE_TYPE`, and network — many GSAs leave the datum/RP fields blank or `0`,
  which is itself a caveat flagged per site.

## Benchmark data from annual report PDFs (`extract_ar_benchmarks.py`)

DWR's central export has **no benchmark measurements for the Tulare Lake subbasin** — the values
live only inside each annual report's **Appendix E, Table E-1 "Land Subsidence RMS Monitoring
Network"** (per-benchmark **annual Fall-to-Fall displacement, feet**). Neither the SGMA-portal
data export (0 readings, all years) nor `gspmd` has them.

`extract_ar_benchmarks.py` pulls Table E-1 straight out of the report PDFs (structured table
extraction) into `data/benchmark_displacement_annual.csv` (long format: report_year, GSA,
station_id, lat, lon, station_type, period, displacement_ft).

```bash
# download the report PDF(s) from the portal, then:
python3 extract_ar_benchmarks.py WY2024=path/to/tulare_lake_wy2024.pdf [WY2023=... ...]
```
Report PDFs: SGMA portal → `…/portal/gspar/preview/<submittal>` → export/documents, or
`…/portal/service/gspar/document/<id>`. **WY2024 Tulare Lake** = submittal `477`, main report
doc `4886` (41-station RMS network; 25 benchmarks surveyed by Kings River Conservation District,
plus CGPS CRCN & LEMA).

**Status:** WY2024 extracted (38 stations). To build the full 2019→2024 annual series, run the
same extractor on each prior-year Tulare Lake report (WY2020–2023) — those submittal/doc ids are
the remaining input (`docs/BACKLOG.md`). Pre-2019 leveling is in the GSP (not annual reports).

> **Survey basis:** these are *annual* Fall-to-Fall increments, not cumulative — sum them (aligned
> to a common start) to get cumulative subsidence. `station_type` distinguishes surveyed
> benchmarks from CGPS. See [SURVEY_BASIS.md](SURVEY_BASIS.md).

## License / attribution
Source data © California DWR, public domain, via the CA Natural Resources Agency Open Data
portal. This repo only reorganizes it.
