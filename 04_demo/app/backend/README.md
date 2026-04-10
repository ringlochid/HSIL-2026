# Backend

This folder holds the **demo backend**.

## Purpose

The backend should do only what the demo needs:
- accept **genetic/genomic report PDF uploads**
- support both **test** and **patient** report kinds
- run one report or a batch of reports independently
- apply narrow deterministic rules around fixture-backed evidence tools
- support clinician review
- export a final PDF report artifact after review

## Implemented API

- `POST /api/v1/reports/upload`
- `POST /api/v1/reports/{report_id}/run`
- `POST /api/v1/runs/batch`
- `POST /api/v1/reports/{report_id}/review`
- `POST /api/v1/runs/{run_id}/review`
- `POST /api/v1/runs/{run_id}/finalize`
- `GET /api/v1/runs/{run_id}/final.pdf`
- `GET /healthz`

## Current behavior

- **test** reports can use deterministic fixture-backed extraction when no AI key is configured
- **patient** reports fail closed if no real extractor / AI-backed parser is configured
- each report run gets its own `run_id`
- batch runs are grouped with a `batch_id`
- reviewed runs can be exported as a stored PDF artifact

## Testing

- local pytest uses a real SQLite database connection
- docker integration test runs against the live compose stack with Postgres
- AI-backed extraction is skipped when no API key is configured

## Guardrail

Do not let backend complexity outrun the demo.
Patient uploads must never silently fall back to demo fixture extraction.
