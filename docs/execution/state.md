# Current project state

Last updated: September 27, 2026 UTC — local skeleton accepted.  
Implementation stage: **Architecture stage A implemented and tested.** First auditable source slice remains incomplete.  
Active supervisor/assignments: None remaining; Astra integrated the work and all three requested Sol workers have finished.  
Latest handoff: [Local skeleton](handoffs/2026-09-27-local-skeleton.md).

## Implemented and verified

- **T001:** Python 3.12.12 / Node 24.21.0 LTS, uv/npm locks, package/CLI, executable Pydantic contracts and generated OpenAPI/TypeScript.
- **T003:** External local data root, separate baseline/private databases, secure layout, initial transactional migrations/checksummed ledgers, maintenance lock, immutable artifacts/version/membership guards. Explicit sealed-release internal export excludes a private sentinel in tests.
- **T004:** Foreground loopback-only API and compiled local assets, one-use fragment launch/session cookie, Host/Origin/CSRF checks, generic error responses, graceful shutdown. No real data endpoints or background jobs.
- **T005:** Four navigation destinations, honest empty/loading/error states, pinned bootstrap state, keyboard and narrow-screen checks. [Reviewed screenshot](screenshots/2026-09-27-empty-overview.png).
- **T002 audit accepted with source blocker:** Three selected ACS metrics and verified metadata; matching boundary ZIP (75 Chesterfield tracts); county document/page locators verified. See [source audit](../source-audit.md) and `source_specs/`.

No real county observations, source artifacts, active release, maps, ingestion job, private brief UI, search, user export, or backup/restore have been implemented. Generic storage guards and synthetic fixtures do not establish the release workflow. Existing schema upgrades intentionally fail closed until paired recovery is available. The runnable product currently requires this source checkout.

## Next ready work and blockers

- **T006a ready:** settle typed candidate/provenance contracts, then implement bounded adapter normalization and synthetic failure tests plus independently retrievable boundary/document work. Assignment/acceptance packet is in [backlog](backlog.md). Supervisor owns shared contracts and migrations; delegate adapters only after those interfaces settle.
- **Full T006 blocked:** corrected ACS three-measure observation request returned HTTP 302 to Census `missing_key.html` with `X-DataWebAPI-KeyError: 1`. Requires an authorized API key or separately verified official download route. No credential was created or searched for. Do not mistake metadata access for observation access.
- T007 validated sealing/explicit activation and T008 map/table/evidence integration remain pending. Preserve units/universe, E/M/EA/MA annotations and uncertainty, geography/vintage, and document's Chesterfield/Colonial Heights scope.
- No personal budget/capacity/backup choice blocks the ready adapter work. Private data stays outside Git; no real research directory was initialized during testing.

## Commands and checks

See [README](../../README.md) for normal setup and daily commands. From this checkout: `uv sync --locked`, `npm --prefix frontend ci`, `npm --prefix frontend run build`; then `uv run --no-sync cdt init`, `uv run --no-sync cdt serve --open`. Use `--data-dir` after the command or `CDT_DATA_DIR` for an external test root.

Verified on ARM64 macOS: Python tests (27 cases), frontend tests (6), production build, clean npm lock installation, uv locked sync, Ruff, generated-OpenAPI drift check, and real server/Chrome smoke (`scripts/smoke.py`). Smoke checked listener address, empty UI, session/reload, keyboard, narrow viewport, local-only requests, offline navigation, maintenance exclusion, and shutdown. A Starlette test-client deprecation warning remains; no test failure remains. Exact commands/outcomes and initial corrected failures are in the handoff.

Session tooling used `UV_CACHE_DIR=/private/tmp/cdt-uv-cache`, `UV_PYTHON_INSTALL_DIR=/private/tmp/cdt-python`, and Node at `/private/tmp/cdt-node/node-v24.21.0-darwin-arm64/bin`. These temporary caches/runtimes may disappear; recreate with the pinned setup rather than depending on them. `.venv` and `frontend/dist` are ignored local artifacts.

## Working tree and processes

Branch `main`, HEAD `7ad18c0`; no commits, resets, pushes or publication. Existing planning/README work was preserved. Implementation, audit, screenshot, and execution records are uncommitted/untracked; transfer them deliberately before changing checkouts. All worker turns and temporary server/browser processes completed; smoke data root removed. Only disposable runtime/dependency caches and audit samples remain under temporary directories. No background automation was created.
