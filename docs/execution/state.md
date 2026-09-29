# Current project state

Last updated: September 29, 2026 (America/New_York).
Implementation stage: **Local skeleton, T006a adapters, T006b retained staging and T007a persisted candidate-set validation accepted and tested.** T006c official-route audit complete with a representation-review boundary; first real three-source slice remains incomplete.
Latest handoff: [Official ACS route audit](handoffs/2026-09-29-acs-route-audit.md).
Explicitly requested `gpt-6-astra` supervisor for scope/source decisions and integrated review; one bounded `gpt-6.1-sol` worker for official route discovery. Coordinator owns repository edits. Tool interfaces do not independently verify actual model metadata. Ownership/process completion is recorded in the latest handoff.

## Implemented and verified

- **T001/T003/T004/T005:** accepted local Python/FastAPI/SQLite/React skeleton, external baseline/private separation, session boundary, pinned bootstrap and honest empty UI. No rebuild. [Skeleton handoff](handoffs/2026-09-27-local-skeleton.md).
- **T002/T006a:** accepted audit/specifications, typed provenance, and bounded ACS/boundary/document normalization. Units, universes, annotations, MOEs, period/vintage, geometry and exact document locators remain as accepted. [Adapter handoff](handoffs/2026-09-29-source-adapters.md).
- **T006b:** immutable candidate versions, ordered import membership, separate retrieval events, exact raw/spec retention and verified readback; explicit real/synthetic runs. [Staging handoff](handoffs/2026-09-29-retained-staging.md).
- **T007a:** baseline-only `CandidateValidation` persists immutable content-addressed reports from an explicit run and bounded tuple of selected imports. It uses staging's complete verified readback in one transaction, then unchanged `validate_slice` semantics. Reports pin import/retrieval/version membership, source/raw/spec/transform identity, mode, validator identity and issues. No implicit latest selection. Failed-input metadata is diagnostic and marked unverified. Equal content reuses the same report.
- Complete generated 225-ACS/75-boundary/3-document selections pass only as synthetic. Missing/duplicate/mixed-run/mixed-mode sources, corrupt/missing evidence and a changed geography revision fail with inspectable reports. Historical report reads check report integrity without rechecking current objects; explicit revalidation checks current evidence availability.
- Audited real boundary/document replay produces a durable **missing ACS** report, never a real-slice pass. During T007a no new source retrieval occurred and no real ACS observations were acquired. Exact audit source/spec pins remain unchanged. Details and reproducible IDs are in the [T007a handoff](handoffs/2026-09-29-candidate-validation.md).
- **T006c:** official-route audit complete. Fresh accepted keyless API query again returns 302 / missing-key header. Official data.census.gov ZIP/CSV route is documented but no export bytes or annotation equivalence acquired. D018 stops before differing-representation ingestion; specs/adapters unchanged. Explicit current-evidence revalidation still verifies both retained real imports / 78 versions and reuses the missing-ACS report; database/object hashes unchanged.

Fresh stores require baseline migration **003**. Accepted baseline 001/002 and private 001 checksums are unchanged. Earlier stores fail closed; T007a compared old 002 database bytes unchanged after initialization/check/validation rejection. No upgrade/recovery or ledger rewrite exists; preserve old roots and use a fresh external root.

Reports establish neither complete release closure nor source authorization. Caller-supplied retrieval and synthetic declarations remain a trust boundary. County PDF redistribution remains unconfirmed, NAD83 remains source geometry, and bounded PDF output is not hard parser process isolation. No sealing, activation, default baseline reads, network jobs, user export, UI or private-research feature was added. Product operation still requires this checkout.

## Next ready work and blockers

- **T006d ready:** bounded official S1901/S1701 export acquisition and representation review, with a concrete [backlog packet](backlog.md). Use supported official public UI/download routes and a fresh external audit directory. Establish actual 2023 tract bytes and E/M/EA/MA semantics before supervisor source/spec/locator/adapter decisions. No export adapter implementation in that packet.
- **Full T006 blocked:** exact compatible API query at `2026-09-29T23:16:53Z` returned HTTP 302 to Census `missing_key.html`, `X-DataWebAPI-KeyError: 1`. Official ZIP/CSV route is unacquired/unvalidated, not proven inaccessible; it differs from accepted `acs-subject/1`. No credentials are sought or authorized. Needs verified compatible authorized observations and a real three-source persisted validation/revalidation. Metadata, fixtures and declared retrieval envelopes do not satisfy the gate.
- **T007/T008 pending:** full release closure, sealing/explicit activation, pinned map/table/evidence reads remain future work. A valid report alone authorizes none of them.

## Commands and checks

T006c changed documentation/evidence only. Seven bounded public HTTP probes recorded in [sanitized evidence](evidence/2026-09-29-acs-routes.json); no observation download. Existing explicit real selection revalidation returned expected exit 1, two verified imports / 78 versions, unchanged report ID, missing ACS. Evidence/hash, pin-preservation and diff checks are recorded in the latest handoff. No new broad test/build run was needed.

Prior T007a checks (not rerun in this audit):

From this checkout: `.venv/bin/pytest -q` **203 passed**, existing Starlette warning only. After adding one semantic revision test and correcting CLI exception-test setup, affected suites were rerun: `tests/test_validation_reports.py` **19 passed**, `tests/test_validation_replay.py` **8 passed**. Supervisor failure/integrity suite **10 passed**. Ruff and `git diff --check` pass. No dependency, API/OpenAPI or frontend changes; builds/browser checks were not repeated.

Use explicit fresh external roots, never the default research directory, for tests/replay. Existing ignored `.venv` uses pinned Python 3.12.12 under `/private/tmp/cdt-python`; audit/dependency temporary files may disappear. Normal setup remains in [README](../../README.md).

## Checkout and process accounting

Actual branch `main`, HEAD `a08ba68` (`hjhkj`). This session started with all accepted T007a code/tests/tool/README/execution/source-audit changes already uncommitted/untracked; they were preserved. T006c adds the dated handoff and sanitized route JSON, and updates source-audit/state/backlog/decisions/start-session. No application, test, migration, source-spec, dependency, API or frontend changes. No commit/reset/push or sibling edits. Official documentation/error responses remain external under `/private/tmp/cdt-t006c-audit-20260929`; no observation bytes or private data entered Git. No new research/staging root, server, browser, account, outreach, publication, spending or automation. Old 002 root untouched; existing 003 root only explicitly revalidated with unchanged database/object hashes.
