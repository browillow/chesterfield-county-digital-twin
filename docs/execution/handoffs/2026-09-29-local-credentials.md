# Session handoff: safe local credential injection

Date: September 29, 2026 (America/New_York). Checkout: `main` / `df43f9e` (`ajlsdf`), sole worktree at `/Users/jordan/projects/osier/enterprise/chesterfield-county-digital-twin`. Started with the prior five uncommitted capability-gate documents; no Git mutations. The earlier [capability handoff](2026-09-29-capability-gate-continuation.md) is preserved as historical. The intervening user-requested source research read official documentation only, made no repository edits and left no running acquisition when interrupted.

## Outcome

**T006f implemented and tested.** The user explicitly lifted the no-credentials constraint and requested safe local app injection. D020 records the new scope. `cdt serve --census-key-source none|prompt|env|keychain` chooses one source, default none, with no fallback:

- `prompt`: terminal-only hidden entry; warning about echoed fallback, EOF or cancellation fails closed.
- `env`: explicit `CDT_CENSUS_API_KEY` development/launcher injection. The loader removes this variable from the serving environment for every mode before browser/helper children; only env mode uses it.
- `keychain`: explicit macOS read of generic-password service `ChesterfieldTwin`, account `census_api_key`, using fixed `/usr/bin/security` argv, no shell, captured output, five-second timeout. No create/edit/delete/enumeration operation.
- `none`: empty provider without prompting or Keychain access.

The private `SecretStr` provider masks repr/str and rejects serialization. Values must be 1–256 non-whitespace printable ASCII characters; this is input hygiene, not proof of Census validity or a claim about exact publisher key length. Failures and CLI parser errors never echo supplied values. App factory/lifespan and CLI failure/shutdown paths clear provider references. The provider is only an internal app dependency, separate from the browser launch secret; no credential/status HTTP endpoint, bootstrap capability, source request, persistence or schema change was added.

Cleanup is reference release, not guaranteed memory zeroization. Environment removal does not clear the parent shell or OS snapshots. No real secret was supplied, searched for or loaded. Native Keychain integration is tested with mocked subprocess responses, not a real Keychain item. Hidden prompting was verified with a synthetic sentinel in a real PTY. Users can run the [README command](../../../README.md#local-census-credentials) and enter their key locally.

## Source direction and next checkpoint

The preceding research and Astra review rank the exact 2023 Subject JSON API as the best match to the accepted one-original-artifact contract. The default JSON response can carry NAME plus the twelve E/M/EA/MA fields in one query. Official [2023 API documentation](https://www.census.gov/data/developers/data-sets/acs-5year.2023.html), [API concepts](https://www.census.gov/data/developers/guidance/api-user-guide.Core_Concepts.html), and [July 2026 key-related updates](https://www.census.gov/data/what-is-data-census-gov/developmental-update.html) support that direction. No API observation call was repeated. Research found no documented public alternative resolving the existing export gate; this is not proof that no other route exists or publisher denial.

**T006g is ready for implementation**, with the exact bounded acquisition/credential-redaction packet in [backlog](../backlog.md). Live acceptance needs a key supplied through the local provider and explicit acquisition invocation. No fetch service exists yet. The current command does not validate the key against Census. T006e remains the blocked alternate ZIP route; its differing-representation and multi-artifact review gates remain in force. Existing API specs/adapters and retained staging/report contracts are unchanged.

T006 remains incomplete: no real ACS response, exact live GEOID/annotation verification or real three-source pass. Any accepted API bytes must use a fresh external schema-003 root, explicit all-three-real-import validation and current revalidation. Prior roots/ledgers stay untouched; reports do not authorize sealing, activation or default reads.

## Changes and ownership

Explicit `gpt-6-astra` supervisor: design freeze and read-only security/integration review. Explicit `gpt-6.1-sol` worker: exclusive `src/chesterfield_twin/credentials.py` and `tests/test_credentials.py`. Coordinator: `cli.py`, `api/app.py`, new runtime/API credential integration tests, README, contracts, decisions, backlog, state, start-session and this handoff. Models were explicitly selected without substitution; returned agent metadata does not independently confirm the runtime model. Ownership was recorded before assignment in `/private/tmp/cdt-local-credentials-20260929/ownership.md`. Neither worker spawned agents.

All changes remain uncommitted. The prior four mutable continuity files were advanced; the prior new capability handoff was preserved. No accepted source spec, migration, adapter, dependency, OpenAPI file, frontend, earlier data root or sibling project was changed. No accounts, outreach, publication, spending or background automation.

## Verification and review

- Worker: `.venv/bin/pytest -q tests/test_credentials.py` — **26 passed**; affected Ruff passed. Mocked source-selection, Keychain timeout/error, prompt warning/EOF/cancel and redaction tests only.
- Integration: `.venv/bin/pytest -q tests/test_credentials.py tests/test_runtime_credentials.py tests/test_api_credentials.py tests/test_runtime.py tests/test_api.py` — **55 passed**, existing Starlette warning. A Ruff import-order finding was fixed before final checks.
- Full suite: `.venv/bin/pytest -q` — **243 passed**, existing Starlette `httpx` deprecation warning only. Includes unchanged OpenAPI equality, adapter/staging/report behavior, unchanged initialized store bytes through credential serve, provider cleanup on app/server/interruption failures and no credential in HTTP responses/errors/schema.
- `.venv/bin/python /private/tmp/cdt-local-credentials-20260929/check_prompt.py` — **passed** actual PTY hidden-entry check using a synthetic key; no key echoed, provider cleared, child reaped.
- `.venv/bin/ruff check src tests scripts` and `git diff --check` — **passed**. No frontend/dependency/API-schema change required a build.

Astra reviewed actual implementation/tests and found no blocking security/integration issues. Coordinator inspected the integrated code and ran the above checks. Astra also accepted final documentation/scope review; its ownership-wording correction was applied. `.venv/bin/python /private/tmp/cdt-local-credentials-20260929/check_continuity.py` passed: exactly 14 intended changed/new paths including prior work, 46 local Markdown targets, all 84 other tracked files byte-identical to HEAD, current task status and `git diff --check`. The check was rerun after final accounting edits. `cdt serve --help` exposes the four explicit sources without a key-value argument.

Sol and Astra completed implementation/security/continuity assignments and returned ownership; no active workers remain. All shell and PTY processes completed. No browser, server, download, source network job or automation remains running. Real Keychain access, Census access and real-byte validation are explicitly untested.

## Startup support follow-up

The user reported `MigrationError` from credential-enabled serve. Read-only file-presence inspection of the resolved default root (`/Users/jordan/Library/Application Support/ChesterfieldTwin`) found neither `baseline.sqlite` nor `private/strategy.sqlite`; no old database was opened or upgraded. The check fails before credential loading. Initialized that missing pair with `.venv/bin/cdt init --data-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin'`, then ran `cdt doctor` with the same explicit root. Both succeeded; doctor reports compatible/writable storage, required SQLite features and built frontend. These commands used approved filesystem escalation because the runtime directory is outside workspace write roots.

The user can rerun the original hidden-prompt serve command in their own terminal. No key was accessed, no app server was left running, and no source request/import/release was performed. This is setup assistance using accepted initialization, not a migration capability or new checkpoint. T006g remains next.
