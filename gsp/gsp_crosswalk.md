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

## Canonical metric → Tulare Lake (coordinated, 2022 Amended GSP)

Unlike Westside, this GSP has **no "Table ES-*" summary** — the headline numbers are in the
water-budget **narrative** (Ch. 3/ES around p36, p146–148). Extraction must handle both patterns.

| Canonical metric | Tulare Lake — term / location |
|---|---|
| `sustainable_yield` | "long-term sustainable yield for agricultural pumping ≈ −229,220 AF/Y" (p148) |
| `total_extraction` | "average groundwater pumping −348,700 AF/Y" (p36, 1998–2010 normal hydrology) |
| `change_in_storage` | "estimated annual change in storage … averaged about −85,690 AF/Y" (p146, 1990–2016) |

**⚠ Sign convention differs:** Tulare Lake writes **pumping and sustainable yield as negative**
(−348,700, −229,220). Canonical form stores them as **positive magnitudes**; only `change_in_storage`
keeps its sign (negative = overdraft). Always check each GSP's sign convention and normalize.

## Notes / conventions
- **Ranges** (e.g. projected sustainable yield 270,000–294,000): store a single representative value
  in `value` and the full range in `notes`.
- **Sign**: `change_in_storage` negative = net loss (overdraft), consistent across subbasins.
- **SMCs vary by area** (San Luis Canal vs remainder; Upper vs Lower Aquifer) — headline value is the
  defining/most-stringent one; the split is recorded in `notes`.
- Recurring GSP consultants to expect: LSCE (Westside), Provost & Pritchard (Kaweah),
  Thomas Harder & Co. (Tule), GEI/Davids/others (Tulare Lake, Kings) — each has its own ES-table
  wording; extend this table per subbasin.
