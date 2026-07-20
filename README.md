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

## Known completeness gap (important)

DWR's central export is **incomplete for physical subsidence benchmarks in some subbasins**. In
the **Tulare Lake subbasin (5-022.12)** every benchmark has only **1–2 submitted measurements
(2019–2020)** — not the annual-since-2000 leveling history that appears in the GSAs' actual
annual reports. The dense multi-decade series in this dataset belong mostly to **Tule,
Delta-Mendota, and Westside** sites (and are often `Remote Sensing`/InSAR points, not physical
benchmarks). Filling the Tulare Lake history requires extracting from the **individual GSA annual
report submittals** (North Fork Kings, South Fork Kings, Southwest Kings, Mid-Kings River,
El Rico, Tri-County WA) — a planned follow-on (`docs/BACKLOG.md`).

## License / attribution
Source data © California DWR, public domain, via the CA Natural Resources Agency Open Data
portal. This repo only reorganizes it.
