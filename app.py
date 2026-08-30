from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from src.pipeline import build_renewal_view, load_exports

st.set_page_config(
    page_title="Renewal Radar",
    page_icon="🔭",
    layout="wide",
)

st.title("Renewal Radar")
st.caption("Upcoming three-month retainer renewals from billing + project exports.")

with st.sidebar:
    st.header("Controls")
    reference_date = st.date_input(
        "Reference date",
        value=date(2026, 8, 30),
    )
    window_days = st.number_input(
        "Renewal window (days)",
        min_value=1,
        max_value=180,
        value=45,
    )

    st.divider()
    st.write("Optional: upload replacement exports.")
    billing_upload = st.file_uploader(
        "Billing CSV",
        type=["csv"],
        key="billing",
    )
    project_upload = st.file_uploader(
        "Project CSV",
        type=["csv"],
        key="project",
    )

try:
    if billing_upload is not None and project_upload is not None:
        billing_raw = pd.read_csv(billing_upload)
        project_raw = pd.read_csv(project_upload)

        from src.normalization import (
            normalize_billing_frame,
            normalize_project_frame,
        )

        billing = normalize_billing_frame(billing_raw)
        projects = normalize_project_frame(project_raw)

        combined, renewals, review, orphan_projects = build_renewal_view(
            billing,
            projects,
            reference_date=reference_date,
            window_days=int(window_days),
        )
    else:
        billing, projects = load_exports()
        combined, renewals, review, orphan_projects = build_renewal_view(
            billing,
            projects,
            reference_date=reference_date,
            window_days=int(window_days),
        )

except Exception as exc:
    st.error(f"Could not process the exports: {exc}")
    st.stop()

window_end = pd.Timestamp(reference_date) + pd.Timedelta(days=int(window_days))

col1, col2, col3, col4 = st.columns(4)
col1.metric("Renewing soon", len(renewals))
col2.metric("Missing end date", int((combined["renewal_status"] == "missing_end_date").sum()))
col3.metric("Expired", int((combined["renewal_status"] == "expired").sum()))
col4.metric("Needs review", len(review))

st.subheader(
    f"Renewals from {reference_date:%d %b %Y} to {window_end:%d %b %Y}"
)

display_columns = [
    "client_name",
    "end_date",
    "days_until_renewal",
    "monthly_fee",
    "currency",
    "services",
    "delivery_status",
    "match_method",
    "match_score",
]

if renewals.empty:
    st.info("No renewals found in the selected window.")
else:
    table = renewals[display_columns].copy()
    table["end_date"] = table["end_date"].dt.strftime("%Y-%m-%d")
    table = table.rename(
        columns={
            "client_name": "Client",
            "end_date": "Renewal Date",
            "days_until_renewal": "Days Left",
            "monthly_fee": "Monthly Fee",
            "currency": "Currency",
            "services": "Services",
            "delivery_status": "Delivery",
            "match_method": "Match",
            "match_score": "Confidence",
        }
    )
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Data quality / review queue"):
    if review.empty:
        st.success("No billing records require review.")
    else:
        review_columns = [
            "client_name",
            "end_date",
            "match_status",
            "match_method",
            "match_score",
            "services",
        ]
        st.dataframe(
            review[review_columns],
            use_container_width=True,
            hide_index=True,
        )

    st.write("Unmatched project records")
    if orphan_projects.empty:
        st.success("No unmatched project records.")
    else:
        st.dataframe(
            orphan_projects[
                [
                    "project_id",
                    "client_name",
                    "services",
                    "last_delivery_date",
                    "delivery_status",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
