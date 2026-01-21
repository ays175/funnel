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
        self._member_search = None
    
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

    def _get_member_search(self):
        """Lazy load member search to avoid circular imports."""
        if self._member_search is None:
            try:
                from app.catalog.member_search import MemberSearch
                members_path = Path(__file__).parents[1] / "catalog" / "members.json"
                if members_path.exists():
                    self._member_search = MemberSearch()
            except ImportError:
                pass
        return self._member_search

    def _extract_sector_id(self, sector_label: str) -> str | None:
        """Convert sector label to sector ID."""
        sector_map = {
            "accounting": ["accounting", "tax", "comptab"],
            "digital": ["it", "digital", "informatique", "web"],
            "marketing": ["marketing", "communication", "com"],
            "legal": ["legal", "juridique", "law"],
            "hr": ["hr", "recruitment", "recrutement", "rh"],
            "construction": ["construction", "renovation", "btp", "travaux"],
            "transport": ["transport", "logistics", "logistique"],
            "training": ["training", "formation", "professional"],
            "cleaning": ["cleaning", "nettoyage", "maintenance", "entretien"],
            "catering": ["catering", "food", "restauration", "traiteur"],
            "telecom": ["telecom", "phone", "communication", "fiber"],
        }
        
        label_lower = sector_label.lower()
        for sector_id, keywords in sector_map.items():
            for keyword in keywords:
                if keyword in label_lower:
                    return sector_id
        return None

    def _extract_department(self, location: str) -> str | None:
        """Extract department code from location string."""
        import re
        # Look for patterns like (93), (75), etc.
        match = re.search(r'\((\d{2,3})\)', location)
        if match:
            return match.group(1)
        
        # Look for department names
        dept_names = {
            "paris": "75",
            "seine-saint-denis": "93",
            "val-d'oise": "95",
            "hauts-de-seine": "92",
            "rhône": "69",
            "bouches-du-rhône": "13",
            "nord": "59",
            "gironde": "33",
            "haute-garonne": "31",
            "bas-rhin": "67",
        }
        
        location_lower = location.lower()
        for name, code in dept_names.items():
            if name in location_lower:
                return code
        
        return None

    def _extract_region(self, location: str) -> str | None:
        """Extract region from location string."""
        regions = [
            "Île-de-France", "Auvergne-Rhône-Alpes", "PACA", 
            "Hauts-de-France", "Occitanie", "Grand Est",
            "Nouvelle-Aquitaine", "Normandie", "Bretagne",
            "Pays de la Loire", "Centre-Val de Loire",
            "Bourgogne-Franche-Comté", "Corse", "DOM"
        ]
        
        location_lower = location.lower()
        for region in regions:
            if region.lower() in location_lower:
                return region
        
        return None

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
        
        # Check if this is a QDA domain request
        if domain_pack == "qda_griffons":
            # Determine search type
            search_type = selections.get("search_type", "Programs & Funding")
            
            if "service provider" in search_type.lower() or "member" in search_type.lower():
                # Member search mode
                self._add_member_results(sections, selections)
            else:
                # Programs & funding search mode
                self._add_catalog_results(sections, selections, domain_pack)

        # Standard instructions
        instructions = "Answer clearly and concisely."
        if user_overrides and user_overrides.get("instructions"):
            instructions = str(user_overrides["instructions"]).strip()

        sections.append(PromptSection(title="Instructions", content=instructions))
        
        return sections

    def _add_catalog_results(
        self, 
        sections: list[PromptSection], 
        selections: dict[str, str | None],
        domain_pack: str
    ):
        """Add catalog service results to prompt sections."""
        catalog_search = self._get_catalog_search()
        if not catalog_search:
            return
            
        filtered_services = catalog_search.filter_services(selections, max_results=8)
        if filtered_services:
            from app.catalog.catalog_search import format_services_for_prompt
            services_text = format_services_for_prompt(filtered_services, max_services=6)
            sections.append(
                PromptSection(
                    title="Recommended Services (Quartiers d'Affaires Catalog)",
                    content=services_text
                )
            )
            
            # Add special instructions for catalog-based response
            catalog_instructions = (
                "IMPORTANT: You are responding in the Quartiers d'Affaires context.\n"
                "1. ONLY recommend services listed above that match the user's profile.\n"
                "2. For each recommended service, explain WHY it fits their situation.\n"
                "3. Mention eligibility criteria and how the user meets them.\n"
                "4. Prioritize Quartiers d'Affaires programs (GRANDIR, ACCÉLÉRER, DÉCOLLER, etc.).\n"
                "5. If complementary services exist (BPI, ADIE, etc.), mention them second.\n"
                "6. Structure the response with most relevant services first.\n"
                "7. For each service, include: name, why it fits, next steps."
            )
            sections.append(
                PromptSection(title="Special Instructions", content=catalog_instructions)
            )

    def _add_member_results(
        self, 
        sections: list[PromptSection], 
        selections: dict[str, str | None]
    ):
        """Add member search results to prompt sections."""
        member_search = self._get_member_search()
        if not member_search:
            return
        
        # Extract search parameters from selections
        sector_label = selections.get("service_sector")
        sector_id = self._extract_sector_id(sector_label) if sector_label else None
        
        location = selections.get("location", "")
        department = self._extract_department(location) if location else None
        region = self._extract_region(location) if location else None
        
        # Search members
        members = member_search.search_members(
            sector=sector_id,
            department=department,
            region=region,
            max_results=6
        )
        
        if members:
            from app.catalog.member_search import format_members_for_prompt
            members_text = format_members_for_prompt(members, max_members=5, include_contact=True)
            sections.append(
                PromptSection(
                    title="QDA Member Businesses Matching Your Search",
                    content=members_text
                )
            )
            
            # Add special instructions for member recommendations
            member_instructions = (
                "IMPORTANT: You are helping find a service provider from the QDA network.\n"
                "1. Present the matching QDA member businesses shown above.\n"
                "2. Highlight why each provider is a good fit (location, services, ratings).\n"
                "3. Emphasize that these are QDA member businesses (trusted network).\n"
                "4. Include their contact details (phone, email) prominently.\n"
                "5. Remind the user to mention 'Quartiers d'Affaires' for preferential rates.\n"
                "6. If the user wants to contact a specific provider, format a clear contact card.\n"
                "7. Suggest the user specify their exact needs when reaching out."
            )
            sections.append(
                PromptSection(title="Special Instructions", content=member_instructions)
            )
        else:
            sections.append(
                PromptSection(
                    title="Search Results",
                    content="No QDA member businesses found matching your exact criteria. Try broadening your search (different region or sector)."
                )
            )
