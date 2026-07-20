# Survey Basis — how to stitch subsidence & water-level series correctly

Elevation/displacement series from different sites, GSAs, and reporting years are only
comparable if they share the same **basis**. Combining series with different baselines, datums,
or reference points produces meaningless offsets. This file documents the basis fields captured
here and the rules for using them.

## Subsidence (`subsidence_data.csv` + `survey_basis.csv`)

`CUM_DISPLACE_ELEV` is **cumulative vertical displacement relative to a baseline date**, not an
absolute elevation. The baseline is `DATE_OF_DISPLACE_START` (per measurement/site).

**Rules:**
1. **Align the baseline.** Two series are only directly comparable if they share the same
   `DATE_OF_DISPLACE_START`. If they differ, re-reference one series to the other's baseline
   (subtract the value at the common date) before combining — and only if both cover that date.
2. **Match the method.** `SITE_TYPE` / `MEAS_METHOD` distinguish *physical* measurements
   (`Surveying/Benchmark Sites` = leveling to a benchmark; `Extensometer`; `Continuous GPS`) from
   *remote-sensing* (`Remote Sensing - Other` = InSAR-derived). Do **not** stitch a leveling
   series onto an InSAR-derived one without noting the method change — they have different
   reference frames and error characteristics.
3. **Check the vertical datum / reference point.** `RP_ELEVATION`, `GS_ELEVATION`,
   `RP_DESCRIPTION` describe the physical reference mark and datum. **Caveat:** in this dataset
   many GSAs left these `0` / `Unknown`, so the absolute datum is frequently *unstated* — treat
   such series as relative-only and flag them.
4. **Sign convention.** Negative `CUM_DISPLACE_ELEV` = subsidence (ground moved down) relative to
   the baseline; positive = uplift. Confirm per source in `COMMENTS`.

## Groundwater level (`groundwater_level_data.csv` + `groundwater_level_sites.csv`)

Water-surface elevations depend on the site's **reference point** and **datum**:
- `RP_ELEVATION` (measuring-point elevation) and `GS_ELEVATION` (ground surface) define the
  vertical reference; a change in RP (e.g., a re-survey) creates an artificial step.
- Prefer water-surface **elevation** (already datum-referenced) over depth-to-water when
  comparing across sites; when using depth-to-water, you must apply each site's RP elevation and
  confirm a common vertical datum (NAVD88 vs NGVD29).
- `MEAS_METHOD` / `MEAS_ACC` capture how/how-accurately each point was measured.

## Practical checklist before merging any two series
- [ ] Same `SUBBASIN_NUMBER`? (or intentional cross-basin)
- [ ] Same baseline (`DATE_OF_DISPLACE_START`) — or re-referenced to one?
- [ ] Same measurement method / site type — or the change is documented?
- [ ] Same vertical datum & reference point — or flagged as relative-only?
- [ ] Overlapping dates exist to tie the series together?

`survey_basis.csv` gives one row per site with all of these fields (keyed by
`GENERAL_SITE_ID` + `DATASET`) so a stitching routine can enforce the checklist programmatically.
