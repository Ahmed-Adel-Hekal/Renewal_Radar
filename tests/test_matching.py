import pandas as pd

from src.matching import match_billing_to_projects
from src.normalization import normalize_billing_frame, normalize_project_frame


def make_data():
    billing = pd.DataFrame(
        [
            {
                "record_id": "B1",
                "client_name": "Acme Inc.",
                "start_date": "2026-06-01",
                "end_date": "2026-09-05",
                "monthly_fee": 5000,
                "currency": "USD",
                "retainer_status": "Active",
            },
            {
                "record_id": "B2",
                "client_name": "Unmatched Client",
                "start_date": "2026-06-01",
                "end_date": "2026-09-10",
                "monthly_fee": 4000,
                "currency": "USD",
                "retainer_status": "Active",
            },
        ]
    )

    projects = pd.DataFrame(
        [
            {
                "project_id": "P1",
                "client_name": "ACME",
                "services": "CRO",
                "scope": "Audit",
                "last_delivery_date": "2026-08-01",
                "delivery_status": "Active",
            }
        ]
    )

    return normalize_billing_frame(billing), normalize_project_frame(projects)


def test_exact_normalized_match():
    billing, projects = make_data()
    matches, _, _ = match_billing_to_projects(billing, projects)

    row = matches.iloc[0]
    assert bool(row["match_found"]) is True
    assert row["match_method"] == "exact_normalized"
    assert row["match_score"] == 100.0


def test_unmatched_billing_is_not_fabricated():
    billing, projects = make_data()
    matches, _, _ = match_billing_to_projects(billing, projects)

    row = matches.iloc[1]
    assert bool(row["match_found"]) is False
    assert row["project_group_key"] is None
