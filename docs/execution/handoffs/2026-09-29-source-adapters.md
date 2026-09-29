# Session handoff: typed source adapters accepted

Date: September 29, 2026 (America/New_York).
Checkout: `/Users/jordan/projects/osier/enterprise/chesterfield-county-digital-twin`.
Branch / HEAD: `main` / `97841eb` (`feat: first checkpoint`). No Git mutations.

Requested supervisor: GPT-6 Astra; this tool interface does not expose supervisor-model verification or switch it. Three fresh-context workers explicitly requested **`gpt-6.1-sol`**; tool responses exposed task IDs, not independent actual-model metadata. No substitute worker model was requested. User direction superseded the older `gpt-5.6-sol` text, now updated in standing instructions/templates.

## Starting state and outcome

Prior state correctly described the accepted skeleton but its HEAD/untracked notes were stale: the skeleton was committed at `97841eb`. The only pre-existing project modification was the user's starter-prompt wording; preserved. No planning or skeleton rebuild occurred.

**T006a accepted. Full T006 remains blocked.** Implemented typed unpublished candidate/provenance contracts, common byte-envelope validation, bounded ACS/boundary/document adapters, synthetic failure tests, cross-source consistency checks and an offline audit replay command. No network fetch service, persisted ingestion, new migration, API capability, release service or UI feature was introduced.

Supervisor owned `domain/candidates.py`, `sources/{__init__,common,validation}.py`, dependency manifests/locks, contract/integration tests, replay script and execution records. Worker exclusive ownership was:

- ACS: `sources/acs.py`, `tests/test_acs_adapter.py`.
- Boundary: `sources/boundaries.py`, `tests/test_boundary_adapter.py`.
- Document: `sources/documents.py`, `tests/test_document_adapter.py`.

Shared contract examples passed before delegation. Workers read focused audit/spec/contracts only. Supervisor reviewed source and tests, requested ACS corrections (numeric median-bound annotations, percentage MOE range, estimate/MOE semantic separation), reviewed boundary parsing/cardinality errors and limits, then integrated and independently verified all adapters. All workers completed; supervisor reclaimed file ownership.

## Evidence and behavior

- ACS: 225 synthetic observation candidates across 75 synthetic rows; source estimate/MOE and EA/MA annotations remain separate. Retains units/universe, 2019–2023 period, 2023 vintage, 2020 tract definitions, aggregation, 90% uncertainty and exact JSON row/field locators. Unknown annotations, malformed/header/duplicate/geography failures return no partial candidates. Identical bytes/spec/transform repeat identity despite a new retrieval event; changed content changes fingerprint under the same natural key.
- Boundary: supervisor replayed `/private/tmp/cdt-boundary.zip`, exact SHA-256 `172e398e73aa6db00bad3b720ca793dc36628cbfa332d3bd3b80926019f9c8bd`. Validates 2,186 state records and returns 75 county candidates. First GEOID `51041100921`, DBF record 28. Preserves EPSG:4269/WKT, source square-metre areas and separately hashed normalized geometry. Candidate-list digest `712ff16b58684f430c43a1e122442947c526dcc65d8b910e11e75b71685faf45`.
- Document: supervisor replayed `/private/tmp/cdt-fy2025`, exact SHA-256 `d0d52e068d3b02dd6b134b2b08dbe29f65b3311197e3b8aee12f72e88650136d`. Returns 3 exact page excerpts, character lengths 3372 / 3338 / 3556, PDF 229–231 / printed 211–213. Page-text hashes/spans and both locality codes/caveat preserved. Candidate-list digest `467279e734e21615d60b858061cb18d7809599fa9b0514a72c2de8ddef9a5bee`. Whole-PDF redistribution remains unconfirmed.
- Combined supervisor probe normalized explicitly synthetic ACS rows using the real boundary GEOIDs, then joined all three adapters: 303 candidates with explicit test opt-in; default real-slice validation rejects `synthetic_evidence` and returns no candidates. This establishes interface compatibility, not real observation evidence.

The two retained artifacts were already downloaded during the previous audit. No fresh boundary/PDF network access was checked. Replay uses the original spec retrieval times and declared expected successful status/media types; original HTTP headers were not re-verified. Source bytes and document text remain outside Git. Official Census annotation documentation was inspected; no ACS observation request was attempted this session.

## Verification

From the checkout:

- `.venv/bin/pytest -q`: **132 passed**, one pre-existing Starlette/httpx deprecation warning. Covers all existing runtime/API/storage/OpenAPI drift checks plus new contracts/adapters/integration tests.
- `.venv/bin/ruff check src tests scripts`: pass after correcting replay-script import order. `git diff --check`: pass after Markdown whitespace cleanup.
- `UV_CACHE_DIR=/private/tmp/cdt-uv-cache UV_PYTHON_INSTALL_DIR=/private/tmp/cdt-python uv sync --locked --offline`: pass, 26 packages resolved / 25 checked. Pinned additions pyshp 2.3.1 and pypdf 6.1.1; accepted Python pin unchanged.
- `.venv/bin/python scripts/replay_audited_sources.py --boundary /private/tmp/cdt-boundary.zip --document /private/tmp/cdt-fy2025`: pass, 75 boundaries / 3 excerpts / no issues. Emits hashes/counts only, not source text.
- Combined adapter probe described above: pass; actual normalized boundary keys + synthetic ACS + audited PDF, synthetic default rejection confirmed.

Initial dependency retrieval failed under sandbox DNS; the authorized scoped download succeeded, followed by offline lock verification. Initial integrated lint caught one import-order issue and whitespace; corrected. No remaining failing check. Frontend/build/browser checks were not repeated because no frontend, runtime or API contract changed. Previous acceptance still applies.

## Decisions and limits

[D012–D014](../decisions.md): byte normalization separated from persisted ingestion; source interpretation/parser limits; current worker selection. [Contracts](../contracts.md) index executable interfaces and remaining closure obligations.

The last verified ACS observation access remains September 27 HTTP 302 to `missing_key.html` with `X-DataWebAPI-KeyError: 1`. Full T006 requires authorized observation bytes or a separately verified official download route. Fixtures, caller-declared metadata and metadata access cannot satisfy it. No accounts, credential searches/requests, outreach, publication or spending commitments.

Production boundary/PDF bytes must match audited pins. Changed artifacts require spec review. Boundary containment grouping is not full topology validation, and source NAD83 is not a prepared WGS84 display layer. PDF byte/page/text/decoded-stream limits bound accepted outputs, not peak parser memory/CPU. Unpinned arbitrary documents need future worker-process resource isolation. No artifact storage, candidate persistence, complete release closure/sealing/activation, or public/private export changes were made.

## Continuity

All new source modules, tests and replay script are untracked; modified manifests/lock, AGENTS and execution/audit documents are uncommitted alongside the preserved starter-prompt change. No commit/reset/push. Sibling workspace content untouched. All worker turns and tool shell commands completed. No server, browser, background job or automation was started. Only existing temporary source/runtime/dependency caches remain; no real research root initialized.

**Next ready: T006b**, retained public artifacts and unpublished candidate staging. Follow its concrete packet in [backlog](../backlog.md). It can progress with real boundary/document bytes and isolated synthetic validation independently of ACS access; no activation or default reads. Full T006 still needs real authorized ACS data, then T007/T008. [Start-session](../start-session.md) has been updated with this handoff and next checkpoint.
