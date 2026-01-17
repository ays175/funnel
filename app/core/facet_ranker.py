from __future__ import annotations

from app.core.facet_discovery import FacetCandidate


class FacetRanker:
    def rank(self, raw_query: str, candidates: list[FacetCandidate]) -> list[FacetCandidate]:
        query = raw_query.lower()

        def score(candidate: FacetCandidate) -> tuple[int, int]:
            keyword_hits = sum(1 for kw in candidate.facet.keywords if kw.lower() in query)
            has_defaults = 1 if candidate.facet.default_value else 0
            return (keyword_hits, has_defaults)

        return sorted(candidates, key=score, reverse=True)
