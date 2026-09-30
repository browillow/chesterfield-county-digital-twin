# T007c activation and pinned application reads

September 29, 2026. Contract owner: explicitly requested `gpt-6-astra` supervisor;
tool metadata does not independently confirm the executing model. Starting clean
sole checkout: `main`, `fcc58c723921707cb7b63a09b2c0216f6df21e57`.

This checkpoint enables inspectable reads of retained tract measures, geography
and document evidence, and prevents default or multi-request views from mixing
releases. It implements activation, bounded application reads and the basic
old/new comparison required by T007. It does not implement T008 UI or T011b agent
access. Preserve baseline migrations 001–004, private 001, source specifications,
adapters, accepted historical reports and all existing sealed content. No schema,
dependency, acquisition, rebuild, replay, upgrade, export or earlier-root access.

The only actual-data root selected for acceptance is
`/Users/jordan/Library/Application Support/ChesterfieldTwin-SealedSlice-20260929`;
the exact release is
`81ec338c8c4ff0da3cd7d3f6aa5acbdebb14c65a9096689d202211629138cf84`.
Its pointer starts null. Coordinator may explicitly activate that selected release
after implementation checks, then independently verify pinned reads. This freeze
itself performs no activation or data-root mutation.

## Executable contracts and storage interface

`domain/application.py` owns new transport models. Existing release/build and
candidate models retain their semantics and bytes. Implement
`storage/application.py`, `ReleaseApplication(root: Path, repository_root: Path)`:

```python
bootstrap() -> Bootstrap
activate(release_id: str) -> ActivationResult
summary(release_id: str) -> ReleaseSummary
records(release_id: str, *, query: RecordQuery | None = None) -> RecordPage
evidence(release_id: str, version_id: str) -> EvidenceResponse
compare(old_release_id: str, new_release_id: str) -> ReleaseComparison
```

All explicit IDs must be lowercase 64-character SHA-256 strings, with no fallback
to pointer, latest row, environment, candidate table or report. Validate IDs and
queries before storage work. `None` query means the model's bounded defaults.
Service checks matter independently of HTTP checks. Only baseline connections and
retained public objects are allowed; no private database access or `ATTACH`.

Reuse the accepted verifier, `ReleaseBuilder._read(db, release_id,
verify_current=True)`, inside the application's own connection and transaction.
Do not change closure semantics, execute retained code, compare historical code
pins to current checkout bytes, call build or candidate validation persistence,
repair missing objects, or use historical-only verification. The repository-root
argument preserves the existing builder constructor; reads use retained build
pins rather than snapshots of the current checkout.

Each read owns one shared maintenance lock, ledger-checked read-only baseline
connection and explicit `BEGIN` snapshot through verification and projection.
Comparison verifies both IDs in that same snapshot. Reuse `CandidateStaging`
connection/lock helpers if useful; do not nest a separate `read_release` snapshot.
Return fully materialized typed responses before closing the connection. A
successful historical report is never substituted for current evidence checking.
For this 303-record release, full verification on each operation is acceptable;
do not add a cache that survives changes to retained objects.

Projection from a completely verified manifest is the preferred small design.
Candidate nodes already bind exact SQL version membership, content and fingerprint.
Construct `BaselineRecord(version_id, candidate)` from each selected candidate node,
rehydrating `provenance.retrieval` from that candidate's selected `retrieval` edge
and its node's `metadata`. Verify the typed candidate fingerprint still equals
the version ID. A shared candidate can have different retrieval support in two
releases; never use a global first/latest retrieval. Preserve all units, numeric
strings, unknown/suppressed states, E/M/EA/MA, 90% MOE, periods, claim classes,
locators, retention, source/spec/transform IDs and source CRS without alteration.
Geometry remains EPSG:4269 source geometry, not a WGS84 display layer. County
document scope remains both localities with its caveat; this grants no PDF export.

`records` returns selected candidate membership only. Filters are ANDed before
sorting/pagination: exact candidate kind, geography ID on observation measurement
or boundary, metric code on observation. Nonapplicable candidate kinds do not
match a supplied geography/metric filter. Sort by version ID. `total` is filtered
count before slicing. Offset 0–303 and limit 1–303 (default 100); no arbitrary
SQL, search expressions or unbounded pagination. Empty selections return an empty
page. Payloads carry `release_id`, `synthetic`, current verification and pagination.

`summary` returns candidate and closure report IDs, counts by candidate kind,
the selected coverage node payload and the three selected source nodes sorted by
node ID. This is current verified release metadata; historical coverage acceptance
prose and historical source access status remain unchanged and visibly historical.
Do not expose current pointer state in a pinned response or rewrite sealed prose
to claim new acceptance.

`evidence` requires membership of the exact version ID. Return its typed record
and the outgoing reachable graph from its candidate node, including that node,
geography candidate where relevant, and selected raw/spec/retrieval/source/metric/
document/transform support. Include only edges whose endpoints are included;
deduplicate and use canonical node/edge ordering. Do not return unrelated nodes,
global artifact registrations, filesystem paths, original bytes, arbitrary file
access or code-object downloads. Unknown/unselected IDs return the same error.

Integration clarification: evidence nodes use application-only `EvidenceNode`,
which adds serialized `node_id` to the existing `kind`, `key`, `payload` fields.
It equals the immutable `ReleaseNode.node_id` and identifies edge endpoints without
requiring consumers to reproduce canonical hashing. This computed transport field
does not participate in node hashing or change the sealed manifest representation.
Summary source nodes retain the original shape because that response has no edges.

`compare` compares record identities by `(kind, natural_key)` after verifying both
complete releases. Return IDs plus both synthetic declarations, unchanged count
and added/removed/changed entries with old/new version IDs (null on the absent
side), sorted by kind and natural key. Maximum 606 entries follows from two
303-member releases. Equal IDs give 303 unchanged and no changes. A changed
retrieval or build/support identity alone is not a changed candidate; this is an
identity comparison, not statistical significance, geographic comparability or
a complete metadata diff. Mixed real/synthetic comparison is rejected. No implicit
previous release or active-pointer selection exists.

## Activation and bootstrap

Activation is an explicit separate authority. Under shared maintenance lock and
a ledger-checked mutable baseline connection, execute `BEGIN IMMEDIATE`, read
the existing singleton pointer, then fully verify the selected sealed closure on
that connection. Reject synthetic releases for activation; there is no runtime
test/fixture override or HTTP/CLI flag. Require the singleton row to exist.
Update only `app_state.active_release_id` after verification, then commit. Return
selected/active ID, prior ID, `changed`, `synthetic=false` and current verification.
Same-ID activation must reverify; it succeeds with `changed=false` and need not
issue an UPDATE. Earlier pinned releases remain readable when the pointer changes.

Any verification/storage failure, SQL abort, exception or interruption before
commit must roll back; connection closure on `BaseException` must preserve the
previous pointer. A crash after commit may leave the complete new pointer, never
a partial state. Do not return success before commit. No files, manifests, reports,
memberships or operational activation log are added. Existing SQL sealed-state
guards remain defense in depth, not a replacement for complete service verification.
Normal same-user filesystem races remain the accepted storage limitation.

`bootstrap` is the only active-release discovery read. Read its pointer once in an
explicit snapshot. Null returns `has_baseline=false`; a nonnull pointer requires
current verification of that exact real sealed release before returning
`has_baseline=true`. Invalid, missing, synthetic or unavailable active state fails
closed, never silently clears/replaces the pointer or shows a fresh empty baseline.
Capabilities when the application service is wired are exactly
`release_activation`, `release_reads`, `release_comparison`; these advertise backend
operations, not T008 UI completion. Existing bare `BaselineRepository.bootstrap`
may remain the internal low-level pointer helper with empty capabilities; production
`serve` must use `ReleaseApplication.bootstrap`. Do not change storage foundation
or the old `Bootstrap` model solely for this checkpoint.

Explicit sealed reads may return synthetic content with `synthetic=true` in every
envelope and unchanged candidate flags. This permits honest fixture inspection;
it is never real baseline acceptance. Synthetic activation is rejected. Tests of
successful activation can use narrowly isolated verifier stubs for transaction
injection, accurately labeled as such; actual real activation is coordinator
acceptance evidence. Do not relabel synthetic fixture content as real evidence.

## API and CLI wiring

Extend `create_app` with optional `application: ReleaseApplication | None = None`,
preserving existing `bootstrap` callable and credential/session behavior. If an
application service is present, bootstrap uses its checked method. Register these
routes even without a service so offline OpenAPI generation sees the contract;
an absent service returns a sanitized 503 `application_unavailable`.

| Method and path under `/api/v1` | Selection and result |
| --- | --- |
| `GET /releases/{release_id}` | Required path ID; `ReleaseSummary` |
| `GET /records` | Required query `release_id`; optional kind/geography_id/metric_code/offset/limit; `RecordPage` |
| `GET /evidence/{version_id}` | Required query `release_id`; path version; `EvidenceResponse` |
| `GET /changes` | Required query `old_release_id`, `new_release_id`; `ReleaseComparison` |
| `POST /releases/{release_id}/activate` | Required path ID, no request body or implicit selection; `ActivationResult` |

The release ID path itself pins summary/activation, so no redundant query ID is
needed there. Existing session, exact Host/Origin, CSRF on mutation and no-store
boundary apply unchanged. Every baseline result echoes its explicit selection;
comparison echoes both IDs. Extra query keys and malformed/duplicate selector keys
must be rejected, not silently ignored; fixed enum filters are allowlisted.
Do not render document text as HTML or add a UI route/consumer.

Define `ApplicationError(StorageError)` in `storage/application.py`, exposing
`code` from this fixed vocabulary, with sanitized fixed messages. HTTP mapping:
`invalid_query` 422, `unknown_release` 404 (unknown or draft), `unknown_evidence`
404 (unknown or outside membership), `synthetic_release` 409 (activation or mixed
comparison), `release_unavailable` 409 (current integrity/closure unavailable).
`StorageBusyError` maps to 503 `storage_busy`; unusable storage/schema maps to 503
`storage_unavailable`. Serialize errors as `{"detail": "<code>"}`; never expose
SQL, paths, submitted secrets or underlying exception text. Existing request
validation 422s may remain FastAPI validation responses for harmless IDs/filters.
Preserve cleanup of credential providers on factory failure/lifespan exit.

Coordinator adds `cdt release activate --data-dir ROOT --release-id ID`, calling
the same service, printing its result as JSON with no success before commit.
Keep build/verify unchanged and separate. A CLI read surface is not needed for
T007c: the service plus authenticated HTTP is the application read boundary.
Wire `serve` to the service without startup acquisition/build/activation. Regenerate
OpenAPI and frontend types from the actual routes; no handwritten divergent schema.

## Ownership, checks and stopping point

Astra exclusively owns this freeze and `domain/application.py`. Sol storage worker
owns new `storage/application.py` and `tests/test_application.py`. Sol API worker
owns `api/app.py` and `tests/test_api_application.py`, and reads the frozen domain
and service signatures. Coordinator owns CLI/runtime wiring, CLI tests, generated
OpenAPI/types and execution documents. No worker writes storage foundation,
accepted migrations, source specs/adapters, release verifier or another worker's
files. Report necessary contract changes before editing. Request `gpt-6.1-sol`
explicitly for fresh-context workers; no further delegation.

Required focused checks:

- Existing sealed synthetic fixture reads preserve flags and all candidate/support
  identities; synthetic activation and mixed-mode comparison reject. Malformed,
  missing, draft, unselected and corrupt evidence fail closed.
- Stage additional versions/retrievals after sealing and demonstrate pinned records,
  evidence, counts, filters and limit membership remain unchanged. Test geography,
  metric, unknown values, pagination bounds/order and private sentinel exclusion.
- Real activation transaction unit tests cover null/prior pointer, same-ID
  revalidation, injected failure before/at UPDATE and commit/interruption rollback.
  Use true nonnull sealed prior pointer fixtures; do not count only null preservation.
  Service rejects a synthetic target before writing. Old pinned reads after a
  pointer switch stay on the requested release.
- Verify current reads fail for missing/corrupt raw/spec/code/report/manifest and
  retain historical-only readback distinction. A broken selected closure cannot
  activate even if its historical report says valid. No read repairs or writes.
- Compare equal releases and two explicitly sealed selections with a changed
  candidate, including add/remove natural-key cases where valid fixture construction
  permits; show support/retrieval-only changes do not invent candidate revisions.
- API tests cover required pins, selector bounds/duplicates/unknown keys, echoed
  IDs, session/Host/Origin/CSRF, absent service, safe error mapping and no implicit
  mutation. Bootstrap only advertises supplied capabilities; schema generation
  opens no root or credentials.
- Coordinator performs focused CLI checks, full Python suite/lint/diff checks and
  generated-type check. No browser/UI acceptance is claimed. Stable-source test
  runs are required because build fixtures measure the executing source bytes.
- Actual selected release: compare before/after preserved public objects, sealed
  tables, private-store bytes and migration/spec/lock hashes; explicitly activate
  once after safety checks; separate-process checked bootstrap, bounded pinned
  observation/boundary/document/evidence reads and self-comparison; record exact
  IDs/counts/caveats and final pointer. Only pointer/database operational bytes may
  change. Do not open/rebuild earlier roots or mistake current source changes for
  a reason to rewrite historical build pins.

Stopping point is accepted T007c activation/read consistency and basic comparison.
T008 UI, generalized release/source support, map reprojection, search, raw download,
export, agent access, backup/recovery and acquisition remain separate work.
