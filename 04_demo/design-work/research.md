# Research notes

## Project frame
- Single-page HSIL demo workspace for a clinician-facing genomic referral-support workflow.
- Page must show: uploaded report PDF -> extracted fields -> evidence-grounded recommendation -> clinician review -> export.
- The product framing stays narrow: decision support for one referral / next-step lane, not a generic genomic report generator.
- The demo page should read as a review workspace, not as a backend pipeline diagram or AI console.

## Anchor references
- Reference 1: Leo's whiteboard / sketch reference (attached 2026-04-10).
  - Borrow: visible workflow progression, distinct source / process / output zones.
  - Avoid: looking like a system diagram instead of a clinician workspace.
- Reference 2: Franklin / Genoox case interpretation workflow.
  - URL: https://help.genoox.com/en/articles/4548752-variant-interpretation-video-tutorial
  - Borrow: persistent case details during interpretation, saved case context, report generation as a downstream action rather than the main screen.
  - Avoid: dense lab-tool chrome, too many variant-classification controls, workbench sprawl.
- Reference 3: VarSome Clinical product framing.
  - URL: https://landing.varsome.com/varsome-clinical
  - Borrow: annotation + classification as support for patient-management decisions, rule-based interpretation posture, professional/regulated tone.
  - Avoid: making pathogenicity/classification verdicts the only thing the page communicates.
- Reference 4: Genomic CDSS prototype / dashboard framing.
  - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC4862762/
  - Borrow: simple dashboard-style interface with actionable clinical measures and visible reliability context.
  - Avoid: sprawling EMR-style information density or generic data platform framing.
- Reference 5: Current HSIL demo frontend scaffold.
  - Files: `04_demo/app/frontend/src/components/AppShell.tsx`, `SectionCard.tsx`, `StatusPill.tsx`, `index.css`
  - Borrow: dark neutral shell, restrained accent, strong section-card rhythm, status chips.
  - Avoid: spreading the story across separate dashboard / case / review pages when the demo now wants one decisive workspace.

## Anti-references / drift families
- Consumer genetics report / wellness report UI.
  - Risk: reads like a broad DNA explainer or take-home artifact instead of a narrow clinician decision workflow.
- Chatbot / agent-console UI.
  - Risk: exposes prompts, model internals, or narrative reasoning instead of grounded evidence and review actions.
- Generic SaaS KPI dashboard / symmetric analytics cards.
  - Risk: buries the actual clinical decision behind equal-weight panels and fake metrics.

## Public implementation references
- shadcn/ui dashboard patterns.
  - URL: https://ui.shadcn.com/examples/dashboard
  - Useful for shell, spacing, and dashboard information rhythm.
- shadcn/ui sidebar blocks.
  - URL: https://ui.shadcn.com/blocks/sidebar
  - Useful for compact case switching / navigation without overbuilding custom layout primitives.
- `satnaing/shadcn-admin`.
  - URL: https://github.com/satnaing/shadcn-admin
  - Useful as a React + Vite + Tailwind example for multi-panel app composition.

## Repeated structure cues
- Header with case identity, current state, and 1-2 primary actions.
- Visible workflow step strip showing where the reviewer is in the process.
- Persistent source/report area that keeps the uploaded document and extracted fields in view.
- Main recommendation area that states the next-step recommendation or blocked state clearly.
- Separate reviewer-control area for notes, confirmation, approve/export, or hold actions.
- Evidence grouped by category (variant, phenotype, pathway/guideline) rather than hidden in tabs.
- Clear missing-data / fail-closed branch that can occupy the same layout as the ready state.
- Audit trail / source provenance near the bottom, not as the hero.

## Repeated visual cues
- Dark or neutral high-contrast shells work well for dense professional review UIs when the typography stays calm.
- Rounded cards are fine, but the page should still feel clinical and controlled rather than playful.
- One accent color should anchor actions and active state; the rest should come from surface depth and status colors.
- Status chips should be compact and legible, not giant banners.
- The recommendation card should visually outrank the source report preview.
- Missing data and limitations need a distinct but non-alarmist presentation.

## Prompt ingredients worth keeping
- one case workspace
- report uploaded
- extracted fields reviewed
- interpretation run
- recommendation ready for clinician review
- evidence bundle
- uncertainty and limitations
- missing data flags
- reviewer actions
- approve and export
- hold for more data
- audit trail
- fixture / live status

## What to borrow
- Franklin-like persistent case context while reviewing evidence.
- VarSome-like professional posture: evidence and rules support decisions but do not replace clinician judgment.
- Current HSIL frontend visual language: dark neutral surfaces, quiet gradients, compact section cards, restrained status pills.
- Dashboard-shell patterns only for layout discipline, not for KPI aesthetics.
- A 3-zone desktop hierarchy: source report / recommendation / reviewer actions.

## What to avoid
- prompt / model / system-jargon modules
- raw score thresholds as the main hero signal
- a page dominated by left-to-right backend pipeline boxes
- consumer report printout aesthetics as the main working surface
- too many equal-weight cards
- strong claims that sound autonomous, diagnostic, or final

## Open questions
- Should the page ship with a disease-specific label (for example inherited retinal / RPE65 lane) or stay generic until the team fully locks the lane?
- Does the uploaded report appear as a real PDF thumbnail, or as a compact source-file card with extracted highlights?
- Should reviewer edits happen inline in the right rail, or in a tighter review drawer/modal?
- Should the blocked comparison case live as a top-level case switcher item, or as an inline comparison card under the main case?
