# NextStep

Offline-first citizen opportunity discovery for scholarships, jobs, farmer
schemes, senior support, and health awareness.

NextStep helps a person answer:

- What government or public opportunity may fit my situation?
- Why did it match or not match?
- Which answers are still unknown?
- Which documents and official links should I check next?

NextStep is an informational helper. It does not replace an official
government portal, an application decision, or medical advice.

## Default demo login credentials

The local development database seeds these accounts automatically on startup:

| Account | Email | Password |
|---|---|---|
| Demo Citizen | `demo@nextstep.local` | `Demo@12345` |
| Student Demo | `student@nextstep.local` | `Student@12345` |

Use the **Sign in** button in the header. The **Name** field is only shown
when switching to account registration. These credentials are for local
testing only; change or remove them before any production deployment.

## What this project does

NextStep accepts a small profile without identity numbers:

- Age
- Education level
- Occupation
- Annual income
- State or region
- One or more needs
- Optional land ownership
- Optional disability status

It evaluates the profile against locally stored opportunity criteria using
deterministic rules. It returns:

- `ELIGIBLE` opportunities
- `POSSIBLY_ELIGIBLE` opportunities when an answer is missing
- `NOT_ELIGIBLE` opportunities when a confirmed rule fails
- Rule-by-rule reasons
- Required documents
- Official source links
- A plain-language explanation
- A practical action plan

The project also provides:

- A searchable health-awareness catalogue
- A responsive browser test UI
- A FastAPI JSON API
- An interactive “Ask NextStep” website guide chatbot powered by Groq when configured
- SQLite persistence through SQLAlchemy
- Local seed data for offline development
- Optional live catalogue synchronization
- Optional Gemini or Groq explanation rewriting
- Protected admin content-management routes
- Audit logs, request-size limits, rate limiting, and security headers

## Project status

### Implemented

- FastAPI application and API routing
- SQLite database and SQLAlchemy models
- Automatic local database creation
- Seed loading from `seed/opportunities.json` and `seed/health_topics.json`
- Deterministic eligibility engine
- Opportunity catalogue and filters
- Health topics and search
- Eligibility checking
- JSON and Markdown action plans
- Template explanations
- Optional AI adapters with deterministic fallback
- Configured data synchronization with `SyncLog` records
- Admin sync and content-management routes
- Audit logging for admin actions
- Basic rate limiting and request body-size protection
- Browser UI
- API, service, validation, seed, accessibility, and UI tests
- Optional Playwright end-to-end test scaffold

### Still requires human or production review

- Verify every government rule, document list, URL, and freshness date
- Confirm that each source is official and currently active
- Configure a production database and shared rate-limit storage
- Configure HTTPS and a production reverse proxy
- Install Playwright browsers for full browser E2E testing
- Perform full screen-reader and accessibility review
- Establish operational monitoring, backups, and alerting

See [docs/CATALOGUE_VERIFICATION.md](docs/CATALOGUE_VERIFICATION.md) before
marking catalogue records as verified.

## Architecture

```text
Browser UI
    |
    | same-origin HTTP requests
    v
FastAPI application
    |
    +-- routers/
    |     +-- health
    |     +-- opportunities
    |     +-- health topics
    |     +-- eligibility
    |     +-- plans
    |     +-- admin
    |
    +-- services/
    |     +-- deterministic matching
    |     +-- explanations
    |     +-- AI adapters
    |     +-- synchronization
    |     +-- action plans
    |
    +-- SQLAlchemy
          |
          +-- SQLite by default
```

Important directories:

```text
app/                  FastAPI backend
app/eligibility/      Rule engine and eligibility types
app/routers/          API route modules
app/schemas/          Pydantic request and response models
app/services/         Matching, plans, sync, AI, and catalogue services
data/                 Local SQLite database directory
docs/                 Operational and verification documentation
seed/                 Offline JSON catalogue data
tests/                Automated tests
tests/e2e/            Optional browser tests
ui/                   Browser test UI
```

## Requirements

### Required

- Git
- Python 3.12
- Internet access only for installing packages or using configured live-data
  and AI providers

The application itself works offline with the local seed data.

### Runtime libraries

Pinned runtime dependencies are listed in
[requirements.txt](requirements.txt):

- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- SQLAlchemy
- HTTPX
- python-dotenv
- Starlette
- AnyIO
- Greenlet
- supporting typing and HTTP packages

### Development and test libraries

Pinned development dependencies are listed in
[requirements-dev.txt](requirements-dev.txt):

- Pytest
- Pytest coverage
- Respx
- Coverage
- Packaging
- Pluggy
- Iniconfig

The optional Playwright E2E test imports Playwright only when it is installed.
It is not required for the normal backend test suite.

## Clone the repository

Replace the URL with your fork if you are working from a fork.

```powershell
git clone https://github.com/navadeepu1/websprint-2026-Next_Step.git
cd websprint-2026-Next_Step
```

## Deploy on Render

This repository includes a [`render.yaml`](render.yaml) Blueprint. In Render,
choose **New > Blueprint**, connect this repository, and apply the Blueprint.
It creates a Python web service with:

- Uvicorn bound to Render's `$PORT`
- `/api/v1/health` as the health check
- A 1 GB persistent disk mounted at `/var/data`
- SQLite stored at `/var/data/nextstep.db`
- Render-generated values for `AUTH_SECRET` and `ADMIN_API_KEY`

The Blueprint uses Render's Starter plan because persistent disks are not
available on the free web-service plan. Before making the service public,
review the generated admin key and replace the seeded demo credentials, or
remove the demo-user seeding in `app/main.py`. Configure `GROQ_API_KEY` and
set `AI_PROVIDER=groq` only if the optional chatbot is wanted. Set
`CORS_ORIGINS` to the final frontend origin when the UI is hosted separately.

To confirm the checkout:

```powershell
git status
git branch --show-current
```

## Windows setup

The following commands use PowerShell.

### 1. Create a virtual environment

```powershell
py -3.12 -m venv .venv
```

If `py -3.12` is unavailable but `python` points to Python 3.12:

```powershell
python -m venv .venv
```

### 2. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation for the current user, run PowerShell as the
current user and use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Upgrade packaging tools

```powershell
python -m pip install --upgrade pip
```

### 4. Install runtime dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Install development and test dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

## Linux and macOS setup

```bash
git clone https://github.com/navadeepu1/websprint-2026-Next_Step.git
cd websprint-2026-Next_Step
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Configuration

Copy the example environment file:

### Windows

```powershell
Copy-Item .env.example .env
```

### Linux/macOS

```bash
cp .env.example .env
```

The application has safe development defaults. The most important settings
are:

| Variable | Default | Purpose |
|---|---|---|
| `APP_NAME` | `NextStep` | Application title |
| `APP_ENV` | `development` | Environment name |
| `DATABASE_URL` | `sqlite:///data/nextstep.db` | SQLAlchemy database URL |
| `CORS_ORIGINS` | empty | Comma-separated allowed origins |
| `ADMIN_API_KEY` | empty | Required for admin routes |
| `AI_PROVIDER` | `groq` | `noop`, `gemini`, or `groq` |
| `GEMINI_API_KEY` | empty | Gemini API key |
| `GROQ_API_KEY` | empty | Groq API key |
| `GROQ_MODEL` | `openai/gpt-oss-20b` | Groq chat-completion model; verify availability in your Groq account |
| `AI_TIMEOUT_SECONDS` | `15` | AI request timeout |
| `AI_MAX_TOKENS` | `300` | Maximum generated explanation length |
| `AI_TEMPERATURE` | `0` | Generation randomness; `0` is deterministic |
| `AI_CACHE_TTL_SECONDS` | `86400` | Successful AI-cache lifetime; `0` never expires |
| `SYNC_ON_START` | `false` | Sync configured sources at startup |
| `DATA_SOURCE_URLS` | empty | Comma-separated JSON catalogue URLs |
| `ALLOWED_STATES` | All Indian state/UT codes plus `ALL` | Accepted profile state codes; override to restrict a deployment |
| `RATE_LIMIT_PER_MINUTE` | `60` | Per-client in-memory request limit |

For open-ended chatbot answers, configure Groq before starting the server:

```powershell
Copy-Item .env.example .env
notepad .env
# Set AI_PROVIDER=groq and GROQ_API_KEY=your-key
python -m uvicorn app.main:app --reload
```

Restart Uvicorn after changing `.env`; settings are loaded when the process
starts. If the chatbot header says “Offline help mode”, the server did not
load a Groq provider/key and will intentionally return only built-in help
responses.

Never put a real key in `.env.example`, README files, screenshots, or chat
messages. The key previously pasted into `.env.example` must be revoked in the
Groq console and replaced with a new key stored only in the ignored local
`.env` file.
| `REQUEST_BODY_LIMIT_BYTES` | `32768` | Maximum request body size |
| `SYNC_TIMEOUT_SECONDS` | `15` | Live-source request timeout |
| `AUDIT_LOG_RETENTION_DAYS` | `365` | Intended audit retention policy |

Never commit `.env`, API keys, or other credentials.

## Run the application locally

From the repository root, with the virtual environment activated:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Linux/macOS:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open the browser UI:

```text
http://127.0.0.1:8000/
```

The database and seed records are created automatically during application
startup. No migration command is required for a fresh local SQLite database.

### Run on another local device

To listen on all network interfaces:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open `http://YOUR-COMPUTER-IP:8000/` from the other device. Only do this
on a trusted network and configure CORS/authentication appropriately.

### Stop the server

Press `Ctrl+C` in the terminal running Uvicorn.

## API documentation

When the server is running:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

## API endpoints

All API routes use the `/api/v1` prefix.

### Health

```text
GET /api/v1/health
```

### Opportunities

```text
GET /api/v1/opportunities
GET /api/v1/opportunities/{opportunity_id}
```

Supported list query parameters:

- `category`
- `verified`
- `active`
- `limit`
- `offset`

Example:

```powershell
curl.exe "http://127.0.0.1:8000/api/v1/opportunities?category=job&active=true&limit=20"
```

### Health topics

```text
GET /api/v1/health-topics
GET /api/v1/health-topics/search?q=heat
GET /api/v1/health-topics/{topic_id}
```

### Eligibility

```text
POST /api/v1/eligibility/check
```

Example request:

```powershell
$profile = @{
  age = 20
  education_level = "undergraduate"
  occupation = "student"
  annual_income = 50000
  state = "PB"
  need = @("study", "work")
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/eligibility/check" `
  -Method Post `
  -ContentType "application/json" `
  -Body $profile
```

### Action plans

JSON:

```text
POST /api/v1/plan
```

Markdown:

```text
POST /api/v1/plan?format=markdown
```

Both endpoints accept the same profile body as the eligibility endpoint.

### Website chatbot

The browser UI includes an **Ask NextStep** chatbot in the lower-right corner.
It accepts free-text questions, not just the suggested prompts. With Groq
configured, it can answer general questions, explain concepts, help draft or
rewrite text, and explain how to use this website. For NextStep questions it
can describe eligibility checks, opportunities, health topics, action plans,
API documentation, and official catalogue links. It is not a replacement for
the eligibility endpoint, professional advice, or an official application
decision.

The API endpoint is:

```text
POST /api/v1/chat
```

## Live-data synchronization

Live synchronization is optional. The application remains usable with local
seed data and no configured source URLs.

### Supported source formats

A source URL may return either:

```json
[
  {
    "id": "example-job",
    "title": "Example job",
    "category": "job",
    "description": "Example description",
    "criteria": {"needs": ["work"]},
    "documents": [],
    "official_url": "https://example.gov/apply",
    "verified": false,
    "active": true
  }
]
```

or:

```json
{
  "opportunities": [],
  "health_topics": []
}
```

Invalid records are rejected individually. Successful and failed runs are
recorded in the `sync_logs` table. Synchronization does not automatically mark
records as verified.

### Configure sources

In `.env`:

```text
DATA_SOURCE_URLS=https://example.gov/catalogue.json,https://example.gov/health.json
SYNC_TIMEOUT_SECONDS=15
```

### Run sync at application startup

```text
SYNC_ON_START=true
```

### Trigger sync manually

Set an admin key first:

```text
ADMIN_API_KEY=replace-with-a-long-random-secret
```

Then call:

```powershell
curl.exe -X POST `
  "http://127.0.0.1:8000/api/v1/admin/sync" `
  -H "X-Admin-Api-Key: replace-with-a-long-random-secret"
```

## Admin content-management API

Admin routes require the `X-Admin-Api-Key` header and are disabled when
`ADMIN_API_KEY` is empty.

Available routes:

```text
POST   /api/v1/admin/sync
PUT    /api/v1/admin/opportunities/{id}
DELETE /api/v1/admin/opportunities/{id}
PUT    /api/v1/admin/health-topics/{id}
```

Admin changes and sync actions create rows in `audit_logs`.

For production, use a proper secret manager, HTTPS, role-based permissions,
and a shared audit/rate-limit store rather than relying only on a single
development API key and in-memory limiter.

## Groq AI explanation workflow

For the complete setup and usage guide, see
[docs/AI_USAGE.md](docs/AI_USAGE.md).

The application always calculates eligibility with deterministic Python rules.
Groq is used only after those rules finish, to rewrite an already-generated
explanation in simpler, respectful language. Groq cannot add opportunities,
change statuses, invent documents, or override a rule result.

The workflow is:

```text
Profile request
    -> deterministic eligibility engine
    -> template explanation
    -> optional Groq rewrite
    -> response with explanation_source = "ai" or "template"
```

Groq is used in both:

- `POST /api/v1/eligibility/check`
- `POST /api/v1/plan`
- `POST /api/v1/chat`

The chatbot sends the current question and at most eight recent messages to
the server. The Groq key remains server-side and is never exposed to the
browser.

The health endpoint reports the active provider, selected model, and whether
the provider key is configured:

```text
GET /api/v1/health
```

The response includes fields similar to:

```json
{
  "ai_provider": "groq",
  "ai_configured": true,
  "ai_model": "openai/gpt-oss-20b"
}
```

### Enable Groq locally

Put the key in your local `.env` file only. Do not put it in `.env.example`,
README files, source code, screenshots, or commits:

```text
AI_PROVIDER=groq
GROQ_API_KEY=your-new-groq-key
GROQ_MODEL=openai/gpt-oss-20b
AI_TIMEOUT_SECONDS=15
AI_MAX_TOKENS=300
AI_TEMPERATURE=0
AI_CACHE_TTL_SECONDS=86400
```

Restart Uvicorn after changing `.env` because settings are loaded when the
application starts:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify configuration without exposing the key:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health |
  Select-Object ai_provider, ai_configured, ai_model
```

If `ai_configured` is `false`, check that `AI_PROVIDER=groq` is present and
that `GROQ_API_KEY` is set in the same environment used to launch Uvicorn.

### Groq request behavior

The application sends a request to Groq's OpenAI-compatible endpoint with:

- `Authorization: Bearer <key>`
- The configured `GROQ_MODEL`
- A protected system instruction
- The deterministic explanation as the user message
- `AI_TEMPERATURE`
- `AI_MAX_TOKENS`
- `AI_TIMEOUT_SECONDS`

Only the generated text is returned. The secret key is never included in an
API response, database cache value, audit record, or application log.

### Cache and fallback behavior

Successful responses are stored in the `ai_cache` table using a SHA-256 key
derived from the provider, model, and prompt. The API key itself is never part
of the cache key. Repeated identical requests within
`AI_CACHE_TTL_SECONDS` reuse the cached result and do not call Groq again.

The deterministic template is returned when:

- `AI_PROVIDER=noop`
- `GROQ_API_KEY` is empty
- Groq returns an HTTP error
- The request times out
- Groq returns malformed or empty content
- The configured provider is unsupported

In all fallback cases the API remains functional and returns
`explanation_source: "template"`.

The default provider is deterministic template output:

```text
AI_PROVIDER=noop
```

To enable Gemini:

```text
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

To enable Groq:

```text
AI_PROVIDER=groq
GROQ_API_KEY=your-key
```

Never use a key that has been pasted into a public file or chat. Revoke
exposed keys in the Groq console and create a replacement.

## Run the test suite

Run all standard tests:

```powershell
pytest
```

Equivalent explicit command:

```powershell
python -m pytest
```

The suite covers:

- Eligibility rules
- Eligibility API
- Opportunity API
- Health-topic API
- Action plans
- Input validation
- Seed loading
- Synchronization and `SyncLog`
- Admin authentication and content updates
- AI fallback behavior
- UI shell delivery
- Basic UI accessibility structure

### Coverage

```powershell
pytest --cov=app --cov-report=term-missing
```

### Python compilation check

```powershell
python -m compileall -q app tests
```

### JavaScript syntax check

If Node.js is installed:

```powershell
node --check ui\app.js
```

## Optional browser end-to-end testing

The browser test is in
[tests/e2e/test_ui_playwright.py](tests/e2e/test_ui_playwright.py).

Install Playwright:

```powershell
python -m pip install playwright
python -m playwright install chromium
```

Start the application in another terminal:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run the browser test:

```powershell
pytest -m e2e tests/e2e
```

Use another server URL if needed:

```powershell
$env:NEXTSTEP_BASE_URL = "http://127.0.0.1:8000/"
pytest -m e2e tests/e2e
```

The normal `pytest` command skips this optional test if Playwright is not
installed.

## Database and local data

Default database:

```text
data/nextstep.db
```

The application creates the `data` directory and tables automatically.

Seed files:

- `seed/opportunities.json`
- `seed/health_topics.json`

To use a different SQLite file for a test or local run:

```powershell
$env:DATABASE_URL = "sqlite:///data/nextstep-local.db"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

To use another SQLAlchemy-compatible database, set `DATABASE_URL` to the
appropriate SQLAlchemy URL and verify the deployment database behavior before
production use.

## Security and privacy

Current protections include:

- Pydantic request validation
- Standardized JSON error envelopes
- Security response headers
- Configurable CORS
- Request body-size limit
- Per-client development rate limiting
- Admin API-key protection
- Admin audit records
- No profile persistence
- Deterministic eligibility decisions
- AI fallback to templates

Important production responsibilities:

- Do not use a weak or shared admin key.
- Do not expose the development server directly to the public internet.
- Put the application behind HTTPS and a reverse proxy.
- Use a shared rate limiter for multiple application instances.
- Rotate credentials and store them outside source control.
- Back up the database.
- Review all catalogue records against official sources.
- Keep health content informational and medically responsible.

## Troubleshooting

### `python` or `py` is not recognized

Install Python 3.12 and ensure the Python Launcher or Python executable is on
PATH. Then recreate the virtual environment.

### `pytest` is not recognized

Activate `.venv` and install development dependencies:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pytest
```

### Port 8000 is already in use

Use another port:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Then open `http://127.0.0.1:8001/`.

### The UI loads but shows `API unavailable`

Confirm that the browser URL and server URL use the same host and port. Then
check:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/api/v1/health
```

### Admin returns `401`

Confirm that `ADMIN_API_KEY` is set in the environment used to launch Uvicorn
and that the request header is exactly:

```text
X-Admin-Api-Key: <same configured value>
```

Restart the server after changing `.env`.

### Synchronization rejects records

Check the source JSON against the schemas in
[app/schemas/opportunity.py](app/schemas/opportunity.py) and
[app/schemas/health.py](app/schemas/health.py). Inspect the `sync_logs` table
and correct invalid fields, categories, URLs, or timestamps.

## Useful commands

Install everything needed for normal development:

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Run the app:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Run tests:

```powershell
python -m pytest
```

Check syntax and patch formatting:

```powershell
python -m compileall -q app tests
git diff --check
```

Check repository status:

```powershell
git status --short
```

## License and external sources

Review the repository's license and attribution requirements before
redistributing the project or catalogue data. Government portal URLs and
content remain subject to their own terms and should be manually verified.
