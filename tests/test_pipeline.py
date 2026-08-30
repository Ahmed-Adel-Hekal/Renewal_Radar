import pandas as pd

from src.pipeline import build_renewal_view
from src.normalization import normalize_billing_frame, normalize_project_frame


def test_45_day_window_is_inclusive():
    billing = pd.DataFrame(
        [
            {
                "record_id": "B1",
                "client_name": "Acme Inc.",
                "start_date": "2026-06-01",
                "end_date": "2026-10-14",
                "monthly_fee": 5000,
                "currency": "USD",
                "retainer_status": "Active",
            },
            {
                "record_id": "B2",
                "client_name": "Nike",
                "start_date": "2026-06-01",
                "end_date": "2026-10-15",
                "monthly_fee": 8000,
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
            },
            {
                "project_id": "P2",
                "client_name": "NIKE",
                "services": "Retention",
                "scope": "Email",
                "last_delivery_date": "2026-08-10",
                "delivery_status": "Active",
            },
        ]
    )

    b = normalize_billing_frame(billing)
    p = normalize_project_frame(projects)

    _, renewals, _, _ = build_renewal_view(
        b,
        p,
        reference_date="2026-08-30",
        window_days=45,
    )

    assert "acme" in renewals["normalized_name"].tolist()
    assert "nike" not in renewals["normalized_name"].tolist()


def test_missing_end_date_is_flagged():
    billing = pd.DataFrame(
        [
            {
                "record_id": "B1",
                "client_name": "Adidas",
                "start_date": "2026-05-01",
                "end_date": "",
                "monthly_fee": 7000,
                "currency": "USD",
                "retainer_status": "Active",
            }
        ]
    )
    projects = pd.DataFrame(
        [
            {
                "project_id": "P1",
                "client_name": "ADIDAS",
                "services": "CRO",
                "scope": "Audit",
                "last_delivery_date": "2026-08-01",
                "delivery_status": "Active",
            }
        ]
    )

    b = normalize_billing_frame(billing)
    p = normalize_project_frame(projects)

    combined, renewals, review, _ = build_renewal_view(
        b,
        p,
        reference_date="2026-08-30",
        window_days=45,
    )

    assert combined.iloc[0]["renewal_status"] == "missing_end_date"
    assert renewals.empty
    assert len(review) == 1


def test_latest_retainers_win_after_resigning():
    billing = pd.DataFrame(
        [
            {
                "record_id": "OLD",
                "client_name": "Acme Inc.",
                "start_date": "2026-01-01",
                "end_date": "2026-04-01",
                "monthly_fee": 5000,
                "currency": "USD",
                "retainer_status": "Expired",
            },
            {
                "record_id": "NEW",
                "client_name": "ACME",
                "start_date": "2026-06-01",
                "end_date": "2026-09-05",
                "monthly_fee": 5500,
                "currency": "USD",
                "retainer_status": "Active",
            },
        ]
    )
    projects = pd.DataFrame(
        [
            {
                "project_id": "P1",
                "client_name": "Acme",
                "services": "CRO",
                "scope": "Audit",
                "last_delivery_date": "2026-08-01",
                "delivery_status": "Active",
            }
        ]
    )

    b = normalize_billing_frame(billing)
    p = normalize_project_frame(projects)

    combined, renewals, _, _ = build_renewal_view(
        b,
        p,
        reference_date="2026-08-30",
        window_days=45,
    )

    assert len(combined) == 1
    assert combined.iloc[0]["record_id"] == "NEW"
    assert len(renewals) == 1
