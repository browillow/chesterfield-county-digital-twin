# Chesterfield County Digital Twin

A private, locally operated county evidence tool. The local skeleton runs: Python/FastAPI serves a React shell, with separate public-baseline and private SQLite stores outside the checkout. The first real three-source candidate slice is retained and currently validated: 225 ACS observations, 75 tract boundaries and 3 document excerpts. No sealed or active release exists; the UI remains the empty shell. The source audit and remaining work are recorded in [current state](docs/execution/state.md).

## Setup and daily use

Supported and verified on ARM64 macOS with **Python 3.12.12**, **Node 24.21.0 LTS**, and uv 0.11.14. Use your Node version manager to select the version in `.node-version`; do not rely on a different globally installed Node. Python is selected by `.python-version`; dependency resolutions are pinned in `uv.lock` and `frontend/package-lock.json`.

From this checkout:

```sh
uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
uv run --no-sync cdt init
uv run --no-sync cdt doctor
uv run --no-sync cdt serve --open
```

The default root is `~/Library/Application Support/ChesterfieldTwin`, outside Git. To use another **local, non-synchronized** directory, set `CDT_DATA_DIR` or pass `--data-dir /absolute/path` after `init`, `doctor`, or `serve`. The checkout and recognized cloud-sync locations are rejected; arbitrary network mounts cannot be identified from pathnames. No test uses your default research directory.

The server binds only `127.0.0.1:8765` (or `--port`). Stop with Ctrl-C. Without `--open`, the terminal displays a one-use session URL; open that URL in the browser. Its fragment is exchanged for an HttpOnly session cookie and immediately removed from history. A restart invalidates prior sessions. Node and network access are not needed for daily serving after installation/build. No background service is installed.

A missing UI build or incompatible/uninitialized stores fail closed. This checkpoint supports new initialization and repeat compatibility checks, **not schema upgrades or backup/restore**. Preserve an incompatible existing data directory; do not delete it to make initialization pass. The application currently runs from its source checkout; a standalone distributable bundle is not implemented.

## Local Census credentials

Choose a credential source explicitly when starting the app. The default is `none`; startup never searches for credentials or falls back to another source. For a one-session key, run this in your own interactive terminal after setup:

```sh
uv run --no-sync cdt serve --census-key-source prompt --open
```

Enter the key at the hidden `Census API key:` prompt. It is not a command argument and is not saved by the app. Noninteractive input or an unavailable hidden-input facility fails closed. Do not paste keys into chat, command arguments, source files, `.env` files, or research documents.

For a key already provisioned in **macOS Keychain**, use:

```sh
uv run --no-sync cdt serve --census-key-source keychain --open
```

The provider reads one generic-password item with service **`ChesterfieldTwin`** and account **`census_api_key`** using the system Keychain utility. Provision/manage that item separately in Keychain Access or your trusted credential-management workflow. The app does not create, edit, enumerate or delete Keychain items. Missing/locked/denied access or a five-second timeout fails without fallback. This integration is covered with mocked system responses; access to a real Keychain item has not been exercised.

For development or a trusted launcher, inject **`CDT_CENSUS_API_KEY`** into the process environment and select `--census-key-source env`. No `.env` file is loaded. The serving process removes this variable before launching the browser or Keychain helper, even if another source or `none` is selected. This does not remove the value from the parent shell or erase OS/process-memory snapshots; hidden prompting or Keychain avoids the environment fallback. No raw-key command-line option exists, and parser errors do not echo supplied arguments.

The key is held in a redacted backend-only provider, separate from the browser session secret. It is absent from HTTP responses/OpenAPI, bootstrap capabilities, databases, artifacts and reports. Shutdown/startup failure releases the provider's reference; memory zeroization is not guaranteed. Restart or select `none` to run without a key. `init` and `doctor` do not acquire credentials.

Startup validates only a bounded nonempty printable credential string, not whether Census accepts it. It makes no Census request and creates no import or release. Acquisition requires the separate explicit command below.

## Explicit Census acquisition

After offline safety tests pass, run this command in your own interactive terminal and enter your existing key at the hidden prompt. Never send the key in chat. Use a **new external audit directory** whose parent exists, and the unchanged, previously audited boundary ZIP:

```sh
uv run --no-sync cdt acquire-acs \
  --audit-dir '/absolute/path/to/new-acs-audit' \
  --boundary '/absolute/path/to/audited-boundary.zip' \
  --census-key-source prompt
```

`none` (default), `env` and `keychain` use the same explicit provider rules as `serve`. Missing credentials cause no request. Boundary and destination checks precede credential loading. This command sends one request for NAME and E/M/EA/MA for the three accepted 2019–2023 measures from the 2023 ACS 5-Year Subject endpoint. It enforces a 20,000,000-byte transfer cap and 60-second total deadline, rejects redirects/proxies/compressed responses and validates the exact 75 tracts against the pinned boundary. The unchanged ACS adapter also imposes its stricter 1,000,000-byte acceptance limit. No limits, endpoint or release selectors can be overridden from the CLI.

Success publishes four files: exact original `response.json`, `manifest.json`, `acs_spec.toml` and `boundary_spec.toml`. The manifest records sanitized actual request/final URLs, observed status/media/time, total elapsed time, exact length/hash and source/geography pins. Unsafe credential echoes or differing representations are rejected before retention; bytes are never rewritten and labeled raw. The audit bundle creates no database, import or release. Output contains only safe success/count/hash information suitable for sharing back. Failures use bounded messages and never print response bodies, authenticated URLs or transport errors. Cancellation terminates the transfer helper; there are no retries or background jobs.

**Live acquisition verified September 29, 2026:** the user ran the hidden-prompt command, retaining an 11,368-byte HTTP 200 JSON response matching the unchanged contract. All 75 exact tracts and 225 observations passed, followed by real three-source staging and current revalidation. See the [real-slice handoff](docs/execution/handoffs/2026-09-29-real-slice.md) for immutable identities and retained paths; do not repeat acquisition just to resume work. For any future explicit local-key run, share only its sanitized result if help is needed. A different response representation still requires source/spec/adapter review.

After a successful acquisition, explicitly stage that bundle with both unchanged audited sources into another **new external root**:

```sh
uv run --no-sync python scripts/stage_acquired_slice.py \
  --acquisition-dir '/absolute/path/to/new-acs-audit' \
  --boundary '/absolute/path/to/audited-boundary.zip' \
  --document '/absolute/path/to/audited-budget.pdf' \
  --data-dir '/absolute/path/to/new-three-source-root'
```

The helper verifies the bundle and all three accepted source contracts before initializing schema 003. It explicitly selects one import per source, persists validation, and invokes validation again to verify current retained artifacts. Output includes the run, three import IDs, both report IDs and actual validity. A later current check uses those exact IDs with `scripts/validate_audited_sources.py`; reading a historical report is insufficient. Boundary/document envelopes remain historical offline replay, not newly observed HTTP responses. Local manifest declarations are not cryptographic proof of acquisition origin. Preserve any partial root on failure; existing roots are never upgraded or reused. Neither command seals, activates, publishes or enables default baseline reads.

## Verification

```sh
uv run --no-sync pytest -q
uv run --no-sync ruff check src tests scripts
npm --prefix frontend run test
npm --prefix frontend run build
uv run --no-sync python scripts/export_openapi.py
npm --prefix frontend run types
# Actual temporary-root server and browser test; requires installed Google Chrome.
uv run --no-sync python scripts/smoke.py
```

The smoke test verifies a loopback listener, session/cookie reload, empty state, keyboard navigation, narrow viewport, local-only page requests, offline navigation, maintenance exclusion, and graceful shutdown. It removes its temporary data root and server, and writes a [review screenshot](docs/execution/screenshots/2026-09-27-empty-overview.png).

Python tests cover observed zero versus suppression, sealed-membership guards, content-addressed artifacts, migration/lock failures, and a private sentinel excluded from the baseline repository export. This export helper is not yet a user export feature or a complete provenance export. The generated API contract is checked against the running app. One dependency warning currently notes Starlette's future move from `httpx` to `httpx2`; tests pass.

## Source access and next work

The [source audit](docs/source-audit.md) selects 2019–2023 ACS median household income, poverty rate, and household count, plus matching 2023 boundaries and a county Social Services budget excerpt. Metadata, boundaries, and the document were retrieved and checked. The historical keyless observation query redirected to Census's missing-key page. Live ACS ingestion requires an explicit local-key acquisition or a separately verified official download route. No credentials or downloaded source documents are in Git.

Retained staging accepts explicit public bytes through the three typed adapters, preserves exact source/specification objects and retrieval events, and verifies complete candidate readback. Real and synthetic runs are explicitly separate. Offline audit replay is available when the retained audit files exist:

```sh
uv run --no-sync python scripts/stage_audited_sources.py --boundary /path/to/audited-boundary.zip --document /path/to/audited-budget.pdf --data-dir /path/to/new-external-test-root
```

This command retains local evidence and repeats each import to verify reuse; it does not fetch, activate or export. It reports counts/hashes only. Retrieval times come from pinned specifications; successful response headers are declared, not freshly verified. The county PDF's redistribution remains unconfirmed. Baseline migration 003 is required: existing 001/002 stores are rejected without upgrading; preserve them and choose a separate new root.

The explicit bounded ACS command and first real three-source ingestion are accepted. Broader job orchestration, validated release build/activation, map/table/evidence inspection, private brief editing and recovery remain future work. Validation reports require an explicit staging run and explicit import IDs; they never choose latest evidence. Complete synthetic selections pass only as synthetic. Historical real boundary/document selections still report missing ACS; the new explicit three-source selection passes. Reports pin inputs and validator identity, remain immutable, and describe evidence verification at creation time; reading an old report does not recheck current object availability. Revalidate explicitly after evidence changes. No report authorizes sealing or activation. Next is the supervised release-closure contract checkpoint; no active release or default baseline reads exist.

For implementation sessions, read [AGENTS.md](AGENTS.md), [state](docs/execution/state.md), [backlog](docs/execution/backlog.md), and [workflow](docs/execution/workflow.md). See the [MVP plan](docs/mvp-plan.md), [technical architecture](docs/technical-architecture.md), and [illustrative UI concepts](docs/ui-concepts/README.md) for intended later behavior.

Report an explicit selection in an initialized current-schema external root:

```sh
uv run --no-sync python scripts/validate_audited_sources.py --data-dir /path/to/test-root --run-id RUN_ID --import-id BOUNDARY_IMPORT_ID --import-id DOCUMENT_IMPORT_ID
```

This command persists an inspectable failure report for missing ACS. See `--help` for exit statuses. It does not initialize or upgrade stores.
