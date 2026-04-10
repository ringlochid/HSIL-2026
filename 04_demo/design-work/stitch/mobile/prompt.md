# Stitch prompt

Create a mobile-first page for a clinician-facing genomic referral-support review workspace.

Goal:
Design one decisive demo page that turns an uploaded genomic report into a grounded, reviewable next-step recommendation. The page should feel like a real clinical review workspace for one case, not a generic report generator, not a lab workbench, and not an AI console.

Required structure:
- compact case header with case identity, status, and primary actions
- workflow step strip with Report uploaded, Fields reviewed, Interpretation run, Reviewer decision
- recommendation card or blocked-state card near the top
- reviewer actions card with approve/export and hold actions
- source report card with extracted fields summary
- evidence bundle with variant, phenotype, and pathway/guideline evidence
- uncertainty and limitations card
- compact audit trail / sources strip near the bottom

Responsive intent:
- Tablet may expand by: moving reviewer actions beside or just below the recommendation and splitting source/evidence into clearer vertical groups
- Desktop may expand by: becoming a 3-zone workspace with left source report, center recommendation and evidence, right reviewer controls
- Keep locked across breakpoints: HSIL, Referral support review, Report uploaded, Fields reviewed, Interpretation run, Reviewer decision, Recommendation, Evidence bundle, Reviewer actions, Uncertainty & limitations, Approve & export, Hold for more data

Visual direction:
- calm, clinical, dark neutral workspace with one restrained accent color
- recommendation should visually outrank the source report and audit strip
- use compact rounded cards, clear spacing, and high-contrast but low-drama typography
- make the human review gate obvious without making the page look alarmist

Semantic lock:
- Required nouns: referral support review, recommendation, evidence bundle, reviewer actions, source report, extracted fields
- Preferred discovery words: uncertainty, missing data, audit trail, sources used
- Banned drift words: AI copilot, system prompt, model reasoning, diagnosis, autonomous eligibility, generic genomic report

Pre-approval lock:
- Page title: Referral support review
- Preserve exact labels for: HSIL, Ravi, Owen, Recommendation, Evidence bundle, Reviewer actions, Uncertainty & limitations, Approve & export, Hold for more data, Report uploaded, Fields reviewed, Interpretation run, Reviewer decision

Copy lock:
- Preserve exact approved mobile labels for page title, workflow step labels, section headings, and CTA text
- Layout may adapt at larger breakpoints; wording should not drift

Use this copy:
- HSIL
- Referral support review
- Review one genomic case with grounded evidence
- Upload or load a genomic report, verify extracted fields, review the evidence-backed next step, and finish with clinician approval before export.
- Recommendation
- Supports specialist review in the selected referral lane
- Grounded in the uploaded report, extracted fields, evidence sources, and narrow decision logic. Final action remains clinician-reviewed.
- Evidence bundle
- Variant interpretation, phenotype context, and pathway evidence appear together in one reviewable bundle.
- Reviewer actions
- Confirm key fields, add a note, then approve and export or hold for more data.
- Why this is safe in demo
- Source report · Structured extraction · Evidence trail · Human review gate
- Draft only. No autonomous clinical decision.
- Approve & export
- Hold for more data

Fix these issues:
- do not make the page look like a left-to-right backend pipeline diagram
- do not let the source PDF card visually outweigh the actual recommendation
- do not hide the reviewer action below the fold with weak hierarchy

Do not introduce:
- chatbot or console UI chrome
- KPI analytics dashboard cards or fake metrics
- consumer-genetics report styling or broad wellness framing
