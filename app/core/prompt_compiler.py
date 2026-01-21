from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptSection:
    title: str
    content: str


class PromptCompiler:
    def __init__(self):
        self._catalog_search = None
    
    def _get_catalog_search(self):
        """Lazy load catalog search to avoid circular imports."""
        if self._catalog_search is None:
            try:
                from app.catalog.catalog_search import CatalogSearch
                catalog_path = Path(__file__).parents[1] / "catalog" / "services.json"
                if catalog_path.exists():
                    self._catalog_search = CatalogSearch(catalog_path)
            except ImportError:
                pass
        return self._catalog_search

    def compile(
        self,
        raw_query: str,
        selections: dict[str, str | None],
        user_overrides: dict | None,
        proceed_defaults: dict[str, str],
        domain_pack: str | None = None,
    ) -> list[PromptSection]:
        applied_defaults = {
            facet_id: value
            for facet_id, value in proceed_defaults.items()
            if facet_id not in selections
        }

        selection_lines = [
            f"- {facet_id}: {value if value is not None else 'unspecified'}"
            for facet_id, value in selections.items()
        ]
        if applied_defaults:
            selection_lines.extend(
                f"- {facet_id}: {value} (default)" for facet_id, value in applied_defaults.items()
            )

        # Build sections
        sections = [
            PromptSection(title="User Query", content=raw_query.strip()),
            PromptSection(title="Selected Facets", content="\n".join(selection_lines) or "None"),
        ]
        
        # Add catalog services if available and in QDA domain
        catalog_search = self._get_catalog_search()
        if catalog_search and domain_pack == "qda_griffons":
            filtered_services = catalog_search.filter_services(selections, max_results=8)
            if filtered_services:
                from app.catalog.catalog_search import format_services_for_prompt
                services_text = format_services_for_prompt(filtered_services, max_services=6)
                sections.append(
                    PromptSection(
                        title="Services Recommandés (Catalogue Quartiers d'Affaires)",
                        content=services_text
                    )
                )
                
                # Add special instructions for catalog-based response
                catalog_instructions = (
                    "IMPORTANT: Vous répondez dans le contexte de Quartiers d'Affaires.\n"
                    "1. Recommandez UNIQUEMENT les services listés ci-dessus qui correspondent au profil.\n"
                    "2. Pour chaque service recommandé, expliquez POURQUOI il correspond à la situation.\n"
                    "3. Mentionnez les critères d'éligibilité et comment l'utilisateur les remplit.\n"
                    "4. Priorisez les programmes Quartiers d'Affaires (GRANDIR, ACCÉLÉRER, DÉCOLLER, etc.).\n"
                    "5. Si des services complémentaires existent (BPI, ADIE, etc.), mentionnez-les en second.\n"
                    "6. Structurez la réponse avec les services les plus pertinents en premier.\n"
                    "7. Pour chaque service, incluez: nom, pourquoi il convient, prochaine étape."
                )
                sections.append(
                    PromptSection(title="Instructions Spéciales", content=catalog_instructions)
                )

        # Standard instructions
        instructions = "Answer clearly and concisely."
        if user_overrides and user_overrides.get("instructions"):
            instructions = str(user_overrides["instructions"]).strip()

        sections.append(PromptSection(title="Instructions", content=instructions))
        
        return sections
