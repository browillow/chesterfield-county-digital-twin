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

The local skeleton, T006a adapters and T006b retained candidate staging
are accepted. Begin T007a: persisted candidate-set validation reports over
explicitly selected staged imports. Read its concrete backlog packet,
current contracts, D015/D016, docs/source-audit.md and source_specs/.
Supervisor owns shared report/storage interfaces, dependencies and any
migration decision. Delegate only after those interfaces settle.

Use verified T006b readback and accepted three-source validation semantics.
Pin input/import/version identities and source/spec/transform lineage in
reports. Keep real and synthetic selections isolated. Audited boundary
and document inputs alone must report missing ACS, never pass a real-slice
gate. T007a adds no release sealing, activation or default baseline reads.
Do not modify existing migration checksums or silently upgrade stores;
use a fresh external temporary root and preserve incompatible older roots.
Full T006 requires authorized observation bytes or a verified official
download route and real three-source validation; fixtures alone do not
satisfy it. Do not create accounts or request credentials in chat.
Follow later state if T007a has progressed. Do not redo accepted skeleton,
adapters, staging, or completed planning.

Resolve routine reversible choices autonomously. Preserve existing work,
the local runtime design, provenance, release pinning, and the private-data
boundary. Report material blockers precisely while progressing independent
work. Run proportionate checks and review the integrated result yourself.

Before finishing, update state and backlog, record material decisions,
and update the session start prompt in the start-session.md file, account for active workers/processes,
and identify the next ready work. Distinguish implemented, tested, and
still proposed capabilities. Do not publish, contact people, or make
spending commitments as part of this task.
```

Current checkpoint reference: [retained-staging handoff](handoffs/2026-09-29-retained-staging.md). The state file takes precedence if work has progressed since this prompt was updated. For a narrower session, replace the checkpoint paragraphs with one specific outcome and stopping condition. Markdown cannot switch or verify the session model; use actual app/tool settings. No project/global Codex configuration has been installed by this execution kit.
