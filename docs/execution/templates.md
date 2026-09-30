# Assignment and handoff templates

Copy only the template needed. Keep packets concise and link exact code/sections. These are not forms that require user approval.

## Supervisor to Sol assignment

```text
Task ID and outcome:
Research capability enabled or concrete failure prevented:
Smallest useful deliverable and stopping condition:
Requested model: gpt-6.1-sol
Why this can run independently:
Repository/checkout and shared-filesystem status:
Current baseline/branch and relevant existing changes:
Read: AGENTS.md, plus these exact files/sections:
Accepted contracts and relevant decisions:
Allowed write paths (exclusive ownership):
Read-only/shared paths and their owner:
Dependencies already satisfied:
Deliverables and observable acceptance criteria:
Checks to run (existing commands, or checks to implement):
Out of scope:
Stop/report if: contract conflict, needed ownership change, actual access blocker.
Return: changed paths, behavior, checks/results, limitations, integration needs.
Do not modify another assignment's files or spawn further agents.
```

## Sol completion report

```text
Task ID:
Outcome: ready for review / blocked / partial
Requested model; actual model if exposed by runtime:
Changed paths:
Behavior or evidence added:
Checks: exact commands, result, relevant fixture/live-data distinction
Contract changes requested or made with supervisor coordination:
Known failures/limitations:
Integration notes and remaining work:
```

## Supervisor session handoff

Store under `docs/execution/handoffs/<date>-<short-topic>.md`, with a unique suffix if needed. Link the latest handoff from state. Workers return messages; the supervisor writes the durable integrated handoff.

```text
# Session handoff: <outcome>
Date / session identifier:
Supervisor and worker models requested; confirmed if exposed:
Checkout / branch / HEAD:
Starting state and session objective:

Accepted task IDs and resulting behavior:
Artifacts changed, including uncommitted/untracked work:
Evidence added: sources, periods, retrieval status, limitations:
Verification: exact commands, pass/fail, what was not checked:
Material decisions: IDs/links, rationale, affected contracts:
Open issues: failure, impact, owner/next action:
Active workers/processes: stopped or explicit ownership transfer:
Next ready task(s) and minimal startup instructions:
```

Do not repeat the complete architecture, full source documents, secrets, or long successful test logs. Record enough evidence to resume and reproduce checks.
