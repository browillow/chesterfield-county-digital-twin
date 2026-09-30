# Current project state

Last updated: September 29, 2026 (America/New_York).
Implementation stage: **T007c activation, pinned application reads and basic comparison implemented, tested, actual-byte verified and accepted by Astra. Minimal T007 is complete.** The explicitly selected real release is now active. Map/table/evidence UI remains T008.
Latest handoff: [T007c activation and pinned reads](handoffs/2026-09-29-activation-reads.md).
Planning context: [Personal research plan alignment](handoffs/2026-09-29-research-plan-alignment.md).
Prior implementation/evidence handoff: [Sealed first-slice build](handoffs/2026-09-29-sealed-build.md).

## Current exact baseline

- Schema-004 root: `/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929`.
- Run: `bc809bfa-e597-4447-8feb-5a988cb2d4ed`.
- ACS / boundary / document imports: `352490fd-8882-4b93-a8df-03c0df1a22f3`, `6d97c8af-ed5c-4f2d-b392-1e400a7908aa`, `351ba05c-73dc-401f-b5a3-6851a9356454`.
- Candidate report: `9f6709caf335f9722c7dba5307d85c8d4f1d3e8d6e825321f72ab8b784947a9e`.
- Sealed release: `81ec338c8c4ff0da3cd7d3f6aa5acbdebb14c65a9096689d202211629138cf84`.
- Closure report: `48ab41e78ef0553ea6571290391d987372eae293eeeb475a664081a9027dd2c8`.
- Active pointer: **`81ec338c8c4ff0da3cd7d3f6aa5acbdebb14c65a9096689d202211629138cf84`**. T007c explicitly activated it from null after safety checks; no repeat build or acquisition.

The release contains 303 candidate versions (225 ACS observations, 75 boundaries, 3 excerpts), 330 complete graph nodes and 1,983 edges. All candidate fingerprints, six raw/spec identities and original retrieval envelopes match the accepted schema-003 slice. T007b initialized and exact-byte replayed this root, never upgraded it, and verified the original schema-003 database and six objects stayed byte-identical. T007c preserved every earlier root without reopening them. [Safe evidence](evidence/2026-09-29-sealed-build.json).

## Implemented and verified

- **T007c:** `ReleaseApplication` verifies current closure inside each explicit read snapshot; activation verifies in the same transaction that changes only the pointer. Real-only activation, checked bootstrap, bounded typed records, selected reachable evidence support, summary and explicit old/new candidate-identity comparison are implemented. Authenticated API routes require and echo release pins; CLI adds separate `release activate`. Invalid/unselected/corrupt evidence fails closed without repair. Synthetic explicit reads stay labeled and cannot be activated. [D024](decisions.md#d024--explicit-activation-and-current-pinned-application-reads-2026-09-29), [Astra freeze](t007c-freeze.md).
- **Actual T007c evidence:** explicit activation returned prior null, selected active ID, real mode and current verification. Separate-process service/ASGI checks verified all 303 fingerprints, four HTTP pages, evidence for each candidate kind, exact counts/caveats and self-comparison. All 59 public objects, 18 non-pointer baseline tables and private-store bytes stayed unchanged. Only `app_state` changed logically; no schema change, replay, source request or earlier-root access. Final serialized node IDs and edge references passed current actual-byte readback. [Safe T007c evidence](evidence/2026-09-29-activation-reads.json). The UI remains a shell; no browser/UI acceptance is claimed.

- **T007b:** explicit `cdt release build` requires root/run/import/report pins, invokes current validation, replays exact retained inputs through unchanged adapters and closes all supporting identities. Manifest, candidate report and closure report objects are persisted and reread before atomic SQL sealing. Build does not write `app_state`. `cdt release verify` checks current retained closure for an explicit release. [D022](decisions.md#d022--complete-first-slice-closure-and-explicit-sealed-build-2026-09-29), [Astra freeze](t007b-freeze.md).
- Reproducibility retains 53 exact allowlisted code/build/config/lock files, HEAD and dirty declaration, file-manifest digest, runtime/package versions, query/configuration and schema pins. Code snapshot digest: `0b916ddd516020ff1643b3caa7a3a60eb9d2138062018ce0152a0401a12c3e78`. This describes the exact build-input tree, not unrelated docs/tests/private/runtime files. Lock sync is not independently certified; measured runtime and locks are both pinned.
- SQL guards protect sealed membership/support, including `INSERT OR REPLACE` bypasses with recursive triggers off. Current verification is read-only; repeat builds reject missing sealed dependencies without repairing them. Tests cover corruption, complete report bindings, substituted code, final object replacement, failed/interrupted build preservation and private-data exclusion. Actual real build and separate-process current verification passed.
- **T006/T006g:** accepted user-local hidden-prompt acquisition retained unchanged 2023 Subject JSON, 11,368 bytes, SHA-256 `df0a0dffa69d4409102a616cc5144b502117c3eaad4907c4afee51d7a0334fdf`, retrieved `2026-09-30T01:04:59.395127Z` (September 29, 9:04 p.m. EDT). All 75 exact tracts and three metrics passed unchanged E/M/EA/MA semantics. No repeat request or credential access occurred during T007b. [Real-slice handoff](handoffs/2026-09-29-real-slice.md), [D021 continuation](decisions.md#d021--explicit-bounded-subject-acquisition-separate-from-injection-2026-09-29).
- **T001/T003/T004/T005:** accepted local Python/FastAPI/SQLite/React skeleton, baseline/private separation, session boundary and honest empty UI. No rebuild or UI change. [Handoff](handoffs/2026-09-27-local-skeleton.md).
- **T002/T006a/T006b:** accepted source specs, typed adapters, retained original/spec objects, immutable candidate versions and separate import/retrieval events. Units, uncertainty, annotations, periods, source geometry and exact document locators are preserved. [Adapters](handoffs/2026-09-29-source-adapters.md), [staging](handoffs/2026-09-29-retained-staging.md).
- **T007a:** immutable content-addressed historical reports over explicit selections. Historical readback checks report integrity; explicit validation checks current evidence. T007b adds distinct explicit build authority and current verification; a report alone never seals or activates. [Handoff](handoffs/2026-09-29-candidate-validation.md).
- **T006f:** explicit credential sources `none|prompt|env|keychain`, default none, no fallback, backend-only redaction and lifecycle cleanup. Startup never fetches. Actual Keychain access remains untested. [Handoff](handoffs/2026-09-29-local-credentials.md).

Fresh stores require baseline **004**. Accepted baseline 001–004 and private 001 checksums are unchanged. Earlier stores fail closed; no upgrade/recovery or ledger rewrite exists. Preserve roots and use explicit new roots when schemas change. Source/spec identities are unchanged, including historical access-status prose.

## Next ready work and limits

- **Planning clarification ([D023](decisions.md#d023--personal-research-value-and-proportionate-delivery-2026-09-29)):** optimize for Jordan's personal business discovery, informed contributions and agent-assisted investigation. Broader source collection may precede UI polish when its actual contracts/safeguards are ready. Retain useful documents before requiring full structured modeling. Planned T011a document intake, T011b bounded access for existing agents and T013a basic protection do not yet exist; basic backup/verified restore precedes irreplaceable private research. That earlier planning-only session changed no runtime capability; T007c implements only the bounded activation/read checkpoint described here.

- **Next ready: T008**, the bounded map/table/evidence workflow using the pinned API. Freeze changed UI/display-geometry contracts before implementation; source geometry is EPSG:4269. Never select latest or mix releases. T007c includes the basic comparison required by T007; no broader metadata/statistical diff is implied.
- **T008 UI remains unimplemented:** the shell can show the active pin but does not query/render county data. T007c now supplies authenticated HTTP reads/activation; it adds no user export, raw-download route, general jobs, private-research features or agent-access boundary.
- **T006e remains an unnecessary blocked alternate ZIP route.** Supported browser downloads lack enforceable transfer bounds and actual response provenance; UI access succeeded, not publisher denial. No unchanged audits, alternate representations or new source/spec/locator contracts are needed. [Continuation](handoffs/2026-09-29-capability-gate-continuation.md).
- Boundary/document provenance remains historical audited-byte replay, not fresh HTTP retrieval. County PDF redistribution is unconfirmed; NAD83 is source geometry. Bounded PDF output is not hard parser isolation. Local retrieval/mode declarations remain a trust boundary. Sealing is local evidence assembly, not external publication or human interpretation review.
- Product operation still requires this checkout. No accounts, outreach, publication, spending, network acquisition or automation occurred. No manual acquisition action is needed.

## Verification and checkout accounting

T007c stable full Python coverage: `.venv/bin/pytest -q -x tests/test_application.py`
— **30 passed**, and `.venv/bin/pytest -q --ignore=tests/test_application.py`
— **471 passed** (**501 total**). This split avoids duplicating the expensive
transaction/corruption matrix; it is not a claim that one combined invocation ran.
The regression partition has the existing Starlette deprecation warning;
the application partition has none. Earlier interrupted/test-fixture runs are
superseded and excluded. Final evidence-node transport checks are recorded separately
in the handoff; no transaction/storage logic changed for that additive response field.

CLI/runtime selection: 35 passed. Final transport HTTP/schema/credential rerun:
64 passed; complete storage projection rerun: 1 passed.
Node 24.21.0 generated types, frontend build and 6 frontend tests passed.
Ruff and diff checks passed. Actual retained-source reads and TestClient routing
are verified separately from synthetic unit fixtures; a single full-record read
with current verification took 0.568 seconds, not a general performance guarantee.
Historical T007b acceptance was 413 tests and remains in its linked handoff.

Current checkout: sole `main` worktree, HEAD
`fcc58c723921707cb7b63a09b2c0216f6df21e57`, started clean. No Git mutation.
The sealed release still pins historical HEAD `e1997e3` plus its exact dirty
build-input snapshot; current application edits do not rewrite it. Current
implementation, tests, generated contracts and documentation remain uncommitted.
Accepted migrations/specs/adapters/verifier and dependency files are byte-identical;
earlier roots were not opened or changed. Current baseline database SHA-256 after
activation: `8be9410ae07badecd1fbf499c7c113b68a87c4e2f8314cb988759662c390b623`.

Explicitly requested `gpt-6-astra` froze contracts and accepted integration;
two explicitly requested `gpt-6.1-sol` workers owned storage and HTTP files.
Runtime model identity is not independently exposed by task metadata. Coordinator
owns CLI, generated contracts, actual-root verification and execution documents.
Astra independently verified the actual active release, all 303 fingerprints, all
three evidence kinds and graph references, self-comparison and all 59 public objects
in a fresh process; baseline hash stayed unchanged. All workers and foreground
commands completed. Final preservation checks passed for 25 protected files; all
19 intended changed/new paths remain uncommitted. See the current handoff.
No server, acquisition, outreach, publication, spending or automation was started.
