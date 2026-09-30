# Session handoff: T007c activation and pinned reads

Date: September 29, 2026 (America/New_York). **T007c accepted by Astra; minimal T007 complete.**

Checkout: sole `main` worktree, HEAD `fcc58c723921707cb7b63a09b2c0216f6df21e57`,
started clean. Earlier handoff HEADs describe earlier sessions. No Git mutations.

Requested models: `gpt-6-astra` supervises the contract freeze and integration
acceptance; two bounded implementation workers explicitly requested `gpt-6.1-sol`
after the freeze. Task metadata does not independently confirm executing models.

## Ownership

- Astra: `docs/execution/t007c-freeze.md`, `domain/application.py`, contract and
  acceptance review. No other writes.
- Coordinator: CLI integration/tests, generated OpenAPI/frontend types, README,
  architecture command status and execution documents except the freeze.
- Sol storage worker: `storage/application.py` and `tests/test_application.py`.
- Sol HTTP worker: `api/app.py` and `tests/test_api_application.py`.
- [Astra freeze](../t007c-freeze.md) completed before both assignments. Storage
  foundation, existing verifier, migrations and source contracts are read-only.
  Workers do not spawn further agents.

## Starting evidence

The explicit release
`81ec338c8c4ff0da3cd7d3f6aa5acbdebb14c65a9096689d202211629138cf84`
in `/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929`
passed `cdt release verify --data-dir <that-root> --release-id <that-id>`:
current dependencies verified, real mode, 303 versions, no pointer change.
Existing maintenance-lock operations used filesystem escalation. No acquisition,
replay, sealing, credential access or earlier-root access occurred.

`/private/tmp/cdt-t007c-20260929/before.json` records starting hashes of 118 tracked
files and 60 public root files. Starting baseline SHA-256:
`7dea9c3fae526401fdfcdaf827bc94be119214cd8709bf9053cac09336b170df`.
Accepted source specs, migrations 001–004, retained objects and historical
evidence must remain unchanged. No new schema is planned.

The research benefit is an explicit, stable baseline that preserves citations,
units, uncertainty and supporting identities across activation changes, enabling
later useful evidence workflows without mixing drafts or unrelated releases.
T008 UI and T011a/T011b/T013a remain outside this checkpoint.

## Integration checks before activation

- New application service read-only preflight against the exact accepted real
  release returned all 303 typed candidates with equal fingerprints. Checked
  bootstrap still returned a null pointer. No evidence mutation occurred.
- Coordinator CLI/runtime/credential selection: `.venv/bin/pytest -q
  tests/test_cli_release.py tests/test_runtime.py tests/test_runtime_credentials.py`
  — 35 passed.
- Sol HTTP selection: `.venv/bin/pytest -q tests/test_api_application.py
  tests/test_api.py tests/test_api_credentials.py` — final 64 passed. Its initial
  run had 63 passed and the expected schema mismatch before regeneration; the
  final run supersedes it. Existing Starlette/httpx deprecation only.
- `.venv/bin/python scripts/export_openapi.py`, Node 24.21.0 `npm --prefix frontend
  run types`, `run build` and `run test` passed; frontend tests: 6. Managed Node
  path: `/private/tmp/cdt-node/node-v24.21.0-darwin-arm64/bin`.
- Astra preliminary review found no additional release/membership/privacy
  blockers. Coordinator findings corrected SQLite BUSY/LOCKED classification and
  moved synchronous HTTP activation off the event loop. At that point final acceptance awaited
  storage transaction/integrity tests and actual activation/read verification;
  their final outcomes appear below.

HTTP tests use isolated transport stubs. Storage fixture tests must retain
synthetic labels; neither is actual source acceptance. No browser/UI acceptance
is claimed. Baseline table digests and private-store byte hash (no private content
inspection) were captured in `before-tables.json` beside the starting hash record.

The first projection repeatedly recomputed candidate node digests while scanning
edges. Indexing retrieval edges per operation removed that work without retaining
a cross-operation cache. A fresh actual 303-record read, including complete closure
verification, took 0.568 seconds; this is one observed sample, not a latency SLO.
Further focused checks corrected strict-query revalidation (`mode='python'`
preserves a constructed boolean rather than converting it to an integer) and
consistent rejection of malformed stored pointers. The unknown-value test needed
an explicit synthetic input because the standard fixture contains observed values.
The corrected case seals synthetic unavailable/suppressed estimates and unavailable
MOE, and separately preserves observed zero.

Preoptimization and stale-test runs were interrupted/superseded. The initial full
suite was stopped after the fixture-assumption failure; none is acceptance evidence.
Final Python coverage is split between the stable application suite and all other
tests, avoiding a duplicate expensive corruption matrix. Commands/counts and
actual activation outcome are recorded below. Tested-source hashes are in
`/private/tmp/cdt-t007c-20260929/tested-code.json`.

Final stable regression partition: `.venv/bin/pytest -q
--ignore=tests/test_application.py` — **471 passed**, one existing Starlette
warning, 149.53 seconds. `.venv/bin/ruff check src tests scripts` and
`git diff --check` passed. Application partition and actual-root acceptance are recorded below.

## Actual activation and final verification

The final stable application partition, `.venv/bin/pytest -q -x
 tests/test_application.py`, passed **30 tests**, exit 0, 731.21 seconds, no
warnings. Together with the 471-test regression partition this covers **501 Python
tests**. All activation fault injections passed before the actual operation.
Astra's safety review authorized the selected activation after those checks.

```sh
.venv/bin/cdt release activate \
  --data-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929' \
  --release-id 81ec338c8c4ff0da3cd7d3f6aa5acbdebb14c65a9096689d202211629138cf84
```

Exited 0: previous pointer null, selected/active ID equal the explicit release,
`changed=true`, `synthetic=false`, `current_dependencies_verified=true`.
Filesystem escalation covered the requested external-root pointer transaction.
No build, replay, acquisition or new report accompanied activation.

Separate-process actual readback used
`/private/tmp/cdt-t007c-20260929/verify_actual.py`, with normal existing-lock
escalation. Checked bootstrap, explicit summary, all 303 typed fingerprints,
four authenticated HTTP pages, each evidence kind, a metric filter, unknown
unselected evidence denial and self-comparison passed. All 59 retained public
objects, all 18 non-pointer baseline tables and private-store bytes match their
starting hashes. Only `app_state` changed logically. Baseline SHA-256 is now
`8be9410ae07badecd1fbf499c7c113b68a87c4e2f8314cb988759662c390b623`.
[Safe durable evidence](../evidence/2026-09-29-activation-reads.json) contains no
observations, excerpts or private content.

The first readback script incorrectly assumed the sealed `ReleaseNode.node_id`
property was serialized. Correcting that harness established full preservation;
Astra then approved a narrow application-only `EvidenceNode` projection so clients
can directly resolve edge endpoints. Its computed ID hashes only the original
kind/key/payload. Accepted sealed models, hashes and manifests were not changed.
The final actual readback additionally verifies serialized IDs against original
canonical hashes and every edge endpoint against included node IDs. No repeat
activation occurred.

After this additive transport change: regenerated OpenAPI/types and Node24 build
passed; final HTTP/schema/credential suite **64 passed**; complete storage
projection test **1 passed** (21.19 seconds). These checks supersede affected
transport checks; prior full transaction/corruption coverage remains applicable.
No other production logic changed. The original frontend **6 passed** result
remains applicable, with no UI source change. No browser/UI acceptance is claimed.

Exact run/import/candidate/build-report IDs remain those in state and the safe
record. The release still has 303 candidates, 330 nodes and 1,983 edges. Boundary
and document provenance remains historical replay, NAD83 is source geometry,
county document coverage includes both localities and redistribution is unconfirmed.
T011a document intake, T011b agent access and T013a backup/restore remain planned.

## Final review and continuity

Astra accepted T007c and minimal T007 with no blockers. Its independent fresh
process verified only the selected current root: full retained closure, checked
active pointer, all 303 typed fingerprints, all three evidence kinds with explicit
node IDs resolving every edge, self-comparison and all 59 retained public objects.
Baseline before/after SHA-256 remained
`8be9410ae07badecd1fbf499c7c113b68a87c4e2f8314cb988759662c390b623`.
No reactivation, private-content access or evidence mutation occurred; only normal
existing-lock escalation. Final checks confirm 25 protected files stayed
byte-identical and only the additive application transport model/generated types
changed after full test coverage; affected checks were rerun. All implementation workers and test processes
completed; no server, acquisition process, background job or automation remains.
No Git mutation; all 19 intended implementation/test/generated/documentation/evidence
paths remain uncommitted in the original sole main worktree. No user work was
reverted. Accepted specs, migrations 001–004/private001, adapters, verifier and
locks remain byte-identical; no earlier data root was opened.

Next ready: T008 map/table/evidence workflow using the pinned
application API. Follow the updated starter prompt, preserve the active selected
release and freeze only the changed UI/display-geometry interfaces. Do not repeat
acquisition, build, replay or activation merely to resume. No manual acquisition
or credential action is needed.


Final documentation/preservation check: 78 local Markdown targets resolve; safe
evidence JSON parses; Ruff and `git diff --check` pass. All 106 tracked files
outside the 12 intended tracked edits remain byte-identical to session start.
Seven new paths bring the uncommitted total to 19. HEAD and sole worktree are
unchanged. All three agent tasks and every foreground command completed.
