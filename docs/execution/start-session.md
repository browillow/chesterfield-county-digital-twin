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

The local skeleton is accepted. Begin T006a: own and settle typed
candidate/provenance contracts, then implement bounded source adapters
and validation tests. Delegate independent adapter work only after its
interfaces are fixed. Use docs/source-audit.md and source_specs/.

Progress boundary/document normalization and explicitly synthetic ACS
validation independently of the live ACS access blocker. Preserve source
hashes, exact locators, units/universes, periods, geographic vintage,
uncertainty and annotations. Full T006 requires authorized observation
bytes or a verified official download route; fixtures alone do not satisfy
it. Do not create accounts or request credentials in chat. Follow later
state if T006a has already progressed. Do not redo accepted skeleton work
or completed planning.

Resolve routine reversible choices autonomously. Preserve existing work,
the local runtime design, provenance, release pinning, and the private-data
boundary. Report material blockers precisely while progressing independent
work. Run proportionate checks and review the integrated result yourself.

Before finishing, update state and backlog, record material decisions,
write a concise session handoff in the start-session.md file, account for active workers/processes,
and identify the next ready work. Distinguish implemented, tested, and
still proposed capabilities. Do not publish, contact people, or make
spending commitments as part of this task.
```

Current checkpoint reference: [local-skeleton handoff](handoffs/2026-09-27-local-skeleton.md). The state file takes precedence if work has progressed since this prompt was updated. For a narrower session, replace the checkpoint paragraphs with one specific outcome and stopping condition. Markdown instructions cannot switch the current session's model or guarantee worker availability; use the actual app/tool settings. No project/global Codex configuration has been installed by this execution kit.
