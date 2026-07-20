# Backlog

## Extract subsidence benchmark history from individual GSA annual reports
DWR's central export lacks the pre-2019 / annual-since-2000 benchmark leveling for several
subbasins (notably **Tulare Lake, 5-022.12**). Fill it by pulling each GSA's annual-report
submittal from the SGMA portal and extracting the subsidence tables, then normalizing to the
survey basis in SURVEY_BASIS.md and appending to `data/subsidence_data.csv`.

Tulare Lake GSAs to source: North Fork Kings, South Fork Kings, Southwest Kings,
Mid-Kings River, El Rico, Tri-County WA.

Feasibility depends on whether each report has a machine-readable data upload vs. PDF tables.

## Add PDF URLs to annual_report_catalog.csv
The catalog currently lists which reports exist (subbasin × area × year). Add direct PDF links
once a reliable SGMA-portal document endpoint is identified.
