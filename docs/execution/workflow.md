# Astra/Sol execution workflow

## Start with a concrete outcome

Use one supervisor session per integration checkpoint, such as “local skeleton runs and the baseline/private boundary is verified.” Do not start a fresh architecture exercise or delegate the whole MVP. Inspect current work before assigning tasks; one active supervisor owns the integration branch/checkout at a time. Separate concurrent supervisor sessions need explicit separate checkouts and an integration owner.

Read `AGENTS.md`, current state, and relevant backlog entries. Read the full architecture once when starting implementation, then route workers to specific sections. The state file is an index, not authority over observed repository facts.

## Delegate deliberately

- Supervisor: requested model `gpt-6-astra`. Workers: requested model `gpt-6.1-sol`. These names express the user's selection, not an automatic model switch performed by Markdown.
- Explicitly pass the worker model in the available delegation tool and check returned metadata where available. Do not infer success from a role label. If the tool does not expose confirmation, report the requested model without claiming it was independently verified.
- In the current collaboration tool, full-history forks cannot override the parent model. Use a fresh-context worker (`fork_turns: "none"`) with an explicit model and complete assignment packet; consult the actual tool schema in each new environment.
- Prefer one or two useful workers initially. Add another only for independent work with clear ownership and available capacity. Keep dependent implementation sequential.
- Give each worker only the mission summary, relevant decisions/contracts, exact files or sections, acceptance checks, and return format. Avoid sending the entire family framework or chat history.
- Reuse a worker for closely related follow-up corrections when helpful. Do not recreate workers merely to ask for status. Use completion notifications/waits and keep the supervisor occupied with integration, shared contracts, or meaningful review.

Codex documents project-scoped instruction discovery in [AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md). Its [subagent guidance](https://learn.chatgpt.com/docs/agent-configuration/subagents) describes inherited model settings, focused worker context, and the extra coordination needed for concurrent edits. The model IDs also appear in official [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model) and the [GPT-6.1 Sol model page](https://developers.openai.com/api/docs/models). Actual availability and tool limits come from the current session.

## Make parallel writes safe

Before launch, record each assignment's owner and allowed paths in current state or its session handoff draft. Reserve shared files with one owner. Package manifests/locks, API types, schemas, migrations, and root configuration are frequent collision points; serialize their edits. A worker may propose a shared-contract change but must not silently implement it across another worker's files.

For a shared checkout, workers report changes already present on disk; do not attempt to cherry-pick nonexistent commits. If using isolated worktrees, record base commit, branch, ownership, and integration mechanism explicitly. Do not depend on a worktree containing uncommitted planning artifacts from the original checkout.

Freeze only the interfaces needed for the current wave. The [contract checklist](contracts.md) defines initial agreements; Pydantic/OpenAPI and migration files become the executable authorities once present. The supervisor updates dependent assignments whenever a contract changes.

## Review and acceptance

A worker returns paths, behavior changed, tests/checks with outcomes, unresolved issues, and contract deviations. The supervisor inspects the diff and exercises the combined behavior against the task's criteria. Use a separate read-only review worker for consequential provenance, privacy, release, or recovery changes when it adds value; routine changes do not need a standing review agent.

Mark backlog work `done` only after integration acceptance. Record `review` for work awaiting integration, `blocked` with the exact dependency for a real blocker, and `planned` for future items lacking readiness. Do not equate a passing mock-based unit test with working live source access or a completed end-to-end slice.

Run targeted checks first and an appropriate integration check after combining changes. Re-run checks affected by follow-up edits; avoid rerunning unrelated suites. Preserve failing output in a concise handoff instead of dumping full logs into every worker context.

## Finish without losing state

Use the [handoff template](templates.md). Update state, backlog, and decisions that materially changed. Record branch/HEAD, uncommitted changes, accepted task IDs, exact checks, evidence added, unresolved work, and next ready tasks. Shut down or explicitly transfer active workers and processes. Never leave “in progress” with no owner or next action.

These artifacts do not install Codex configuration, create sessions, or select the supervisor model in the app. Select Astra when creating the next session and use the [starter prompt](start-session.md).
