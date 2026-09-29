# Current project state

Last updated: September 29, 2026 (America/New_York).
Implementation stage: **Local skeleton and T006a normalization accepted and tested.** First auditable source slice remains incomplete.
Active supervisor/assignments: None remaining. All three explicitly requested `gpt-6.1-sol` workers completed; supervisor reviewed and integrated their files.
Latest handoff: [Typed source adapters](handoffs/2026-09-29-source-adapters.md).

## Implemented and verified

- **T001/T003/T004/T005:** accepted Python/FastAPI/SQLite/React local skeleton, external data root, baseline/private separation, initial migration guards, loopback session security, pinned bootstrap and honest empty UI. No skeleton work was redone. Details remain in the [previous handoff](handoffs/2026-09-27-local-skeleton.md).
- **T002:** source audit/specifications accepted with the ACS access blocker below.
- **T006a:** typed unpublished candidates, retrieval/provenance and locators; source/spec/geometry/text hashes; natural keys and deterministic version fingerprints; structured atomic validation failures. Three bounded byte-to-candidate adapters validate the pinned ACS slice, NAD83 boundaries and FY2025 document. They do not fetch, persist or activate anything.
- ACS preserves E/M/EA/MA, annotations, suppression/null versus zero, bounds, published 90% MOEs, units/universes, periods and geography. All ACS observations used in checks were **synthetic**.
- Independent replay of retained audited bytes succeeded: boundary ZIP validates 2,186 Virginia records and returns **75 Chesterfield candidates**; county PDF returns **3 exact page excerpts** (PDF 229–231 / printed 211–213), preserving both Chesterfield and Colonial Heights scope. Actual hashes match `source_specs/`. This is offline replay, not a fresh source-access check.
- Cross-source validation requires 75 tracts × 3 metrics and the three document locators, consistent snapshot identities/period/vintage, and rejects synthetic candidates by default. A combined replay with synthetic ACS on the real boundary keys returns 303 candidates only with explicit test opt-in; the real-slice check rejects it.

No real ACS observations, persisted source candidates/artifacts, active release, maps, ingestion jobs, private brief UI, search, user export, or backup/restore have been added. Typed adapter validation does not establish complete persisted provenance/release closure. NAD83 source geometry is not a WGS84 display layer or full topology-validity proof. PDF accepted-output limits are not hard peak-memory/CPU isolation. Existing schema upgrades still fail closed. Product operation still requires this checkout.

## Next ready work and blockers

- **T006b ready:** retained public artifacts and candidate staging from the accepted adapter contracts, using independently available boundary/document bytes and explicitly isolated synthetic tests. Concrete assignment/acceptance packet in [backlog](backlog.md). Supervisor owns storage/shared contracts/migration decisions; no activation or default baseline reads.
- **Full T006 blocked:** last verified corrected ACS request (September 27) returned HTTP 302 to Census `missing_key.html`, `X-DataWebAPI-KeyError: 1`. Still needs authorized observation bytes or a separately verified official download route. No live ACS request was made this session; metadata/docs and fixtures are not observation access. No account or credential was created or searched for.
- T007 release validation/sealing/explicit activation and T008 pinned map/table/evidence remain pending. Retention, artifact availability, complete membership closure and synthetic isolation must be enforced in those services.
- No personal decision blocks T006b. Private data remains outside Git; tests use temporary roots and no real research directory was initialized.

## Commands and checks

From this checkout: `uv sync --locked`, `npm --prefix frontend ci`, `npm --prefix frontend run build`; then `uv run --no-sync cdt init` and `uv run --no-sync cdt serve --open`. See [README](../../README.md). Use an external temporary `--data-dir` for tests.

This session: `.venv/bin/pytest -q` **132 passed**, including existing API/storage/runtime/OpenAPI drift checks, with the existing Starlette test-client deprecation warning; Ruff and whitespace checks pass after correcting one import order and Markdown whitespace. `uv sync --locked --offline` passes with 26 resolved packages. Added/pinned pyshp 2.3.1 and pypdf 6.1.1. No frontend change; previous frontend/browser acceptance was not repeated.

Replay: `.venv/bin/python scripts/replay_audited_sources.py --boundary /private/tmp/cdt-boundary.zip --document /private/tmp/cdt-fy2025`. Requires retained audit files with exact spec hashes; reports no document text. Original retrieval dates come from specifications; successful status/media types are declared expected envelopes, not re-verified headers.

Session environment: `UV_CACHE_DIR=/private/tmp/cdt-uv-cache`, `UV_PYTHON_INSTALL_DIR=/private/tmp/cdt-python`; pinned Python 3.12.12. Temporary runtimes/audit files may disappear. `.venv` and frontend build artifacts remain ignored.

## Working tree and processes

Actual branch `main`, HEAD `97841eb` (`feat: first checkpoint`), reconciled against stale `7ad18c0` in the prior state. Starting project modification was the user's `start-session.md` wording; preserved and advanced. New adapters/contracts/tests/replay script and changed locks/docs are uncommitted. No Git commit/reset/push/publication occurred; sibling workspace content was untouched.

All workers completed; file ownership returned to supervisor. Every shell command completed. No API/browser/background process or automation was started this session. Existing temporary audit/dependency files remain disposable; no source bytes or private data were added to Git.
