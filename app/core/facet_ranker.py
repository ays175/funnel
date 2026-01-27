from __future__ import annotations

import json
import re

from app.core.facet_discovery import FacetCandidate
from app.core.llm_client import LLMClient


class FacetRanker:
    def rank(self, raw_query: str, candidates: list[FacetCandidate]) -> list[FacetCandidate]:
        query = raw_query.lower()

        def score(candidate: FacetCandidate) -> tuple[int, int]:
            keyword_hits = sum(1 for kw in candidate.facet.keywords if kw.lower() in query)
            has_defaults = 1 if candidate.facet.default_value else 0
            return (keyword_hits, has_defaults)

        return sorted(candidates, key=score, reverse=True)

    def rank_with_llm(
        self,
        raw_query: str,
        candidates: list[FacetCandidate],
        llm_client: LLMClient,
    ) -> list[FacetCandidate]:
        if not candidates:
            return candidates

        facets_payload = [
            {
                "id": item.facet.id,
                "title": item.facet.title,
                "question": item.facet.question,
            }
            for item in candidates
        ]
        prompt_sections = [
            (
                "Task",
                "Reorder the facets by relevance to the query. Keep all facets, only reorder.",
            ),
            ("User Query", raw_query.strip()),
            ("Facets", json.dumps(facets_payload)),
            (
                "Output JSON",
                (
                    "Return JSON only with this shape:\n"
                    '{ "facet_order": ["id1", "id2", "id3"] }\n'
                    "Rules:\n"
                    "- Include every facet id exactly once.\n"
                    "- Do not add or remove ids.\n"
                ),
            ),
        ]
        raw, _ = llm_client.generate(prompt_sections)
        order = self._parse_facet_order(raw)
        if not order:
            return self.rank(raw_query, candidates)

        by_id = {item.facet.id: item for item in candidates}
        ordered = [by_id[item_id] for item_id in order if item_id in by_id]
        missing = [item for item in candidates if item.facet.id not in order]
        return ordered + missing

    def _parse_facet_order(self, raw: str) -> list[str]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                return []
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                return []
        if not isinstance(data, dict):
            return []
        order = data.get("facet_order", [])
        if not isinstance(order, list):
            return []
        return [str(item) for item in order if item]
