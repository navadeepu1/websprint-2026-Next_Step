# NextStep AI usage guide

This guide explains how to enable, verify, use, and troubleshoot the optional
AI explanation workflow.

## What AI does in NextStep

NextStep does **not** use AI to decide eligibility. Eligibility is calculated
by the deterministic rule engine first. AI can only rewrite that existing
explanation in clearer language.

```text
Profile
  -> deterministic rules
  -> eligibility results and template explanation
  -> optional AI rewrite
  -> API response
```

AI cannot:

- change `ELIGIBLE`, `POSSIBLY_ELIGIBLE`, or `NOT_ELIGIBLE`
- add or remove opportunities
- invent criteria, documents, links, or guarantees
- make medical diagnoses or provide treatment advice
- replace an official application decision

## Providers

| Provider | Configuration | Behavior |
|---|---|---|
| Template | `AI_PROVIDER=noop` | Offline, deterministic, no API key |
| Groq | `AI_PROVIDER=groq` | Optional hosted rewrite using Groq |
| Gemini | `AI_PROVIDER=gemini` | Optional hosted rewrite using Gemini |

For this project, Groq is the recommended hosted provider workflow.

## Enable Groq

1. Create or rotate a Groq API key in the Groq console.
2. Copy `.env.example` to `.env` if you have not already done so.
3. Set these values in `.env`:

```text
AI_PROVIDER=groq
GROQ_API_KEY=your-groq-key
GROQ_MODEL=openai/gpt-oss-20b
AI_TIMEOUT_SECONDS=15
AI_MAX_TOKENS=300
AI_TEMPERATURE=0
AI_CACHE_TTL_SECONDS=86400
```

4. Restart the application:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Never put a real key in `.env.example`, README files, source code, tests,
screenshots, commits, or chat messages. The `.env` file must remain local and
must not be committed.

## Verify the configuration

Use the health endpoint:

```powershell
$health = Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
$health | Select-Object ai_provider, ai_configured, ai_model
```

Expected output:

```text
ai_provider   ai_configured   ai_model
------------  --------------  ----------------------
groq          True            openai/gpt-oss-20b
```

The endpoint reports configuration state only. It never returns the API key.
`ai_configured: true` confirms that a key is present; it does not guarantee
that the key has quota or that a provider request will succeed.

## Use AI through the API

AI is automatically attempted by these endpoints:

```text
POST /api/v1/eligibility/check
POST /api/v1/plan
POST /api/v1/plan?format=markdown
```

The browser UI also includes an **Ask NextStep** chatbot. It accepts any
free-text question and uses Groq for general conversation, explanations,
brainstorming, short drafting or rewriting tasks, and questions about the
website. For example, it can explain where to find an eligibility check, how
to browse opportunity records, where official links appear, or how to open
the API docs:

```text
POST /api/v1/chat
```

Example request:

```json
{
  "message": "Where can I see official links?",
  "history": [
    {"role": "user", "content": "How does this website work?"},
    {"role": "assistant", "content": "NextStep helps you discover opportunities."}
  ]
}
```

Example response:

```json
{
  "reply": "Open Opportunities and select a record to see its official source.",
  "source": "ai",
  "provider": "groq"
}
```

The server limits each message to 1,200 characters and keeps at most eight
recent messages. It supplies fixed NextStep website context to Groq without
restricting the user to predefined options. If Groq is not configured or
unavailable, common website questions use a deterministic built-in guide and
return `"source": "template"`; general open-ended questions require Groq to
be configured.

The request body is the normal NextStep profile. Example:

```powershell
$profile = @{
  age = 20
  education_level = "undergraduate"
  occupation = "student"
  annual_income = 50000
  state = "PB"
  need = @("study", "work")
} | ConvertTo-Json

$result = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/eligibility/check" `
  -Method Post `
  -ContentType "application/json" `
  -Body $profile

$result.explanation
$result.explanation_source
```

When Groq succeeds:

```text
explanation_source = ai
```

When template mode is active or Groq fails safely:

```text
explanation_source = template
```

The browser UI uses the same endpoints automatically. No separate frontend
configuration is required.

## How the Groq request works

The application calls Groq's OpenAI-compatible chat-completions endpoint with:

- `Authorization: Bearer <GROQ_API_KEY>`
- `GROQ_MODEL`
- A system instruction restricting the model to rewriting
- The deterministic explanation as the user message
- `AI_TEMPERATURE`
- `AI_MAX_TOKENS`
- `AI_TIMEOUT_SECONDS`

The system instruction prevents the model from changing facts or making
eligibility decisions. The application validates that the provider returns
non-empty text before using it.

## Caching

Successful AI responses are cached in the `ai_cache` database table.

- Cache identity includes provider, model, and prompt.
- The API key is never included in the cache key.
- The default cache lifetime is 24 hours.
- Set `AI_CACHE_TTL_SECONDS=0` to disable expiry.
- A cached response avoids a second provider call for the same explanation.

Changing the profile, model, or deterministic explanation produces a different
cache key.

## Fallback behavior

The API always remains usable if AI is unavailable. It returns the deterministic
template explanation when:

- `AI_PROVIDER=noop`
- The selected provider key is missing
- The provider times out
- The provider returns a non-success status
- The provider response is malformed
- The response is empty or oversized
- The provider is unsupported

This is intentional: AI improves wording but is never required for eligibility
logic or action-plan generation.

## Configuration reference

| Setting | Meaning | Recommended development value |
|---|---|---|
| `AI_PROVIDER` | Active provider | `noop` or `groq` |
| `GROQ_API_KEY` | Secret Groq credential | Local `.env` only |
| `GROQ_MODEL` | Groq model name | `openai/gpt-oss-20b` |
| `AI_TIMEOUT_SECONDS` | Maximum provider wait | `15` |
| `AI_MAX_TOKENS` | Maximum rewrite size | `300` |
| `AI_TEMPERATURE` | Generation randomness | `0` |
| `AI_CACHE_TTL_SECONDS` | Cache lifetime | `86400` |

## Troubleshooting

### `ai_configured` is false

Check all of the following:

```text
AI_PROVIDER=groq
GROQ_API_KEY=your-key
```

Make sure `.env` is in the repository root and restart Uvicorn. Settings are
loaded at application startup.

### `explanation_source` is `template`

This means the deterministic fallback was used. Check the server logs for the
provider failure, then verify the key, model name, network access, account
quota, and timeout setting. The API intentionally does not expose secret
values or provider credentials in errors.

### Groq returns a model error

Set `GROQ_MODEL` to a model available to your Groq account. The default is:

```text
openai/gpt-oss-20b
```

### Revoke an exposed key

If a key has appeared in a repository, terminal transcript, screenshot, or
chat, revoke it immediately in the Groq console and create a replacement.
Updating `.env` is not enough because the old key may already be copied.

## Testing the AI workflow

The repository includes mocked tests for:

- missing-key template fallback
- Groq Bearer authentication
- configured model submission
- successful response handling
- cache reuse

Run them with:

```powershell
pytest tests/test_production_features.py
```

The tests do not contact Groq and do not require a real API key.

## Privacy and safety

Do not send identity numbers, passwords, private documents, or unnecessary
personal data to the AI provider. NextStep sends the generated explanation
prompt, not the user's secret API key. Keep the deterministic result as the
source of truth and verify official programme details before applying.
