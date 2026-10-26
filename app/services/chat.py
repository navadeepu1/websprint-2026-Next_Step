from collections.abc import Sequence

import httpx

from app.config import get_settings
from app.services.ai import _clean_output, _remote_explanation

SITE_CONTEXT = """
You are NextStep Guide, a friendly, capable general-purpose conversational AI
assistant inside the NextStep website. Answer the user's actual question
directly, even when it is not about the website. You can explain concepts,
help brainstorm, summarize text the user provides, translate short text, help
write drafts, and answer general knowledge questions. Do not pretend to have
live browsing or current facts you cannot verify.

NextStep is an offline-first citizen opportunity discovery tool.
Users can browse opportunities, check eligibility, read health-awareness
topics, and create an action plan.

Website navigation:
- Overview: the dashboard and quick explanation of how NextStep works.
- Check eligibility: enter age, education, occupation, income, state, needs,
  land ownership, and disability status.
- Opportunities: browse and filter scholarships, jobs, farmer schemes, and
  senior support, then open official source details.
- Health topics: search general health-awareness information.
- My action plan: generate a checklist and official links after an eligibility
  check.
- API documentation: /docs and /redoc.

Important behavior:
- Eligibility is calculated by deterministic rules, not by AI.
- Missing answers are shown as possibly eligible, not automatically rejected.
- Official portals make the final decision. Users should verify current rules,
  documents, dates, and links before applying.
- Health content is general awareness only and is not medical advice.
- Never ask for or process passwords, identity numbers, API keys, payment
  details, or private documents. If the user volunteers sensitive data, tell
  them to remove it and do not repeat it.
- For medical, legal, financial, or safety-sensitive questions, provide
  general educational information, state relevant uncertainty, and recommend
  a qualified professional or emergency service when appropriate. Do not
  diagnose, guarantee outcomes, or present NextStep as an authority.

Useful official portals may appear in the catalogue, including myScheme,
National Scholarship Portal, National Career Service, PM-KISAN, PMFBY, and
NSAP. Only recommend an official link returned by the catalogue or the user's
request; do not invent URLs.
"""


def _fallback(message: str) -> str:
    lowered = message.lower()
    if any(word in lowered for word in ("eligib", "qualify", "profile")):
        return "Use “Check eligibility” in the navigation. Enter your basic profile and NextStep will show eligible, possibly eligible, and not eligible results with reasons. You can then create an action plan."
    if any(word in lowered for word in ("opportun", "scheme", "scholar", "job", "farmer")):
        return "Open “Opportunities” to browse scholarships, jobs, farmer schemes, and senior support. Use the category and verification filters, then open a record to see its description, documents, and official source."
    if any(word in lowered for word in ("health", "medical", "symptom")):
        return "Open “Health topics” for general awareness information and search by topic. This content is not medical advice; seek a qualified clinician for personal medical guidance or urgent care."
    if any(word in lowered for word in ("plan", "checklist", "document", "next step")):
        return "Run an eligibility check first, then open “My action plan” to generate a checklist, document list, and official links in JSON or printable Markdown."
    if any(word in lowered for word in ("api", "developer", "swagger", "redoc")):
        return "The interactive API documentation is available at /docs, and the alternative documentation view is at /redoc while the server is running."
    if any(word in lowered for word in ("link", "website", "portal", "access", "where")):
        return "Use the Opportunities section to open the official source for a catalogue record. NextStep does not replace those portals, so verify the current application instructions there."
    return "I can explain how to use NextStep, find the right section, or describe the eligibility, opportunities, health-topic, and action-plan workflows. What would you like to do?"


def answer_chat(message: str, history: Sequence[dict[str, str]]) -> tuple[str, str]:
    settings = get_settings()
    fallback = _fallback(message)
    if settings.ai_provider != "groq" or not settings.groq_api_key:
        return fallback, "template"

    conversation = "\n".join(
        f"{item['role'].upper()}: {item['content'][:1200]}" for item in history[-8:]
    )
    prompt = (
        f"{SITE_CONTEXT}\n\nConversation so far:\n{conversation or '(new conversation)'}"
        f"\n\nUSER: {message}\n\nAnswer the user's question first, then add "
        "relevant NextStep directions only when useful. Keep it concise but "
        "complete (normally under 250 words). Ask one clarifying question only "
        "when the request is genuinely ambiguous. Never claim that you "
        "performed an action, checked a live source, or know private user data "
        "when you did not."
    )
    try:
        reply = _remote_explanation(prompt, settings.ai_provider, settings.groq_api_key)
        return _clean_output(reply), "ai"
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return fallback, "template"
