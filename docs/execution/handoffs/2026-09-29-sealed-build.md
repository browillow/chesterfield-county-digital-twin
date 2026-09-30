# Session handoff: T007b release closure and sealed build

Date: September 29, 2026 (America/New_York). **T007b accepted by Astra after integrated checks and independent real sealed readback.**

The nested project checkout started clean on `main` at
`e1997e3d95b81ea063a287d65b1518045644a91f`, with one worktree. The previous
handoff's `eef7bba` and uncommitted paths are historical: that work was committed
before this session. No Git mutation is planned. The parent repository is separate.

Explicitly requested `gpt-6-astra` supervises the contract/schema freeze and
integrated acceptance. Tool metadata names the task but does not independently
verify the executing model. Two implementation workers explicitly requested `gpt-6.1-sol` after the freeze.

## Ownership

- Astra: `domain/releases.py`, baseline migration 004, and
  `docs/execution/t007b-freeze.md`; contract freeze and integrated review.
- Coordinator: CLI/replay integration and their focused tests, execution state,
  backlog, decisions, contracts index, README and starter prompt.
- Sol service worker (explicit `gpt-6.1-sol`): `storage/releases.py` and
  `tests/test_release_build.py` exclusively.
- Sol integrity worker (explicit `gpt-6.1-sol`):
  `tests/test_release_integrity.py` and `tests/test_storage.py` exclusively.

Astra completed [the contract/schema freeze](../t007b-freeze.md) before either
implementation assignment. Migration 004 initializes a fresh store only.

## Starting evidence and preservation

The exact schema-003 selection in [the accepted real-slice handoff](2026-09-29-real-slice.md)
was explicitly revalidated with `scripts/validate_audited_sources.py`: report
`26e19a013ddb23741caae80d5a66ce01ffa66a33fd486b4afcb7f4fc1c7ba432`,
`real_slice_valid=true`, three verified inputs, 303 versions, no issues.
The existing verification lock was used with filesystem escalation. The baseline
database and six retained objects stayed byte-identical.

Before migration 004 was written, the accepted implementation at starting HEAD
verified the three exact imports through its complete retained readback in one
read-only transaction. Exact raw/spec bytes, original retrieval envelopes and
ordered candidate fingerprints were captured outside the repository for replay.
No network request or credential access occurred. Evidence and preservation
hashes are under `/private/tmp/cdt-t007b-20260929`.

The schema-003 root and all earlier roots must remain preserved. A new schema
means a fresh external root with exact-byte replay, not an upgrade. Boundary and
document retrieval envelopes remain historical audited-byte replay.

## Exact-byte schema-004 replay

New root: `/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929`.

- Run: `bc809bfa-e597-4447-8feb-5a988cb2d4ed`.
- ACS import: `352490fd-8882-4b93-a8df-03c0df1a22f3`.
- Boundary import: `6d97c8af-ed5c-4f2d-b392-1e400a7908aa`.
- Document import: `351ba05c-73dc-401f-b5a3-6851a9356454`.
- Initial and current candidate report: `9f6709caf335f9722c7dba5307d85c8d4f1d3e8d6e825321f72ab8b784947a9e`.

The unchanged `scripts/stage_acquired_slice.py` consumed the original acquisition
bundle plus the two exact verified raw objects. Both validation calls passed with
three verified real inputs / 303 versions. Separate read-only verification compared
all 303 ordered fingerprints, all six raw/spec identities and every original
retrieval envelope with the captured accepted schema-003 inputs. All match.
The replay creates new run/import/retrieval IDs without claiming new retrievals.
No generic replay/recovery service, source adapter change or acquisition occurred.

```sh
.venv/bin/python scripts/stage_acquired_slice.py \
  --acquisition-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin-ACS-20260929' \
  --boundary /private/tmp/cdt-t007b-20260929/verified-inputs/boundary.raw \
  --document /private/tmp/cdt-t007b-20260929/verified-inputs/document.raw \
  --data-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929'
```

This command succeeded once. Do not rerun it against the existing root. Temporary
capture files are session evidence; durable originals remain in the preserved
schema-003 root and were replayed into the new root. Filesystem escalation covered
the new external root and normal locks.

## Review and test accounting

Astra resolved the SQLite `INSERT OR REPLACE` trigger bypass in migration 004,
then reviewed full report bindings, raw/spec adapter replay, executing-code identity,
retained locks, immutable current readback, no implicit repair on repeat builds,
and final manifest/report rereads before atomic sealing. Existing 001–003 SQL bytes
remain unchanged. No activation service or HTTP read endpoint was added.

The Sol service worker passed 10 focused tests before a final malformed-project
type guard and 4 affected dependency tests afterward. The independent Sol worker
passed 79 integrity/storage tests on final stable source. Coordinator CLI/acquisition/
credential regression checks passed 36 tests. An earlier full suite overlapped a
source edit and correctly rejected mismatched loaded/snapshotted code; its 360
passes, 50 fixture errors and 2 unreached injection checks are not acceptance.
A fresh stable-source full suite supersedes it; final outcome follows below.

## Accepted result and exact sealed identities

**T007b done; T007c next ready; T008 UI pending.** One real release is sealed,
with 303 candidate versions, 330 complete nodes and 1,983 closure edges.
The active pointer remains **null**. No activation or baseline read endpoint exists.

- Release / canonical manifest object: `81ec338c8c4ff0da3cd7d3f6aa5acbdebb14c65a9096689d202211629138cf84`.
- Closure report: `48ab41e78ef0553ea6571290391d987372eae293eeeb475a664081a9027dd2c8`.
- Code snapshot file-manifest digest: `0b916ddd516020ff1643b3caa7a3a60eb9d2138062018ce0152a0401a12c3e78`.
- Code HEAD: `e1997e3d95b81ea063a287d65b1518045644a91f`, dirty tree explicitly recorded.
- Exact retained code/build/config/lock files: 53. Documentation and tests are outside the declared build-input snapshot scope.
- Runtime: Python 3.12.12 / SQLite 3.50.4, installed package inventory retained; `lock_sync_verified=false` accurately distinguishes pins from a lock-sync proof.

Canonical manifest and reports are content-addressed objects registered in the
baseline store. All supporting raw/spec/retrieval/source/metric/geography/document/
transform identities and query/config/schema/dependency/code pins are closed.
Complete manifest/report readback precedes atomic SQL seal; build never changes
`app_state`. Current verification replays the retained source bytes and verifies
all memberships/dependencies without writing or repairing evidence.

```sh
.venv/bin/cdt release build \
  --data-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929' \
  --run-id bc809bfa-e597-4447-8feb-5a988cb2d4ed \
  --import-id 352490fd-8882-4b93-a8df-03c0df1a22f3 \
  --import-id 6d97c8af-ed5c-4f2d-b392-1e400a7908aa \
  --import-id 351ba05c-73dc-401f-b5a3-6851a9356454 \
  --report-id 9f6709caf335f9722c7dba5307d85c8d4f1d3e8d6e825321f72ab8b784947a9e

.venv/bin/cdt release verify \
  --data-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929' \
  --release-id 81ec338c8c4ff0da3cd7d3f6aa5acbdebb14c65a9096689d202211629138cf84
```

Both exited 0. Build returned sealed=true, synthetic=false, no issues and
active_pointer_changed=false. Separate-process verification returned
current_dependencies_verified=true and 303 versions. Normal external-root lock
and build writes used filesystem escalation. Do not rebuild merely to resume;
the explicit verification command is the current-read operation.

Astra independently used a fresh process and a read-only baseline transaction to
verify this exact sealed release, all source/support/reproducibility pins and
candidate joins, original retrieval envelopes, and the null active pointer. Its
before/after baseline SHA-256 remained
`7dea9c3fae526401fdfcdaf827bc94be119214cd8709bf9053cac09336b170df`.
Astra accepted **T007b only**. Safe durable evidence is in
[the evidence record](../evidence/2026-09-29-sealed-build.json); its independent
review summary remains at `/private/tmp/cdt-t007b-20260929/astra-sealed-review.json`.
No raw observations, document text or credentials were added to Git.

## Final checks, limits and continuity

- `.venv/bin/pytest -q`: **413 passed**, 1 existing Starlette deprecation warning, 137.02 seconds. This is the fresh stable-source complete acceptance run.
- `.venv/bin/ruff check src tests scripts`: passed.
- `git diff --check`: passed.
- CLI/acquisition/credential regression selection: 36 passed. Independent integrity/storage: 79 passed. Final service malformed-dependency checks: 4 passed; the full suite includes them.
- Accepted source specs and migrations 001–003/private 001 remain byte-identical. Old schema-003 database and all six public objects remain byte-identical. No other earlier/default roots were opened or changed.
- Frontend, OpenAPI and dependency manifests/locks are unchanged; no browser/frontend rerun was needed. UI remains the existing unactivated shell.

All workers completed; all test/build/verify processes exited. No server,
acquisition, scheduled task or background process remains from this work. No
accounts, credential scanning, outreach, publication, spending or automation.
The local evidence seal grants no source redistribution rights: county PDF
redistribution remains unconfirmed and boundary/document HTTP provenance is
historical. General job orchestration, package portability and upgrade/recovery
remain outside this checkpoint.

Checkout remains the original sole `main` worktree and HEAD. All implementation,
tests and documentation changes remain uncommitted; no user work was reverted.
New implementation paths: `domain/releases.py`, `storage/releases.py`, baseline
migration 004 and release tests. CLI is extended; the two old fake-seal storage
tests now assert rejection under the stronger contract. README, architecture
command status and execution documents/evidence carry the accepted result.

Next session: follow [the starter prompt](../start-session.md), inspect the exact
sealed release above, freeze T007c activation/pinned-read interfaces under Astra,
and preserve all existing work. Do not repeat acquisition, replay or sealing to
resume. No manual source action is needed.

Final preservation/link check: all 64 local Markdown links in changed/new prose
resolve; safe evidence JSON parses; final tested code bytes remain identical;
12 protected spec/migration/dependency/OpenAPI files remain identical; sealed
baseline bytes remain unchanged after verification; schema-003 database and six
objects remain unchanged. Branch/HEAD/sole worktree unchanged, 18 intended
modified/untracked paths. All three worker tasks are completed.
