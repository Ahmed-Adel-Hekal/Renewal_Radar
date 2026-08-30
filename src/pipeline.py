from datetime import date, timedelta
from typing import Optional, Tuple

import pandas as pd

from .config import DEFAULT_BILLING_FILE, DEFAULT_PROJECT_FILE, RENEWAL_WINDOW_DAYS
from .matching import match_billing_to_projects
from .normalization import normalize_billing_frame, normalize_project_frame


def load_exports(
    billing_path=DEFAULT_BILLING_FILE,
    project_path=DEFAULT_PROJECT_FILE,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    billing = pd.read_csv(billing_path)
    projects = pd.read_csv(project_path)
    return normalize_billing_frame(billing), normalize_project_frame(projects)


def resolve_current_retainers(billing_df: pd.DataFrame) -> pd.DataFrame:
    """
    Resolve re-signed/duplicate retainers.

    Keep the latest record by start_date for each normalized client.
    Historical rows are preserved in the source DataFrame; only the
    current renewal view is reduced.
    """
    result = billing_df.copy()

    result = result.sort_values(
        by=["normalized_name", "start_date", "record_id"],
        ascending=[True, False, False],
        na_position="last",
    )

    return result.drop_duplicates(
        subset=["normalized_name"],
        keep="first",
    ).reset_index(drop=True)


def summarize_project_history(
    project_df: pd.DataFrame,
    billing_matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate all project history for matched client groups.

    For each matched client:
    - combine unique services/scope values
    - use the latest delivery date
    - use the status from the latest delivery record
    """
    matched = billing_matches[
        billing_matches["match_found"] == True  # noqa: E712
    ].copy()

    if matched.empty:
        return pd.DataFrame(
            columns=[
                "project_group_key",
                "services",
                "scope",
                "last_delivery_date",
                "delivery_status",
            ]
        )

    groups = []
    for group_key in matched["project_group_key"].dropna().unique():
        group_projects = project_df[
            project_df["normalized_name"] == group_key
        ].copy()

        if group_projects.empty:
            continue

        group_projects = group_projects.sort_values(
            "last_delivery_date",
            ascending=False,
            na_position="last",
        )

        services = sorted(
            {
                str(value).strip()
                for value in group_projects["services"].dropna()
                if str(value).strip()
            }
        )
        scopes = sorted(
            {
                str(value).strip()
                for value in group_projects["scope"].dropna()
                if str(value).strip()
            }
        )

        latest = group_projects.iloc[0]

        groups.append(
            {
                "project_group_key": group_key,
                "services": " | ".join(services) if services else None,
                "scope": " | ".join(scopes) if scopes else None,
                "last_delivery_date": latest["last_delivery_date"],
                "delivery_status": latest["delivery_status"],
            }
        )

    return pd.DataFrame(groups)


def build_renewal_view(
    billing_df: pd.DataFrame,
    project_df: pd.DataFrame,
    reference_date: Optional[date | pd.Timestamp] = None,
    window_days: int = RENEWAL_WINDOW_DAYS,
):
    """
    Produce the full current-retainer view plus renewal subset and data issues.
    """
    if reference_date is None:
        reference = pd.Timestamp.today().normalize()
    else:
        reference = pd.Timestamp(reference_date).normalize()

    # Exact duplicate rows only.
    billing_df = billing_df.drop_duplicates().copy()
    project_df = project_df.drop_duplicates().copy()

    current = resolve_current_retainers(billing_df)

    matches, _, _ = match_billing_to_projects(
        current,
        project_df,
    )

    project_summary = summarize_project_history(
        project_df,
        matches,
    )

    current = current.reset_index(drop=True)
    matches = matches.reset_index(drop=True)

    combined = current.merge(
        matches[
            [
                "billing_record_id",
                "project_group_key",
                "match_method",
                "match_score",
                "match_status",
            ]
        ],
        left_on="record_id",
        right_on="billing_record_id",
        how="left",
    )

    if not project_summary.empty:
        combined = combined.merge(
            project_summary,
            on="project_group_key",
            how="left",
        )
    else:
        combined["services"] = None
        combined["scope"] = None
        combined["last_delivery_date"] = pd.NaT
        combined["delivery_status"] = None

    combined["days_until_renewal"] = (
        combined["end_date"] - reference
    ).dt.days

    window_end = reference + pd.Timedelta(days=window_days)

    combined["renewal_status"] = "outside_window"

    missing_end = combined["end_date"].isna()
    combined.loc[missing_end, "renewal_status"] = "missing_end_date"

    expired = (
        combined["end_date"].notna()
        & (combined["end_date"] < reference)
    )
    combined.loc[expired, "renewal_status"] = "expired"

    renewing = (
        combined["end_date"].notna()
        & (combined["end_date"] >= reference)
        & (combined["end_date"] <= window_end)
    )
    combined.loc[renewing, "renewal_status"] = "renewing_soon"

    # Business-facing subset: upcoming renewals.
    renewals = (
        combined[combined["renewal_status"] == "renewing_soon"]
        .sort_values("end_date")
        .reset_index(drop=True)
    )

    # Records requiring data/match review.
    review = combined[
        combined["renewal_status"].isin(["missing_end_date"])
        | (combined["match_status"] != "matched")
    ].copy()

    # Project records that were not connected to a billing client.
    matched_project_keys = set(
        matches.loc[matches["match_found"], "project_group_key"].dropna()
    )
    orphan_projects = project_df[
        ~project_df["normalized_name"].isin(matched_project_keys)
    ].copy()

    return combined, renewals, review, orphan_projects


def run_pipeline(
    billing_path=DEFAULT_BILLING_FILE,
    project_path=DEFAULT_PROJECT_FILE,
    reference_date: Optional[date | pd.Timestamp] = None,
    window_days: int = RENEWAL_WINDOW_DAYS,
):
    billing, projects = load_exports(
        billing_path=billing_path,
        project_path=project_path,
    )
    return build_renewal_view(
        billing_df=billing,
        project_df=projects,
        reference_date=reference_date,
        window_days=window_days,
    )
