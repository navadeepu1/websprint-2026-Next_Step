# NextStep

Offline-first eligibility helper for scholarships, government skilling and jobs, farmer schemes, senior support, and health awareness. NextStep complements official portals such as myScheme and the National Scholarship Portal. It does not replace them.

## Chosen Vertical

Inclusive Citizen Opportunity Discovery

Track: AI and Intelligent Web for Good Ecosystem (AI-WEB ECOS)

## Problem Statement

People who need study support, work, farming help, retirement support, or health information must search many government portals. Eligibility rules are spread out, and a missed answer is often treated like a rejection. NextStep takes a short profile (no ID numbers) and returns what may apply, what is unclear, and what to do next.

## Approach and Logic

Eligibility is evaluated by deterministic rules. Optional AI is not required for
the current workflow; explanations are generated from the rule results. Missing
answers produce `POSSIBLY_ELIGIBLE`, never an automatic rejection.

## How the Solution Works

The application seeds a local SQLite database from `seed/`, accepts a minimal
profile without identity numbers, evaluates matching opportunities, and returns
explanations, documents, official links, and follow-up questions. Health topics
are available as a separate awareness catalogue. The browser test UI is served
by the same FastAPI process.

## Architecture

`app/` contains the FastAPI application, SQLAlchemy models, Pydantic schemas,
eligibility rules, services, and routers. `seed/` contains offline catalogue
data. `ui/` contains the dependency-free browser test UI. `tests/` covers the
rules, APIs, validation, seed loading, plans, and UI shell.

## Setup and Run (works offline)

Python 3.12.

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Test UI

The browser test UI is served by the same FastAPI application. After installing
the dependencies, start the server and open `http://127.0.0.1:8000/`:

```text
uvicorn app.main:app --reload
```

The UI covers the health status check, opportunity catalogue filters and
details, health-topic search and details, eligibility evaluation, and action
plan generation in JSON or Markdown. It uses the API at `/api/v1` and does not
require a separate frontend build step.

## API Reference

Base path: `/api/v1`.

- `GET /health`
- `GET /opportunities`
- `GET /opportunities/{id}`
- `GET /health-topics`
- `GET /health-topics/search?q=...`
- `GET /health-topics/{id}`
- `POST /eligibility/check`
- `POST /plan`
- `POST /plan?format=markdown`

Interactive API documentation is available at `/docs` and `/redoc`.

## Testing

```text
pip install -r requirements-dev.txt
pytest
```

## Security Notes

Profiles are evaluated in memory and are not written to the database or logs.
The API applies validation, CORS configuration, standard error envelopes, and
basic security response headers. Seed records remain unverified until manually
reviewed against their official sources.

## Accessibility Notes

The test UI labels form controls, uses semantic sections and buttons, supports
keyboard-accessible native controls, and includes a responsive phone layout.
Full screen-reader, contrast, and automated browser accessibility testing remain
recommended before production use.

## Assumptions

See `docs/ASSUMPTIONS.md`.

## Milestone status

Completed:

- M0 foundation and configuration
- M1 local database and seed data
- M2 deterministic eligibility engine
- M3 opportunity catalogue API
- M4 health-topic API
- M5 eligibility API
- M6 JSON and Markdown action plans
- M7 template explanations
- M8 browser test UI
- M9 automated baseline tests

Remaining roadmap:

- Implement configured live-data synchronization and `SyncLog` updates.
- Manually verify catalogue rules, documents, URLs, and freshness dates.
- Add optional AI provider adapters with caching and deterministic fallback.
- Add authenticated admin/content-management workflows.
- Add rate limiting, audit logging, and production deployment hardening.
- Add browser end-to-end and automated accessibility coverage.
