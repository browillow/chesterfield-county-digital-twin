# Current project state

Last updated: September 29, 2026 (America/New_York).
Implementation stage: **Local skeleton, T006a adapters, T006b retained staging, T007a persisted candidate-set validation and T006f local credential injection accepted and tested.** First real three-source slice remains incomplete; T006g API acquisition is ready for implementation.
Latest handoff: [Local credential injection](handoffs/2026-09-29-local-credentials.md).
Explicitly requested `gpt-6-astra` supervisor for scope/source decisions and integrated review; one bounded `gpt-6.1-sol` worker for credential-provider implementation/tests. Coordinator owns integration and shared/runtime documentation edits; Sol owned the provider and its tests. Tool interfaces do not independently verify actual model metadata. Ownership/process completion is recorded in the latest handoff.

## Implemented and verified

- **T006f:** user explicitly lifted the no-credentials constraint. `cdt serve --census-key-source none|prompt|env|keychain` injects a backend-only redacted provider, default none, no fallback. Hidden prompt fails closed; Keychain lookup is fixed/read-only; environment key is removed before children. CLI and app clear provider references on startup failure/shutdown. No credential is persisted or exposed by HTTP/OpenAPI, no fetch occurs, and no real key has been supplied. Synthetic PTY input and sentinel tests pass; real Keychain access remains untested. [D020](decisions.md#d020--explicit-local-credential-injection-authorized-2026-09-29).

- **T001/T003/T004/T005:** accepted local Python/FastAPI/SQLite/React skeleton, external baseline/private separation, session boundary, pinned bootstrap and honest empty UI. No rebuild. [Skeleton handoff](handoffs/2026-09-27-local-skeleton.md).
- **T002/T006a:** accepted audit/specifications, typed provenance, and bounded ACS/boundary/document normalization. Units, universes, annotations, MOEs, period/vintage, geometry and exact document locators remain as accepted. [Adapter handoff](handoffs/2026-09-29-source-adapters.md).
- **T006b:** immutable candidate versions, ordered import membership, separate retrieval events, exact raw/spec retention and verified readback; explicit real/synthetic runs. [Staging handoff](handoffs/2026-09-29-retained-staging.md).
- **T007a:** baseline-only `CandidateValidation` persists immutable content-addressed reports from an explicit run and bounded tuple of selected imports. It uses staging's complete verified readback in one transaction, then unchanged `validate_slice` semantics. Reports pin import/retrieval/version membership, source/raw/spec/transform identity, mode, validator identity and issues. No implicit latest selection. Failed-input metadata is diagnostic and marked unverified. Equal content reuses the same report.
- Complete generated 225-ACS/75-boundary/3-document selections pass only as synthetic. Missing/duplicate/mixed-run/mixed-mode sources, corrupt/missing evidence and a changed geography revision fail with inspectable reports. Historical report reads check report integrity without rechecking current objects; explicit revalidation checks current evidence availability.
- Audited real boundary/document replay produces a durable **missing ACS** report, never a real-slice pass. During T007a no new source retrieval occurred and no real ACS observations were acquired. Exact audit source/spec pins remain unchanged. Details and reproducible IDs are in the [T007a handoff](handoffs/2026-09-29-candidate-validation.md).
- **T006c (historical):** official-route audit completed with a fresh keyless API 302 / missing-key response. Official ZIP/CSV route was documented but no export bytes or annotation equivalence acquired. D018 stopped before differing-representation ingestion; specs/adapters unchanged. At that checkpoint explicit revalidation verified both retained real imports / 78 versions and reused the missing-ACS report with unchanged database/object hashes. This is not a T006d current artifact check.
- **T006d:** public UI access succeeded for both S1901/S1701 with only 2023 ACS 5-Year Subject selected in each ZIP vintage dialog. No final downloads triggered: supported browser APIs lack enforceable transfer bounds and actual response URL/status/media metadata. D019 accepts this tool blocker, not publisher denial or export compatibility. No export bytes/annotations validated; accepted specs/adapters unchanged. Two-table exports also require reviewed multi-artifact lineage before implementation.

Fresh stores require baseline migration **003**. Accepted baseline 001/002 and private 001 checksums are unchanged. Earlier stores fail closed; T007a compared old 002 database bytes unchanged after initialization/check/validation rejection. No upgrade/recovery or ledger rewrite exists; preserve old roots and use a fresh external root.

Reports establish neither complete release closure nor source authorization. Caller-supplied retrieval and synthetic declarations remain a trust boundary. County PDF redistribution remains unconfirmed, NAD83 remains source geometry, and bounded PDF output is not hard parser process isolation. No sealing, activation, default baseline reads, network jobs, user export, UI or private-research feature was added. Product operation still requires this checkout.

## Next ready work and blockers

- **T006g ready for implementation:** bounded explicit acquisition from the unchanged 2023 Subject JSON API using T006f. This is the best existing-contract fit; credentials are now allowed through local injection. Implement transfer limits and sanitized actual retrieval provenance, then perform a live run only with a locally supplied authorized key. See the concrete [backlog packet](backlog.md).
- **T006e remains blocked as the alternate ZIP route:** current path-only browser download capabilities lack enforceable transfer bounds and actual response envelopes. T006d's successful public UI navigation is historical, not publisher denial. D019 remains applicable; no differing-representation spec/adapter or multi-artifact design is approved.
- **Full T006 remains incomplete:** the compatible API request at `2026-09-29T23:16:53Z` was historically key-blocked and was not retried. No real ACS bytes, current GEOID/annotation verification or three-source pass exist. T006f solves injection, not acquisition. Metadata, rendered UI values, fixtures and historical reports cannot satisfy live acceptance.
- **T007/T008 pending:** full release closure, sealing/explicit activation and pinned map/table/evidence reads remain future work. A report alone authorizes none of them.

## Commands and checks

T006f checks: `.venv/bin/pytest -q` **243 passed**, existing Starlette warning only; `.venv/bin/ruff check src tests scripts` and `git diff --check` pass. Initial affected suites passed **55 tests**; the full suite includes unchanged source adapters/staging/report behavior and OpenAPI equality. A real PTY check with a synthetic sentinel verified hidden entry, no echoed key and provider cleanup. Keychain calls were mocked; no real credential lookup or Census request was performed.

No frontend, dependency, source-spec or migration changes; no browser/build repetition was needed. No staging, historical report readback or current revalidation occurred. Earlier T006c artifact checks remain historical. See the latest handoff for commands, preservation/link checks and source/supervisor review.

Use explicit fresh external roots, never the default research directory, for tests/replay. Existing ignored `.venv` uses pinned Python 3.12.12 under `/private/tmp/cdt-python`; audit/dependency temporary files may disappear. Normal setup remains in [README](../../README.md).

## Checkout and process accounting

Actual branch `main`, HEAD `df43f9e` (`ajlsdf`), sole listed worktree. This turn started with five uncommitted execution documents from the preceding capability gate; they were preserved and extended where current. The interrupted documentation-research follow-up made no repository writes or acquisitions. T006f adds the provider and three test files, changes CLI/app/README/contracts and continuity documents, and adds a credential handoff. The previous capability handoff remains unchanged. No Git mutations, dependency/spec/migration changes or sibling edits. External ownership/PTY/check scripts are under `/private/tmp/cdt-local-credentials-20260929`.

No actual credential values were inspected or requested; the user can enter a key locally. All tests use sentinels and isolated roots; earlier research/staging roots stayed unopened. All workers and shell/PTY processes completed; no tabs, downloads, servers or automation remain. No accounts, outreach, publication or spending.

Startup support follow-up: the user's default root had no baseline/private databases, causing `MigrationError` before credential loading. Initialized the missing pair at `/Users/jordan/Library/Application Support/ChesterfieldTwin`; explicit `cdt doctor` passed with compatible/writable stores and built frontend. No older database was opened/upgraded, credential accessed, source fetched or server left running. See the latest handoff.
