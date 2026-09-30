# Shared contracts for the first implementation wave

Status: First-wave interfaces accepted in T001 on September 27, 2026. `src/chesterfield_twin/domain/contracts.py` owns bootstrap/session/measurement transport validation; `openapi.json` and `frontend/src/api/schema.d.ts` are generated. First-slice retained evidence, validation and sealed-build services are now accepted below; activation and application reads remain pending.

## Ownership and authority

The supervisor owns contract changes. A worker identifies a needed change, its consumer impact, and an example; the supervisor settles it and informs affected workers. Once code exists, Pydantic/OpenAPI owns transport shapes, versioned SQL migrations own persistence, and source specifications own source-specific mappings. This document remains a short index of invariants, not a duplicate schema.

## C001 — Local runtime and bootstrap

- Package: `chesterfield_twin`; CLI: `cdt`; data root resolved centrally from explicit configuration/`CDT_DATA_DIR`, otherwise the architecture's Application Support path.
- Initialization is idempotent and accepts an isolated test data root. Runtime data never defaults into the source checkout.
- Normal server: `127.0.0.1`, port 8765 by default. The compiled frontend and API share an origin.
- `GET /healthz`: minimal process readiness, no source/private detail. Authenticated `GET /api/v1/bootstrap`: `api_version`, `active_release_id` (nullable), `has_baseline`, and `capabilities` listing actually implemented operations. No private narrative or machine paths.
- Initial frontend renders a truthful empty state when there is no active release. A capability absent from the server is unavailable in the UI.

## C002 — Evidence and release boundary

- All baseline data requests carry `release_id`; responses echo it. Bootstrap alone can discover the active release. The UI pins that result until an explicit switch.
- Release membership versions names, geometry, metrics, source references, relationships, coverage, and reviews as well as values.
- Claim classes: reported, calculated, inference, hypothesis, scenario. Numeric value states: observed, suppressed, unavailable, not_applicable. Only observed may contain a numeric value; zero is valid.
- Identifiers are opaque strings; geography identifiers preserve leading zeroes. Source periods, publication/retrieval dates, units/universe, uncertainty, and evidence locators are distinct fields.
- Draft import, validation, sealing, and activation are separate operations. A build does not silently activate itself.
- Synthetic fixtures contain explicit example markers and cannot enter a real source release as purported observations.

## C003 — Source adapters

Adapters discover, fetch, normalize, and validate. They return typed candidate records and structured issues, never mutate the active release or private strategy. Retried input is idempotent. Raw bytes, retrieval metadata, and derived-record identity are separate. Retention limitations are explicit.

T002 supplies actual source-specific field definitions and sample locators. T006 may adjust the provisional schema using those samples through supervisor coordination. Do not freeze ACS variable names or geography releases without checking the source.

## C004 — Private boundary and checks

Private services may read pinned public claims through a read-only interface; baseline services/exporters cannot open the strategy store. Tests use a temporary root with distinctive private sentinel values and assert they never appear in baseline exports or baseline search. Private reference validation is explicit because cross-database foreign keys do not exist.

Before passing a contract to two workers, the supervisor supplies at least one valid and one invalid example and names the check that verifies it. Contract tests belong beside implementation and should test user-visible/domain behavior, not reproduce every schema line.

## Accepted wave-one examples and assignments

- Valid empty bootstrap: `{"api_version":"v1","active_release_id":null,"has_baseline":false,"capabilities":[]}`. UI must not advertise absent capabilities.
- Session: `POST /api/v1/session` with `{"secret":"<fragment secret>"}` and exact Origin; returns `{"csrf_token":"..."}` and HttpOnly SameSite=Strict cookie. Subsequent GET bootstrap uses the cookie. Mutations also need exact Origin and `X-CSRF-Token`. Secret is one-use per launch.
- Measurement valid example: reported, observed `"0"`, people, explicit universe/geography/vintage/period. Invalid: suppressed with numeric `"0"`; non-observed requires null plus a reason. `tests/test_contracts.py` checks these boundaries. These examples are synthetic, not county claims.
- Central path resolver: `config.resolve_data_root(explicit=None) -> pathlib.Path`, rejects the checkout and recognized cloud-sync roots. Caller is responsible for choosing a genuinely local filesystem; arbitrary network mounts cannot be inferred from a pathname.
- Storage wave: `storage.initialize(root: Path)`, `BaselineRepository(root).bootstrap() -> Bootstrap`, `.export_release(release_id) -> dict` (explicit sealed release only); `PrivateRepository` is separate and never passed to baseline/export services. New initialization only; future upgrades must fail closed until paired backup/recovery is implemented.
- Browser assets are public application code; all data-bearing API routes require session, and all baseline data routes additionally require explicit release IDs. No baseline data route is added in the skeleton.

## Implemented authorities and remaining limits

- Runtime routes: `src/chesterfield_twin/api/app.py`; `scripts/export_openapi.py` regenerates `openapi.json` from this real app, then `npm --prefix frontend run types` generates TypeScript.
- Initial schema authority: `src/chesterfield_twin/storage/migrations/{baseline,private}/001_initial.sql`. Ordered checksums are enforced; existing unmatched/partial pairs fail closed. Migrations are packaged with Python rather than duplicated at repository root.
- Public version registry, version links, measurement staging, artifacts/retrievals, release memberships and active pointer exist. Version payloads and sealed memberships are immutable; T006a source candidates now have typed provenance and adapter validation; general claim classes remain future work. T007b now validates complete persisted closure for the bounded three-source first slice, including supporting membership, synthetic isolation, uncertainty and source mappings; broader claim/release classes are not implemented. The separate measurement table is candidate staging, not a displayed release fact.
- `BaselineRepository.export_release` is a read-only, explicit-sealed-release internal boundary check. It has no HTTP/CLI export route and does not yet produce the full versioned/retention-filtered export promised by T013. No baseline search exists yet.
- `storage.maintenance_lock` supplies a nonblocking shared serving/exclusive initialization lock; `check_initialized` checks both ledgers, integrity and foreign keys. Private repository remains separate. No upgrades, backup, restore or cross-database reference validation is advertised.


## T006a — Accepted normalization interfaces (September 29, 2026)

Executable authorities: `domain/candidates.py`, `sources/common.py`, and source-specific adapters. The three functions `normalize_acs`, `normalize_boundaries`, and `normalize_document` accept `(raw: bytes, retrieval: Retrieval, spec_bytes: bytes, *, synthetic: bool)` and return `CandidateBatch`. They have no network, database, private-store or release side effects. Discovery, fetching to retained artifacts, persistence and job lifecycle remain future work.

- `Retrieval` records original time, status, media type, optional ETag/Last-Modified and a public HTTPS URL; only `get`/`for`/`in` query selectors are permitted. Credential removal must occur before constructing it. It is caller-supplied metadata, not proof of HTTP access or authorization.
- `Provenance` binds every candidate to SHA-256 of exact source bytes and specification bytes, source ID, transform ID, size, retrieval metadata, explicit synthetic flag, and retention/redistribution policy. Original source artifacts are not embedded or persisted by adapters. County PDF redistribution remains unconfirmed.
- Natural keys identify the source assertion; fingerprints include normalized content, source/spec hashes, transform identity and synthetic status, excluding retrieval-event metadata. Same bytes re-retrieved repeat identity; changed bytes/spec/transform change the version. This defines identities, not database upsert behavior.
- ACS candidates preserve E/M/EA/MA separately, source strings/nulls, uncertainty at 90%, aggregation, units, universe, 2019–2023 period, 2023 geographic vintage and 2020 tract definitions. Annotations override numeric interpretation; bounds are unavailable as point values, not silently rounded or clamped. Unknown annotations fail closed.
- Boundary candidates retain source NAD83 (`EPSG:4269`) coordinates/WKT and separately hash normalized geometry. DBF member/zero-based record locates source geometry and square-metre area attributes. This is not a WGS84 display layer or full topological validity proof.
- Document candidates retain exact extracted page text, page-text hash, character span, one-based PDF/printed pages, heading, FY2025 period, both locality codes, and scope caveat. Extraction is pinned to pypdf 6.1.1 and a transform version. Text matching verifies headings/scope, not an inferred causal relationship.
- Structural failures return issues with an empty candidate list. `validate_slice` checks county coverage/joins, source-version consistency, period/vintage and document coverage. It rejects synthetic evidence by default; its explicit test opt-in cannot authorize a real release. A valid in-memory batch does not establish retained-byte availability or complete release-membership closure.

Valid/invalid shared examples remain in `tests/test_candidates.py`: observed `"0"` is valid; suppressed with numeric `"0"` is invalid. Adapter and cross-source tests are explicitly synthetic. Original audit-byte replay is a separate command (`scripts/replay_audited_sources.py`) and reports no ACS observation access.

## T006b — Accepted staging interface (September 29, 2026)

Supervisor owns `storage/staging.py`, storage foundations and `002_candidate_staging.sql`. No dependency or accepted adapter changes were required. New databases only; old stores fail their exact migration-ledger check. All operations use an explicit external initialized root, a shared maintenance lock and baseline-only connections.

- `CandidateStaging(root).create_run(*, synthetic: bool) -> str` creates an immutable run with mandatory real/synthetic mode.
- `.stage(run_id, source, raw, retrieval, spec_bytes, *, synthetic: bool) -> StageResult`, where source is exactly `acs`, `boundary`, or `document`, chooses the accepted adapter internally. Mode must match the run. Validation precedes any artifact/metadata write. Failed normalization raises `StagingValidationError` with `.issues`; storage/integrity errors raise `StorageError`. No arbitrary candidate batch is accepted for persistence.
- Frozen `StageResult`: `run_id`, `import_id`, `retrieval_id`, `version_ids: tuple[str, ...]`, `new_versions: int`. Every successful stage creates a distinct import/retrieval event, even when original retrieval metadata is repeated in offline replay. Candidate IDs are fingerprints and exclude retrieval metadata.
- `.read_import(run_id, import_id) -> CandidateBatch` requires matching explicit run, re-verifies exact raw/spec SHA-256 and sizes, ordered membership digest/count, typed candidate fingerprints and indexed lineage, then injects that import's retrieval metadata. It returns the complete original batch including validation warnings. Missing/corrupt evidence fails closed; this is internal staging access, not a baseline release query or export.
- `ArtifactStore.read(digest) -> bytes` verifies bytes against the address; object creation is file- and directory-synced before metadata commits. Retained spec bytes preserve publisher/terms/publication information beyond candidate fields. Candidate payload preserves all accepted source values, annotations, locators and policies without flattening into the older measurement table.
- Accepted local retention is only the audited ACS response, boundary archive and county PDF policy. County redistribution stays unconfirmed. Caller-supplied retrieval and synthetic declarations remain a trust boundary; neither proves live access or authorization.

Valid example: initialize a temporary external root, create a `synthetic=True` run, stage the generated 75-row ACS fixture with `synthetic=True`, and rehydrate 225 candidates. Invalid example: the same fixture declaration submitted to a `synthetic=False` run fails before retention. `tests/test_staging.py` verifies these examples, idempotent versions/separate events, changed content, preservation, validation failure and interruption. `scripts/stage_audited_sources.py` replays real pinned boundary/PDF bytes in a real-only run with no source text output.

## T007a — Accepted report interface (September 29, 2026)

`storage/validation.py`: `CandidateValidation(root).validate(run_id, import_ids: tuple[str, ...]) -> ValidationReport`; `read_report(run_id, report_id)` reads a historical attestation. Executable frozen types are in `domain/validation_reports.py`. Empty through 16 IDs are accepted selections; ordering is canonical, duplicates remain errors. Run identity is required. Unknown run, invalid call or unavailable persistence raises `StorageError`. Unknown/cross-run/mixed-mode imports, missing/corrupt objects and missing/duplicate sources yield persisted issues. Valid synthetic content has `valid=True`, `synthetic=True`, `real_slice_valid=False`; missing real ACS has both validity properties false. No sealing or activation capability.

Each input pins diagnostic metadata and ordered version IDs; `verified=True` means staging's complete retained readback succeeded at validation time. Reports contain no raw bytes, excerpts or private data. Content hashes include validator ID, run/mode, inputs and issues, excluding creation timestamps. Identical content reuses the immutable report. Readback verifies that hash without reopening artifacts, so a past result remains inspectable after object loss; callers must revalidate for current availability. Migration 003 is for fresh stores only.

## T006f — Local credential injection (September 29, 2026)

User authorized credentials for local runtime injection (D020), superseding the earlier no-credentials scope. `credentials.py` owns `CensusCredentialProvider.get_census_api_key() -> SecretStr | None`, `clear()` and `load_census_credentials(source)`. Only `none`, `prompt`, `env`, `keychain` are supported, chosen explicitly by `cdt serve --census-key-source`; default none, no fallback. The provider rejects serialization and masks repr/str; raw access is an explicit trusted-backend operation, not a transport field.

The loader removes `CDT_CENSUS_API_KEY` from the serving environment for every source before browser/helper children; uses it only for explicit env. Prompt requires a terminal and aborts on echoed-input fallback, EOF or cancellation. Keychain is macOS-only, read-only fixed service `ChesterfieldTwin` / account `census_api_key`, captured system-helper output and five-second timeout. Invalid/missing/backend failures use sanitized fixed errors. No plaintext argv/config/disk storage, implicit lookup, credential CRUD, automatic source request, or frontend status is added.

`create_app(..., credentials=provider)` takes lifecycle ownership, stores only an internal backend dependency, and clears on lifespan exit/factory failure. CLI also clears on startup/server failure, including interruption. Cleanup releases references, not guaranteed erasure of memory or parent environments. `init`/`doctor` never load a key. Sentinel tests cover source selection, redaction, child-environment removal, lifecycle and unchanged HTTP/OpenAPI/storage behavior. Actual Keychain retrieval and real Census access remain untested. Future acquisition must sanitize authenticated requests/errors before retention; T006f supplies no fetch implementation or release authority.

## T006g — Explicit bounded acquisition and continuation (September 29, 2026)

Astra froze this contract before Sol implementation. `acquisition.py` owns side-effect-free `preflight_acquisition(*, boundary_path, audit_dir)`, explicit `acquire_acs(*, credentials, boundary_path, audit_dir) -> AcquisitionResult`, and offline `read_acquisition(*, audit_dir, boundary_path) -> AcquiredInput`. CLI preflight precedes credential loading; acquisition repeats it. Caller owns provider cleanup. `cdt acquire-acs` requires both paths, supports the same four credential sources with default none, and has no key-value/URL/limit/release overrides. No existing startup or import path initiates acquisition.

The fixed request is one HTTPS response from `2023/acs/acs5/subject`, NAME plus E/M/EA/MA for S1901_C01_012, S1901_C01_001 and S1701_C03_001, `for=tract:*`, `in=state:51 county:041`. Exact 75-tract identity comes from the unchanged hash-pinned boundary ZIP and adapter. The transport ceiling is 20,000,000 bytes and 60 seconds total including helper launch/DNS/TLS/headers/body; unchanged adapter acceptance remains capped at 1,000,000 bytes. The helper receives its key through stdin only, has a minimal environment, no redirects/proxies/decompression/retries, bounded captured output and discarded stderr. Parent cancellation/deadline terminates and reaps it. Unsafe credential echoes, error bodies and differing representations are rejected, never rewritten as raw evidence.

Only a successfully accepted original response can be published to a new external audit directory. Fixed files: `response.json` (original bytes), `manifest.json`, `acs_spec.toml`, `boundary_spec.toml`. The manifest pins schema/kind/real-mode acceptance, actual sanitized request/final URLs, status/media/UTC time/total elapsed time, byte count/SHA-256, exact source specification and boundary identities, geography digest and counts. `geoid_sha256` uses `digest(sorted(unique_geoids))`. Readback requires strict exact keys/types, unchanged retained/current specs, exact byte/hash identity, accepted URLs/envelope, unchanged adapter semantics and exact tract match. Its raw/spec fields are hidden from repr. Caller-controlled local manifests are not cryptographic proof of HTTP origin.

Acquisition creates no store/import/release. `scripts/stage_acquired_slice.py` explicitly takes the bundle, boundary, PDF and new external root. It verifies all three sources and cross-source semantics before exclusive root creation/schema-003 initialization. It stages one real import per source, explicitly selects all three IDs for persisted validation, then calls validation again against current artifacts. Boundary/document envelopes retain historical spec timestamps with declared expected status/media, not fresh HTTP verification. Existing roots, specifications, adapters and ledgers remain unchanged. Failures preserve any created root/bundle; no upgrade, sealing, activation or default-read authority exists. Synthetic tests are not live acceptance. The subsequent user-local hidden-prompt acquisition passed unchanged-contract readback, and the fresh real three-source root passed initial and explicit current validation; identities are in the latest state/handoff. This advances traceable ingestion only, with no release authority.


## T007b — Accepted release closure and explicit build (September 29, 2026)

Executable authorities are `domain/releases.py`, `storage/releases.py` and baseline `004_release_closure.sql`; complete semantics are in the [Astra freeze](t007b-freeze.md). `ReleaseBuilder(root, repository_root).build(run_id, import_ids, expected_report_id=...)` explicitly constructs and seals a complete first-slice release. `read_release(release_id, verify_current=True)` verifies current retained closure; historical-only readback is explicitly weaker. CLI exposes separate `release build` and `release verify` commands with required root and selection pins. No activation or baseline query endpoint is added.

Build returns a persisted closure report, optional manifest and sealed flag. The selected candidate report must match fresh current validation. Each of the 303 candidates and every supporting identity is closed in a canonical graph and normalized SQL membership. Reproducibility captures exact allowlisted code/config bytes, locks, runtime inventory, schemas, selection and transforms. Complete manifest/report objects are durable before sealing; failures preserve prior releases and the active pointer. A synthetic seal stays synthetic and is never real-source acceptance. New initialization requires 004; no accepted earlier migration or root is upgraded. Integration evidence and remaining limits are in the latest handoff.
