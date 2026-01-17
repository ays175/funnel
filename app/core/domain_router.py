from __future__ import annotations

import json
from pathlib import Path


class DomainRouter:
    def __init__(self, packs_dir: Path) -> None:
        self.packs_dir = packs_dir

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
            if normalized in self.available_packs():
                return normalized

        query = raw_query.lower()
        for pack_name in self.available_packs():
            if pack_name == "universal":
                continue
            pack = self.load_pack(pack_name)
            keywords = pack.get("keywords", [])
            if any(keyword.lower() in query for keyword in keywords):
                return pack_name

        return "universal"
