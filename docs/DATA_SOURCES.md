# Data sources

Seed data is local JSON under `seed/`. Live government endpoints are never hardcoded. Optional sync URLs come from `DATA_SOURCE_URLS`.

## Confirmed portals (manual review still required)

- National Scholarship Portal: https://scholarships.gov.in/
- myScheme: https://www.myscheme.gov.in/
- PM-KISAN: https://pmkisan.gov.in/
- NSAP: https://nsap.nic.in/
- National Career Service: https://www.ncs.gov.in/
- PMFBY: https://pmfby.gov.in/

## TODO — verify before marking `verified: true`

- Income ceilings, age bounds, document lists, and Punjab-specific add-ons for every seed opportunity.
- Current PMKVY / skill-india application URL.
- Ayushman Bharat senior (70+) eligibility start date and official apply URL.
- Health topic pages: confirm each `source_url` still hosts the cited public information.
