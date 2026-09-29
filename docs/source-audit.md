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


## T006a replay and interpretation update — September 29, 2026

The accepted adapters were independently replayed against the retained boundary ZIP and PDF above: exact audited hashes matched; 75 boundary candidates and three exact extracted page candidates validated. No new download occurred, and no source bytes/text were added to Git. `scripts/replay_audited_sources.py` reproduces this check when the temporary audit artifacts are available; its HTTP envelope is declared from the original audit/spec expectations rather than fresh headers.

ACS checks remain explicitly synthetic. [Official annotation guidance](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html), inspected this session, informs independent E/M interpretation: preserve nulls/sentinels/annotations, recognize numeric open-ended median annotations as bounds rather than point estimates, and preserve controlled-MOE annotations without fabricating observed zero. Percentage MOE is not clamped to the percentage estimate range. Unknown interpretations fail closed. The prior live ACS blocker remains unresolved; this session made no observation request.


## T006b retained replay — September 29, 2026

The same audited boundary ZIP and county PDF were retained with their exact specification bytes in an isolated external staging root. Durable readback preserved 75 boundaries and 3 exact excerpts; identical repeats reused all 78 candidate versions and produced distinct retrieval/import events. A separate-process supervisor replay normalized the retained inputs and confirmed complete typed equality. Both original artifact hashes above remain unchanged; no source bytes or county text were committed.

This was offline replay using the original specification retrieval times and declared expected status/media envelopes. No fresh network request or real ACS observation access was tested. ACS persistence checks used explicitly synthetic runs, separate from the real boundary/document run. Raw/spec hashes, transform identity and retention/redistribution caveats survive staging. County PDF remains local research evidence with unconfirmed redistribution. See the [retained-staging handoff](execution/handoffs/2026-09-29-retained-staging.md).

## T007a persisted validation — September 29, 2026

A fresh external store re-staged the already audited boundary/PDF bytes and persisted an explicitly selected real-mode report over 75 boundaries and 3 document excerpts. Both imports passed retained-byte/readback verification, but the report correctly failed the three-source gate with missing ACS. Ordered input/version membership and exact source/spec/transform pins survive in the immutable report. Separate-process worker and supervisor readback verified the result; no source text or bytes entered Git. See [candidate-validation handoff](execution/handoffs/2026-09-29-candidate-validation.md).

No fresh HTTP access or real ACS observation was obtained. Complete three-source tests used wholly synthetic byte fixtures in separate runs and validate only as synthetic. Report reads are historical attestations; current artifact availability requires explicit revalidation. The proposed next official alternate ACS route audit was unexecuted at T007a; see the dated T006c result below.


## T006c official alternate-route audit — September 29, 2026

**Bounded audit complete; no compatible ACS observation bytes acquired.** The exact accepted keyless query was retried at `2026-09-29T23:16:53Z`: HTTP **302**, `X-DataWebAPI-KeyError: 1`, `Location: https://api.census.gov/data/missing_key.html`, zero-byte body, no content type returned. Redirect was not followed. This freshly confirms the direct compatible API route's key requirement; no credentials were sought. Initial sandbox DNS failure was resolved by an authorized network retry and is not publisher evidence.

[Sanitized HTTP evidence](execution/evidence/2026-09-29-acs-routes.json) records every coordinator probe's exact URL, UTC time, status, selected headers, byte length and full SHA-256. Raw documentation, headers and the bounded probe script remain outside Git in `/private/tmp/cdt-t006c-audit-20260929`. These are documentation/error-response hashes, **not observation provenance**. Requests used HTTPS, no automatic redirects, a 10-second connect timeout, 30-second total timeout and 2 MB maximum body. No authentication or accounts were used.

| Official route / evidence | Result and interpretation |
| --- | --- |
| [ACS Data Tables](https://www.census.gov/programs-surveys/acs/data/data-tables.html) | HTTP 200 HTML, 369,145 bytes. Its Subject Tables section links Census API and [five-year Subject Tables on data.census.gov](https://data.census.gov/cedsci/all?d=ACS+5-Year+Estimates+Subject+Tables). Product availability is documented; selected observations are not thereby verified. |
| [Data via FTP](https://www.census.gov/programs-surveys/acs/data/data-via-ftp.html) and [Summary File](https://www.census.gov/programs-surveys/acs/data/summary-file.html) | HTTP 200 HTML, 340,276 / 358,156 bytes. Summary File supplies Detailed Tables, not the selected Subject Tables; substituting B/C tables or computing a poverty rate would violate the pin. |
| [2023 ACS data index](https://www2.census.gov/programs-surveys/acs/data/2023/) | HTTP 200 HTML, 14,983 bytes. Exposed children are one-year geographic comparison and ranking tables; no compatible tract Subject file verified there. This is a bounded finding, not proof no alternate exists anywhere. |
| [Legacy Subject page](https://www.census.gov/programs-surveys/acs/data/data-tables/subject-tables.html) | HTTP 301 HTML, 326,146 bytes, redirects to `/acs/www/data/data-tables-and-tools/subject-tables/`; coordinator did not follow. Worker separately read the official destination, which defaults to a later release. Latest-default links cannot replace 2019–2023. |
| [February 2026 GEOID download guide](https://www2.census.gov/data/api-documentation/how-to-download-tables-as-a-csv-file-that-includes-geoids.pdf) | HTTP 200 PDF, 520,856 bytes; SHA-256 `a4dd3fb94473bafc33bfbf7395df68d75301b13786102f52479d3d9ee0b26429`. Documents selecting a table/vintage and downloading ZIP containing CSV; warns customizations do not transfer. This format differs from the accepted API JSON adapter. |

The Sol worker also inspected official [2023 table-shell documentation](https://www.census.gov/programs-surveys/acs/technical-documentation/table-shells/2023.html) and exposed S1701/S1901 XLSX shells: layouts/metadata are not observations. The linked data.census.gov page required JavaScript in the web tool; constructed pinned table links could not be opened by that tool. Neither is a measured Census HTTP failure or proof that export access is blocked. No native browser/UI export was attempted. Worker discovery used web-rendered documentation; only the coordinator probes have retained HTTP envelopes.

**Supervisor review / D018:** the documented ZIP/CSV route is an unacquired alternate representation, not input accepted by `acs-subject/1`. Stop before export acquisition/ingestion for the separately scoped T006d representation review. Do not reshape an export into purported API raw bytes, falsify its retrieval URL, infer null EA/MA, or substitute Detailed Tables/fixtures. Exact selected measures, tract coverage, E/M/EA/MA equivalence, null/sentinel meaning, units/universes and published 90-percent MOEs remain unverified for any export. No source spec, adapter, transform or retention policy changed.

Remaining blocker: direct compatible API observations require authorized access; the official export route still needs bounded acquisition and source/spec/locator/adapter review. Full T006 is blocked; T006c itself is complete as an audit. No new staging root or real ACS import/report was created. A fresh current-schema external root is required if future compatible observations can be staged; preserve all earlier roots.

The existing migration-003 real boundary/document selection was **explicitly revalidated**, not merely read historically. Both imports / 78 candidate versions still verified and reused report `c17e2b341bec5814fd6107697fa3c74bb07cad58fe8c2e1d6e06ac89e8358fab`, with `missing_source` / `incomplete_source`, `valid=false`, `real_slice_valid=false`. Current-root database and object hashes remained unchanged; old 002 root was untouched. This is current retained-evidence verification, not fresh boundary/PDF retrieval or a real three-source pass. Exact command and IDs are in the [T006c handoff](execution/handoffs/2026-09-29-acs-route-audit.md).

## T006d Subject export preflight — September 29, 2026

**Bounded review complete with an acquisition-tool blocker; zero exports acquired.** Official public UI navigation reached both 2023 ACS 5-Year Subject ZIP vintage dialogs for S1901/S1701. Only 2023 was checked in each. UI size estimates were 17.9 kB and 56.3 kB; these are not verified transfer sizes. [Preflight evidence](execution/evidence/2026-09-29-subject-export-preflight.json) records exact page URLs/control observations and their UTC times. The JSON is a coordinator transcription of supported browser observations, not raw publisher response evidence. No HTTP download status/media/hash is claimed.

Chrome was unavailable, but the supported in-app browser worked. An initial direct tract selector returned a filter-specific unavailable result; official geography navigation resolved to all Chesterfield County tracts. Subsequent search defaulted to 2024 and was explicitly changed to 2023 for each table. The final observed URLs retained the initial unrecognized geography selector alongside the UI-generated county/all-tract selector. This does not prove 75-tract coverage; start from a clean selection and inspect actual GEOIDs when acquisition resumes. Transient loading/selector failures resolved and are not evidence of publisher denial. Rendered UI values are not retained raw observations.

The supported browser download API exposes a saved path and wait timeout without an enforceable byte cap/cancellation or the actual download response URL/status/media envelope. Both final ZIP dialogs had zero links, only a download button. The page-assets API cannot bundle ZIP exports, and the S1901 page offered no WebMCP tools. Under predeclared 20 MB/60-second transfer limits (100 MB expanded/32 members per archive), Astra stopped before final Download ZIP. No export transfer was refused by Census; no account/key was sought and no unpublished endpoint was inspected or invoked. Original archive/member bytes and hashes therefore remain absent.

### Documentation versus actual representation

The [official February 2026 GEOID guide](https://www2.census.gov/data/api-documentation/how-to-download-tables-as-a-csv-file-that-includes-geoids.pdf) supports the ZIP → vintage → download workflow and CSV data member, while warning that table customizations do not transfer. The [format FAQ](https://www.census.gov/data/what-is-data-census-gov/guidance-for-data-users/frequently-asked-questions/what-does-the-output-actually-look-like.html) distinguishes ZIP from presentation downloads; its inspected web text does not establish selected member schema.

The [2023 ACS documentation](https://www.census.gov/data/developers/data-sets/acs-5year/2023.html), [S1901 metadata](https://api.census.gov/data/2023/acs/acs5/subject/groups/S1901.html) and [S1701 metadata](https://api.census.gov/data/2023/acs/acs5/subject/groups/S1701.html) support existing 2019–2023 pins: household count `S1901_C01_001`, household median income `S1901_C01_012` in 2023 inflation-adjusted dollars, and published poverty percentage `S1701_C03_001` for the population whose poverty status is determined. These labels/metadata are not observations or proof of exported fields.

[Variable-type documentation](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-api-variable-types.html) and [annotation notes](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html) support annotation priority, distinct sentinel meanings and median bounds in the API. [ACS MOE training, slide 12](https://www.census.gov/content/dam/Census/programs-surveys/acs/guidance/training-presentations/20170419_MOE.pdf) establishes Census's standard 90% confidence level. None proves that selected ZIPs contain separate EA/MA columns or that a blank/absent column equals JSON null. All actual delivered E/M/EA/MA, units/universes, MOE field identity, tokens and geography remain unverified. Sol's external documentation note records the required byte checks; its hashes identify a local research note only.

### Supervisor disposition

[D019](execution/decisions.md#d019--subject-export-acquisition-tool-boundary-2026-09-29) preserves accepted source specs and `acs-subject/1`. No export contract or implementation is accepted. Two original archives also conflict with today's one-raw-artifact ACS staging and one-import-per-source validation contract; a future reviewed packet must preserve each original retrieval/archive/member plus distinct derived identity and full verified readback. No converted CSV masquerading as raw API JSON or fabricated annotations.

[T006e](execution/backlog.md) is a blocked conditional continuation requiring supported bounded acquisition with actual response provenance, then actual-byte review. No new staged imports, persisted report, historical report read or current revalidation occurred; earlier roots were unopened. T006c's prior two-import verification remains historical. Full T006 stays blocked; T007/T008 remain pending. No release sealing/activation/default reads are authorized by this review. [Session handoff](execution/handoffs/2026-09-29-subject-export-review.md).
