# Backend

This folder holds the **demo backend**.

## Purpose

The backend should do only what the demo needs:
- intake a case
- call tool wrappers / evidence adapters
- apply narrow decision rules
- produce a clinician-reviewable draft
- return a final review-ready output

## Recommended ownership

- `app/api/routes/` — FastAPI endpoints
- `app/agents/` — optional LangChain `create_agent(...)` wrappers for tool orchestration / explanation
- `app/tools/` — API adapters such as Franklin, Ensembl VEP, ClinVar
- `app/services/` — orchestration logic / draft assembly
- `app/rules/` — deterministic disease/referral rules
- `app/schemas/` — Pydantic request/response models
- `app/fixtures/` — fixture responses and example payloads
- `tests/` — backend tests for happy path + fallback cases

## Guardrail

Do not let backend complexity outrun the demo.
The decision logic should stay readable and mostly deterministic.
