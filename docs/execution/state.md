# Current project state

Last updated: September 29, 2026 (America/New_York).
Implementation stage: **Local skeleton, T006a normalization and T006b retained candidate staging accepted and tested.** First auditable source slice remains incomplete.
Active supervisor/assignments: None remaining. Three explicitly requested `gpt-6.1-sol` workers completed (synthetic tests, audited replay, read-only review); supervisor inspected and verified the integrated result. Requested supervisor: GPT-6 Astra; actual supervisor/worker model metadata is not independently exposed by this tool interface.
Latest handoff: [Retained candidate staging](handoffs/2026-09-29-retained-staging.md).

## Implemented and verified

- **T001/T003/T004/T005:** accepted Python/FastAPI/SQLite/React local skeleton, external data root, baseline/private separation, loopback session security, pinned bootstrap and honest empty UI. No skeleton rebuild. See [skeleton handoff](handoffs/2026-09-27-local-skeleton.md).
- **T002/T006a:** accepted source audit, pinned specifications, typed provenance/locators and three bounded normalization adapters. Hashes, natural assertions, transform identity, ACS E/M/EA/MA, uncertainty, units/universes, period/vintage, geometry and exact document excerpts remain as accepted. See [adapter handoff](handoffs/2026-09-29-source-adapters.md).
- **T006b:** `CandidateStaging` validates accepted public byte inputs before retaining exact source/spec objects; appends immutable candidate versions, ordered import membership and separate retrieval events. Re-imports reuse fingerprints; changed source/spec/transform content creates new versions of the same assertions. Required real/synthetic run modes cannot mix. Complete typed readback re-verifies raw/spec SHA-256/size, retrieval/index consistency and membership/fingerprints. No private-store access, release mutation or HTTP capability was added.
- File and directory synchronization precede SQLite metadata commits. Failed validation writes no evidence; interruption after retention may leave complete unreferenced objects; metadata failures roll back; retry reuses valid objects. Corrupt objects are rejected, not silently overwritten. County PDF remains local evidence with redistribution unconfirmed; only the three audited retention policies are accepted.
- **Audited offline staging:** 75 real boundary candidates and 3 real document excerpts, 78 unique versions, 4 raw/spec objects and 4 successful import/retrieval events after repeat imports. Worker replay and separate-process supervisor readback/re-normalization from retained bytes both passed. Source hashes match `source_specs/`. This does not verify fresh HTTP access.
- **Synthetic ACS only:** 225 candidates from generated 75-row fixtures; complete persistence/readback, annotations, suppression/null/zero, MOEs and identity changes verified in isolated synthetic runs. No synthetic observations entered the audited real run.

New baseline migration **002** is required for fresh stores. Both accepted **001 checksums are unchanged**. Existing 001 stores fail closed and remain byte-for-byte unchanged in the migration rejection test; no upgrade/backup/recovery path exists. Preserve old roots and use a separate new root for this checkpoint.

No real ACS observations, active release, map/table/evidence UI, fetch orchestration/jobs, private brief UI, search, user export or backup/restore were added. Staging does not establish full release membership closure or prove caller-supplied authorization/retrieval declarations. NAD83 is not a prepared WGS84 display layer; PDF accepted-output bounds are not hard parser resource isolation. Product operation still requires this checkout.

## Next ready work and blockers

- **T007a ready:** persisted candidate-set validation reports, a bounded prerequisite of T007, from explicitly selected staged imports. Concrete packet in [backlog](backlog.md). It can progress with isolated synthetic tests and report missing real ACS without sealing/activation or baseline reads. This is proposed work, not an implemented capability.
- **Full T006 blocked:** last verified corrected ACS request (September 27) returned HTTP 302 to Census `missing_key.html`, `X-DataWebAPI-KeyError: 1`. Needs authorized observation bytes or a separately verified official download route and subsequent real three-source validation. No new ACS request, account creation, credential search/request or network source access occurred this session. Fixtures and declared retrieval metadata do not satisfy this gate.
- T007 sealing/explicit activation and T008 pinned map/table/evidence remain pending. Complete supporting membership, retention-aware release/export access and source availability must be checked before accepting a real release.
- No personal decision blocks T007a. Private data stays outside Git; no actual research directory was initialized.

## Commands and checks

From this checkout: `.venv/bin/pytest -q` **167 passed**, with the existing Starlette test-client deprecation warning. `.venv/bin/ruff check src tests scripts` and `git diff --check` pass. Focused new tests: 16 staging, 10 integrity/migration, 9 replay-tool tests. One injected metadata abort initially leaked a SQLite exception; corrected and verified. No dependency/lock, API/OpenAPI or frontend changes; dependency sync/build/browser checks were not repeated.

Audited retained replay:

```sh
.venv/bin/python scripts/stage_audited_sources.py --boundary /private/tmp/cdt-boundary.zip --document /private/tmp/cdt-fy2025 --data-dir /private/tmp/cdt-t006b-worker-replay-20260929-4c8f19
```

Replay output contains only counts/hashes/status; original retrieval times are from specifications and expected successful status/media headers are caller-declared. A separate-process supervisor check read all four imports, independently normalized both retained artifacts/specs, verified complete equality, a private test sentinel boundary and no release/active pointer. Details in handoff. The replay root remains disposable and external; source objects and generated candidate text are not in Git.

Normal setup commands remain in [README](../../README.md). Use an explicit new external temporary `--data-dir` for checks. Existing ignored `.venv` uses pinned Python 3.12.12 under `/private/tmp/cdt-python`; dependency caches and audit files may disappear.

## Working tree and processes

Actual branch `main`, HEAD `b623129` (`feat: next checkpoint`). Previous state said `97841eb` and uncommitted adapters; those files are now committed. The only starting modification was the user's `start-session.md` correction/removal of stale handoff prose; preserved while advancing the prompt.

This session's storage service/migration/replay/tests and README/execution/source-audit updates are uncommitted. No commit/reset/push/publication occurred; sibling workspace content was untouched. All three workers completed and ownership returned to supervisor. All shell commands completed; no server, browser, background job or automation was started. External test root above retains public evidence plus a synthetic private sentinel only.
