# GSP crosswalk — consultant terms → canonical metric

Each subbasin's GSP is written by a different consultant with different wording. This maps their
terms onto the canonical `metric` names in `gsp_metrics.csv`, so cross-subbasin joins work. Add a
column per subbasin as each GSP is cataloged. **Where the headline numbers live: the Executive
Summary tables** (Table ES-* in most GSPs) — sustainable yield, undesirable results, SMC summary,
and PMA summary are almost always tabulated there.

## Canonical metric → where each GSP puts it

| Canonical metric | Westside (LSCE, 2025) — term / location |
|---|---|
| `sustainable_yield` | "Sustainable Yield (AFY)" — Table ES-1 (p33); detail p146 |
| `total_extraction` | "long-term average pumping" (p146) |
| `change_in_storage` | "decline in storage" (p146) |
| `smc_subsidence_mt_annual` / `_cumulative` | Table ES-3 "Land Subsidence" MT (p35); split San Luis Canal vs Other sites |
| `smc_gwl_mt` | Table ES-3 "Chronic Lowering of Groundwater Levels" MT (p35) |
| `smc_storage_ur` | Table ES-3 "Reduction of Groundwater Storage" (p35) |
| `smc_wq_mt` | Table ES-3 "Degraded Water Quality" (p35) |
| `smc_isw_mt` | Table ES-3 / TOC "Interconnected Surface Water" |
| `rms_count_subsidence` | Table 3-15 "Proposed Monitoring Network for Subsidence" (p361) |
| `rms_count_gwl` | Table 3-14 "Proposed Monitoring Network for Water Levels" (p360) |
| `pma_count` / `pma_supply_vs_demand` | Table ES-4 "Project and Management Actions" (p39) |

## Notes / conventions
- **Ranges** (e.g. projected sustainable yield 270,000–294,000): store a single representative value
  in `value` and the full range in `notes`.
- **Sign**: `change_in_storage` negative = net loss (overdraft), consistent across subbasins.
- **SMCs vary by area** (San Luis Canal vs remainder; Upper vs Lower Aquifer) — headline value is the
  defining/most-stringent one; the split is recorded in `notes`.
- Recurring GSP consultants to expect: LSCE (Westside), Provost & Pritchard (Kaweah),
  Thomas Harder & Co. (Tule), GEI/Davids/others (Tulare Lake, Kings) — each has its own ES-table
  wording; extend this table per subbasin.
