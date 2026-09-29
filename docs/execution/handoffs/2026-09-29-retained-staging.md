# Session handoff: retained candidate staging accepted

Date: September 29, 2026 (America/New_York).
Checkout: `/Users/jordan/projects/osier/enterprise/chesterfield-county-digital-twin`.
Branch / HEAD: `main` / `b623129` (`feat: next checkpoint`). No Git mutations.
Requested supervisor: GPT-6 Astra; this tool interface cannot inspect/switch its actual model. Three fresh-context workers explicitly requested `gpt-6.1-sol`; tool responses exposed task IDs, not independently confirmed actual model metadata. No alternative worker model was requested.

## Starting state and acceptance

Reconciled stale prior state: accepted T006a was already committed at `b623129`; only the user's `start-session.md` correction/removal of obsolete handoff prose was modified. Preserved that intent and advanced the reusable prompt. No accepted skeleton/adapter work was repeated.

**T006b accepted. Full T006 remains blocked.** Implemented baseline-only retained staging from the accepted adapters, immutable indexed candidate versions, separate retrieval/import events, explicit real/synthetic runs, full typed rehydration with artifact/integrity checks, and an audited replay tool. No network ingestion, active release, HTTP capability, UI change, user export or private research store initialization.

Supervisor settled [T006b contracts](../contracts.md) and [D015](../decisions.md) before delegation and owned shared storage, migration 002, integration tests, dependencies (unchanged) and execution records. Exclusive worker ownership:

- `staging_tests`: `tests/test_staging.py`, synthetic persistence/failure acceptance.
- `staging_replay`: `scripts/stage_audited_sources.py`, `tests/test_staging_replay.py`, offline audited staging verification.
- `staging_review`: read-only review; no write ownership or findings within scope.

Supervisor reviewed all worker code and tests, added independent migration/metadata/retention/transform/I/O checks, and verified the retained store in a separate process. An injected SQLite abort exposed an unwrapped exception; translated it to `StorageError` after rollback and confirmed retry. Final supervisor review extended the same boundary to filesystem I/O and verified directory-sync failure prevents metadata commit.

## Result and evidence

`storage/staging.py` uses required external initialized roots. Each run has an immutable synthetic mode; each successful import gets its own retrieval event and ordered membership. Fingerprints reuse the accepted full candidate identity excluding retrieval; payloads retain locators, units/universes, uncertainty, annotations, periods/vintage, geometry/excerpt hashes, retention and redistribution. Exact source and spec bytes live in SHA-256 objects; retained specs preserve publisher/terms and other metadata not flattened into candidate fields. Only the three reviewed local retention policies are accepted. County PDF redistribution remains unconfirmed.

Validation occurs before retention. Complete object file and directory synchronization precedes one SQLite metadata transaction. Interrupted operations may leave complete unreferenced bytes, which retry reuses; corruption is rejected, not replaced. Readback re-verifies raw/spec hashes and sizes, ordered membership digest/count, typed candidate fingerprints/index lineage and event consistency. Services never connect the strategy store or mutate releases. Caller declarations remain a trust boundary, not proof of source access/authorization.

Audited real-only replay root remains at `/private/tmp/cdt-t006b-worker-replay-20260929-4c8f19`. It holds 78 unique versions, four raw/spec objects, four imports/retrieval events (initial plus repeat for each source), no releases/memberships/active pointer. Supervisor added only a synthetic private test sentinel and confirmed it never appears in candidate readback. No genuine private data was read.

| Evidence | Candidates | Exact raw SHA-256 | Exact spec SHA-256 | Transform |
| --- | --- | --- | --- | --- |
| 2023 Virginia boundary ZIP | 75 | `172e398e73aa6db00bad3b720ca793dc36628cbfa332d3bd3b80926019f9c8bd` | `e71cd8d72fefc05a585148dff44e7b1b5ccaa124b73a033d0dcbb51a4006f07a` | `boundaries/1` |
| FY2025 Social Services PDF excerpts | 3 | `d0d52e068d3b02dd6b134b2b08dbe29f65b3311197e3b8aee12f72e88650136d` | `77ece34af9e1c6f9acd2a4f63893c53468fadda3a56264dfdf87f8369d5bdf38` | `county-budget-pypdf-6.1.1/1` |

Both source hashes match the original audit. Repeat imports added zero candidate versions and distinct events. Worker full-batch readbacks matched accepted normalization; separate-process supervisor read all four imports and independently re-normalized both retained source/spec inputs, confirming complete equality. Geometry remains source NAD83; documents preserve PDF 229–231/printed 211–213 and both locality scopes. No source text/bytes were added to Git or summary output.

These were already retrieved audit bytes. Original spec retrieval times and caller-declared expected status/media envelopes were used; no HTTP headers or current access were re-verified. ACS checks used 75 generated rows/225 candidates in separate synthetic runs, covering zero/suppressed/unavailable states, bounds, raw annotations, 90% MOEs and source/spec/transform revisions. No real ACS observation was acquired or staged.

## Migration and verification

New `storage/migrations/baseline/002_candidate_staging.sql` adds run/index/import/member tables and immutable metadata/membership guards. Fresh initialization applies it; old 001 stores fail closed. The rejection test compared both old database files byte-for-byte after initialization, compatibility and staging attempts. No upgrade or recovery implementation exists. Accepted checksums remain:

- Baseline 001: `44ddafb2a26c5781cb35d4345a17106ac892e603267a9f8b128d2fe8cfabbd93`.
- Private 001: `77e1e2e2df710676b00b3c37b40b1292cae78d47c9eb2be7ebdffe4abf7ca616`.

Commands from the checkout:

- `.venv/bin/pytest -q`: **167 passed**, existing Starlette/httpx deprecation warning only.
- `.venv/bin/pytest -q tests/test_staging.py tests/test_staging_integrity.py tests/test_staging_replay.py`: **35 passed** (16 + 10 + 9); fixtures/mocks are explicitly separate from real replay.
- `.venv/bin/ruff check src tests scripts`: pass. `git diff --check`: pass.
- `.venv/bin/python scripts/stage_audited_sources.py --boundary /private/tmp/cdt-boundary.zip --document /private/tmp/cdt-fy2025 --data-dir /private/tmp/cdt-t006b-worker-replay-20260929-4c8f19`: exit 0, 75/3 candidates, full roundtrip/reuse verified.
- Separate `.venv/bin/python -` supervisor probe: `check_initialized`, read all four `staging_import` rows, call `read_import`, re-normalize `ArtifactStore.read` source/spec inputs for each source and assert complete equality; inspect 78 versions/4 objects/4 events, empty release tables, null active pointer and private sentinel exclusion. Passed.
- `shasum -a 256` on both 001 files plus comparison to Git HEAD: unchanged.

Dependency files, pins, adapter implementations and API/OpenAPI/frontend were unchanged. No dependency synchronization, frontend build or browser rerun was needed. This checkpoint does not establish future release closure, retention-filtered exports, fetch/job recovery or hard parser resource isolation.

## Remaining work and continuity

Last verified ACS observation route remains September 27 HTTP 302 to Census `missing_key.html` with `X-DataWebAPI-KeyError: 1`. Full T006 needs authorized observation bytes or a verified official alternative and real three-source validation. No account creation, credential search/request, source network call, outreach, publication, spending commitment or automation occurred.

**Next ready: T007a persisted candidate-set validation reports**, described in [backlog](../backlog.md) and D016. It is proposed work that can validate explicit wholly synthetic selections and report missing real ACS independently; it must not seal/activate or certify a real slice. Full T007/T008 remain pending. Shared report contracts and any new append-only migration are the next supervisor's responsibility. [Start-session](../start-session.md) now carries that prompt.

All three worker turns completed; supervisor reclaimed ownership. Every shell process completed; no server/browser/background job was started. External replay root and prior temporary audit/dependency files remain disposable; no actual research root was initialized. New staging service/migration/script/tests and README/source-audit/execution documents are uncommitted. Existing starter-prompt intent preserved; no commit/reset/push and no sibling workspace changes.
