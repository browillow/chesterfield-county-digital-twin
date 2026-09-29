# Session handoff: official ACS route audit

Date: September 29, 2026 (America/New_York).
Checkout: `/Users/jordan/projects/osier/enterprise/chesterfield-county-digital-twin`.
Branch / HEAD: `main` / `a08ba68` (`hjhkj`). Existing accepted T007a implementation, tests and documentation were already uncommitted/untracked; preserved in place. No Git mutations.

Explicit model requests: `gpt-6-astra` supervisor for scope/source/spec decisions and final review; `gpt-6.1-sol` for bounded official route discovery, both with fresh focused context. Returned task IDs do not independently confirm actual runtime model metadata. Parent coordinator executes the supervisor's decision, owns repository edits and independently reviews integrated evidence.

## Outcome and decision

**T006c bounded audit complete; full T006 remains blocked.** Fresh exact compatible keyless API request returns HTTP 302 to `missing_key.html` with `X-DataWebAPI-KeyError: 1`. Official data.census.gov ZIP/CSV Subject export workflow is documented, but no export observation bytes or E/M/EA/MA equivalence were obtained. It is not evidence of an unavailable export service. Summary File Detailed Tables and XLSX shells are not substitutes for the pinned Subject Tables.

Astra reviewed the representation boundary and explicitly closed T006c before UI export acquisition/ingestion (D018). No spec/adapter/transform/retention change, observation import or newly staged report. The accepted `acs-subject/1` requires exact API JSON, actual accepted URL/selectors, 75 tract rows and 12 measure fields. Never convert an export and pretend its bytes/URL are the API response. No sealing/activation/default baseline reads authorized.

Next ready **T006d**: acquire at most one bounded official export per S1901/S1701 into a fresh external audit directory, inspect actual geography/release/three measures/E/M/EA/MA/nulls/sentinels/units/universes/MOEs, retain raw archive/member identities and actual retrieval envelopes, then settle supervisor source/spec/locator/adapter contracts. It is a review packet, not an implemented export parser. Full T006 and T007/T008 remain blocked/pending until their real evidence/release gates are met.

## Ownership and changes

- `astra_supervisor`: read-only supervisor decisions and integration review, no writes or network probes.
- `official_route_discovery`: exclusive `/private/tmp/cdt-t006c-route-discovery.md` only, official web documentation/index inspection. Repository read-only; no additional workers. Discovery completed and ownership returned.
- Parent coordinator: all repository edits, exact bounded HTTP probes and explicit current-evidence revalidation. No competing writers.

This session changed `docs/source-audit.md`, execution state/backlog/decisions/start-session, this handoff and `docs/execution/evidence/2026-09-29-acs-routes.json`. All runtime/test/spec/migration/README/contract changes visible in the checkout belong to the preserved T007a starting work, not this audit. Prior untracked T007a artifacts remain listed in its [handoff](2026-09-29-candidate-validation.md). No source bytes, county excerpts or private data entered Git.

## Evidence

Seven coordinator HTTP probes have complete sanitized envelopes in [route evidence](../evidence/2026-09-29-acs-routes.json); interpretation and official links are in [source audit](../../source-audit.md#t006c-official-alternate-route-audit--september-29-2026). Exact raw bodies, headers, per-probe JSON and `probe.py` remain external in `/private/tmp/cdt-t006c-audit-20260929` (temporary, may disappear). The repository JSON preserves route/status/media/length/full hashes but does not retain source bodies. No observations or fixture substitution.

Fresh accepted query: `2026-09-29T23:16:53.570019+00:00`, 302, zero body, no media type supplied, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Initial sandbox DNS error was environmental; authorized network retry succeeded and returned publisher missing-key evidence. Other public probes returned five 200 documentation/index responses and one legacy Subject-page 301; no redirects followed. Byte bounds: 2 MB, 10-second connect, 30-second total timeout. No credential search/request or account work.

Official February 2026 GEOID guide describes ZIP containing CSV, not API JSON. Worker separately found JavaScript required at the linked Subject UI; pinned constructed table URLs failed in the web tool. These are tool limitations, not measured publisher denial. No browser/UI export, unsupported backend access, bulk download or observation-body claim.

## Current retained-evidence revalidation

The existing current-schema migration-003 root was available; no fresh staging root was needed because no new observations were obtained. Ran the actual accepted validator with explicit IDs, not merely historical report readback:

```sh
.venv/bin/python scripts/validate_audited_sources.py --data-dir /private/tmp/cdt-t007a-replay-20260929-7f3c28 --run-id 4a705204-7159-44bb-9077-c9fd9078e29b --import-id 43176614-544a-49b9-b4d1-74c9ba63c35f --import-id f8d605c9-97be-4bf1-9d88-b8f7daa58bc8
```

Exit **1**, expected persisted invalid selection: `synthetic=false`, two verified inputs / 78 versions, `valid=false`, `real_slice_valid=false`, `missing_source` and `incomplete_source`. Same report ID `c17e2b341bec5814fd6107697fa3c74bb07cad58fe8c2e1d6e06ac89e8358fab`. A wrapper verified these exact results and compared every current-root `.sqlite` and object SHA before/after: unchanged. JSON result is external `revalidation.json`. Old 002 root was never opened or changed; no ledger rewrite or upgrade. This confirms retained boundary/PDF evidence currently verifies, not fresh access or three-source completeness.

## Verification and limitations

- `.venv/bin/python` evidence probe: re-read all seven external bodies, checked manifest lengths/full SHA-256 and allowed header fields; all passed. Asserted exact API redirect/key error.
- Passed the actual zero-byte HTTP-302 response and actual absent media header to unchanged `normalize_acs(..., synthetic=False)`: rejected with `http_status`, zero candidates. No staging/retention as observations.
- `git diff --exit-code -- source_specs src/chesterfield_twin/sources src/chesterfield_twin/storage/migrations/baseline/001_initial.sql src/chesterfield_twin/storage/migrations/baseline/002_candidate_staging.sql src/chesterfield_twin/storage/migrations/private/001_initial.sql`: pass; accepted pins/adapters/earlier migrations unchanged.
- `git diff --check`: pass. 25 local Markdown link targets across six updated documents and evidence JSON checked successfully.
- No broad pytest/frontend/build rerun for documentation-only audit; prior T007a test results remain historical in its handoff and state, not newly claimed. Live HTTP probes, rejection check and explicit retained-evidence revalidation are this session's checks.

Final Astra review accepted T006c and D018 with no semantic/scope corrections. Supervisor independently recomputed all seven retained body lengths/hashes and matched external envelopes to the repository manifest; confirmed unchanged accepted specs/adapters/earlier migrations. Its two record corrections (qualify T007a historical retrieval wording and mark this review complete) are applied. Parent independently reviewed integrated evidence and continuity records.

Process accounting: route worker and supervisor completed; all ownership returned. All shell commands completed; no long-running process/server/browser/automation started. No publication, contact, spending or credential activity. Existing local runtime, private-data separation and release pins preserved.
