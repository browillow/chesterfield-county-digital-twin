# First-slice public-source audit

Audit date: 2026-09-27 UTC  
Scope: one ACS five-year release, three published tract measures, compatible tract boundaries, and one official local public-function document. This is a source/access audit, not an ingested release. Temporary retrievals were made under `/tmp`; no source bytes are committed.

## Decision and integration status

Use the **2019–2023 ACS 5-Year Subject Tables** (`2023/acs/acs5/subject`) for the first slice. The release reports tract geography and publishes the selected measures with estimate (`E`), 90-percent margin of error (`M`), estimate annotation (`EA`), and margin-of-error annotation (`MA`) fields. Join its Virginia/Chesterfield tract keys to the **2023 1:500,000 Virginia Census Tract Cartographic Boundary File** on the 11-character tract GEOID.

The selection is ready for adapter implementation from a schema/meaning perspective, but **live ACS observation retrieval is blocked pending an authorized Census API key or a separately verified official download route**. On 2026-09-27, all three official group-metadata endpoints returned JSON without a key, while an initial keyless observation query followed a redirect to HTTP 200 HTML titled `Missing Key` rather than JSON. The supervisor retried the corrected three-measure query at `2026-09-27T03:53:40Z`: it returned HTTP 302, `X-DataWebAPI-KeyError: 1`, and `Location: https://api.census.gov/data/missing_key.html` (redirect not followed). No account or key was created. T006 must not call this source complete until it obtains and validates observation bytes.

Boundary and local-document retrieval succeeded. Their bytes were inspected in `/tmp`, hashed, and then left outside the repository. The proposed specifications are in `source_specs/`.

## ACS release and measures

Release documentation: <https://www.census.gov/data/developers/data-sets/acs-5year/2023.html>  
Dataset discovery: <https://api.census.gov/data/2023/acs/acs5.html>  
Variable-type documentation: <https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-api-variable-types.html>  
API terms: <https://www.census.gov/data/developers/about/terms-of-service.html>  
Citation/public-use guidance: <https://www.census.gov/about/policies/citation.html>

Reference period is 2019–2023; dataset vintage is 2023. The measures are published subject-table values, not locally derived percentages. `M` is the published ACS 90-percent margin of error. Preserve `EA` and `MA` even when null. An annotation, when present, supersedes interpretation of a numeric sentinel; the adapter must map documented non-values to an explicit non-observed state rather than zero.

| Metric code | Fields | Published label | Unit | Universe | Aggregation / interpretation |
| --- | --- | --- | --- | --- | --- |
| `median_household_income` | `S1901_C01_012E`, `EA`, `M`, `MA` | Households — Median income (dollars) | 2023 inflation-adjusted dollars per household | Households | Median; never sum across tracts. Compare with its own MOE and period. |
| `poverty_rate` | `S1701_C03_001E`, `EA`, `M`, `MA` | Percent below poverty level — Population for whom poverty status is determined | percent | Population for whom poverty status is determined | Published percentage; do not treat as percent of total population or infer individuals. |
| `household_count` | `S1901_C01_001E`, `EA`, `M`, `MA` | Households — Total | households | Households | Published count; additive only when input geographies are mutually exclusive and use the same release. |

The official group metadata is the authority for labels, concepts, types, and companion fields:

- <https://api.census.gov/data/2023/acs/acs5/subject/groups/S1901.json>
- <https://api.census.gov/data/2023/acs/acs5/subject/groups/S1701.json>

`S2501_C06_001E` was investigated and rejected as a renter-share candidate. In S2501, `C06` is the percent distribution within the renter-occupied column and row `001` is that column's total; the label alone does not establish renters divided by all occupied units. It must not be mapped to renter tenure share.

Expected observation request (the key value must come from the configured secret provider and must be redacted from logs/manifests):

```text
https://api.census.gov/data/2023/acs/acs5/subject?get=NAME,S1901_C01_001E,S1901_C01_001EA,S1901_C01_001M,S1901_C01_001MA,S1901_C01_012E,S1901_C01_012EA,S1901_C01_012M,S1901_C01_012MA,S1701_C03_001E,S1701_C03_001EA,S1701_C03_001M,S1701_C03_001MA&for=tract:*&in=state:51%20county:041&key=REDACTED
```

Expected JSON is an array whose first row is the requested field names followed by `state`, `county`, and `tract`; remaining rows are strings/nulls. Construct `geoid = state + county + tract`, preserving zeroes. Expected Chesterfield cardinality is 75 rows if it aligns with the verified boundary file; T006 must treat a mismatch, duplicate GEOID, HTML response, or absent requested column as structural failure.

### Retrieval evidence and blocker

At `2026-09-27T03:45:19Z`, the selected tables' two metadata JSON responses were retrieved successfully:

| URL / artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `S1901.json` | 89,864 | `6fda6e9ed091685a0f9c3a1f6b01b0bd6ce817ef16caed0f7a85725194f6accc` |
| `S1701.json` | 274,324 | `c481faaed946322f0ea2b9f5b4f3292a9f1de455529b9b4f04154eac5b14a85a` |

The initial S1701-only candidate observation request (not the final combined query shown above) followed a redirect and returned 8,531 bytes of HTML (`Missing Key`), SHA-256 `c2f4687e09b80676de7f68dec92ebea395209616dbc6f895520e547c5f68c0f5`. That hash documents a failed retrieval and is not fixture provenance. Census's current examples state that data queries require a key; the key guide says registration is free but email-based. Account creation was out of scope. The API terms permit retrieval/display/analysis, require non-identification behavior, request a specific API attribution notice, permit service limits/termination, and do not promise continuous access. Retain successful API bytes for reproducibility subject to those terms, but also retain sanitized request metadata and checksums because the service itself is not an archival guarantee.

## Compatible tract boundaries

Documentation: <https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.2023.html>  
Exact artifact: <https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_51_tract_500k.zip>

The artifact retrieved successfully on 2026-09-27: 1,773,760 bytes, SHA-256 `172e398e73aa6db00bad3b720ca793dc36628cbfa332d3bd3b80926019f9c8bd`. It contains Shapefile components plus ISO metadata. The DBF has 2,186 Virginia records and 75 rows where `COUNTYFP == "041"`. Relevant fields are `STATEFP`, `COUNTYFP`, `TRACTCE`, `GEOIDFQ`, `GEOID`, `NAME`, `NAMELSAD`, `ALAND`, and `AWATER`; the first verified Chesterfield GEOID was `51041100921`. CRS is NAD83 geographic coordinates (the `.prj` uses degrees).

Compatibility is based on common 2020 Census tract definitions used by the 2023 statistical release and 2023 boundary vintage, not merely similar names. The ACS response key `51` + `041` + six-character tract joins exactly to boundary `GEOID`. Cartographic boundaries are simplified for small-scale thematic mapping; they are appropriate for the proposed choropleth, not parcel/location authority. Preserve the original archive and metadata, hash any generated display geometry separately, and never calculate area/distance directly in its geographic degrees.

The Census API terms cited above directly govern API content. The boundary page and embedded ISO metadata describe public download and intended use, but this audit did not locate a boundary-specific retention duration or license grant. T006 may retain the downloaded federal artifact for local reproducibility, with Census attribution and the source URL/checksum, but should record the absence of an explicit retention promise rather than infer permanence.

## Official local public-function document

Index page: <https://www.chesterfield.gov/251/Budget-Development-and-Documents>  
Exact PDF route: <https://www.chesterfield.gov/DocumentCenter/View/36170/>  
Title: *FY2025 Budget and FY2025–FY2029 Capital Improvement Program*  
Publisher: Chesterfield County, Virginia  
PDF metadata: created 2024-07-01; modified 2024-12-17; 424 pages  
Retrieved 2026-09-27: 25,649,160 bytes; SHA-256 `d0d52e068d3b02dd6b134b2b08dbe29f65b3311197e3b8aee12f72e88650136d`

Use the Social Services departmental summary. Exact locators:

- PDF page 229, printed page 211, heading `Departmental Summaries > Social Services > Description`: department scope, three divisions, program areas, mission, and the explicit caveat that services cover both Chesterfield County **and the City of Colonial Heights**.
- PDF page 230, printed page 212, heading `Department Blueprint: Priorities, Programs, and Performance`: program list and descriptions for Adult Services and the Assessment and Resources Team.
- PDF page 231, printed page 213, program headings `Housing Choice Voucher` and `Public Assistance`: public-function descriptions related to housing affordability and low-income assistance.

These passages support a linked profile describing reported public functions. They do not establish that a tract-level ACS condition caused demand, prove program eligibility, or isolate Chesterfield-only service counts. Store them as reported document claims with page/heading locators.

The stable numeric DocumentCenter route returned PDF bytes; a descriptive suffix variant returned 404 during this audit, so use the numeric route. The county index demonstrates public availability and maintains annual-budget links, but no explicit redistribution license, guaranteed retention period, or immutable-version promise was found. Retain one local evidence copy for private research/reproducibility, provide citation/link rather than republishing the whole PDF, and mark redistribution and long-term source availability as unconfirmed.

## Required T006 validation

1. Obtain an authorized API key through the project's secret process or verify an official non-key download route; never commit/log the key.
2. Save response headers/status/content type before accepting bytes. Reject the observed HTTP-200 HTML failure.
3. Validate all 12 measure fields plus `state`, `county`, and `tract`; parse estimates/MOEs independently from annotations and map documented sentinels to value states.
4. Require 11-character GEOIDs, unique tract/metric/period natural keys, exactly one matching boundary feature per observation, and review any cardinality other than the currently observed 75.
5. Keep the ACS universe/unit on each metric definition, preserve the 2019–2023 period and 2023 vintage separately, and label all MOEs as published 90-percent uncertainty.
6. Retain raw successful bytes and the boundary ZIP only if the operational retention decision accepts the cited terms/caveats. Hash every retained artifact. For the county PDF, retain locally but block redistribution in exports until rights are clarified.

## Reproduction notes

The audit used bounded `curl` requests to the exact URLs above, `shasum -a 256`, `unzip -l`, a Python standard-library DBF header/record reader, `pdfinfo`, and `pypdf` text extraction. Temporary paths began `/tmp/cdt-`; they are not application fixtures. Proposed TOML is syntax-checked separately and contains no secrets or source bytes.
