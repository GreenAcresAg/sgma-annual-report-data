# Source referencing — every number is verifiable

**All source documents (GSPs + annual reports) live in Google Drive:**
https://drive.google.com/drive/folders/12mUnbM_7podiWyyj2vviOV9u3gkkQLhp

Every dataset in this repo must let a human open the exact document and page to check a value.

## The rule
Each extracted value carries:
- **`source_doc`** — the human-readable **GSP/report name including version**, e.g.
  `Kaweah Subbasin GSP — Greater Kaweah GSA (Draft, 2024)` or
  `Tule Subbasin Annual Report WY2025`. (Not a bare filename.)
- **`page`** (and/or table number) — where in that document the value appears.

`docs/source_documents.csv` is the **registry**: it maps each `source_doc` /
`ref_id` to its `local_filename`, subbasin, GSA, version, date, and key table/page
locations — and those filenames are what live in the Drive folder above.

## Where provenance lives per dataset
| Dataset | source_doc | page/table |
|---|---|---|
| `gsp/gsp_metrics.csv` | `source_doc` col (canonical name) | `page` col |
| `data/westside_subsidence_network.csv` | `source_doc` col | `source_page` col (GSP Table 3-15, p361) |
| `data/tule_benchmark_coords.csv` | `source_doc` col | `source_page` col (LTRID GSP Table 4-4, p278) |
| `data/benchmark_displacement_annual.csv` | `source_doc` col | `source_ref` col (report table + page) |

## For new extractions (going forward)
- Add a row to `docs/source_documents.csv` for any new GSP/report before extracting from it.
- Extractors should emit `source_doc` (canonical name) + `page`/table on every row.
- When a value is a range or model output, note that in the row's `notes`/`source_ref`.
