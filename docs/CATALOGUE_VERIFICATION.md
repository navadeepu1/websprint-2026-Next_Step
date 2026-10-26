# Catalogue verification checklist

Automated validation confirms that records have the expected shape, but it
cannot prove that a government programme's current rules are correct. Before
setting `verified: true`, a reviewer must complete the following for each
opportunity:

- Open the stored `official_url` and confirm it is the official government or
  authorised portal.
- Confirm the current age, income, education, occupation, state, land,
  disability, and need criteria.
- Confirm every document in `documents` is still required and add any missing
  document.
- Confirm the application instructions and availability date.
- Set `last_verified` to the review date.
- Record the reviewer and evidence in the team's change/audit process.

Health topics require the same review of `source_url`, summary, warning signs,
and escalation guidance. Health content must remain general awareness
information and must not be presented as diagnosis or treatment advice.

The sync endpoint validates payload shape and records rejected rows in
`SyncLog`; it does not mark unverified records as verified.
