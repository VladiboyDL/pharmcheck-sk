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


class DrugDetail(BaseModel):
    id: int
    trade_name: str
    active_substance: str
    atc_code: Optional[str] = None
    atc_group: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = None
    sukl_code: Optional[str] = None
    interaction_count: int = 0
    related_drugs: List[Drug] = []


class DrugSearchResult(BaseModel):
    results: List[Drug]


class InteractionCheckRequest(BaseModel):
    drug_ids: List[int]


class InteractionDrug(BaseModel):
    id: int
    trade_name: str
    active_substance: str


class Interaction(BaseModel):
    drug_a: InteractionDrug
    drug_b: InteractionDrug
    severity: str
    mechanism: Optional[str] = None
    management: Optional[str] = None
    alternatives: Optional[str] = None
    source: str = "db"  # "db" = DDInter, "ai" = Claude AI, "ai_cached" = cached AI


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
    ai_enabled: bool = False


class AlternativeSuggestion(BaseModel):
    original_drug: Drug
    alternative: Drug
    reason: str
    interactions_avoided: int


class ResolverResponse(BaseModel):
    suggestions: List[AlternativeSuggestion]
    original_interaction_count: int


class ATCGroup(BaseModel):
    code: str
    name: str
    drug_count: int


class ATCBrowseResponse(BaseModel):
    groups: List[ATCGroup]
    drugs: List[Drug]


class DatabaseStats(BaseModel):
    total_drugs: int
    total_interactions: int
    drugs_with_interactions: int
    severity_breakdown: dict
    top_atc_groups: List[ATCGroup]
