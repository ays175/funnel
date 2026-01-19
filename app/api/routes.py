from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    AnswerRequest,
    AnswerResponse,
    Choice,
    DiscoverRequest,
    DiscoverResponse,
    FacetCandidate,
    ProceedDefaults,
    PromptBundle,
    PromptSection,
    RefineRequest,
    RefineResponse,
    TraceEvent,
)
from app.core.config import load_settings
from app.core.domain_router import DomainRouter
from app.core.facet_discovery import FacetCandidate as CoreFacetCandidate, FacetDiscoveryEngine
from app.core.facet_ranker import FacetRanker
from app.core.llm_client import LLMClient
from app.core.prompt_compiler import PromptCompiler
from app.core.trace_ledger import TraceLedger
from app.storage.trace_store import TraceStore

router = APIRouter()

settings = load_settings()
store = TraceStore(settings.trace_db_url)
ledger = TraceLedger(store)
router_engine = DomainRouter(packs_dir=__import__("pathlib").Path(__file__).parents[1] / "packs")
discovery = FacetDiscoveryEngine()
ranker = FacetRanker()
compiler = PromptCompiler()
_llm_client: LLMClient | None = None


def _get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(settings)
    return _llm_client


def _serialize_candidates(candidates: list[CoreFacetCandidate]) -> list[FacetCandidate]:
    results: list[FacetCandidate] = []
    for candidate in candidates:
        facet = candidate.facet
        results.append(
            FacetCandidate(
                id=facet.id,
                title=facet.title,
                question=facet.question,
                reason=candidate.reason,
                suggested_values=facet.suggested_values,
                choices=[Choice(value=c.value, subchoices=c.subchoices) for c in facet.choices],
            )
        )
    return results


@router.post("/discover", response_model=DiscoverResponse)
def discover(payload: DiscoverRequest) -> DiscoverResponse:
    request_id = str(uuid4())
    active_domain_pack = router_engine.choose_pack(payload.raw_query, payload.domain_hint)
    pack = router_engine.load_pack(active_domain_pack)
    if settings.enable_llm_facet_proposals:
        if not settings.openai_api_key:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")
        candidates = discovery.discover_round1_llm(
            payload.raw_query,
            pack,
            settings.max_facet_questions,
            _get_llm_client(),
        )
    else:
        candidates = discovery.discover_round1(payload.raw_query, pack)

    ranked = ranker.rank(payload.raw_query, candidates)
    limited = ranked[: settings.max_facet_questions]

    created_at = datetime.now(timezone.utc).isoformat()
    store.create_request(request_id, payload.raw_query, active_domain_pack, created_at)

    ledger.append(
        request_id,
        "DETECT_DOMAIN",
        {"active_domain_pack": active_domain_pack, "domain_hint": payload.domain_hint},
    )
    ledger.append(
        request_id,
        "SUGGEST_FACETS",
        {"round": 1, "facet_ids": [item.facet.id for item in limited]},
    )

    proceed_defaults = {
        item.facet.id: item.facet.default_value or "unspecified" for item in limited
    }

    return DiscoverResponse(
        request_id=request_id,
        active_domain_pack=active_domain_pack,
        facet_candidates=_serialize_candidates(limited),
        proceed_defaults=ProceedDefaults(
            selected_facet_ids=[],
            assumed_defaults=proceed_defaults,
        ),
    )


@router.post("/refine", response_model=RefineResponse)
def refine(payload: RefineRequest) -> RefineResponse:
    request = store.get_request(payload.request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Unknown request_id")

    if payload.refine_round > settings.max_refine_rounds:
        return RefineResponse(facet_candidates=[], why_these_facets=["Max refine rounds reached"])

    pack = router_engine.load_pack(request["domain_pack"])
    selections = {selection.id: selection.value for selection in payload.facet_selections}
    selected_ids = list(selections.keys())

    if settings.enable_llm_facet_proposals:
        if not settings.openai_api_key:
            raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")
        candidates = discovery.discover_round2_llm(
            request["raw_query"],
            pack,
            selections,
            settings.max_facet_questions,
            _get_llm_client(),
        )
    else:
        if not selected_ids:
            refinement_ids = list(pack.get("refinements", {}).keys())
            selected_ids = refinement_ids[: settings.max_facet_questions]
        candidates = discovery.discover_round2(request["raw_query"], pack, selected_ids)
    ranked = ranker.rank(request["raw_query"], candidates)
    limited = ranked[: settings.max_facet_questions]

    ledger.append(
        payload.request_id,
        "SUGGEST_FACETS",
        {"round": payload.refine_round, "facet_ids": [item.facet.id for item in limited]},
    )

    why_these = [candidate.reason for candidate in limited] or ["No additional facets found"]
    return RefineResponse(
        facet_candidates=_serialize_candidates(limited),
        why_these_facets=why_these,
    )


@router.post("/answer", response_model=AnswerResponse)
def answer(payload: AnswerRequest) -> AnswerResponse:
    request = store.get_request(payload.request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Unknown request_id")

    selections = {selection.id: selection.value for selection in payload.facet_selections}
    pack = router_engine.load_pack(request["domain_pack"])
    defaults = {
        item["id"]: item.get("default_value", "unspecified")
        for item in pack.get("facets", [])
    }
    prompt_sections = compiler.compile(
        raw_query=request["raw_query"],
        selections=selections,
        user_overrides=payload.user_overrides or {},
        proceed_defaults=defaults,
    )

    ledger.append(payload.request_id, "USER_SELECT", {"selections": selections})
    ledger.append(
        payload.request_id,
        "COMPILE_PROMPT",
        {"sections": [section.__dict__ for section in prompt_sections]},
    )

    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is not configured")

    answer_text, reasoning = _get_llm_client().generate(
        [(section.title, section.content) for section in prompt_sections]
    )

    ledger.append(
        payload.request_id,
        "MODEL_RESPONSE",
        {
            "model": settings.openai_model,
            "answer_preview": answer_text[:200],
            "has_reasoning": reasoning is not None,
        },
    )

    trace_events = [
        TraceEvent(**event) for event in ledger.list_events(payload.request_id)
    ]

    return AnswerResponse(
        answer=answer_text,
        trace=trace_events,
        compiled_prompt=PromptBundle(
            sections=[PromptSection(title=s.title, content=s.content) for s in prompt_sections]
        ),
        reasoning=reasoning,
    )
