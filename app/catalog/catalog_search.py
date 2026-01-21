"""
Catalog search engine for filtering services based on user selections.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class CatalogSearch:
    """Search and filter services from the catalog based on user selections."""

    def __init__(self, catalog_path: str | Path | None = None):
        if catalog_path is None:
            catalog_path = Path(__file__).parent / "services.json"
        self.catalog_path = Path(catalog_path)
        self.services = self._load_catalog()

    def _load_catalog(self) -> list[dict]:
        """Load services from JSON catalog."""
        if not self.catalog_path.exists():
            return []
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("services", [])

    def filter_services(
        self, 
        selections: dict[str, str | None],
        max_results: int = 10
    ) -> list[dict]:
        """
        Filter services based on user selections.
        
        Args:
            selections: Dict of facet_id -> selected value
            max_results: Maximum number of services to return
            
        Returns:
            List of matching services, sorted by relevance score
        """
        scored_services = []
        
        # Parse selections into structured data
        parsed = self._parse_selections(selections)
        
        for service in self.services:
            score = self._calculate_match_score(service, parsed)
            if score > 0:
                scored_services.append({
                    **service,
                    "_score": score,
                    "_match_reasons": self._get_match_reasons(service, parsed)
                })
        
        # Sort by score descending
        scored_services.sort(key=lambda x: x["_score"], reverse=True)
        
        return scored_services[:max_results]

    def _parse_selections(self, selections: dict[str, str | None]) -> dict[str, Any]:
        """Parse user selections into structured data for matching."""
        parsed = {
            "years": None,
            "revenue": None,
            "employees": None,
            "needs": [],
            "profiles": [],
            "location": None,
            "stage": None,
        }
        
        for facet_id, value in selections.items():
            if value is None:
                continue
                
            value_lower = value.lower()
            
            # Business stage
            if facet_id == "business_stage":
                if "idée" in value_lower or "projet" in value_lower:
                    parsed["stage"] = "idée"
                    parsed["years"] = 0
                elif "< 2 ans" in value_lower or "jeune" in value_lower:
                    parsed["stage"] = "jeune"
                    parsed["years"] = 1
                elif "2-5 ans" in value_lower or "établie" in value_lower:
                    parsed["stage"] = "établie"
                    parsed["years"] = 3
                elif "> 5 ans" in value_lower or "mature" in value_lower:
                    parsed["stage"] = "mature"
                    parsed["years"] = 6
            
            # Revenue
            elif facet_id == "revenue_range":
                if "pas encore" in value_lower:
                    parsed["revenue"] = 0
                elif "moins de 50" in value_lower or "< 50" in value_lower:
                    parsed["revenue"] = 25000
                elif "50 000" in value_lower and "100 000" in value_lower:
                    parsed["revenue"] = 75000
                elif "100 000" in value_lower and "500 000" in value_lower:
                    parsed["revenue"] = 250000
                elif "plus de 500" in value_lower or "> 500" in value_lower:
                    parsed["revenue"] = 600000
            
            # Employees
            elif facet_id == "employees":
                if "solo" in value_lower or "seul" in value_lower:
                    parsed["employees"] = 0
                elif "1 à 5" in value_lower or "1-5" in value_lower:
                    parsed["employees"] = 3
                elif "6 à 20" in value_lower or "6-20" in value_lower:
                    parsed["employees"] = 10
                elif "plus de 20" in value_lower or "> 20" in value_lower:
                    parsed["employees"] = 25
            
            # Main needs
            elif facet_id == "main_need":
                needs_map = {
                    "financement": ["financement", "prêt", "subvention", "investisseur", "garantie"],
                    "formation": ["formation", "gestion", "digital", "commercial", "export"],
                    "accompagnement": ["accompagnement", "mentorat", "coaching", "réseau", "conseil"],
                    "recrutement": ["recrutement", "alternance", "stage", "cdi", "équipe"],
                    "formalités": ["formalités", "création", "modification", "certifications"],
                }
                for key, keywords in needs_map.items():
                    if any(kw in value_lower for kw in keywords):
                        parsed["needs"].append(key)
            
            # Profile
            elif facet_id == "profile":
                if "femme" in value_lower:
                    parsed["profiles"].append("femme")
                if "jeune" in value_lower or "< 26" in value_lower:
                    parsed["profiles"].append("jeune")
                if "senior" in value_lower or "> 50" in value_lower:
                    parsed["profiles"].append("senior")
                if "handicap" in value_lower or "rqth" in value_lower:
                    parsed["profiles"].append("handicap")
                if "demandeur" in value_lower or "chômage" in value_lower:
                    parsed["profiles"].append("demandeur_emploi")
                if "rsa" in value_lower:
                    parsed["profiles"].append("rsa")
            
            # Location
            elif facet_id == "location":
                parsed["location"] = value_lower
                if "île-de-france" in value_lower or "idf" in value_lower or "paris" in value_lower or "93" in value_lower or "seine-saint-denis" in value_lower:
                    parsed["location"] = "ile-de-france"
        
        return parsed

    def _calculate_match_score(self, service: dict, parsed: dict) -> float:
        """
        Calculate match score for a service based on parsed selections.
        
        Returns a score from 0 to 1, where higher is better.
        """
        score = 0.0
        eligibility = service.get("eligibility", {})
        
        # Base score for being in catalog
        score += 0.1
        
        # Check eligibility criteria
        
        # Years in business
        if parsed["years"] is not None:
            min_years = eligibility.get("min_years", 0)
            max_years = eligibility.get("max_years", 100)
            if min_years <= parsed["years"] <= max_years:
                score += 0.15
            elif parsed["years"] < min_years:
                # Slightly negative if not yet eligible
                score -= 0.05
        
        # Revenue
        if parsed["revenue"] is not None:
            min_revenue = eligibility.get("min_revenue", 0)
            max_revenue = eligibility.get("max_revenue", float("inf"))
            if min_revenue <= parsed["revenue"] <= max_revenue:
                score += 0.15
            elif parsed["revenue"] < min_revenue:
                # Future eligibility possible
                score += 0.02
        
        # Employees
        if parsed["employees"] is not None:
            min_emp = eligibility.get("min_employees", 0)
            max_emp = eligibility.get("max_employees", float("inf"))
            if min_emp <= parsed["employees"] <= max_emp:
                score += 0.1
        
        # Profile matching (big bonus)
        profile_eligibility = eligibility.get("profile", [])
        if profile_eligibility and parsed["profiles"]:
            for profile in parsed["profiles"]:
                if profile in profile_eligibility:
                    score += 0.25
        
        # Needs matching
        category = service.get("category", "")
        subcategory = service.get("subcategory", "")
        tags = service.get("tags", [])
        
        for need in parsed["needs"]:
            if need in category or need in subcategory:
                score += 0.2
            if any(need in tag for tag in tags):
                score += 0.1
        
        # Location matching
        if parsed["location"]:
            loc_eligibility = eligibility.get("location", "all")
            if loc_eligibility == "all":
                score += 0.05
            elif parsed["location"] in str(loc_eligibility).lower():
                score += 0.15
            elif "qpv" in str(loc_eligibility).lower():
                # QPV services get bonus for likely QPV users
                score += 0.1
        
        # Bonus for free services
        if service.get("price", 0) == 0:
            score += 0.05
        
        # Bonus for QDA services (flagship)
        if service.get("provider") == "Quartiers d'Affaires":
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0

    def _get_match_reasons(self, service: dict, parsed: dict) -> list[str]:
        """Generate human-readable reasons why this service matches."""
        reasons = []
        eligibility = service.get("eligibility", {})
        
        # Check what makes this service relevant
        if parsed["years"] is not None:
            min_years = eligibility.get("min_years", 0)
            max_years = eligibility.get("max_years", 100)
            if min_years <= parsed["years"] <= max_years:
                if min_years == 0 and max_years < 100:
                    reasons.append(f"Adapté aux entreprises de moins de {max_years} ans")
                elif min_years > 0:
                    reasons.append(f"Vous avez l'ancienneté requise ({min_years}+ ans)")
        
        if parsed["revenue"] is not None:
            min_revenue = eligibility.get("min_revenue", 0)
            if parsed["revenue"] >= min_revenue and min_revenue > 0:
                reasons.append(f"Votre CA correspond aux critères (>{min_revenue:,}€)")
        
        # Profile reasons
        profile_eligibility = eligibility.get("profile", [])
        for profile in parsed["profiles"]:
            if profile in profile_eligibility:
                profile_labels = {
                    "femme": "Programme dédié aux femmes entrepreneures",
                    "jeune": "Programme dédié aux jeunes entrepreneurs",
                    "senior": "Programme dédié aux seniors",
                    "handicap": "Aide spécifique handicap",
                    "demandeur_emploi": "Accessible aux demandeurs d'emploi",
                    "rsa": "Accessible aux bénéficiaires RSA",
                }
                reasons.append(profile_labels.get(profile, f"Correspond à votre profil"))
        
        # Category reasons
        category = service.get("category", "")
        for need in parsed["needs"]:
            if need in category:
                need_labels = {
                    "financement": "Répond à votre besoin de financement",
                    "formation": "Répond à votre besoin de formation",
                    "accompagnement": "Répond à votre besoin d'accompagnement",
                    "recrutement": "Répond à votre besoin de recrutement",
                }
                reasons.append(need_labels.get(need, f"Correspond à vos besoins"))
        
        # Price reason
        if service.get("price", 0) == 0:
            reasons.append("Gratuit")
        
        return reasons[:3]  # Limit to 3 reasons

    def get_service_by_id(self, service_id: str) -> dict | None:
        """Get a specific service by its ID."""
        for service in self.services:
            if service.get("id") == service_id:
                return service
        return None

    def get_services_by_category(self, category: str) -> list[dict]:
        """Get all services in a specific category."""
        return [s for s in self.services if s.get("category") == category]

    def get_all_categories(self) -> list[str]:
        """Get list of all unique categories."""
        return list(set(s.get("category", "") for s in self.services))


def format_services_for_prompt(services: list[dict], max_services: int = 5) -> str:
    """
    Format filtered services into a string for injection into the LLM prompt.
    
    Args:
        services: List of services from filter_services()
        max_services: Maximum number to include
        
    Returns:
        Formatted string for prompt injection
    """
    if not services:
        return "Aucun service spécifique trouvé pour ce profil."
    
    lines = ["SERVICES CORRESPONDANT À VOTRE PROFIL :\n"]
    
    for i, service in enumerate(services[:max_services], 1):
        lines.append(f"{i}. **{service['name']}** ({service['provider']})")
        lines.append(f"   {service['description'][:200]}...")
        
        # Add match reasons
        reasons = service.get("_match_reasons", [])
        if reasons:
            lines.append(f"   ✓ {' | '.join(reasons)}")
        
        # Add highlights
        highlights = service.get("highlights", [])
        if highlights:
            lines.append(f"   → {', '.join(highlights[:2])}")
        
        # Add price info
        price = service.get("price", 0)
        if price == 0:
            lines.append("   💰 Gratuit")
        else:
            lines.append(f"   💰 {price:,}€")
        
        lines.append("")
    
    return "\n".join(lines)
