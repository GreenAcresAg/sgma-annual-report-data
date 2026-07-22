# GSP cross-subbasin comparison — schema

One normalized long table (`gsp_metrics.csv`) that every subbasin's GSP maps into, so comparison is
a filter/pivot. "Headline numbers first": ~20 defining figures per subbasin across four domains,
then deepen only where a workflow needs it.

## Columns (`gsp_metrics.csv`)

| Column | Meaning |
|---|---|
| `subbasin` | Bulletin 118 id, e.g. `5-022.09` (the join key) |
| `subbasin_name` | e.g. `Westside` |
| `area_name` | GSA / management area / `Subbasin` for basin-wide values |
| `category` | one of: `water_budget`, `storage`, `smc`, `monitoring`, `pma`, `metadata` |
| `metric` | canonical metric name (see gsp_crosswalk.md) — this is what you GROUP BY |
| `period` | `historical` / `current` / `projected` / water year / `-` |
| `value` | numeric (or short text for definitions) |
| `units` | `AF/yr`, `ft`, `ft/yr`, `ft msl`, `count`, `acres`, `date`, `text` … |
| `per_area` | value normalized by subbasin area where sensible (e.g. `AF/acre`, `ft` of water); else blank |
| `source_doc` | the PDF filename (ties to the document manifest) |
| `page` | source page in that PDF |
| `notes` | scenario, water-year type, caveats, consultant term used |

## Canonical metrics (headline set)

**water_budget / storage** (AF/yr unless noted): `sustainable_yield`, `change_in_storage`
(period historical = overdraft; projected = with-GSP), `total_extraction`, `total_recharge`,
`total_inflow`, `total_outflow`.

**smc** (one defining figure per indicator): `smc_subsidence_mt_annual` (ft/yr),
`smc_subsidence_mt_cumulative` (ft), `smc_gwl_mt` (ft, representative/range),
`smc_storage_ur` (text/AF), `smc_wq_constituents` (text) + `smc_wq_mt`, `smc_isw_mt`.

**monitoring** (`count`): `rms_count_gwl`, `rms_count_subsidence`, `rms_count_wq`, `rms_count_isw`,
`rms_count_streamgage`.

**pma**: `pma_count` (count), `pma_expected_yield` (AF/yr), `pma_supply_vs_demand` (text).

**metadata**: `consultant`, `gsp_date`, `basin_area` (acres), `n_gsas` (count).

## Rules that keep subbasins matchable
1. **Map every consultant term to a canonical `metric`** — record the original wording in `notes`
   and the mapping in `gsp_crosswalk.md`. Never invent a new metric name for the same concept.
2. **Consistent units** (AF/yr, feet); fill `per_area` for anything you'd want to compare across
   differently-sized subbasins.
3. **Always record `source_doc` + `page`** so every number is traceable and re-verifiable.
4. SMCs are per-RMS in the GSP — the headline `smc_*` value is the basin-level *defining* threshold
   (or a representative/range); note in `notes` if it varies by area.
