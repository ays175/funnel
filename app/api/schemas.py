from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Choice(BaseModel):
    value: str
    subchoices: list[str] = Field(default_factory=list)


class FacetCandidate(BaseModel):
    id: str
    title: str
    question: str
    reason: str
    suggested_values: list[str] = Field(default_factory=list)
    choices: list[Choice] = Field(default_factory=list)


class FacetSelection(BaseModel):
    id: str
    value: str | None = None


class ProceedDefaults(BaseModel):
    selected_facet_ids: list[str] = Field(default_factory=list)
    assumed_defaults: dict[str, str] = Field(default_factory=dict)


class DiscoverRequest(BaseModel):
    raw_query: str
    domain_hint: str | None = None
    user_prefs: dict[str, Any] | None = None


class DiscoverResponse(BaseModel):
    request_id: str
    active_domain_pack: str
    facet_candidates: list[FacetCandidate]
    proceed_defaults: ProceedDefaults


class RefineRequest(BaseModel):
    request_id: str
    facet_selections: list[FacetSelection]
    refine_round: int = 2
    exclude_facet_ids: list[str] = Field(default_factory=list)  # Already shown facets to exclude


class RefineResponse(BaseModel):
    facet_candidates: list[FacetCandidate]
    why_these_facets: list[str]


class AnswerRequest(BaseModel):
    request_id: str
    facet_selections: list[FacetSelection]
    user_overrides: dict[str, Any] | None = None


class TraceEvent(BaseModel):
    event_type: str
    data: dict[str, Any]
    timestamp: str


class PromptSection(BaseModel):
    title: str
    content: str


class PromptBundle(BaseModel):
    sections: list[PromptSection]


class AnswerResponse(BaseModel):
    answer: str
    trace: list[TraceEvent]
    compiled_prompt: PromptBundle
    reasoning: str | None = None  # Model's internal reasoning (o-series models)