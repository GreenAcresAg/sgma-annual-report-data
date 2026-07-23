# Wells per GSA (GEARS extraction wells) — Tule & Tulare Lake

Per-GSA well counts from the **GEARS** (Groundwater Extraction Accounting & Reporting System)
portal data maintained in the GreenAcresAg/GEARS-map repo (portal export 2026-07-13,
`data/gears_wells.csv`, 5,968 deduplicated wells). GEARS covers only the Tule (5-022.13) and
Tulare Lake (5-022.12) subbasins.

- **wells_pip** — this project's independent point-in-polygon assignment of GEARS well coordinates
  to the DWR SGMA GSA boundaries (subbasins_gsas.geojson), counted per GSA + by purpose of use.
- **gears_reported** — GEARS' own per-GSA well count (GEARS-map `data/gsa_stats.json`, which used
  GEARS' surrounding_gsas.geojson boundaries).
- **Cross-check:** the two agree to within ±1 well per GSA (Tule 3,249 vs 3,248; Tulare Lake 2,556
  vs 2,558) — the ±1s are boundary-edge wells between two near-identical boundary versions.
- These are self-reported **extraction** wells (irrigation/household/livestock/public-supply/etc.),
  distinct from the DWR RMS **monitoring** wells shown at subbasin level in gsp_metrics.csv.

Source: GreenAcresAg/GEARS-map. Do not re-derive from OSWCR.
