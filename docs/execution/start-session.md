# Start the next implementation session

Select **GPT-6 Astra** and use the existing `chesterfield-county-digital-twin` checkout. Preserve and reconcile uncommitted work before changing worktrees. Markdown does not switch or verify the model. Root `AGENTS.md` supplies standing instructions.

Paste this prompt:

```text
Implement the next ready checkpoint for Chesterfield County Digital Twin.

Read AGENTS.md, docs/execution/state.md, workflow.md, the latest linked
handoff, relevant backlog/contracts, decisions D017–D020 and source_specs/.
Reconcile actual branch/HEAD/worktree and preserve uncommitted work.
Use GPT-6 Astra as supervisor; explicitly request gpt-6.1-sol for bounded
workers where useful, with focused context, exclusive ownership, concrete
deliverables and checks. Never silently substitute models.

The local skeleton, T006a adapters, T006b staging, T007a reports and T006f
local credential injection are accepted. Do not rebuild them. The user
explicitly lifted the no-credentials constraint and authorized safe local
injection. T006f supports serve --census-key-source none|prompt|env|keychain,
default none, no fallback, backend-only redaction and lifecycle cleanup.
No real key or live API access has been verified. Never request a secret
in chat, scan for credentials, create accounts, or put keys in argv/files.

T006g is ready for implementation: an explicit bounded acquisition service
and entry point using the accepted 2023 ACS 5-Year Subject JSON contract
and T006f provider. Freeze the acquisition/command contract with Astra
before delegation. Pin 2019–2023/2023, NAME plus E/M/EA/MA for the existing
three measures in one response, and Chesterfield County's 75 exact tracts.
Enforce 20 MB and 60-second total transfer bounds. Retain original bytes
and actual sanitized request/final URL, status, media, time, length and hash.
Prevent credential leakage via logs/errors/redirects/proxies or echoed
response content. Do not sanitize changed bytes and label them raw.
Use synthetic transport tests before live invocation. Local credential
injection alone authorizes no automatic network call at startup.

After an explicitly invoked live acquisition with a locally supplied key,
only bytes matching the unchanged accepted API contract may use a fresh
external schema-003 root. Preserve earlier roots; no upgrade path exists.
Validate all three explicitly selected real imports and explicitly revalidate
current artifacts. Historical report readback is not current verification.
Reports authorize no sealing/activation/default reads.

T006e remains a blocked alternative ZIP route: supported browser downloads
lack bounds and actual response provenance. Prior UI access succeeded;
this is not publisher denial. Do not repeat unchanged API/FTP audits or
create audit-only tickets. If a materially changed supported export route
is needed, follow T006e: clean geography selection, at most one official
S1901/S1701 ZIP each, 100 MB/32-member expansion caps, exact bytes and
semantics. Stop for Astra source/spec/locator/adapter review before any
differing-representation implementation or ingestion. No replacement
multi-artifact original/derived lineage/readback contract is approved.
No fixtures, Detailed Table substitutions, invented null annotations,
unpublished endpoints or CSV relabeled as API JSON.

Resolve routine reversible choices autonomously. Preserve local runtime,
private-data separation, release pinning and provenance. Run proportionate
checks and review integrated work. Before finishing update state/backlog,
material decisions, handoff and this starter prompt; account for workers
and processes and distinguish implemented/tested/proposed capabilities.
No outreach, publication, spending or background automation.
```

Current checkpoint: [Local credential injection](handoffs/2026-09-29-local-credentials.md). Follow later state if advanced. The [capability gate continuation](handoffs/2026-09-29-capability-gate-continuation.md) records the earlier credential-free blocker; D020 supersedes its credential restriction only.

Startup support note: the default local store pair was initialized and passed `cdt doctor` after a missing-database error. This is a fresh schema-003 store, not an upgraded prior root; no credentials or observations were acquired. Recheck current state before running commands.
