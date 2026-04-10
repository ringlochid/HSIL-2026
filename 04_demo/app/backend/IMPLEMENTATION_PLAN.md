# Backend Implementation Plan (file-to-file)

## Goal
Build a minimal but production-shaped backend for the HSIL demo using:
- FastAPI
- a **report-upload-first** workflow
- LangChain as the standard LLM/tool layer
- deterministic decision rules
- fixture-first fallbacks

Current demo constraint: **one disease/referral lane at a time**, with robust fallback behavior.
The primary input is an uploaded **genetic/genomic report PDF**, which is then turned into structured data for the rest of the workflow.

---

## Intake meaning in this project

`intake` means:
1. user uploads a **genetic/genomic report PDF**,
2. backend stores the file + metadata,
3. backend extracts text / relevant sections,
4. LangChain turns report text into structured fields,
5. only then do evidence tools and deterministic rules run.

So in this app, **intake is report ingestion**, not manual form-first case entry.

---

## Folder bootstrap (create now)

```text
04_demo/app/backend/
├── .env.example
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── README.md
├── IMPLEMENTATION_PLAN.md
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── logging.py
│   │   └── deps.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── reports.py
│   │       ├── runs.py
│   │       ├── reviews.py
│   │       └── health.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── report.py
│   │   ├── run.py
│   │   └── draft.py
│   ├── repos/
│   │   ├── __init__.py
│   │   ├── reports_repo.py
│   │   └── run_repo.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── report_pdf.py
│   │   ├── franklin.py
│   │   ├── ensembl_vep.py
│   │   ├── spliceai.py
│   │   ├── clinvar.py
│   │   └── registry.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── intake.py
│   │   ├── workflow.py
│   │   ├── recommendation.py
│   │   └── draft_render.py
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── clinic_rules.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── tools.py
│   │   └── prompts.py
│   ├── fixtures/
│   │   ├── reports/
│   │   │   ├── ravi.pdf
│   │   │   └── ravi_extracted.json
│   │   └── tools/
│   │       ├── vep_fixtures.json
│   │       ├── spliceai_fixtures.json
│   │       ├── clinvar_fixtures.json
│   │       └── franklin_fixtures.json
│   └── tests/
│       ├── conftest.py
│       ├── test_report_api.py
│       ├── test_run_flow.py
│       ├── test_review_api.py
│       └── test_docker_integration.py
```

---

## 1) Environment + settings

### `.env.example`
Create and commit this file.

Suggested keys:
- `ENV=dev`
- `APP_NAME=hsil-demo-backend`
- `HOST=0.0.0.0`
- `PORT=8000`
- `DEBUG=true`
- `API_PREFIX=/api/v1`
- `ALLOWED_ORIGINS=http://localhost:5173`

Upload / ingestion:
- `UPLOAD_DIR=./data/uploads`
- `MAX_UPLOAD_MB=20`

LLM / LangChain:
- `OPENAI_API_KEY=`
- `LLM_PROVIDER=openai|mock`
- `LANGCHAIN_API_KEY=`
- `LANGCHAIN_TRACING_V2=false`

External APIs:
- `USE_REAL_APIS=false`
- `VEP_BASE_URL=https://rest.ensembl.org`
- `SPLICEAI_BASE_URL=https://spliceai-38-xwkwwwxdwq-uc.a.run.app/spliceai/`
- `CLINVAR_BASE_URL=https://eutils.ncbi.nlm.nih.gov/entrez/eutils`
- `FRANKLIN_BASE_URL=https://api.genoox.com`

State:
- `DATABASE_URL=sqlite+pysqlite:///./data/app.db`

### `.env`
Create locally only. Do not commit.
Use it for real API keys and local overrides.

### `app/core/config.py`
Responsibilities:
- define `Settings` via `pydantic-settings`
- validate upload limits and URLs
- expose `get_settings()` singleton
- centralize LangChain/OpenAI/API toggle config

---

## 2) Project plumbing

### `requirements.txt`
At minimum:
- `fastapi`
- `uvicorn[standard]`
- `python-multipart`
- `pydantic>=2`
- `pydantic-settings`
- `httpx`
- `python-dotenv`
- `langchain`
- `langchain-openai`
- `langchain-community`
- `pypdf`
- `pytest`
- `pytest-asyncio`
- `orjson`
- `SQLAlchemy`
- `psycopg[binary]`

Optional later:
- `pymupdf` if PDF extraction quality becomes an issue
- `ruff`
- `black`

### `pyproject.toml`
Use for:
- tool config (`ruff`, `black`, `pytest`)
- optional package metadata
- cleaner local dev config than scattering tool files

### `Dockerfile`
Use a simple Python image:
- base: `python:3.12-slim`
- install dependencies from `requirements.txt`
- copy project files
- start with `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### `docker-compose.yml`
Use a two-service stack:
- `db` = Postgres for real persistence
- `backend` = FastAPI app connected via `DATABASE_URL`
- mount env file
- expose backend on port 8000
- mount upload directory if needed
- wait for Postgres health before backend boot

### `.dockerignore`
Ignore at minimum:
- `.env`
- `__pycache__`
- `.pytest_cache`
- `.ruff_cache`
- `.venv`
- `node_modules`
- `.git`

### `app/main.py`
Responsibilities:
- create FastAPI app
- add CORS
- register routers
- expose `/healthz`
- add startup log

### `app/core/logging.py`
- structured logger helper
- attach run/report IDs when available

### `app/core/deps.py`
- dependency providers for settings, repositories, and services

---

## 3) API contracts first

**Schema rule:** keep **3 schema files total** for MVP.
Do not add extra schema modules unless the real code forces it later.

### `app/schemas/report.py`
Use for upload/report metadata **and extracted report content**.

Keep this file minimal.
Suggested models:
- `UploadedReport`
- `ReportUploadResponse`
- `ExtractedCase`
- `ExtractedVariant`
- `ExtractionIssue`

### `app/schemas/run.py`
Use for run request/response **and compact evidence summaries**.

Keep this file minimal.
Suggested models:
- `RunRequest`
- `RunStatus`
- `EvidenceSourceSummary`
- `RunResponse`

### `app/schemas/draft.py`
Keep this file minimal.
Suggested models:
- `DraftPayload`
- `ClinicianReviewPayload`
- `ReviewResult`

**Dropped on purpose:**
- no separate `extracted_case.py`
- no separate `evidence.py`
- no generic API wrapper schema file

## 4) Repository / state layer

### `app/core/db.py`
Responsibilities:
- build SQLAlchemy engine + session factory
- define DB tables for reports and runs
- initialize tables on app startup/import path
- expose a simple DB health ping

### `app/repos/reports_repo.py`
Store uploaded report records in the real database.
Responsibilities:
- save file metadata
- save extraction result snapshot
- retrieve report by `report_id`
- save/retrieve review payloads

### `app/repos/run_repo.py`
Store run lifecycle in the real database.
Responsibilities:
- create run
- append run events
- persist latest run response
- get run by `report_id`

Tests should use a real DB connection as well:
- local pytest -> SQLite database file
- docker integration -> Postgres container

---

## 5) Tools layer

### `app/tools/base.py`
Common tool contracts.
Suggested types:
- `ToolResult`
- `ToolError`
- `ToolContext`

### `app/tools/report_pdf.py`
Responsibilities:
- accept uploaded PDF path
- load pages/text
- return raw extracted text and per-page metadata
- fallback cleanly if the PDF is partially unreadable

### `app/tools/franklin.py`
Responsibilities:
- parse/search variant text
- normalize vendor response into internal schema
- use fixtures when live APIs are off

### `app/tools/ensembl_vep.py`
Responsibilities:
- annotate variant with transcript/consequence data
- normalize to internal evidence schema
- fallback to fixtures

### `app/tools/spliceai.py`
Responsibilities:
- query splice-impact predictions for candidate variants
- normalize SpliceAI delta scores / positions into compact evidence
- fallback to fixtures
- always set `distance` and `mask` explicitly

### `app/tools/clinvar.py`
Responsibilities:
- fetch ClinVar evidence
- normalize classification, review status, disease traits
- fallback to fixtures

### `app/tools/registry.py`
Responsibilities:
- define the LangChain-visible tool registry
- map tool names to local callables
- keep tool descriptions short and precise

### Demo-case hardcoded request mapping (`RPE65 c.260A>G`)
For the first demo lane, the tool layer can hardcode the stable request inputs instead of trying to infer everything from scratch on every run.

- **ClinVar**
  - search-once form:
    - `GET /entrez/eutils/esearch.fcgi?db=clinvar&term=RPE65[gene] AND c.260A>G&retmode=json&retmax=1`
  - stable fetch for tool use:
    - `clinvar_id = 1421454`
    - call `esummary` directly with that id

- **Ensembl VEP**
  - hardcoded HGVS input:
    - `NM_000329.3:c.260A>G`
  - fetch via:
    - `GET /vep/human/hgvs/NM_000329.3:c.260A>G?content-type=application/json`
  - canonical filter in tool:
    - `gene_symbol == RPE65`
    - `cds_start == 260`
    - `protein_start == 87`

- **Franklin**
  - hardcoded search text:
    - `RPE65:c.260A>G`
  - optional normalization:
    - `POST https://franklin.genoox.com/api/parse_search`
  - interpretation search:
    - `GET https://api.genoox.com/v2/search/snp/?search_text=RPE65:c.260A%3EG`
    - requires auth

- **SpliceAI**
  - use the normalized genomic hg38 form, not the transcript HGVS string
  - hardcoded request values:
    - `hg = 38`
    - `variant = chr1-68444869-T-C`
    - `distance = 500`
    - `mask = 0`

Important normalization rule:
`RPE65` is on the minus strand, so transcript `c.260A>G` maps to genomic `T>C` on GRCh38 for tools like SpliceAI.

---

## 6) Rules + workflow

### `app/rules/base.py`
Define deterministic rule contracts.
Suggested types:
- `DecisionInput`
- `DecisionOutput`
- `DecisionRule`

### `app/rules/clinic_rules.py`
Main narrow-lane rule file.
Responsibilities:
- map extracted case + evidence -> recommendation band
- enforce fail-closed behavior when evidence is insufficient
- compute missing info flags

### `app/services/intake.py`
Responsibilities:
1. accept uploaded file
2. save it
3. call `report_pdf.py`
4. call LangChain extraction prompt
5. persist extracted structured case
6. emit extraction warnings

### `app/services/workflow.py`
Use a **fixed linear workflow**, not a graph/orchestration runtime.

Responsibilities:
1. load extracted case from uploaded report
2. normalize/parse variant
3. collect evidence from tools (VEP / SpliceAI / ClinVar / Franklin as enabled)
4. combine evidence
5. apply deterministic rules
6. compute confidence + missing fields

### `app/services/recommendation.py`
Responsibilities:
- turn workflow output into structured draft content
- build evidence summary blocks
- prepare final recommendation object

### `app/services/draft_render.py`
Responsibilities:
- use LangChain to produce clinician-friendly wording
- fallback to deterministic templates if LLM call fails

---

## 7) LangChain layer (optional at runtime, thin when enabled)

LangChain is the standard LLM/tool layer **when an API key is configured**.
If no API-backed model is configured, skip the AI layer and use deterministic / fixture-backed paths.

What it should do when enabled:
- report text -> structured extraction
- evidence summarization
- clinician-friendly draft wording
- limited tool calling where it clearly helps

What it should **not** own:
- final referral rule branching
- fail-closed safety logic
- core recommendation thresholds
- a larger orchestration runtime

### `app/agents/client.py`
- build the LangChain chat model client
- choose provider based on settings

### `app/agents/tools.py`
- wrap local tool functions for LangChain use
- expose only the small tool set we actually need

### `app/agents/prompts.py`
Create concise prompt builders for:
- report extraction
- evidence summarization
- draft rendering

### `app/agents/__init__.py`
Expose helpers like:
- `build_extraction_chain(settings)`
- `build_draft_chain(settings)`
- `build_tool_enabled_llm(settings)`

---

## 8) API routes

### `app/api/routes/reports.py`
Recommended endpoints:
- `POST /api/v1/reports/upload`

### `app/api/routes/runs.py`
Recommended endpoints:
- `POST /api/v1/reports/{report_id}/run`

### `app/api/routes/reviews.py`
Recommended endpoints:
- `POST /api/v1/reports/{report_id}/review`

### `app/api/routes/health.py`
Recommended endpoints:
- `GET /healthz`

---

## 9) Test plan

### `tests/conftest.py`
- app fixture
- test client
- real SQLite DB connection per test run
- override settings to fixture mode for external APIs

### `tests/test_report_api.py`
- upload report returns a report id
- upload response includes initial extraction status + summary
- reject invalid file types / oversize payloads

### `tests/test_run_flow.py`
- uploaded fixture PDF and `POST /run` returns deterministic draft payload
- run path from parsing -> evidence -> rules remains testable
- tool fallback behavior is covered here instead of a separate test module
- verify warning / degraded-evidence state stays visible in the run response

### `tests/test_review_api.py`
- review payload accepted
- edited draft stored correctly
- review cannot silently erase required draft fields

### `tests/test_docker_integration.py`
- skip unless docker stack URL is provided
- call live backend container over HTTP
- verify `/healthz` includes database OK
- upload -> run -> review against the live Postgres-backed stack

---

## 10) Containerization / boot

### `Dockerfile`
Keep it simple.
Needed behavior:
- install Python deps
- copy source
- expose port 8000
- run uvicorn

### `docker-compose.yml`
Needed behavior:
- start Postgres and backend together
- use `.env`
- backend uses `DATABASE_URL` pointed at Postgres
- mount upload directory if useful
- keep backend on internal port `8000`

### Local boot flow
Target commands:
- `cp .env.example .env`
- `docker compose up --build`
- optional docker-stack integration test (containerized execution):
  - `docker compose exec backend env HSIL_DOCKER_BASE_URL=http://localhost:8000 pytest -q tests/test_docker_integration.py`
- if you expose backend port explicitly on host, you can alternatively:
  - `HSIL_DOCKER_BASE_URL=http://localhost:<host_port> pytest -q tests/test_docker_integration.py`

Optional local non-Docker boot:
- `python -m venv .venv`
- `pip install -r requirements.txt`
- `uvicorn app.main:app --reload`

---

## 11) Suggested implementation order (1st sprint)

### Phase A
1. `.env.example`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`
2. `config.py`, `db.py`, `main.py`, logging, deps
3. upload/report schemas + DB-backed repos
4. `reports/upload` API

### Phase B
5. PDF loading tool + fixture PDF
6. LangChain extraction chain
7. run workflow skeleton
8. run endpoint implementation

### Phase C
9. VEP / SpliceAI / ClinVar / Franklin fixture-backed tools
10. deterministic rules
11. draft rendering
12. review endpoint

### Phase D
13. tests (real SQLite DB + docker integration coverage)
14. small frontend contract sync
15. optional live API toggle after golden path is stable

---

## 12) Acceptance criteria

- `POST /api/v1/reports/upload` accepts a sample report PDF
- `POST /api/v1/reports/{id}/run` completes in local fixture mode within 5s
- run response returns structured sections + confidence + limitations + next step
- review endpoint stores reviewer edits
- tool failures do not break the golden path
- local pytest uses a real DB connection
- docker integration test passes when the compose stack is up
- one command boots backend successfully

---

## 13) Implementation status (applied)

Completed in this pass:
1. infra files: `.env.example`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`
2. core files: `app/main.py`, `app/core/*`
3. schemas + repos (**3 schema files only**)
4. report upload route + fixture PDF pathing
5. LangChain extraction layer that auto-skips when no API-backed model is configured
6. workflow + draft + review routes
7. tests + fixtures
8. shared contracts sync via `app/shared/contracts/backend-api.json`

## 14) Verification status

- ✅ local tests pass: `pytest`
- ✅ local pytest uses a real SQLite DB connection
- ✅ endpoints exercised: upload/run/review + health
- ✅ fallback coverage inside run-flow test
- ✅ docker integration test file added for compose-stack verification
- ✅ tool mapping keeps only confirmed parameters in query strings
- ✅ implementation plan/docs aligned to current route set

