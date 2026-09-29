# Shared contracts for the first implementation wave

Status: First-wave interfaces accepted in T001 on September 27, 2026. `src/chesterfield_twin/domain/contracts.py` owns bootstrap/session/measurement transport validation; `openapi.json` and `frontend/src/api/schema.d.ts` are generated. Later evidence/release services remain pending.

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
- Public version registry, version links, measurement staging, artifacts/retrievals, release memberships and active pointer exist. Version payloads and sealed memberships are immutable; T006a source candidates now have typed provenance and adapter validation; general claim classes and complete persisted release closure are **not yet validated**. T006/T007 must validate provenance closure, supporting metadata membership, synthetic isolation, uncertainty and source mappings before any real release can be sealed. The separate measurement table is candidate staging, not a displayed release fact.
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
