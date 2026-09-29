# Chesterfield County Digital Twin: MVP plan

Status: Target scope and delivery plan; local skeleton implemented September 27, 2026. See [execution state](execution/state.md) for current verified capabilities.  
Prepared: September 26, 2026.  
Primary user: Jordan Osier.  
Release model: Private, single-user, locally operated research tool.

## 1. Product outcome

Build a small, auditable county observatory that helps Jordan decide **which local responsibilities and institutions deserve deeper investigation, why, and what evidence would change that judgment**.

The MVP should support a repeatable research session: survey the county, inspect a sector or community function, follow its evidence, compare possible actions, and choose the next research step. Its value is better strategic judgment, including a justified decision to stop pursuing an idea.

The county-wide ambition remains intact. The release achieves breadth through a coverage ledger and published aggregates; it achieves depth through a deliberately small collection of documented organizations, functions, and relationships. It does not claim exhaustive knowledge of county activity.

This plan translates the [digital-model brief](../../chesterfield_county_digital_model_brief.md), especially sections 2, 6–14, and the [family strategic framework](../../osier_family_strategic_framework.md), especially sections 3–10, into a bounded first release. These source documents currently live outside the Git repository; preserve that context when sharing or moving the plan.

## 2. What success looks like

Jordan can complete these workflows using one saved release of the evidence:

1. **Orient:** See major economic sectors, employer and nonemployer activity, household conditions, and coverage gaps without confusing establishments, jobs, people, and households.
2. **Investigate:** Open an organization or function profile and follow each substantive statement to a source record, document page, or reproducible calculation.
3. **Understand a dependency:** Compare resident-worker and workplace employment geography, with explicit coverage and dates, and inspect a few documented institutional relationships.
4. **Compare actions:** Read three short candidate briefs with counterevidence, unknowns, family-capacity requirements, and a next validation step. A candidate may be an operating responsibility, partnership, or support for an existing institution.
5. **Revisit:** Refresh one source, see changes and possible revisions, and reconstruct the previous answer.

Business demand, private finances, family risk capacity, and spiritual health remain unknown unless supported by appropriate evidence or explicit personal input. A sector's size alone cannot qualify it as an opportunity.

## 3. Release scope

| Component | Required in the MVP | Deferred depth |
| --- | --- | --- |
| County observatory | County sector table; 8–12 selected household indicators at county and tract level where published; one tract map; coverage and freshness views | Parcel inventory, continuous feeds, full historical series, comprehensive development monitoring |
| Evidence graph | Structured organizations, places, functions, typed relationships, claims, sources, and review decisions; linked profiles | Dedicated graph database, graph visualization, automated ownership mapping |
| Scenario workbench | One reproducible sensitivity worksheet attached to a candidate brief; explicit baseline, assumptions, ranges, omissions, and decision thresholds | County macroeconomic simulation, causal forecasts, predicted AI unemployment |
| Private strategy layer | Three candidate briefs, separate assessment dimensions, a prioritized research queue, Markdown/CSV/JSON export | CRM, customer accounts, billing, acquisition screening, client-confidential workspaces |

**Depth budget:** Target 15–25 curated organizations across businesses, public bodies, nonprofits, congregations, and cultural/community institutions; six function profiles spanning economic, public, and community responsibilities; and ten documented relationships. These are planning targets for useful examples, not a representative sample or permission to manufacture evidence. If evidence does not support a target, record the search and resulting gap.

Choose these examples after the broad scan. Preserve physical work, care, infrastructure, and production alongside administrative and professional work. Include regional providers where their service to the county is documented. Do not select a favored industry in advance.

**Coverage ledger:** Give every major NAICS sector and each institutional/household category a disposition: observed, partially covered, unresolved, searched without evidence, or outside defined scope. Track aggregate coverage separately from named-organization coverage. Each row records sources searched, limitations, last review, and next research action. The existence of one record never establishes complete coverage.

**Excluded from this release:** Public launch, paid product validation, outreach, private individual profiles, inferred personal religion or health, automated entity merges, autonomous publication, comprehensive web crawling, live sensor feeds, and a general conversational interface. Saved questions and document search provide the initial question-answering experience.

## 4. Source plan and access gate

The following is a proposed source portfolio. Official documentation was spot-checked while preparing this plan; no county datasets have been downloaded, reconciled, or validated. A listed source is not an implemented connector. Exact releases, variables, retrieval routes, licenses, and geography identifiers must be pinned in milestone 0.

| Source family | Minimum slice and purpose | Access/comparability checks | Refresh proposal |
| --- | --- | --- | --- |
| ACS five-year tables | 8–12 household/population measures for county and tracts: age, income, poverty, housing costs, tenure, education, employment, and access where available | Preserve estimate, margin of error, annotations, universe, and period; select published measures first; do not treat overlapping windows as independent annual measurements | Check for releases quarterly; ingest after validation |
| County Business Patterns | County employer-establishment and employment measures across published major sectors | Industry vintage, exclusions, suppression, employment universe; no firm-level buyer list and no parent/child double counting | Annual release |
| Nonemployer Statistics | County sector counts and receipts, displayed separately from employer statistics | Units, coverage, classification and methodology breaks; receipts are not profit | Annual release |
| Geographic boundaries | County and tract outlines matching selected statistical geography; identifier-based joins | Store vintage and coordinate system; simplified display boundaries are not parcel-level location authority | With geography changes |
| LEHD/LODES | One year of county residence/workplace aggregates and county-to-county job flows | Explicit job type and release; validate cross-state flows, block crosswalks, and main/auxiliary files; reconcile only within compatible universes | Annual release |
| Curated official/local documents | Bounded extracts from county budget/function descriptions and public organizational program pages | Page/section citations; county versus school scope; reported claims versus independently established facts; retention terms per source | Manual quarterly review |

ACS exposes estimates and margins of error through its API conventions. The CBP and NES documentation currently states that Census API queries require a key; plan for an authorized key or a verified official download route, without committing credentials. NES documentation also warns that its 2022 methodology change affects historical comparison. These checks belong before trend implementation. Sources: [ACS query guide](https://www.census.gov/data/developers/guidance/api-user-guide.Example_API_Queries.html), [CBP documentation](https://www.census.gov/data/developers/data-sets/cbp-zbp/cbp-api.html), [NES documentation](https://www.census.gov/data/developers/data-sets/nonemp-api.2020.html).

LODES provides residence, workplace, and origin-destination products based on administrative/modelled data; its limitations differ from ACS sampling uncertainty. Do not force LODES, ACS, and CBP totals to agree. Use the selected release's documentation to establish a complete retrieval strategy before claiming all out-of-county destinations are represented. Source: [LEHD data and technical-documentation index](https://lehd.ces.census.gov/data/).

Census cartographic boundaries are intended for thematic mapping. Chesterfield also offers downloadable GIS data, but parcel and address integration can wait. Sources: [Census boundaries](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html), [Chesterfield GIS catalog](https://opengisdata.chesterfield.gov/).

County financial pages distinguish government payments from school-division payments. The MVP uses budget documents for public-function descriptions; automated payment analysis is a later extension. Source: [Chesterfield financial information](https://www.chesterfield.gov/231/Budget-and-Performance-Management).

**Access failure policy:** Time-box initial investigation of each source. Prefer an official download or a reproducible manual import if an API is unavailable. If neither is viable, record a blocked source and the affected acceptance question. Continue independent work, but explicitly revise the release scope before claiming the missing capability is complete.

**Next sources after the MVP:** QCEW for additional employment/wage context; planning and permits for development status; procurement/payments for buying relationships; IRS data for partial nonprofit coverage; health, education, infrastructure, licensing, and cultural sources as the ledger identifies decision-relevant gaps. O*NET can later suggest workflow hypotheses, with local presence clearly unverified.

## 5. First end-to-end slice

Start with **“How do household conditions vary across the county, and how certain is that comparison?”**

Use one ACS release, three published tract-level measures, compatible county/tract boundaries, and one cited local document describing a related public function. Avoid inferring demand or individual characteristics from area statistics.

Deliver a small table/map and one linked function profile. From a displayed value, Jordan can inspect its unit, population universe, period, uncertainty, source record, archived input where permitted, and transformation. Re-running the build from the same inputs reproduces the same result.

This slice deliberately exercises structured data, geography, documents, claims, and presentation before committing to an application framework or widening ingestion. Its completion is a useful stopping point even if the broader MVP is paused.

## 6. Proposed architecture and data contract

Use a local application with a small number of components:

```text
Official files / APIs / curated documents
                    |
          Source register + snapshots
                    |
      Validated extraction and transformations
                    |
       Baseline database + document index
                    |
       Read-only views and portable exports
                    |
    Separate private briefs and scenario inputs
```

**Local implementation design:** The [technical architecture](technical-architecture.md) supersedes the initial PostgreSQL/PostGIS proposal following the decision to optimize for one MacBook. Use Python/FastAPI, SQLite with local document search, immutable evidence files, and a React UI served by the Python process. Prepare geographic layers in Python and process large tabular inputs in a bounded worker, using DuckDB where needed. Validate the design through the first slice before expanding; PostgreSQL/PostGIS remains an option if later spatial or concurrency requirements justify it. A separate graph service, vector database, distributed queue, and cloud deployment are unnecessary for the proposed release.

| Record group | Minimum fields / behavior |
| --- | --- |
| Source and snapshot | Stable ID, publisher, URL, terms/retention notes, scope, release, retrieved-at time, checksum, local artifact reference, access status |
| Place | Internal ID, external geography ID, type, boundary vintage, geometry where applicable; distinguish service area, work location, and legal address |
| Organization | Internal ID, names, external IDs, entity/establishment/public-unit type; parent/branch links only with evidence |
| Function and relationship | Trigger, outcome, accountable role, dependencies; typed endpoints, dates, supporting claim IDs, and unknown capacity |
| Observation and claim | One of reported observation, calculated measure, inference, hypothesis, scenario result; value/text, unit, denominator, geography, period, uncertainty, limitation, review status |
| Evidence and derivation | Source record/page/excerpt; input claim IDs; query/script version and parameters; calculation outputs |
| Review and revision | Candidate matches, merge/reversal decisions, conflicts, superseded records; effective dates and recorded-at dates kept distinct |
| Coverage and ingestion run | Category/disposition, searches and gaps, refresh cadence, last success, failure details, release manifest |
| Private brief and scenario | Baseline release ID, referenced claims, family assumptions, separate assessment dimensions, scenario parameters, outputs, next research action |

Store assets and dated events only where needed by the initial profiles; defer specialized inventories. Use stable internal IDs throughout. Shared names/addresses propose matches but never silently merge records. Distinguish zero, unavailable, suppressed, and not applicable in storage and presentation.

An inference must link to its supporting claims and reasoning; a calculation must link to all inputs. Never overwrite a conflicting or superseded observation. A release manifest fixes input snapshots and code versions so later evidence does not silently change an earlier brief.

Keep private strategy records in a separate local store outside the repository, with a distinct export path. Public-baseline exports must exclude family notes and scenario preferences. Before importing source-document contents into Git, check repository visibility and sensitivity. Bind the initial application to localhost; remote access and authentication are later scope decisions.

## 7. User experience and decision artifacts

Build four compact views:

1. **County overview:** Sector comparison, selected household indicators and tract map; prominent reference periods and coverage gaps.
2. **Evidence explorer:** Search/filter profiles and documents; follow relationships; inspect claim type, citations, calculations, unknowns, and unresolved conflicts.
3. **Research desk:** Three candidate briefs and a research queue, ordered by decision affected, potential to change the decision, feasibility, and effort. Use explained ordinal priorities rather than invented expected-value scores.
4. **Sources and changes:** Source register, last successful refresh, stale/failed sources, and a comparison with the previous saved release.

Every map has an equivalent table. Filters must expose reference period, geography, and coverage. Empty results say whether the information is unavailable, suppressed, outside scope, or genuinely zero. A fixed set of sourced question pages is sufficient; general natural-language Q&A is deferred.

Each candidate brief contains: responsibility and beneficiary; trigger and accountable buyer where known; current alternatives; local evidence; counterevidence; an explicit demand hypothesis; economics still to validate; founder time/capital/availability required; family resilience; community contribution; institutional/transferable capability; evidence quality; disconfirming conditions; next validation action. Assess these dimensions separately without a default composite ranking.

The first scenario can examine one candidate's delivery economics under alternative productivity, price, demand, and review-cost assumptions. Compute contribution after delivery labor, founder labor, tools, selling effort, maintenance, and fixed costs; distinguish one-time setup. Use supplied assumptions or conspicuously illustrative ranges, never invented local finances. Show the break-even threshold and mechanisms omitted. This supports a decision about what to investigate; it does not forecast county employment or establish willingness to pay.

## 8. Delivery sequence and effort

Estimates below are planning judgments for combined hands-on engineering, research, and review effort, assuming existing equipment and a modest interface. They are not delivery commitments or estimates of autonomous-agent runtime. Re-estimate after the first source audit and end-to-end slice.

| Gate | Work and concrete artifacts | Exit criterion | Effort |
| --- | --- | --- | --- |
| 0 — Foundation | Source register; coverage taxonomy; metric dictionary; evidence schema; private-data policy; sample access checks | Each core source has a verified access route or explicit blocker; first-slice variables and geography are pinned | 6–10 hours |
| 1 — Traceable slice | ACS/boundary loaders; one curated document; repeatable build; table/map; evidence drill-down | A fresh local build reproduces the selected answer and exposes provenance, uncertainty, and unknowns | 14–22 hours |
| 2 — Broad baseline | CBP and NES ingestion; remaining indicators; LODES county aggregation; populated coverage ledger | Every category has a disposition; published sectors are represented; employment universes and geographic joins are validated | 20–30 hours |
| 3 — Institutional depth | Curated profiles/functions/relationships; document search; review queue | Profiles span economic, public, and community functions; every asserted relationship has evidence; ambiguous identity remains unresolved | 12–20 hours |
| 4 — Decision support | Three briefs; ranked research queue; one sensitivity worksheet | Each conclusion separates evidence and assumptions, includes counterevidence, and names a practical next test | 10–16 hours |
| 5 — Release and handoff | Refresh/diff; exports; backup/restore; acceptance report; operating instructions | Release checks pass; one real research session is completed; previous evidence and answers remain reproducible | 8–12 hours |

Base estimate: **70–110 hours**. Allow approximately 25% contingency and round the planning envelope to **90–140 hours**. At five hours/week that is roughly 18–28 weeks; at ten hours/week, 9–14 weeks. Weekly capacity, budget, and reduced availability around March 2027 are unresolved; no completion date is assumed.

The first two gates form a **20–32-hour base-effort checkpoint**. Continue only if the evidence chain is useful and maintenance looks sustainable. If the schedule is too long, reduce curated depth and interface polish or pause at that checkpoint. Do not remove provenance, uncertainty, private-data separation, or honest coverage reporting to meet a date. Defer LODES only through an explicit scope change that also marks the resident/workplace question deferred.

Jordan supplies personal constraints and resolves consequential strategic choices. Deterministic checks handle routine validation; ambiguous identities, conflicting evidence, and causal interpretations require review. If agents are used during implementation, give each a bounded source/domain assignment, the common evidence schema, and a requirement to return gaps and counterevidence. Extraction does not automatically promote a claim to accepted evidence.

## 9. Acceptance and connection to the original brief

| Original evaluation question | MVP treatment |
| --- | --- |
| 1. Major industry segments and coverage | Required sector table plus separate aggregate/entity coverage ledger |
| 2. Resident jobs versus county jobs | Required LODES-based comparison with explicit job universe and year; not equated with ACS residents |
| 3. Geographic household conditions | Required tract table/map with margins of error and source universes |
| 4. Development changes | Deferred systematic feed; represent any curated event with proposal/approval/completion status |
| 5. Public purchasing relationships | Deferred systematic analysis; budget evidence cannot substitute for payments or contracts |
| 6. Providers of important functions | Required curated profiles; capacity explicitly unknown where unreported |
| 7. Cultural/spiritual institutions and gaps | Required selected institutions and coverage gaps; no spiritual-health score |
| 8. External dependencies | Required county job flows and supported examples of regional service links; no comprehensive supply-chain claim |
| 9. Commercial responsibilities and demand | Required candidate briefs with evidence stages and validation steps |
| 10. Conclusions sensitive to assumptions | Required bounded scenario; broader county/AI scenarios deferred |
| 11. Changes versus revisions | Required saved releases and source refresh/diff demonstration |
| 12. Most useful next research | Required queue with explained priorities |

Before release, verify:

- Every displayed quantitative result and substantive profile/brief claim has traceable evidence or an explicit hypothesis/scenario label; no orphaned evidence references.
- Rebuild from saved inputs reproduces published outputs; re-ingesting the same snapshot does not duplicate observations.
- Known test cases cover suppression versus zero, incompatible units/vintages, geographic mismatch, parent/child industry double counting, and unsupported entity merges.
- A source correction preserves the prior value; a failed refresh leaves the last valid release intact and visibly stale.
- Independently inspect a small stratified sample from every source family, all ten target relationships, and every claim driving a brief's conclusion. Failed consequential claims block that conclusion until corrected.
- Scenario boundary cases and break-even calculations are independently checked; illustrative parameters remain visibly distinct from observations.
- A baseline export contains no private strategy records; a backup restores a complete release and its evidence links.
- Jordan completes a research session, records a pursue/defer/reject decision or a concrete validation step, and can explain what evidence would change it. A conclusion that nothing is ready for action is acceptable.

These are future implementation checks, not tests already performed during planning.

## 10. Operation, risks, and next work

Use manually invoked refresh commands initially, with per-source cadence and stale indicators. Review quarterly or before an important decision; annual datasets need not be fetched daily. Record source-specific success/failure and preserve the last valid release. Test restoration before relying on the tool. Aim for routine upkeep within one short monthly session outside major source releases; measure actual effort before treating that as achieved.

| Risk | Planned response |
| --- | --- |
| Research grows without producing decisions | Gate expansion on completed sourced answers and candidate briefs; freeze the first source portfolio |
| Sources cannot support the desired inference | Return unknown; specify the missing evidence; move the question into the research queue |
| Data access or cleanup consumes the schedule | Time-box access audit, use documented manual imports, and re-estimate at gate 1 |
| Incompatible statistics produce confident errors | Preserve universes/vintages and limitations; reconcile only with an explicit method |
| Agent extraction creates plausible false claims | Require exact citations, deterministic validation, and review of consequential claims |
| Model maintenance competes with family capacity | Local operation, pause/resume checkpoints, reproducible handoffs, measured upkeep |
| Strategy or commercial preferences distort evidence | Separate baseline and private stores; reference fixed evidence releases from briefs |

The plan assumes existing equipment and avoids requiring new paid services. API/model spending, hosting, household finances, weekly availability, and any commercial test remain unestablished. None is necessary to write the schema and run the first access checks. Before making a calendar commitment, establish sustainable weekly capacity; before a venture comparison becomes a recommendation to act, establish relevant family constraints.

**First implementation session:** Create the source register and coverage ledger; verify access to ACS, matching boundaries, and one local public-function document; select three measures; define the observation/evidence contract; record unresolved access issues. The next decision is whether that slice supports a useful, inspectable answer at manageable cost.

**Planning handoff:** Reviewed both foundational artifacts and the repository's initial state. Added this plan and a README link. Spot-checked official source documentation; identified API-key and comparability considerations. No datasets were ingested, no application was built, and no external commitments were made. The next gate is foundation/access validation.
