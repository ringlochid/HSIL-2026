# Backend

This folder holds the **demo backend**.

## Purpose

The backend should do only what the demo needs:
- accept a **genetic/genomic report PDF upload**
- extract usable structured data from that report
- call tool wrappers / evidence adapters
- apply narrow decision rules
- produce a clinician-reviewable draft
- return a final review-ready output

## Recommended ownership

- `app/api/routes/` — FastAPI endpoints
- `app/agents/` — thin LangChain layer for report extraction, limited tool use, and draft wording
- `app/tools/` — API adapters such as Franklin, Ensembl VEP, SpliceAI, and ClinVar
- `app/services/` — ingestion, workflow, and draft assembly logic
- `app/rules/` — deterministic disease/referral rules
- `app/schemas/` — minimal Pydantic request/response models
- `app/fixtures/` — fixture responses and example payloads
- `tests/` — backend tests for upload, run flow, review, and fallback coverage

## Guardrail

Do not let backend complexity outrun the demo.
Use LangChain as the standard LLM/tool layer, but keep the decision logic readable and mostly deterministic.

## File-level plan

See `IMPLEMENTATION_PLAN.md` for the full file-by-file backend build plan (including env/settings, requirements, Dockerfile, and docker-compose).
