# Current project state

Last updated: September 29, 2026 (America/New_York).
Implementation stage: **Local skeleton, T006a adapters, T006b retained staging and T007a persisted candidate-set validation accepted and tested.** T006d completes with a precise acquisition-tool blocker; first real three-source slice remains incomplete.
Latest handoff: [Subject export acquisition review](handoffs/2026-09-29-subject-export-review.md).
Explicitly requested `gpt-6-astra` supervisor for scope/source decisions and integrated review; one bounded `gpt-6.1-sol` worker for official export-semantic documentation. Coordinator owns repository edits. Tool interfaces do not independently verify actual model metadata. Ownership/process completion is recorded in the latest handoff.

## Implemented and verified

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

- **T006d complete as a blocker review:** official UI reached both pinned ZIP dialogs; zero exports triggered. [D019](decisions.md#d019--subject-export-acquisition-tool-boundary-2026-09-29) and [preflight evidence](evidence/2026-09-29-subject-export-preflight.json) distinguish successful public UI navigation from absent raw transfer evidence.
- **T006e blocked conditional continuation:** needs a supported official download route/tool with enforceable size/time bounds and actual sanitized response URL/status/media/time plus original bytes. Then acquire and review S1901/S1701 in a fresh external audit directory. No independent application implementation packet is ready on this dependency chain. Inspect changed supported capabilities first in a future session; do not repeat unchanged API/FTP audits. See the [backlog packet](backlog.md).
- **Full T006 blocked:** T006c's compatible API request at `2026-09-29T23:16:53Z` was key-blocked; that historical result was not retried here. Export bytes, 75 exact GEOIDs and E/M/EA/MA equivalence remain unverified. No credentials are sought or authorized. Real three-source persisted validation and explicit current revalidation remain required; metadata, rendered UI cells, fixtures and historical reports do not satisfy this gate.
- **T007/T008 pending:** full release closure, sealing/explicit activation, pinned map/table/evidence reads remain future work. A valid report alone authorizes none of them.

## Commands and checks

T006d changed documentation/evidence only. Supported browser controls verified both 2023 ZIP vintage dialogs and capability gaps; no export was triggered. Accepted implementation/spec preservation, evidence consistency/hash and local-link checks plus `git diff --check` are recorded in the latest handoff. No source normalization, staging, historical report readback or current-root revalidation was performed. The earlier T006c two-import / 78-version verification is historical, not a current artifact check. No new broad test/build run was needed.

Prior T007a checks (not rerun in this audit):

From this checkout: `.venv/bin/pytest -q` **203 passed**, existing Starlette warning only. After adding one semantic revision test and correcting CLI exception-test setup, affected suites were rerun: `tests/test_validation_reports.py` **19 passed**, `tests/test_validation_replay.py` **8 passed**. Supervisor failure/integrity suite **10 passed**. Ruff and `git diff --check` pass. No dependency, API/OpenAPI or frontend changes; builds/browser checks were not repeated.

Use explicit fresh external roots, never the default research directory, for tests/replay. Existing ignored `.venv` uses pinned Python 3.12.12 under `/private/tmp/cdt-python`; audit/dependency temporary files may disappear. Normal setup remains in [README](../../README.md).

## Checkout and process accounting

Actual branch `main`, HEAD `77678ac` (`feat: next checkpoint`), clean at session start. Earlier accepted implementation/T006c work is now committed; older handoff branch/worktree descriptions remain historical. This session adds a Subject export handoff and sanitized preflight JSON and updates source-audit/state/backlog/decisions/start-session. No application, test, migration, source-spec, dependency, API or frontend changes, Git mutations or sibling edits. External notes/check scripts remain under `/private/tmp/cdt-t006d-audit-20260929`; no original export bytes were acquired. All earlier research/staging roots were left unopened. One temporary official-public-data browser tab was closed; no accounts, credentials, outreach, publication, spending, servers, downloads or automation. Worker/process accounting and final review are in the latest handoff.
