# Renewal Radar

Renewal Radar is a small web application for Harbourline account leads. It combines a billing export and a project export, resolves messy client names, handles re-signed retainers and missing dates, and highlights renewals due within the next 45 days.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit.

## Project structure

```text
renewal_radar/
├── app.py
├── data/
│   ├── billing_export.csv
│   ├── project_export.csv
│   └── DATASET_NOTES.md
├── src/
│   ├── config.py
│   ├── matching.py
│   ├── models.py
│   ├── normalization.py
│   └── pipeline.py
├── tests/
│   ├── test_matching.py
│   ├── test_normalization.py
│   └── test_pipeline.py
└── requirements.txt
```

## Judgement calls

### 1. Normalize before fuzzy matching

I normalize casing, punctuation, legal suffixes, `&`/`and`, and whitespace before matching. Exact normalized matches are preferred because they are easier to audit and less likely to create false positives.

### 2. Fuzzy matching is a fallback, not the default

Unresolved names use RapidFuzz only when the best candidate is at least 90% similar and is at least 5 points better than the second candidate. Otherwise the record is sent to manual review. This favors precision over silently linking the wrong brand.

### 3. Re-signed clients use the latest retainer

When multiple billing rows map to the same normalized client, the renewal view keeps the record with the latest start date. Historical rows remain in the source data; they are not deleted.

### 4. Missing end dates are not guessed

A missing contract end date is flagged for review instead of inferring a date from the start date. A guessed renewal could create a false alert.

### 5. The 45-day window is inclusive

The rule is:

```text
reference_date <= renewal_date <= reference_date + 45 days
```

So a renewal exactly 45 days away is included.

### 6. Renewal date comes from billing

The billing export is the source of truth for the renewal date (`end_date`). Project delivery dates are used only as context.

## What the app shows

The Account Lead sees:

- renewals due within the selected window
- days remaining
- monthly fee and currency
- current services
- latest delivery status
- matching method/confidence
- records requiring review
- project records with no billing match

## Data problems covered

The included sample exports intentionally contain:

- no shared client ID
- casing and spelling differences
- legal suffixes
- spacing and punctuation differences
- missing end dates
- duplicate/re-signed retainers
- project-only records
- renewal dates inside, exactly at, and outside the 45-day window

## Tests

Run:

```bash
pytest -q
```

The tests cover normalization, matching, the inclusive 45-day boundary, missing end dates, and latest-retainer selection.
# Renewal_Radar
