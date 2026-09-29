# Execution backlog

Status is maintained by the supervisor. Statuses reflect September 29 T006b acceptance; live ACS observation access and full three-source/release acceptance remain incomplete. `ready` requires completed dependencies and a concrete assignment; `pending` has a defined outcome but unmet dependencies; `planned` requires decomposition before delegation. Once claimed, use `in_progress`, then `review`, then `done` after supervisor acceptance, or `blocked` with an explicit cause. For detailed packets, use [templates](templates.md).

| ID | Deliverable | Depends on | Status |
| --- | --- | --- | --- |
| T001 | Managed runtime, package scaffold, initial interface agreement | — | done |
| T002 | First-slice source/access audit and metric selection | — | done |
| T003 | Local storage, baseline/private separation, initial migrations | T001 | done |
| T004 | Loopback API, session boundary, static asset serving | T001, T003 | done |
| T005 | React application shell and honest empty states | T001 | done |
| T006 | ACS, boundary, and one-document ingestion slice | T002, T003 | blocked |
| T006a | Independent adapter groundwork (partial T006 only) | T002, T003 | done |
| T006b | Retained public artifacts and unpublished candidate staging | T006a | done |
| T007a | Persisted candidate-set validation reports (partial T007) | T006b | ready |
| T007 | Minimal sealed release, explicit activation, pinned reads | T006 | pending |
| T008 | Integrated map/table/evidence workflow | T004, T005, T007 | pending |
| T009 | Job lifecycle, interruption and retry, failed-refresh preservation | T007 | planned |
| T010 | CBP/NES/LODES and broad coverage | T008, T009 | planned |
| T011 | Curated profiles, relationships, review and lexical search | T008 | planned |
| T012 | Private briefs, research queue and sensitivity worksheet | T008, T011 | planned |
| T013 | Export, migrations/recovery, backup and restore | T009, T012 | planned |
| T014 | MVP acceptance review and operating handoff | T010, T011, T012, T013 | planned |

## Accepted checkpoint and next assignments

- **T001/T003/T004/T005 done:** managed locks/runtime, separate initial stores, loopback session API, and built React empty shell accepted with unit, component, and real browser checks. See [handoff](handoffs/2026-09-27-local-skeleton.md). Source checkout operation only; schema upgrades, complete evidence validation, and release services remain absent.
- **T002 done as an audit with an explicit blocker:** metric metadata, boundary/document retrieval, and report accepted. This does **not** satisfy live-source readiness for the full T006 slice. The corrected ACS query returned HTTP 302 to `missing_key.html` with `X-DataWebAPI-KeyError: 1` on September 27. No key was created.
- **T006 blocked for full acceptance:** requires authorized ACS observation bytes or a separately verified official download route, then real three-source validation; do not infer data from metadata. No account creation or credential request is authorized by this backlog.
- **T006a done:** supervisor settled `domain/candidates.py`/`sources/common.py`, then explicitly requested three `gpt-6.1-sol` workers with separate ACS/boundary/document ownership. Adapters and cross-source checks are accepted after supervisor review, 132 passing Python tests, and independent audited-byte replay (75 boundaries, 3 document excerpts). ACS validation is synthetic only. Source/spec/transform hashes, exact locators, annotations, uncertainty, units/universes and periods are preserved. No ingestion persistence, live ACS access or release completion is claimed. See [handoff](handoffs/2026-09-29-source-adapters.md).
- **T006b done:** supervisor-owned append-only migration 002 and staging service retain exact raw/spec objects, immutable candidate versions and separate retrieval/import events, with explicit real/synthetic isolation and verified full readback. Audited offline replay staged 75 boundaries and 3 excerpts; repeats reused versions. Synthetic ACS/failure checks are separate. Existing 001 stores remain fail-closed; checksums unchanged. Integrated suite: 167 passed. See [handoff](handoffs/2026-09-29-retained-staging.md).
- **T007a ready:** persist validation reports over explicit staged-import selections, independently of the real ACS access blocker. This decomposes only the validation prerequisite of T007; no sealing/activation or baseline-read acceptance is implied.
- T007/T008 remain pending: generic storage guards are groundwork, not release validation/sealing/activation or a map/table/evidence workflow. Confirm source-specific and complete provenance closure contracts before exposing baseline reads or user exports.

T007 deliberately precedes acceptance of the end-to-end slice: the UI must not ship with an unversioned baseline that needs to be retrofitted later. This sequences the architecture's stages B and C together for the minimum slice.

## First implementation packets

### T001 — Shared foundation

Supervisor owns this checkpoint, optionally delegating bounded research. Select compatible project runtimes; create Python package, lockfile, frontend manifest/lock, minimal module layout, and ignore rules. Finalize the slice's [contracts](contracts.md) without building future components. Verify dependency resolution on ARM64, package import, CLI help, frontend build, and the intended runtime feature checks. Record actual commands in state. No source data, infrastructure services, or full schema implementation required.

Ownership: root build/config files, `src/chesterfield_twin/__init__.py`, CLI entry point, frontend bootstrap/config, shared contract decisions. After acceptance, hand frontend feature paths to T005 and storage paths to T003. One writer owns each dependency file.

### T002 — Bounded public-source audit

Can run alongside T001. Inspect the MVP source plan and architecture ingestion/geography sections. Select one ACS release, three published tract measures including uncertainty/annotations, compatible boundary data, and one local public-function document. Verify a retrieval route with a small sample where available; distinguish documentation inspected from retrieval succeeded. Record terms, locator format, units/universe, geographic vintage, expected schema, access blockers, and reproducible fixture provenance.

Ownership: `docs/source-audit.md` and initial source specification proposals. No application code, dependency files, private directories, account creation, outreach, or large downloads. Do not invent metrics to fill a blocked source. Done means a reproducible access/selection report or an explicit source blocker with independent work completed; a blocker does not make the ingestion prerequisite complete.

### T003 — Persistence foundation

Implement data-root resolution, two database initialization paths, migration ledger, required SQLite settings, and minimal evidence/release tables needed by the slice. Include artifact addressing and baseline/private repository boundaries. Do not build every conceptual entity yet. Test repeated init, foreign keys, suppression-versus-zero representation, separate stores, and export-service access boundaries using synthetic records.

Ownership: assigned storage/domain modules, ordered migrations, storage fixtures/tests. Supervisor explicitly delegates migration ordering to this owner during the task. Dependency additions are proposals to the supervisor. Acceptance includes a temporary data root; no test writes to the user's real research directory.

### T004 — Local API and runtime

Implement loopback startup, health/bootstrap responses, shutdown, static UI delivery, Host/Origin/session controls, and bounded error handling. Verify no data is exposed without the local session boundary, no wildcard listener, and a built UI can load without external assets. Use the accepted contracts and code-generated API types. This task does not implement ingestion in an HTTP request.

Ownership: runtime/API modules and their tests; coordinate any CLI integration through its current owner. The supervisor owns final wiring if T003/T005 are still active.

### T005 — Frontend shell

Implement the four navigation destinations, design tokens from the concepts, release-aware application state, and empty/loading/error states. Use the agreed bootstrap contract and clearly labeled synthetic fixtures. No live county claims, remote fonts/tiles, or invented API shapes. Verify a production build, keyboard navigation, and empty/error rendering; capture a screenshot for review.

Ownership: `frontend/src` feature/style files and frontend tests excluding shared/generated API contracts and package/build configuration unless explicitly transferred. The final map is T008; avoid dashboard ornament before evidence drill-down works.

### T006 — Traceable ingestion

Using T002's confirmed specifications, ingest three measures, boundaries, and a document excerpt into candidate records. Preserve source artifacts/locators, values, uncertainty, units, geography/vintage, and lineage. Test identical re-import, changed source content, suppression, malformed input, and incompatible geography. Fixture tests are distinct from a real small source run. Done requires a sourced candidate dataset and a reported access limitation wherever live retrieval remains unavailable.

### T006b — Retained public artifacts and candidate staging (accepted)

Accepted bounded checkpoint, independent of the live ACS access blocker. Supervisor owns storage service integration, shared contracts and any migration decision. Reuse initial schema/artifact safeguards where suitable; do not modify existing migration checksums or silently upgrade stores. Delegate only disjoint adapter/service tests after persistence interfaces settle.

Accept explicit authorized public bytes/retrieval metadata and pinned specs; normalize/validate first, retain exact permitted bytes in the external content-addressed object store, then append typed candidate versions and separate retrieval events. Re-importing equal source/spec/transform content reuses candidate versions; changed content remains a separate version of the same natural assertion. Preserve full source/spec/transform lineage and exact locator/retention/synthetic metadata. County PDF remains local research evidence with unconfirmed redistribution. No private-store dependency, automatic activation, baseline HTTP reads, or user exports.

Acceptance: isolated temporary data root; boundary/document real-byte replay staged durably; identical re-import, changed synthetic content, failed validation, absent/corrupt artifact and interrupted artifact-before-metadata cases; raw SHA-256 re-verification and complete candidate rehydration; no active-pointer change or private sentinel leakage. Explicitly isolate synthetic observations from real candidate runs. Document any new schema requirement before implementing it; existing user stores must remain fail-closed. Full T006 remains blocked until real authorized ACS bytes or an official alternative is verified, followed by three-source validation. Future fetch/job orchestration remains separately scoped.

### T007a — Persisted candidate-set validation reports

Next ready bounded checkpoint. Depends on accepted T006b; full T007 remains dependent on real T006. Supervisor first settles explicit import-selection/report contracts and any append-only schema requirement. Rehydrate selected ACS/boundary/document imports through T006b's verified read path, require one mode and explicit run identity, apply the accepted `validate_slice` semantics, and persist an immutable report pinning input import/version membership, source/spec hashes, transform identities, validator identity, issues and real/synthetic status. Report incomplete/missing real observations precisely; never silently select latest candidates or substitute fixtures.

Acceptance: temporary external roots; a complete explicitly synthetic selection can validate only as synthetic, missing/duplicate/mixed-source selections and missing/corrupt artifacts fail with inspectable reports, identical inputs produce stable validation content, and real/synthetic selection cannot mix. Audited boundary/document candidates alone must report missing ACS rather than pass a real-slice gate. Keep existing migration checksums and old-store fail-closed behavior; no activation, release sealing, default baseline reads, export or fetch orchestration. Worker ownership can cover disjoint tests after shared contracts settle. The report is groundwork for future complete release closure, not full T006/T007 acceptance.

### T007 — Release contract

Implement draft membership, validation report/manifest, sealing, explicit activation, read filtering, and a basic old/new comparison. Test that failed builds cannot advance the active pointer, sealed members cannot change, and all displayed metadata is pinned. The supervisor coordinates API/schema consumers rather than allowing independent contract edits.

### T008 — First useful acceptance gate

Connect map selection, the equivalent table, and the evidence inspector to one pinned release. Start from a fresh temporary root, ingest/replay pinned inputs, activate, and reproduce the answer. Verify uncertainty, exact source locator, unknown states, and offline viewing of retained material. Inspect the actual UI. Only then mark the first auditable slice accepted and refine T009 onward into similarly bounded packets.

Future items intentionally remain coarse. Split them when their prerequisites reveal actual data shapes; do not expand the entire MVP into speculative tickets now.
