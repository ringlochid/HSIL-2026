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

## Implemented API

- `POST /api/v1/reports/upload`
- `POST /api/v1/reports/{report_id}/run`
- `POST /api/v1/reports/{report_id}/review`
- `GET /healthz`

## Implemented shape

- thin FastAPI app
- real SQLAlchemy-backed persistence
- docker compose stack with Postgres
- thin LangChain layer that is **skipped** when no API key is configured
- fixture-backed evidence tools for the demo lane
- hardcoded stable request mapping for the RPE65 demo case
- deterministic review-required draft generation

## Testing

- local pytest uses a real SQLite database connection
- docker integration test can run against the live compose stack when the container is up

## Guardrail

Do not let backend complexity outrun the demo.
Use LangChain only when an API key is actually present, and keep the decision logic readable and mostly deterministic.

## File-level plan

See `IMPLEMENTATION_PLAN.md` for the current implementation-aligned plan.
