from __future__ import annotations
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class ReviewStatus(str, Enum):
    AI_SUGGESTED="AI_SUGGESTED"; RULE_DERIVED="RULE_DERIVED"; HUMAN_REVIEWED="HUMAN_REVIEWED"; SOURCE_VERIFIED="SOURCE_VERIFIED"
class GapState(str, Enum):
    NOT_SEARCHED_OR_UNKNOWN="NOT_SEARCHED_OR_UNKNOWN"; SEARCH_INCOMPLETE="SEARCH_INCOMPLETE"; SEARCHED_NO_DIRECT_EVIDENCE_FOUND="SEARCHED_NO_DIRECT_EVIDENCE_FOUND"; INDIRECT_OR_NOT_COMPARABLE_EVIDENCE="INDIRECT_OR_NOT_COMPARABLE_EVIDENCE"; DIRECT_EVIDENCE_FOUND="DIRECT_EVIDENCE_FOUND"; MULTIPLE_INDEPENDENT_DIRECT_SOURCES="MULTIPLE_INDEPENDENT_DIRECT_SOURCES"; RESTRICTED_ACCESS="RESTRICTED_ACCESS"; OUTDATED_OR_TEMPORALLY_MISMATCHED="OUTDATED_OR_TEMPORALLY_MISMATCHED"; INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION="INSUFFICIENT_GEOGRAPHIC_OR_POPULATION_DISAGGREGATION"
class RelationClass(str, Enum):
    DIRECT_MATCH="DIRECT_MATCH"; HARMONIZABLE="HARMONIZABLE"; PROXY="PROXY"; CONCEPTUALLY_RELATED="CONCEPTUALLY_RELATED"; INCOMPATIBLE="INCOMPATIBLE"; UNKNOWN_REQUIRES_REVIEW="UNKNOWN_REQUIRES_REVIEW"
class EvidenceClaim(BaseModel):
    model_config=ConfigDict(extra="forbid")
    evidence_quote: str
    source_location: str | None = None
    source_id: str
    extraction_method: str
    confidence: float = Field(ge=0, le=1)
    review_status: ReviewStatus
class Source(BaseModel):
    id: str; title: str; source_type: str="report"; url: str|None=None; doi: str|None=None; producer: str|None=None; collected_by: str|None=None; access_status: str="unknown"; synthetic: bool=False
class DataProduct(BaseModel):
    id: str; source_id: str; name: str; product_type: str; geography_level: str; population: str|None=None; observation_period: str|None=None; synthetic: bool=False
class Indicator(BaseModel):
    id: str; data_product_id: str; name: str; definition: str; unit: str|None=None; denominator: str|None=None; reference_period: str|None=None; synthetic: bool=False
class Variable(BaseModel):
    id: str; indicator_id: str; original_name: str; definition: str; unit: str|None=None; age_band: str|None=None; synthetic: bool=False
class Observation(BaseModel):
    id: str; variable_id: str; value: float|str|None=None; unit: str|None=None; geography: str; geography_level: str; period: str|None=None; synthetic: bool=False; transformation: str|None=None
class GapClaim(BaseModel):
    id: str; source_id: str; claim: str; quote: str; location: str|None=None; review_status: ReviewStatus
class Alignment(BaseModel):
    id: str; target_indicator_id: str; observed_indicator_id: str; relation_class: RelationClass; rationale: str; review_status: ReviewStatus; evidence_quote: str|None=None; source_id: str|None=None
class Barrier(BaseModel):
    id: str; barrier_type: str; description: str; evidence: str|None=None; source_id: str|None=None; review_status: ReviewStatus
class RawCandidate(BaseModel):
    id: str; title: str; url: str|None=None; doi: str|None=None; source_type: str="report"; metadata: dict[str,Any]=Field(default_factory=dict); synthetic: bool=False
