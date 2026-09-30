# Current project state

Last updated: September 29, 2026 (America/New_York).
Implementation stage: **T007b first-slice release closure and sealed build implemented, tested and verified against the accepted real bytes.** One real release is sealed; **no release is active**. Explicit activation and pinned application reads remain T007c; map/table/evidence UI remains T008.
Latest handoff: [Personal research plan alignment](handoffs/2026-09-29-research-plan-alignment.md).
Latest implementation/evidence handoff: [Sealed first-slice build](handoffs/2026-09-29-sealed-build.md).

## Current exact baseline

- New schema-004 root: `/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929`.
- Run: `bc809bfa-e597-4447-8feb-5a988cb2d4ed`.
- ACS / boundary / document imports: `352490fd-8882-4b93-a8df-03c0df1a22f3`, `6d97c8af-ed5c-4f2d-b392-1e400a7908aa`, `351ba05c-73dc-401f-b5a3-6851a9356454`.
- Candidate report: `9f6709caf335f9722c7dba5307d85c8d4f1d3e8d6e825321f72ab8b784947a9e`.
- Sealed release: `81ec338c8c4ff0da3cd7d3f6aa5acbdebb14c65a9096689d202211629138cf84`.
- Closure report: `48ab41e78ef0553ea6571290391d987372eae293eeeb475a664081a9027dd2c8`.
- Active pointer: **null**. No activation operation was performed.

The release contains 303 candidate versions (225 ACS observations, 75 boundaries, 3 excerpts), 330 complete graph nodes and 1,983 edges. All candidate fingerprints, six raw/spec identities and original retrieval envelopes match the accepted schema-003 slice. The new root was initialized and exact-byte replayed, never upgraded. Original schema-003 database and six objects remain byte-identical; every earlier root is preserved. [Safe evidence](evidence/2026-09-29-sealed-build.json).

## Implemented and verified

- **T007b:** explicit `cdt release build` requires root/run/import/report pins, invokes current validation, replays exact retained inputs through unchanged adapters and closes all supporting identities. Manifest, candidate report and closure report objects are persisted and reread before atomic SQL sealing. Build does not write `app_state`. `cdt release verify` checks current retained closure for an explicit release. [D022](decisions.md#d022--complete-first-slice-closure-and-explicit-sealed-build-2026-09-29), [Astra freeze](t007b-freeze.md).
- Reproducibility retains 53 exact allowlisted code/build/config/lock files, HEAD and dirty declaration, file-manifest digest, runtime/package versions, query/configuration and schema pins. Code snapshot digest: `0b916ddd516020ff1643b3caa7a3a60eb9d2138062018ce0152a0401a12c3e78`. This describes the exact build-input tree, not unrelated docs/tests/private/runtime files. Lock sync is not independently certified; measured runtime and locks are both pinned.
- SQL guards protect sealed membership/support, including `INSERT OR REPLACE` bypasses with recursive triggers off. Current verification is read-only; repeat builds reject missing sealed dependencies without repairing them. Tests cover corruption, complete report bindings, substituted code, final object replacement, failed/interrupted build preservation and private-data exclusion. Actual real build and separate-process current verification passed.
- **T006/T006g:** accepted user-local hidden-prompt acquisition retained unchanged 2023 Subject JSON, 11,368 bytes, SHA-256 `df0a0dffa69d4409102a616cc5144b502117c3eaad4907c4afee51d7a0334fdf`, retrieved `2026-09-30T01:04:59.395127Z` (September 29, 9:04 p.m. EDT). All 75 exact tracts and three metrics passed unchanged E/M/EA/MA semantics. No repeat request or credential access occurred during T007b. [Real-slice handoff](handoffs/2026-09-29-real-slice.md), [D021 continuation](decisions.md#d021--explicit-bounded-subject-acquisition-separate-from-injection-2026-09-29).
- **T001/T003/T004/T005:** accepted local Python/FastAPI/SQLite/React skeleton, baseline/private separation, session boundary and honest empty UI. No rebuild or UI change. [Handoff](handoffs/2026-09-27-local-skeleton.md).
- **T002/T006a/T006b:** accepted source specs, typed adapters, retained original/spec objects, immutable candidate versions and separate import/retrieval events. Units, uncertainty, annotations, periods, source geometry and exact document locators are preserved. [Adapters](handoffs/2026-09-29-source-adapters.md), [staging](handoffs/2026-09-29-retained-staging.md).
- **T007a:** immutable content-addressed historical reports over explicit selections. Historical readback checks report integrity; explicit validation checks current evidence. T007b adds distinct explicit build authority and current verification; a report alone never seals or activates. [Handoff](handoffs/2026-09-29-candidate-validation.md).
- **T006f:** explicit credential sources `none|prompt|env|keychain`, default none, no fallback, backend-only redaction and lifecycle cleanup. Startup never fetches. Actual Keychain access remains untested. [Handoff](handoffs/2026-09-29-local-credentials.md).

Fresh stores require baseline **004**. Accepted baseline 001–003 and private 001 checksums are unchanged. Earlier stores fail closed; no upgrade/recovery or ledger rewrite exists. Preserve roots and use explicit new roots when schemas change. Source/spec identities are unchanged, including historical access-status prose.

## Next ready work and limits

- **Planning clarification ([D023](decisions.md#d023--personal-research-value-and-proportionate-delivery-2026-09-29)):** optimize for Jordan's personal business discovery, informed contributions and agent-assisted investigation. Broader source collection may precede UI polish when its actual contracts/safeguards are ready. Retain useful documents before requiring full structured modeling. Planned T011a document intake, T011b bounded access for existing agents and T013a basic protection do not yet exist; basic backup/verified restore precedes irreplaceable private research. No source, schema, access or runtime capability changed in this documentation session.

- **Next ready: T007c**, explicit activation and release-filtered application reads, after an Astra contract/API freeze. Pin the release above; never select latest implicitly. Preserve failure atomicity and all supporting memberships. T007 overall is incomplete until this checkpoint is accepted.
- **T008 pending:** map/table/evidence workflow follows T007c. Current UI remains the unactivated shell. No HTTP release query/activation endpoints, default baseline reads, user export, background jobs or private-research features were added in T007b.
- **T006e remains an unnecessary blocked alternate ZIP route.** Supported browser downloads lack enforceable transfer bounds and actual response provenance; UI access succeeded, not publisher denial. No unchanged audits, alternate representations or new source/spec/locator contracts are needed. [Continuation](handoffs/2026-09-29-capability-gate-continuation.md).
- Boundary/document provenance remains historical audited-byte replay, not fresh HTTP retrieval. County PDF redistribution is unconfirmed; NAD83 is source geometry. Bounded PDF output is not hard parser isolation. Local retrieval/mode declarations remain a trust boundary. Sealing is local evidence assembly, not external publication or human interpretation review.
- Product operation still requires this checkout. No accounts, outreach, publication, spending, network acquisition or automation occurred. No manual acquisition action is needed.

## Verification and checkout accounting

Prior T007b implementation acceptance: `.venv/bin/pytest -q` — **413 passed**, existing Starlette deprecation warning only. `.venv/bin/ruff check src tests scripts` and `git diff --check` passed. The independent integrity/storage suite passed 79 tests; service focused tests and CLI/credential regressions also passed. A source-edit race invalidated an earlier full run; it was discarded and superseded by the fresh complete pass. No frontend/API/dependency change required browser or frontend reruns.

Actual nested checkout for the documentation alignment: `main`, HEAD `94f8ae9e8f8f1c6f65b5535bb4423583e9b23766` (`feat: next checkpoint`), sole worktree, started clean. Prior T007b changes were committed before this session. Its sealed build still correctly pins historical code HEAD `e1997e3` plus its exact dirty build-input snapshot. No Git mutations or sibling changes here; only the new documentation changes are uncommitted. Application code, tests, accepted specs/migrations, dependency locks and historical evidence are preserved. The 413-test result above is prior implementation acceptance; this documentation-only session checks consistency, links and preservation without rerunning application tests or opening data roots.

T007b model/process accounting: explicitly requested `gpt-6-astra` supervised freeze and acceptance; two explicitly requested `gpt-6.1-sol` workers owned service and independent integrity tests. Tool metadata did not independently verify actual executing model. Coordinator owned CLI, actual replay/build/verification and execution documents. All workers and foreground commands completed; no server, acquisition process or background automation remains. See the linked implementation handoff for those commands and acceptance evidence. The current planning handoff records the separate documentation review and checks.

Documentation alignment checks: one explicitly requested Astra read-only review accepted the changes; `git diff --check` and 69 local link checks passed. Nine existing Markdown files plus one handoff changed; all other 108 tracked files remained byte-identical. No runtime tests or data-root access were needed. The reviewer completed; no implementation workers or background processes were started. These checks do not advance runtime acceptance beyond T007b.
