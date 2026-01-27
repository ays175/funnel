from __future__ import annotations

import json
from pathlib import Path


class DomainRouter:
    def __init__(self, packs_dir: Path) -> None:
        self.packs_dir = packs_dir
    
    def _pack_terms(self, pack: dict) -> list[str]:
        terms: list[str] = []
        for keyword in pack.get("keywords", []):
            terms.append(str(keyword))
        for facet in pack.get("facets", []):
            for value in [facet.get("title"), facet.get("question")]:
                if value:
                    terms.append(str(value))
            for choice in facet.get("choices", []):
                if isinstance(choice, dict) and choice.get("value"):
                    terms.append(str(choice["value"]))
                    for sub in choice.get("subchoices", []):
                        terms.append(str(sub))
        return [term.lower() for term in terms if term]

    def available_packs(self) -> list[str]:
        return sorted([p.stem for p in self.packs_dir.glob("*.json")])

    def load_pack(self, name: str) -> dict:
        pack_path = self.packs_dir / f"{name}.json"
        if not pack_path.exists():
            raise ValueError(f"Unknown domain pack: {name}")
        return json.loads(pack_path.read_text())

    def choose_pack(self, raw_query: str, domain_hint: str | None) -> str:
        if domain_hint:
            normalized = domain_hint.strip().lower()
            for pack_name in self.available_packs():
                if normalized == pack_name or normalized in pack_name or pack_name in normalized:
                    return pack_name
                pack = self.load_pack(pack_name)
                keywords = pack.get("keywords", [])
                if any(normalized in str(keyword).lower() for keyword in keywords):
                    return pack_name

        query = raw_query.lower()
        best_pack = "universal"
        best_score = 0
        for pack_name in self.available_packs():
            if pack_name == "universal":
                continue
            pack = self.load_pack(pack_name)
            terms = self._pack_terms(pack)
            score = sum(1 for term in terms if term and term in query)
            if score > best_score:
                best_score = score
                best_pack = pack_name

        return best_pack
