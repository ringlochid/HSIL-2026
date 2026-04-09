# Solution Brief

## Vision

Build a tight clinician workflow tool where the user inputs a small set of case signals and gets:

- a structured interpretation draft,
- evidence-linked rationale,
- a review/edit step before finalizing output.

## MVP definition

- Single-page workflow with one canonical path
- Data input panel (manual + deterministic sample mode)
- Variant/context interpretation summary (rule + retrieval backed, not generative first)
- Recommendation card + action suggestions + confidence caveat
- Explicit human review gate before final copy

## Non-goals (MVP)

- Replacing a specialist
- Clinical diagnosis automation
- Direct treatment/medication prescribing
- Universal healthcare pathway claim across specialties

## Technical direction (starter)

- Frontend: lightweight web app
- Backend: API layer with strict schema validation
- Data: deterministic demo fixtures first, then optional external lookups behind clear guardrails

## Risk controls

- Do not overclaim automation
- Preserve uncertainty + missing-data warnings
- Keep logs/audit trail for each generated draft
