# Refinement prompts

Built-in image_gen edits used to correct the first-pass concepts. See [concept notes and initial prompts](README.md).

## Refinement: 02-evidence-explorer.png

```text
Use case: ui-mockup edit. Preserve this entire UI screenshot exactly: layout, color, text, sidebar, evidence inspector, diagram, and all other details. Make ONLY one correction in the Claims and questions table: replace the second row sentence 'The pantry likely receives food from a regional supplier.' with '2 documented relationships in this example.' Keep its 'Calculated' badge. This makes that row accurately describe a count of the two diagram relationships. Do not change any other content or design.
```

## Refinement: 03-research-desk.png

```text
Use case: ui-mockup edit. Preserve this entire UI screenshot: layout, palette, panels, table, typography, curves, controls, sidebar and all other details. Make ONLY these corrections: change chart x-axis title from 'Hours per engagement' to 'Engagements per month' so increasing contribution corresponds to increasing engagement volume; change y-axis title from 'Contribution' to 'Monthly contribution ($)'. Change top-right user display name 'Jamie D.' to 'Jordan O.' and avatar initials 'JD' to 'JO'. Keep all illustrative-data and scenario assumption labels. Do not modify anything else.
```

