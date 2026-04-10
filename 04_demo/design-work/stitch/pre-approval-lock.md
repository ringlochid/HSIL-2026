# Pre-approval lock

## Approved intent source
- brief: `design-work/brief.md`
- copy pack: `design-work/copy-pack.md`

## Exact labels to preserve
- site title: HSIL
- page title: Referral support review
- primary nav labels:
  - Ravi
  - Owen
- search placeholder: 
- key section headings:
  - Recommendation
  - Evidence bundle
  - Reviewer actions
  - Uncertainty & limitations
- key CTA / link labels:
  - Approve & export
  - Hold for more data
- footer tagline: 
- footer links:

## Required nouns
- recommendation
- evidence
- review
- source report
- extracted fields

## Banned drift words
- AI copilot
- system prompt
- model reasoning
- diagnosis
- autonomous eligibility
- generic genomic report

## Notes
- This is the pre-approval wording/framing gate for Stage B.
- Use it to catch wrong labels or wrong product/category language before approving mobile.
- Do not allow extra decorative top-framing labels, mood subtitles, or poetic support tags unless they are explicitly intended and written into this lock.
- Blocking checks should use visible rendered text only.
- Do not fail approval because of placeholders, `alt`, `data-alt`, `aria-label`, or HTML `<title>` metadata.
- Prefer a **small lock** over a comprehensive one.
- Lock only what the human would actually care about seeing on the approved mobile screen: page title, key headings, truly important nav labels, essential CTA labels, and the strongest product nouns.
- If a field is optional, decorative, footer-only, future-state, or uncertain, leave it blank instead of forcing it into the gate.
- If Stage B fails because the lock over-specified nonessential visible labels, revise the lock inside Stage B before spending more edit budget.
- If an item is genuinely not meant to appear, leave it blank or keep the bracket placeholder.
