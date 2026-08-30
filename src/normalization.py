import re
from typing import Optional

import pandas as pd


LEGAL_SUFFIXES = {
    "inc",
    "incorporated",
    "llc",
    "ltd",
    "limited",
    "co",
    "company",
    "corp",
    "corporation",
    "plc",
}

AMPERSAND_WORDS = {
    "and": "and",
    "ampersand": "and",
}


def normalize_brand_name(name: object) -> str:
    """Normalize a client/brand name for entity matching."""
    if name is None or pd.isna(name):
        return ""

    text = str(name).strip().lower()

    # Treat & as the word "and" so "River & Reed" ~= "River and Reed".
    text = text.replace("&", " and ")

    # Remove punctuation/non-alphanumeric characters.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    tokens = []
    for token in text.split():
        if token in LEGAL_SUFFIXES:
            continue
        tokens.append(AMPERSAND_WORDS.get(token, token))

    # Removing spaces makes BlueBottle and Blue Bottle comparable.
    return "".join(tokens)


def normalize_date(value: object) -> pd.Timestamp:
    """Parse supported date values; invalid/missing values become NaT."""
    if value is None or pd.isna(value) or str(value).strip() == "":
        return pd.NaT

    return pd.to_datetime(value, errors="coerce")


def normalize_billing_frame(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    required = {
        "record_id",
        "client_name",
        "start_date",
        "end_date",
        "monthly_fee",
        "currency",
        "retainer_status",
    }
    missing = required - set(result.columns)
    if missing:
        raise ValueError(f"Billing export missing columns: {sorted(missing)}")

    result["normalized_name"] = result["client_name"].apply(normalize_brand_name)
    result["start_date"] = result["start_date"].apply(normalize_date)
    result["end_date"] = result["end_date"].apply(normalize_date)
    result["monthly_fee"] = pd.to_numeric(result["monthly_fee"], errors="coerce")

    return result


def normalize_project_frame(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    required = {
        "project_id",
        "client_name",
        "services",
        "scope",
        "last_delivery_date",
        "delivery_status",
    }
    missing = required - set(result.columns)
    if missing:
        raise ValueError(f"Project export missing columns: {sorted(missing)}")

    result["normalized_name"] = result["client_name"].apply(normalize_brand_name)
    result["last_delivery_date"] = result["last_delivery_date"].apply(
        normalize_date
    )

    return result
