from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class Drug(BaseModel):
    id: int
    trade_name: str
    active_substance: str
    atc_code: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = None


class DrugSearchResult(BaseModel):
    results: List[Drug]


class InteractionCheckRequest(BaseModel):
    drug_ids: List[int]


class InteractionDrug(BaseModel):
    trade_name: str
    active_substance: str


class Interaction(BaseModel):
    drug_a: InteractionDrug
    drug_b: InteractionDrug
    severity: str
    mechanism: Optional[str] = None
    management: Optional[str] = None
    alternatives: Optional[str] = None


class SafePair(BaseModel):
    drug_a: str
    drug_b: str
    note: str = "No clinically significant interaction found."


class InteractionSummary(BaseModel):
    total_pairs_checked: int
    major: int
    moderate: int
    minor: int
    none: int


class InteractionCheckResponse(BaseModel):
    interactions_found: int
    interactions: List[Interaction]
    safe_pairs: List[SafePair]
    summary: InteractionSummary
