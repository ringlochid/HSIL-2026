# Project brief

## Product summary

Design a single-page clinician-facing HSIL demo workspace that turns one uploaded genomic report into a narrow, reviewable referral-support decision.

The page should show the full story in one place:
- source report,
- extracted fields,
- evidence-grounded recommendation,
- uncertainty / missing-data status,
- and the final clinician review action.

This is not a generic genomic report generator, chatbot, or lab workbench.
It is a focused review workspace for one case and one decision lane.

## Target user

- clinician / reviewer / coordinator handling genomic case review and the related referral / next-step decision
- secondary audience in the demo: judges who need to understand the workflow in seconds

## Primary goal

Make the reviewer's decision legible fast.

Within the first screenful, the page should answer:
1. what case is being reviewed,
2. what the current recommendation or block state is,
3. what evidence supports it,
4. and what the reviewer can do next.

## Core screens and pages

- One primary page only: `Referral support review`
- The same page should support at least two states:
  - ready-for-review hero case
  - blocked / missing-data comparison case
- No separate dashboard is required for the demo if the case-switching state can live inside this page.

## Information hierarchy

1. Case identity + workflow state + primary actions
2. Recommendation / blocked outcome
3. Reviewer actions
4. Source report + extracted fields
5. Evidence bundle
6. Uncertainty / limitations / missing data
7. Audit trail / provenance / fixture-live badge

## Reference cues

- Leo sketch: keep the sense of workflow progression, but turn it into a real review workspace.
- Franklin/Genoox: persistent case context and report-as-output, not report-as-product.
- VarSome Clinical: professional evidence posture and non-autonomous decision support framing.
- Current HSIL frontend scaffold: dark shell, compact cards, restrained accent, calm status treatments.

## Visual tone

- clinician-facing
- grounded
- calm
- high-contrast
- technically credible
- low-noise

Use the existing dark neutral palette from the current frontend scaffold.
The page should feel serious and modern, not consumer-friendly, playful, or overly enterprise-generic.

## Constraints

- one page only for the demo
- must fit the current repo framing: upload-first workflow, narrow referral-support lane, human review gate
- avoid prompt / model / agent internals in the UI
- avoid generic report-generator framing
- blocked / missing-data state must be visibly safe and fail-closed
- live API dependence must not be required for the page to make sense
- recommendation language must stay assistive rather than autonomous

## Responsive priority
- Source of truth breakpoint: mobile-first
- Required mobile modules:
  - case header
  - workflow step strip
  - recommendation or blocked-state card
  - reviewer actions card
  - source report card
  - extracted fields summary
  - evidence bundle
  - uncertainty and limitations
  - audit trail
- Tablet expansion rules:
  - keep case header and recommendation highly visible
  - split into a main column and a secondary column only when scan speed improves
  - reviewer actions may move beside or just below the recommendation
- Desktop expansion rules:
  - use a 3-zone workspace
  - left: source report + extracted fields
  - center: recommendation + evidence + uncertainty
  - right: reviewer actions + checklist + notes + export / hold controls
  - bottom: audit trail / provenance strip
- Copy that must stay locked across breakpoints:
  - HSIL
  - Referral support review
  - Report uploaded
  - Fields reviewed
  - Interpretation run
  - Reviewer decision
  - Recommendation
  - Evidence bundle
  - Uncertainty & limitations
  - Reviewer actions
  - Approve & export
  - Hold for more data
- Probe failure signals to watch for:
  - the page reads like a backend pipeline instead of a review workspace
  - the recommendation falls below the report/source card
  - the reviewer CTA disappears out of the first viewport on larger breakpoints
  - the PDF/source module visually outweighs the actual decision
  - the blocked state looks weaker or less intentional than the ready state

## Success criteria

- The page explains the workflow in one glance without extra narration.
- The recommendation feels grounded in evidence rather than generated from nowhere.
- The human review gate is visually undeniable.
- The blocked comparison case proves safe failure instead of weak confidence theater.
- The layout can present Ravi and Owen with the same core structure.
- The page feels demo-ready on desktop while preserving a clean mobile-first story.

## Open questions

- Should the launch copy name the specific disease / referral lane, or stay generic until the team locks it?
- Should the source report be a real thumbnail preview or a tighter file summary card?
- Does reviewer editing happen inline in the right rail, or through a focused modal/drawer?
- Is export framed as a note, a PDF, or a review-ready packet?

## Approval status
- State: approved
- Notes: Approved by Leo on 2026-04-10 to proceed into Phase 2 mobile generation for the one-page HSIL demo workspace.
