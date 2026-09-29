# Project working instructions

## Purpose and startup

Build a private, locally operated Chesterfield County research tool that improves strategic decisions through inspectable evidence. Preserve the distinction between observations, calculations, inferences, hypotheses, and scenarios.

At session start, read [current state](docs/execution/state.md), then the relevant items in [backlog](docs/execution/backlog.md). The supervisor also reads [workflow](docs/execution/workflow.md). Read only the architecture sections and source files needed for the selected work. The existing MVP and architecture define intended behavior; state and repository inspection establish what actually works.

Check the current directory, branch, working tree, and available commands before editing. Preserve existing work. Architecture command examples are not proof those commands exist. If plans and implementation conflict, investigate and record the resolution; do not silently rewrite either.

## Supervisor and workers

The requested workflow uses **GPT-6 Astra (`gpt-6-astra`) as supervisor** and **GPT-5.6 Sol (`gpt-5.6-sol`) as subagents**. Use subagents for bounded independent work when delegation helps. Request the worker model explicitly; do not silently substitute GPT-6 Sol or inherit the supervisor model. If the requested model is unavailable, report it and continue independent supervisor work while resolving the delegation choice.

The supervisor selects scope, settles shared contracts, assigns file ownership, integrates, verifies acceptance, and updates project state. Each worker receives the [assignment template](docs/execution/templates.md) with exact deliverables, dependencies, allowed paths, checks, and stop conditions. Workers do not spawn additional agents unless assigned that responsibility. Use only available concurrency; do not fill slots without useful independent work.

Assume shared filesystem state unless the runtime says otherwise. One writer owns a file at a time. The supervisor owns dependency manifests/locks, shared API/domain contracts, migration ordering, and execution-state documents unless explicitly assigning them to one worker. Workers report out-of-scope needs rather than editing another assignment's files. Only the supervisor coordinates Git operations; do not revert another agent's changes.

## Implementation constraints

- Follow the local architecture: Python/FastAPI, SQLite, React, local artifacts, and bounded on-demand jobs. No new infrastructure without a demonstrated requirement.
- Keep private strategy data outside the repository and separate from baseline stores, indexes, and exports.
- Preserve provenance, units, geography/vintage, uncertainty, suppression, and reproducible derivations. Unknown is not zero. Generated UI examples are not source data.
- All baseline queries pin a release. Sealed memberships and referenced versions are immutable. Shared contracts change through supervisor coordination.
- Keep source research within public-data scope. No outreach, publication, spending commitments, or background automation is implied by implementation work.
- Follow existing session authorization. Resolve routine reversible implementation choices without adding approval steps. Escalate only material unresolved scope/personal constraints or an actual permission boundary.

## Completion and continuity

Run checks appropriate to changed behavior; avoid duplicate broad test runs without a reason. A worker's “done” means ready for supervisor review, not accepted. The supervisor inspects the integrated result and records exact commands, outcomes, limitations, and remaining work.

Before ending a substantive session, update current state and backlog and write a concise handoff using the template. Stop or account for active workers. Record uncommitted artifacts and the next ready task. Do not claim code, source access, tests, or acceptance gates are complete without evidence.
