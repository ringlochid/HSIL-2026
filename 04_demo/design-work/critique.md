# Design critique

## Output under review
- Phase: Stage B mobile first pass
- Project id: `6966097640981800851`
- Screen id: `ad4ec032f3f54489b8a28ca9c83b1cc3`
- Artifact: `design-work/stitch/mobile/screen.png`

## Brief alignment
- The output does establish a clinician-facing review surface rather than a consumer report.
- The page title, key workflow strip, recommendation card, reviewer actions, evidence bundle, source report, and uncertainty card are all present.
- The recommendation is visibly near the top and reads as the primary decision module.
- However, the page still drifts toward a generic app dashboard because of the avatar, bottom navigation, and extra product-area labels.

## Comparison to anchor references
- Compared with Franklin/Genoox-style case review, the page keeps useful persistent case context and a downstream review posture.
- Compared with the intended one-workspace HSIL direction, it still carries too much generic app chrome instead of feeling like a focused single-case review board.
- Compared with the current HSIL frontend scaffold, it is visually cleaner in mobile rhythm, but it introduces extra product framing that the repo does not need.

## Comparison to anti-references or adjacent drift
- It avoids the worst consumer-genetics report styling.
- It partially drifts into dashboard/app-shell territory through the bottom nav and moduleized app labels.
- It also introduces wording drift by using `diagnosis` in the footer.

## What is working
- Strong recommendation card placement near the top.
- Reviewer actions sit close enough to the recommendation to support a clear decision flow.
- Workflow strip is legible and helps orient the page.
- Card rhythm is calm and professional.
- Uncertainty card exists and is visually distinct.

## What is not working
- The page still feels like a product shell with sections such as `Referrals`, `Pipeline`, and `Archive` rather than one decisive review workspace.
- The header line `Case ID: HSIL • Ravi, Owen` collapses multiple concepts into one awkward status line instead of a clean case switcher.
- The avatar/headshot adds decorative dashboard chrome without helping the clinical story.
- The source report sits below the evidence bundle even though the intended mobile narrative should surface source context before evidence detail.
- Footer safety wording drifts into banned language and overexplains.

## Mobile issues
- Remove the bottom nav entirely.
- Replace the avatar + case-id string with a simple HSIL brand label and an explicit Ravi/Owen switcher.
- Move `Source report` above `Evidence bundle`.
- Tighten footer trust copy so it supports the page without turning into legalistic noise.
- Keep the page feeling like a single case-review workspace, not a multi-area app.

## Tablet issues
- Not yet probed.
- Current mobile shell hints that larger breakpoints may inherit too much app chrome if left unchanged.

## Desktop issues
- Not yet probed.
- Current bottom-nav-driven shell should not be the basis for desktop expansion.

## Semantic fidelity check
- `semanticCheck`: failed.
- Cause: banned term `diagnosis` appeared once in footer copy.
- Required mobile nouns and required-any workflow labels all appeared successfully.

## Responsive probe results
- Not run yet.
- Mobile should not be approved until semantic and pre-approval checks pass.

## Responsive repair recommendation
- Stay in Stage B and run one targeted mobile edit pass.
- Focus on hierarchy cleanup and semantic drift removal before any responsive probes.

## Copy lock fidelity
- Not applicable yet because mobile is not approved.

## Copy and messaging issues
- Footer line `does not constitute a final medical diagnosis` breaks the banned-word gate.
- `Case ID: HSIL • Ravi, Owen` is semantically muddy and weakens the case-switching story.
- `Referrals`, `Pipeline`, and `Archive` create unsupported product-area meaning.

## What to keep
- overall dark neutral palette
- workflow strip
- top recommendation card emphasis
- reviewer actions card position near the recommendation
- evidence card grouping style
- compact uncertainty card treatment

## Exact next edit moves
- remove bottom navigation and all extra product-area tabs
- replace the avatar/header status line with a simple HSIL brand label and a visible Ravi/Owen case switcher
- move `Source report` above `Evidence bundle`
- preserve page title, workflow strip, recommendation, reviewer actions, uncertainty heading, and CTA labels
- replace footer safety copy with the locked wording: `Draft only. No autonomous clinical decision.`
- keep the page as one single-case review workspace with no dashboard or pipeline drift

## Acceptance status
- revision required
