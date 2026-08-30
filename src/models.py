from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class MatchResult:
    billing_record_id: str
    billing_client_name: str
    normalized_name: str
    project_group_key: Optional[str]
    match_found: bool
    match_method: str
    match_score: Optional[float]
    match_status: str


@dataclass(frozen=True)
class RenewalRecord:
    client_name: str
    normalized_name: str
    renewal_date: Optional[date]
    days_until_renewal: Optional[int]
    monthly_fee: Optional[float]
    currency: Optional[str]
    services: Optional[str]
    scope: Optional[str]
    last_delivery_date: Optional[date]
    delivery_status: Optional[str]
    match_status: str
    renewal_status: str
