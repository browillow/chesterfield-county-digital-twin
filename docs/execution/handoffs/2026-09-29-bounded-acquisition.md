# Session handoff: bounded exact Subject acquisition

Date: September 29, 2026 (America/New_York). Actual nested checkout: `main` / `eef7bba61ac5a3342e087794a828c124e7768102` (`feat: credential loading`), sole worktree at `/Users/jordan/projects/osier/enterprise/chesterfield-county-digital-twin`. Clean at startup; the prior credential checkpoint had been committed. Parent repository branch/HEAD are unrelated. No Git mutation; this session's changes remain uncommitted.

## Outcome and next manual action

T006g implementation and offline checks are accepted after final Astra review. No blocking security or integration findings remain. No actual key, Census API call, real ACS artifact, new staging root or current real three-source report exists from this session. Full T006 remains incomplete; T007/T008 remain pending. No sealing/activation/default reads.

The user corrected the workflow: ask for concrete manual assistance to unlock live progress rather than stopping with synthetic tests. They selected **an existing key at the hidden terminal prompt**. After safety acceptance, give this exact command for their own terminal:

```sh
cd /Users/jordan/projects/osier/enterprise/chesterfield-county-digital-twin
.venv/bin/cdt acquire-acs \
  --audit-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin-ACS-20260929' \
  --boundary /private/tmp/cdt-boundary.zip \
  --census-key-source prompt
```

Ask them to share only the sanitized terminal result, never the key. Both named original public files (`/private/tmp/cdt-boundary.zip`, `/private/tmp/cdt-fy2025`) still match accepted byte lengths/hashes. Side-effect-free acquisition preflight validated the 75 boundary GEOIDs and the above fresh destination. Recheck these prerequisites if resuming later. These local checks establish neither fresh publisher access nor current staged-artifact validity; no earlier store was opened.

On success, inspect the exact bundle through `read_acquisition`, then explicitly run:

```sh
.venv/bin/python scripts/stage_acquired_slice.py \
  --acquisition-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin-ACS-20260929' \
  --boundary /private/tmp/cdt-boundary.zip \
  --document /private/tmp/cdt-fy2025 \
  --data-dir '/Users/jordan/Library/Application Support/ChesterfieldTwin-FirstSlice-20260929'
```

This continuation validates all three unchanged contracts before exclusive fresh schema-003 initialization, selects one real import per source, persists validation and explicitly revalidates current artifacts. Record its actual run/import/report IDs and validity; none exist yet. Boundary/document envelopes are historical spec timestamps plus declared expected status/media. Preserve any created root on failure and investigate; no reuse/upgrade. If a source differs, stop for Astra review rather than change accepted semantics.

## Implemented contract and ownership

Explicitly requested `gpt-6-astra`: read-only design freeze before delegation and integrated security review. Explicitly requested `gpt-6.1-sol`: exclusive `acquisition.py`, `_acs_transfer.py`, `test_acquisition.py`, `test_acquisition_transport.py`. Coordinator: CLI, `stage_acquired_slice.py`, its tests, CLI tests, README and execution documents. Tool metadata does not independently verify actual runtime model. Neither worker spawned agents. Ownership and initial 98 tracked-file hashes are recorded under `/private/tmp/cdt-acquisition-20260929`.

[D021](../decisions.md#d021--explicit-bounded-subject-acquisition-separate-from-injection-2026-09-29) records the frozen [interfaces](../contracts.md#t006g--explicit-bounded-acquisition-and-continuation-september-29-2026): explicit acquisition with provider ownership in the caller, preflight before loading a key, strict offline bundle readback and an independent offline three-source continuation. Existing injection/adapters/staging/report implementations are reused unchanged.

The fixed one-response Subject request carries NAME and twelve E/M/EA/MA variables, exact county selectors and accepted 2019–2023/2023 pins. A stdlib isolated helper receives the key via stdin, never argv/environment/files; proxies/redirects/encoding/retries are disabled. Parent enforces 60 seconds including launch/DNS/TLS/headers/body, bounded stdout and child kill/reap. Response body cap is 20,000,000 bytes; accepted ACS adapter cap remains 1,000,000. Metadata/body/final bundle scans reject raw, URL-encoded and JSON-escaped credential echoes before disk retention. No response/error body or authenticated URL is printed.

Successful publication atomically and exclusively creates the new audit directory containing original `response.json`, safe `manifest.json` and exact ACS/boundary specs. Files and directories are synchronized. Manifest retains actual sanitized request/final URL, observed status/media/retrieval time, total elapsed time, original byte count/hash and spec/boundary/geography pins. Readback re-verifies strict keys/types, byte identity, current/retained spec equality, exact geography and unchanged adapter acceptance. Local declarations are a trust boundary, not cryptographic proof of source access. Any post-publication failure leaves the bundle preserved for inspection; CLI wording does not falsely guarantee absence.

No dependency, frontend, OpenAPI, source spec, accepted adapter, credential provider or migration change. No alternate ZIP implementation or new original/derived lineage contract. D018/D019 and T006e remain unchanged.

## Verification and limits

- Sol: `.venv/bin/pytest -q tests/test_acquisition.py tests/test_acquisition_transport.py` — **57 passed**; Ruff on its four owned files passed.
- Coordinator: `.venv/bin/pytest -q tests/test_cli_acquisition.py tests/test_acquired_slice.py` — **21 passed**; affected Ruff passed.
- Integrated: `.venv/bin/pytest -q` — **321 passed**, one existing Starlette `httpx` deprecation warning; `.venv/bin/ruff check src tests scripts` and `git diff --check` passed.
- `.venv/bin/cdt acquire-acs --help` exposes only explicit audit/boundary paths and four credential sources. No key-value, selector, endpoint or limit override exists.
- Local named-file SHA-256/length checks and real boundary preflight passed without a key/network/write. Accepted source identities remain unchanged.

Tests cover exact request selectors, unchanged raw retention, strict manifest/spec/geography readback, unknown annotations/stricter adapter cap, no-key/no-request, fresh destinations, framing/size/media/encoding/status failures, encoded/escaped echoes and provider cleanup. Actual subprocess tests execute the helper entry point with offline substituted transfer stalls/drip, verify timeout/interruption kill/reap, bounded stdout and suppressed secret-bearing errors. DNS/TLS/HTTP envelopes are mocked; no actual live socket was exercised. The staging helper's success-path tests mock input acceptance/staging to verify explicit selection and two validation calls; existing real staging/report services retain their independently tested behavior. Those mocks are not real evidence.

Standard HTTP framing treats Content-Length as the body boundary; unread bytes beyond an incorrectly small declared length cannot be certified as part of the response body. Truncation, conflicting/duplicate lengths and observed body limits are checked. No wire-level packet capture is claimed. Reference cleanup is not memory zeroization. Real Keychain, key validity, live source semantics and the three-source gate remain unverified.

## Review, preservation and completion

Astra approved the contract before Sol delegation, reviewed staging preflight/explicit selections/current validation, and requested honest post-publication failure wording, which was corrected. Coordinator reviewed code and required full-bundle echo checks, parent-total timing, durable directory publication and cancellation cleanup before integrated tests. Astra’s final read-only review accepted the implementation and the manual command, with no blocking findings. Astra inspected code/tests but did not rerun the coordinator’s 321-test suite. Both Astra and Sol completed their assignments and returned ownership; no active agents or shell/check processes remain.

No browser, server, real acquisition process or automation was started. All synthetic helper children are killed/reaped or complete within tests. Sol returned ownership after its checks. Earlier roots/default runtime remain unopened, with no key discovery, accounts, outreach, publication or spending. The next action belongs to the user in their own terminal, followed by coordinator inspection and explicit real staging/current revalidation; do not create another audit-only checkpoint.

Final preservation/link check: all **91 other tracked files** remain byte-identical to the starting commit; exactly seven intended tracked files changed, with eight new session files. All **43 local Markdown links** in changed/new execution prose resolve; final `git diff --check` passed. Branch/HEAD/worktree remain unchanged. No source specs, migrations, accepted adapters/provider, lockfiles or sibling files changed.
