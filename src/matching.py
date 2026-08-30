from typing import Dict, Tuple

import pandas as pd
from rapidfuzz import fuzz, process

from .config import MATCH_MARGIN, MATCH_THRESHOLD
from .models import MatchResult


def _unique_normalized_names(project_df: pd.DataFrame) -> list[str]:
    return [
        value
        for value in project_df["normalized_name"].dropna().unique().tolist()
        if value
    ]


def match_billing_to_projects(
    billing_df: pd.DataFrame,
    project_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, set[int], list[MatchResult]]:
    """
    Match billing clients to project-client names.

    Decision order:
    1. Exact normalized match.
    2. Fuzzy match only when the best score is >= threshold AND
       clearly better than the second candidate.
    3. Otherwise mark for manual review.
    """
    project_names = _unique_normalized_names(project_df)
    results: list[MatchResult] = []
    matched_project_indexes: set[int] = set()

    name_to_indexes: Dict[str, list[int]] = {}
    for idx, name in project_df["normalized_name"].items():
        if name:
            name_to_indexes.setdefault(name, []).append(idx)

    for billing_idx, row in billing_df.iterrows():
        billing_name = row["client_name"]
        normalized = row["normalized_name"]

        if not normalized:
            results.append(
                MatchResult(
                    billing_record_id=str(row["record_id"]),
                    billing_client_name=str(billing_name),
                    normalized_name="",
                    project_group_key=None,
                    match_found=False,
                    match_method="none",
                    match_score=None,
                    match_status="manual_review",
                )
            )
            continue

        # 1. Exact normalized match.
        if normalized in name_to_indexes:
            for project_idx in name_to_indexes[normalized]:
                matched_project_indexes.add(project_idx)

            results.append(
                MatchResult(
                    billing_record_id=str(row["record_id"]),
                    billing_client_name=str(billing_name),
                    normalized_name=normalized,
                    project_group_key=normalized,
                    match_found=True,
                    match_method="exact_normalized",
                    match_score=100.0,
                    match_status="matched",
                )
            )
            continue

        # 2. Fuzzy fallback.
        candidates = process.extract(
            normalized,
            project_names,
            scorer=fuzz.ratio,
            limit=2,
        )

        if not candidates:
            results.append(
                MatchResult(
                    billing_record_id=str(row["record_id"]),
                    billing_client_name=str(billing_name),
                    normalized_name=normalized,
                    project_group_key=None,
                    match_found=False,
                    match_method="none",
                    match_score=None,
                    match_status="unmatched",
                )
            )
            continue

        best_name, best_score, _ = candidates[0]
        second_score = candidates[1][1] if len(candidates) > 1 else 0.0

        confident = (
            best_score >= MATCH_THRESHOLD
            and (best_score - second_score >= MATCH_MARGIN)
        )

        if confident:
            for project_idx in name_to_indexes[best_name]:
                matched_project_indexes.add(project_idx)

            results.append(
                MatchResult(
                    billing_record_id=str(row["record_id"]),
                    billing_client_name=str(billing_name),
                    normalized_name=normalized,
                    project_group_key=best_name,
                    match_found=True,
                    match_method="fuzzy",
                    match_score=round(float(best_score), 2),
                    match_status="matched",
                )
            )
        else:
            results.append(
                MatchResult(
                    billing_record_id=str(row["record_id"]),
                    billing_client_name=str(billing_name),
                    normalized_name=normalized,
                    project_group_key=None,
                    match_found=False,
                    match_method="fuzzy_review",
                    match_score=round(float(best_score), 2),
                    match_status="manual_review",
                )
            )

    result_df = pd.DataFrame([r.__dict__ for r in results])
    return result_df, matched_project_indexes, results
