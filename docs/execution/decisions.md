# Decision register

These are current working design choices from the existing artifacts and the user's workflow preference. They are not claims that implementation or validation has occurred. Amend with rationale and a superseding decision; avoid reopening them every session without new evidence.

| ID | Decision | Basis / revisit trigger |
| --- | --- | --- |
| D001 | Run locally on one MacBook using native processes | Explicit user direction; revisit for actual remote/multiuser need |
| D002 | Python/FastAPI + compiled React UI, SQLite, local evidence files | Architecture sections 1–5; validate first slice before broadening |
| D003 | DuckDB only for bounded bulk transformation; geographic preprocessing initially | Architecture sections 4, 10, 12; add complexity only after measured need |
| D004 | Baseline and private strategy use separate stores and export paths | Mission and architecture sections 5, 11; maintain through all iterations |
| D005 | Immutable evidence versions and sealed, explicitly activated releases | Architecture sections 6–9; every baseline view pins a release |
| D006 | Astra supervisor, GPT-6.1 Sol workers requested explicitly | Updated user direction September 29; `gpt-6-astra` / `gpt-6.1-sol`; supersedes older worker selection |
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


## D012 — Typed unpublished adapters before ingestion services (2026-09-29)

T006a settles byte-to-candidate contracts separately from fetch/storage/release operations. The three adapters have no network/database side effects and fail atomically. Raw/spec hashes and versioned transform identity form reproducible fingerprints; retrieval events remain separate. Fixed boundaries/PDF require the audited content pins; changed official artifacts fail pending source-spec review. Synthetic status is required at the adapter boundary and rejected by the cross-source real-slice validator. No migration or bootstrap capability changes were needed. This preserves the accepted skeleton and leaves T006 live-source/persistence and T007 closure gates explicit. Revisit when implementing retained-byte ingestion and persisted candidate reconciliation.

## D013 — Source interpretation and parser scope (2026-09-29)

ACS annotations take priority independently for estimates and MOEs; numeric median bounds remain unavailable as exact points, and controlled MOE remains not_applicable with its original raw/annotation values. Source authority: [Census annotation values](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-estimate-and-annotation-values.html) and [variable types](https://www.census.gov/data/developers/data-sets/acs-1year/notes-on-acs-api-variable-types.html), inspected this session. The three selected metrics retain their audited units/universes and period; no derived rates are introduced.

Use pinned pure-Python pyshp 2.3.1 and pypdf 6.1.1 for bounded local normalization. Preserve NAD83 source geometry; reprojection/display and complete topology validation remain separate work. Document extraction retains exact full selected pages with locators and two-locality scope, without treating those pages as Chesterfield-only statistics. PDF byte/page/output checks do not guarantee peak parser-memory or CPU bounds; future fetch/job execution needs process-level resource isolation before accepting arbitrary unpinned documents. Current non-synthetic PDF acceptance requires the exact audited artifact hash.

## D014 — Current worker selection (2026-09-29)

The user's current explicit `gpt-6.1-sol` worker request supersedes the older `gpt-5.6-sol` standing text. Three focused fresh-context assignments requested the exact new ID after shared contracts passed tests. Update AGENTS/workflow/template references accordingly; historical handoffs retain their original facts. The delegation tool exposes task IDs but does not independently confirm actual model metadata. Markdown cannot change or verify the supervisor's model setting; Astra remains the requested supervisor.

## D015 — Retained staging schema and failure boundary (2026-09-29)

Settled before implementation and accepted after T006b integration: append baseline `002_candidate_staging.sql`; never edit either `001_initial.sql`. Fresh initialization applies both baseline migrations. Existing 001 stores remain incompatible and must fail closed; no upgrade, ledger rewrite, or backup/recovery capability is introduced. The generic version/artifact/retrieval tables lack typed candidate indexing, run isolation and ordered import membership, so an explicit migration is preferable to hiding those relationships in unindexed JSON.

Reuse immutable `version` payloads (candidate JSON excluding retrieval), raw/spec content-addressed artifacts, and separate retrieval events. Add immutable staging runs with required synthetic mode, typed candidate lineage indexes, import manifests and ordered membership. Each import uses one accepted adapter, validates before object retention, retains both exact inputs, then commits all metadata atomically. An interruption can leave an unreferenced complete object; retry reuses it. Reads re-verify hashes, membership, typed payload identity and event lineage. Staging services open only baseline storage and do not create releases, activate, expose HTTP reads or export evidence. Retention is limited to the three audited local-retention policies; unsupported policy changes fail closed. Revisit for T007 closure and T013 paired migration/recovery.


## D016 — Validation groundwork remains independent of real-source acceptance (2026-09-29)

With T006b accepted, T007a is ready as a bounded next packet for persisted validation reports over explicit staged imports. This is proposed implementation work; no report service exists yet. It may use wholly synthetic selections for checks and report that the real boundary/document selection lacks ACS. Full T006 still needs authorized ACS observation bytes or a verified official alternative; T007 real release sealing/activation and T008 remain pending. This avoids idle independent validation work without weakening the evidence gate or inventing observation access. Revisit when ACS access is established and a real three-source candidate set can pass validation.
