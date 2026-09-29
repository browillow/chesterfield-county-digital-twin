# Decision register

These are current working design choices from the existing artifacts and the user's workflow preference. They are not claims that implementation or validation has occurred. Amend with rationale and a superseding decision; avoid reopening them every session without new evidence.

| ID | Decision | Basis / revisit trigger |
| --- | --- | --- |
| D001 | Run locally on one MacBook using native processes | Explicit user direction; revisit for actual remote/multiuser need |
| D002 | Python/FastAPI + compiled React UI, SQLite, local evidence files | Architecture sections 1–5; validate first slice before broadening |
| D003 | DuckDB only for bounded bulk transformation; geographic preprocessing initially | Architecture sections 4, 10, 12; add complexity only after measured need |
| D004 | Baseline and private strategy use separate stores and export paths | Mission and architecture sections 5, 11; maintain through all iterations |
| D005 | Immutable evidence versions and sealed, explicitly activated releases | Architecture sections 6–9; every baseline view pins a release |
| D006 | Astra supervisor, GPT-5.6 Sol workers requested explicitly | User workflow preference; exact IDs `gpt-6-astra` / `gpt-5.6-sol` |
| D007 | One supervisor integrates; parallel workers get disjoint ownership | Coordination choice; worktrees only when their integration benefit justifies them |
| D008 | First milestone proves ACS + geography + one document end to end | MVP section 5; broad research follows a trustworthy useful slice |

For a new material decision, record: ID, status, context, chosen approach, alternatives rejected and why, affected tasks/contracts, evidence, and revisit trigger. Routine local implementation details do not need an entry.

No change here independently grants permission to contact people, publish, incur spending commitments, or change app/account settings.

## D009 — Accepted runtime pins and checkout operation (2026-09-27)

Accepted for T001–T005: Python 3.12.12 managed by uv and Node 24.21.0 LTS, with exact dependency locks. ARM64 resolution/build/import and SQLite 3.50.4 FTS5/foreign-key probes passed. Node archive matched the official SHA-256 (`bed7eea5325e1108f32ce5228ddd6a5f0f08a499ee42aa7442aea583702f6057`). [Node release](https://nodejs.org/en/blog/release/v24.21.0); [Python release](https://www.python.org/downloads/release/python-31212/). Keep rollback journaling; no additional infrastructure. Global Node 25 was not used for verification. This is an editable source-checkout runtime; packaged desktop distribution is deferred. Revisit pins for deliberate maintenance/security updates with fresh checks, not silently each session.

## D010 — Initial persistence only; release acceptance remains separate (2026-09-27)

Accepted for T003/C002/C004: packaged ordered SQL migrations, generic immutable public versions and evidence links, candidate measurement staging, separate baseline/private stores, and sealed-membership guards. This establishes a tested boundary without inventing a complete source schema before adapter work. Per-store initial migration transactions and exact checksum compatibility are implemented; partial or changed pairs fail closed. Upgrades await paired backup/recovery work; do not mutate existing ledgers. T006/T007 must add typed source candidates, complete release-membership closure, uncertainty, retention, validation/manifests, and synthetic exclusion before accepting real releases. Internal synthetic export tests prove separation, not the future full export product.

## D011 — First-slice metrics and access gate (2026-09-27)

Accepted T002 audit selects 2019–2023 ACS published household median income, poverty rate, and household count, with matching 2023 cartographic tracts and FY2025 Social Services document locators. This pinned release has verified metadata and compatible downloadable geography; latest-release selection is not a requirement for the first traceable slice. Supervisor rejected `S2501_C06_001E` as an unsupported renter-share interpretation and verified the replacement's official metadata. The final keyless combined query returns HTTP 302 with a Census missing-key error; full T006 acceptance is blocked until authorized observation bytes or an official alternative are verified. Boundary/document and synthetic adapter work can proceed. County PDF redistribution remains unconfirmed; citations and local research retention do not authorize whole-document export. Evidence: [source audit](../source-audit.md).
