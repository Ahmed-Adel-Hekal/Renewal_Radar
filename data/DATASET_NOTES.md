# Renewal Radar Sample Dataset

Reference date: **2026-08-30**

- `billing_export.csv`: 60 rows
- `project_export.csv`: 60 rows

Intentional messiness:
- No shared client ID.
- Case differences: `NIKE` / `nike`.
- Legal suffix differences: `Acme Inc.` / `ACME`.
- Spacing/punctuation differences: `Blue Bottle` / `BlueBottle`.
- Missing billing end dates.
- Multiple records for re-signed clients.
- Project-only clients with no billing match.
- Renewal dates inside, exactly at, and outside the 45-day window.
- Status casing inconsistencies.

Suggested test rule:
`today <= renewal_date <= today + 45 days` (inclusive).

Recommended handling for missing end dates:
flag for review rather than inventing a renewal date.

Recommended handling for duplicates:
use the latest/current valid retainer for the renewal view while preserving historical rows.
