from __future__ import annotations

from dataclasses import dataclass
import json
import re

from app.core.llm_client import LLMClient


@dataclass(frozen=True)
class Choice:
    value: str
    subchoices: list[str]


@dataclass(frozen=True)
class Facet:
    id: str
    title: str
    question: str
    keywords: list[str]
    suggested_values: list[str]
    choices: list[Choice]
    default_value: str | None


@dataclass(frozen=True)
class FacetCandidate:
    facet: Facet
    reason: str


class FacetDiscoveryEngine:
    def discover_round1(self, raw_query: str, pack: dict) -> list[FacetCandidate]:
        query = raw_query.lower()
        candidates: list[FacetCandidate] = []
        for item in pack.get("facets", []):
            facet = self._to_facet(item)
            reason = self._reason_from_keywords(query, facet)
            candidates.append(FacetCandidate(facet=facet, reason=reason))
        return candidates

    def discover_round1_llm(
        self,
        raw_query: str,
        pack: dict,
        max_facets: int,
        llm_client: LLMClient,
    ) -> list[FacetCandidate]:
        prompt_sections = [
            (
                "Task",
                "Generate facet options for a prompt builder. Focus on the topic itself.",
            ),
            ("User Query", raw_query.strip()),
            (
                "Domain Context",
                json.dumps(
                    {
                        "domain": pack.get("domain"),
                        "keywords": pack.get("keywords", []),
                        "base_facets": pack.get("facets", []),
                    }
                ),
            ),
            (
                "Output JSON",
                (
                    "Return JSON only with this shape:\n"
                    "{\n"
                    '  "facets": [\n'
                    "    {\n"
                    '      "id": "topic_focus",\n'
                    '      "title": "Topic Focus",\n'
                    '      "question": "Which aspect of the topic should be emphasized?",\n'
                    '      "reason": "Short reason tied to query terms",\n'
                    '      "choices": [\n'
                    '        {"value": "value1", "subchoices": ["sub1", "sub2"]},\n'
                    '        {"value": "value2", "subchoices": []}\n'
                    "      ],\n"
                    '      "default_value": "value1"\n'
                    "    }\n"
                    "  ]\n"
                    "}\n"
                    "Rules:\n"
                    f"- Provide 3 to {max_facets} facets.\n"
                    "- At least 3 facets must be topic-specific (not audience/format/scope).\n"
                    "- Choices must be concrete and can include subchoices (up to 10).\n"
                    "- Keep ids short and snake_case.\n"
                    "- If the query mentions regions, locations, geographies, or areas, include a facet named \"Geographical Focus\" with options like \"National (All)\" and specific regions.\n"
                    "- Whenever you use the word \"specific\" in any facet title, question, or choice value, add a follow-up facet that lets the user choose the specific items or areas as multiple options (with up to 10 concrete choices).\n"
                ),
            ),
        ]
        raw, _ = llm_client.generate(prompt_sections)  # Unpack tuple, ignore reasoning
        parsed = self._parse_llm_json(raw)
        candidates: list[FacetCandidate] = []
        for item in parsed[:max_facets]:
            facet = self._to_facet(item)
            reason = item.get("reason") or self._reason_from_keywords(
                raw_query.lower(), facet
            )
            candidates.append(FacetCandidate(facet=facet, reason=reason))
        return candidates

    def discover_round2(
        self, raw_query: str, pack: dict, selected_ids: list[str]
    ) -> list[FacetCandidate]:
        refinements = pack.get("refinements", {})
        candidates: list[FacetCandidate] = []
        query = raw_query.lower()
        for selected_id in selected_ids:
            for item in refinements.get(selected_id, []):
                facet = self._to_facet(item)
                reason = self._reason_from_keywords(query, facet, selected_id)
                candidates.append(FacetCandidate(facet=facet, reason=reason))
        return candidates

    def discover_round2_llm(
        self,
        raw_query: str,
        pack: dict,
        selections: dict[str, str | None],
        max_facets: int,
        llm_client: "LLMClient",
    ) -> list[FacetCandidate]:
        prompt_sections = [
            (
                "Task",
                "Propose follow-up facets based on the user's selected facets and values.",
            ),
            ("User Query", raw_query.strip()),
            (
                "Selected Facets",
                json.dumps(selections, ensure_ascii=False),
            ),
            (
                "Domain Context",
                json.dumps(
                    {
                        "domain": pack.get("domain"),
                        "keywords": pack.get("keywords", []),
                    }
                ),
            ),
            (
                "Output JSON",
                (
                    "Return JSON only with this shape:\n"
                    "{\n"
                    '  "facets": [\n'
                    "    {\n"
                    '      "id": "subtopic",\n'
                    '      "title": "Subtopic Focus",\n'
                    '      "question": "Which subtopic should be expanded?",\n'
                    '      "reason": "Tie to selected facet/value",\n'
                    '      "choices": [\n'
                    '        {"value": "value1", "subchoices": ["sub1", "sub2"]},\n'
                    '        {"value": "value2", "subchoices": []}\n'
                    "      ],\n"
                    '      "default_value": "value1"\n'
                    "    }\n"
                    "  ]\n"
                    "}\n"
                    "Rules:\n"
                    f"- Provide 1 to {max_facets} facets.\n"
                    "- Must reflect the user's selections.\n"
                    "- Choices must be concrete and can include subchoices (up to 10).\n"
                    "- Keep ids short and snake_case.\n"
                ),
            ),
        ]
        raw, _ = llm_client.generate(prompt_sections)  # Unpack tuple, ignore reasoning
        parsed = self._parse_llm_json(raw)
        candidates: list[FacetCandidate] = []
        for item in parsed[:max_facets]:
            facet = self._to_facet(item)
            reason = item.get("reason") or "Derived from user selections"
            candidates.append(FacetCandidate(facet=facet, reason=reason))
        return candidates

    def _to_facet(self, data: dict) -> Facet:
        facet_id = data.get("id") or self._slugify(data.get("title", "facet"))
        choices_data = data.get("choices", [])
        choices: list[Choice] = []
        for item in choices_data:
            if isinstance(item, dict) and item.get("value"):
                choices.append(
                    Choice(
                        value=str(item["value"]),
                        subchoices=[str(v) for v in item.get("subchoices", []) if v],
                    )
                )

        if choices and all(choice.value.lower() != "all options" for choice in choices):
            choices.append(Choice(value="all options", subchoices=[]))

        suggested = list(data.get("suggested_values", []))
        if choices and not suggested:
            suggested = [choice.value for choice in choices]
        if suggested and all(val.lower() != "all options" for val in suggested):
            suggested.append("all options")
        return Facet(
            id=facet_id,
            title=data.get("title", facet_id),
            question=data.get("question", "Choose an option"),
            keywords=data.get("keywords", []),
            suggested_values=suggested,
            choices=choices,
            default_value=data.get("default_value"),
        )

    def _reason_from_keywords(
        self, query: str, facet: Facet, selected_id: str | None = None
    ) -> str:
        matches = [kw for kw in facet.keywords if kw.lower() in query]
        if matches:
            return f"Matches keywords: {', '.join(matches)}"
        if selected_id:
            return f"Refines selection: {selected_id}"
        return "Default facet for this domain"

    def _parse_llm_json(self, raw: str) -> list[dict]:
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
        facets = data.get("facets", [])
        if not isinstance(facets, list):
            return []
        return [item for item in facets if isinstance(item, dict)]

    def _slugify(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
        return text or "facet"
