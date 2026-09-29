# Start the next implementation session

Create the session in the `chesterfield-county-digital-twin` repository and select **GPT-6 Astra** as its model. Use the existing checkout unless you deliberately transfer its uncommitted implementation and execution files. Verify those files are present before using a new worktree. Root `AGENTS.md` supplies standing project instructions. It will not necessarily be discovered from the parent `enterprise` directory.

Paste this prompt:

```text
Implement the next ready checkpoint for Chesterfield County Digital Twin.

Read AGENTS.md, docs/execution/state.md, docs/execution/workflow.md,
the latest handoff linked from state, and the relevant backlog/contracts.
Reconcile them with the actual checkout.
Use GPT-6 Astra as supervisor and explicitly request gpt-6.1-sol for
bounded subagent work where delegation helps. Do not silently substitute
another worker model. Give each worker focused context, exclusive file
ownership, concrete deliverables, and acceptance checks.

The local skeleton and T006a are accepted. Begin T006b: implement retained
public artifacts and unpublished candidate staging from the accepted typed
adapters. Read the concrete T006b packet in backlog, current contracts,
docs/source-audit.md and source_specs/. Supervisor owns shared storage
interfaces, dependencies and any migration decision. Delegate independent
work only after those interfaces settle.

Progress boundary/document staging and explicitly isolated synthetic ACS
validation independently of the live ACS access blocker. Preserve source
and specification hashes, transform identity, exact locators, units/universes,
periods, geographic vintage, uncertainty, annotations and retention policies.
Do not modify existing migration checksums or silently upgrade stores.
Full T006 requires authorized observation bytes or a verified official
download route; fixtures alone do not satisfy it. Do not create accounts or
request credentials in chat. Follow later state if T006b has progressed.
Do not redo accepted skeleton/adapter work or completed planning.

Resolve routine reversible choices autonomously. Preserve existing work,
the local runtime design, provenance, release pinning, and the private-data
boundary. Report material blockers precisely while progressing independent
work. Run proportionate checks and review the integrated result yourself.

Before finishing, update state and backlog, record material decisions,
and update the session handoff in the start-session.md file, account for active workers/processes,
and identify the next ready work. Distinguish implemented, tested, and
still proposed capabilities. Do not publish, contact people, or make
spending commitments as part of this task.
```

Current checkpoint reference: [typed-source-adapter handoff](handoffs/2026-09-29-source-adapters.md). The state file takes precedence if work has progressed since this prompt was updated. For a narrower session, replace the checkpoint paragraphs with one specific outcome and stopping condition. Markdown cannot switch or verify the session model; use actual app/tool settings. No project/global Codex configuration has been installed by this execution kit.

## Session handoff — September 29, 2026

T006a is implemented, reviewed and accepted: typed provenance/candidates, three bounded normalization adapters, synthetic ACS failure tests and cross-source validation. Full Python suite: **132 passed**; Ruff and locked offline sync pass. Supervisor independently replayed the hash-pinned boundary ZIP (75 county candidates) and PDF (3 exact page excerpts). No live ACS observations, candidate persistence or release service was added.

Checkout `main` / `97841eb`; session changes remain uncommitted, including preserved prior starter-prompt wording. All three explicitly requested `gpt-6.1-sol` workers completed, and no server/background process was started. Current next ready work is **T006b retained public artifacts and candidate staging**, as detailed in backlog. Full T006 remains blocked on authorized ACS observation bytes or a verified official alternative. See the linked handoff for exact checks, evidence hashes, limitations and ownership.
