# NextStep

Offline-first eligibility helper for scholarships, government skilling and jobs, farmer schemes, senior support, and health awareness. NextStep complements official portals such as myScheme and the National Scholarship Portal. It does not replace them.

## Chosen Vertical

Inclusive Citizen Opportunity Discovery

Track: AI and Intelligent Web for Good Ecosystem (AI-WEB ECOS)

## Problem Statement

People who need study support, work, farming help, retirement support, or health information must search many government portals. Eligibility rules are spread out, and a missed answer is often treated like a rejection. NextStep takes a short profile (no ID numbers) and returns what may apply, what is unclear, and what to do next.

## Approach and Logic

_To be completed in later milestones._ Code decides eligibility. Optional AI only rephrases explanations. Missing answers produce possibly eligible, never an automatic no.

## How the Solution Works

_To be completed in later milestones._

## Architecture

_To be completed in later milestones._

## Setup and Run (works offline)

Python 3.12.

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Application startup and API commands will be added in later milestones.

## API Reference

_To be completed in later milestones._ Base path: `/api/v1`.

## Testing

```text
pip install -r requirements-dev.txt
pytest
```

## Security Notes

_To be completed in later milestones._

## Accessibility Notes

The backend is JSON-only in this phase. A later test UI (not built until requested) must label every input, support keyboard use, and work at phone width.

## Assumptions

See `docs/ASSUMPTIONS.md`.

## Limitations

Scaffold only (milestone M0). Eligibility engine, APIs, sync, and full tests are not present yet.

## Future Work

Complete milestones M1–M9 of the backend. Do not add a UI until explicitly requested.
