"""
Member search engine for finding service providers in the QDA network.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MemberSearch:
    """Search and filter member businesses from the QDA network."""

    def __init__(
        self,
        members_path: str | Path | None = None,
        sectors_path: str | Path | None = None,
        departments_path: str | Path | None = None,
    ):
        base_dir = Path(__file__).parent
        
        if members_path is None:
            members_path = base_dir / "members.json"
        if sectors_path is None:
            sectors_path = base_dir / "sectors.json"
        if departments_path is None:
            departments_path = base_dir / "departments.json"
            
        self.members = self._load_json(members_path, "members")
        self.sectors = self._load_json(sectors_path, "sectors")
        self.departments = self._load_json(departments_path, "departments")
        
        # Build indexes
        self._sector_index = {s["id"]: s for s in self.sectors}
        self._dept_index = {d["code"]: d for d in self.departments}

    def _load_json(self, path: Path, key: str) -> list[dict]:
        """Load JSON data from file."""
        path = Path(path)
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, [])

    def search_members(
        self,
        sector: str | None = None,
        department: str | None = None,
        region: str | None = None,
        keywords: list[str] | None = None,
        min_rating: float | None = None,
        max_results: int = 10,
    ) -> list[dict]:
        """
        Search for member businesses with various filters.
        
        Args:
            sector: Sector ID to filter by (e.g., "digital", "accounting")
            department: Department code to filter by (e.g., "93", "75")
            region: Region name to filter by (e.g., "Île-de-France")
            keywords: Keywords to search in name, description, services
            min_rating: Minimum rating filter
            max_results: Maximum number of results to return
            
        Returns:
            List of matching members, sorted by relevance score
        """
        scored_members = []
        
        for member in self.members:
            score = self._calculate_score(
                member, sector, department, region, keywords, min_rating
            )
            if score > 0:
                scored_members.append({
                    **member,
                    "_score": score,
                })
        
        # Sort by score (descending), then by rating
        scored_members.sort(
            key=lambda x: (x["_score"], x["stats"]["rating"]),
            reverse=True
        )
        
        return scored_members[:max_results]

    def _calculate_score(
        self,
        member: dict,
        sector: str | None,
        department: str | None,
        region: str | None,
        keywords: list[str] | None,
        min_rating: float | None,
    ) -> float:
        """Calculate relevance score for a member."""
        score = 0.0
        
        # Rating filter (disqualifying)
        if min_rating and member["stats"]["rating"] < min_rating:
            return 0.0
        
        # Sector match (required if specified)
        if sector:
            # Normalize sector input
            sector_lower = sector.lower()
            member_sector = member["sector"].lower()
            
            # Direct match
            if member_sector == sector_lower:
                score += 1.0
            # Partial match via keywords
            elif self._sector_matches_keywords(member_sector, sector_lower):
                score += 0.8
            else:
                return 0.0  # Sector mismatch = disqualified
        else:
            score += 0.1  # Base score if no sector filter
        
        # Department match (required if specified)
        if department:
            dept_lower = department.lower().strip()
            member_dept = member["location"]["department"].lower()
            
            if member_dept == dept_lower:
                score += 0.5
            else:
                return 0.0  # Department mismatch = disqualified
        
        # Region match (required if specified, when no department)
        elif region:
            member_region = member["location"]["region"].lower()
            region_lower = region.lower()
            
            # Handle PACA alias
            if region_lower == "paca":
                region_lower = "provence-alpes-côte d'azur"
            
            if member_region == region_lower or region_lower in member_region or member_region in region_lower:
                score += 0.3
            else:
                return 0.0  # Region mismatch = disqualified
        
        # Keyword matching
        if keywords:
            keyword_score = self._keyword_score(member, keywords)
            score += keyword_score * 0.3
        
        # Rating bonus
        rating = member["stats"]["rating"]
        score += (rating - 4.0) * 0.1  # Bonus for ratings above 4.0
        
        # QDA program bonus
        if member["qda_member"].get("program"):
            score += 0.05
        
        # Reviews bonus (more reviews = more trusted)
        reviews = member["stats"]["reviews_count"]
        score += min(reviews / 100, 0.1)
        
        return score

    def _sector_matches_keywords(self, member_sector: str, search_term: str) -> bool:
        """Check if a sector matches via keywords."""
        sector_info = self._sector_index.get(member_sector, {})
        keywords = sector_info.get("keywords", [])
        
        for keyword in keywords:
            if search_term in keyword.lower() or keyword.lower() in search_term:
                return True
        
        # Also check sector name
        sector_name = sector_info.get("name", "").lower()
        if search_term in sector_name:
            return True
            
        return False

    def _keyword_score(self, member: dict, keywords: list[str]) -> float:
        """Calculate keyword match score."""
        score = 0.0
        
        # Build searchable text
        searchable = " ".join([
            member["company_name"],
            member["description"],
            member["sector_label"],
            " ".join(member.get("services", [])),
            member["location"]["city"],
            member["location"]["department_name"],
        ]).lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in searchable:
                score += 1.0
        
        # Normalize by number of keywords
        return score / len(keywords) if keywords else 0.0

    def get_member_by_id(self, member_id: str) -> dict | None:
        """Get a specific member by ID."""
        for member in self.members:
            if member["id"] == member_id:
                return member
        return None

    def get_member_contact(self, member_id: str) -> dict | None:
        """
        Get contact details for a specific member.
        Returns formatted contact information for display.
        """
        member = self.get_member_by_id(member_id)
        if not member:
            return None
        
        contact = member["contact"]
        location = member["location"]
        founder = member["founder"]
        
        return {
            "company_name": member["company_name"],
            "contact_person": contact.get("contact_person", founder["name"]),
            "title": founder["title"],
            "phone": contact["phone"],
            "mobile": contact.get("mobile"),
            "email": contact["email"],
            "website": contact.get("website"),
            "preferred_contact": contact.get("preferred_contact", "phone"),
            "address": {
                "city": location["city"],
                "postal_code": location["postal_code"],
                "department": location["department_name"],
                "region": location["region"],
            },
            "qda_badge": f"QDA Member since {member['qda_member']['since']}",
            "qda_program": member["qda_member"].get("program"),
            "discount_message": "Mention 'Quartiers d'Affaires' to get preferential rates",
        }

    def get_sectors_list(self) -> list[dict]:
        """Get list of all available sectors."""
        return [
            {"id": s["id"], "name": s["name"], "name_fr": s["name_fr"]}
            for s in self.sectors
        ]

    def get_departments_by_region(self, region: str | None = None) -> list[dict]:
        """Get departments, optionally filtered by region."""
        if region:
            return [
                {"code": d["code"], "name": d["name"]}
                for d in self.departments
                if d["region"].lower() == region.lower()
            ]
        return [{"code": d["code"], "name": d["name"]} for d in self.departments]

    def get_regions_list(self) -> list[str]:
        """Get list of unique regions."""
        return list(set(d["region"] for d in self.departments))


def format_members_for_prompt(
    members: list[dict],
    max_members: int = 5,
    include_contact: bool = False,
) -> str:
    """
    Format member search results for injection into LLM prompt.
    
    Args:
        members: List of members from search_members()
        max_members: Maximum number to include
        include_contact: Whether to include full contact details
        
    Returns:
        Formatted string for prompt injection
    """
    if not members:
        return "No member businesses found matching your criteria."
    
    lines = ["QDA MEMBER BUSINESSES MATCHING YOUR SEARCH:\n"]
    
    for i, member in enumerate(members[:max_members], 1):
        rating = member["stats"]["rating"]
        reviews = member["stats"]["reviews_count"]
        stars = "★" * int(rating) + "☆" * (5 - int(rating))
        
        lines.append(f"{i}. **{member['company_name']}** {stars} ({rating}/5, {reviews} reviews)")
        lines.append(f"   📍 {member['location']['city']} ({member['location']['department']}) - {member['location']['region']}")
        lines.append(f"   💼 {member['sector_label']}")
        lines.append(f"   📝 Services: {', '.join(member['services'][:4])}")
        
        if member["qda_member"].get("program"):
            lines.append(f"   🏆 QDA {member['qda_member']['program']} alumnus")
        
        if include_contact:
            contact = member["contact"]
            lines.append(f"   ☎️  {contact['phone']}")
            lines.append(f"   📧  {contact['email']}")
            if contact.get("website"):
                lines.append(f"   🌐  {contact['website']}")
        
        lines.append("")
    
    if not include_contact:
        lines.append("💡 Select a member to get full contact details (phone, email, website).")
    
    return "\n".join(lines)


def format_contact_card(contact: dict) -> str:
    """
    Format contact details as a card for display.
    
    Args:
        contact: Contact dict from get_member_contact()
        
    Returns:
        Formatted contact card string
    """
    if not contact:
        return "Member not found."
    
    lines = [
        f"═══════════════════════════════════════════════",
        f"  📞 CONTACT: {contact['company_name']}",
        f"═══════════════════════════════════════════════",
        f"",
        f"  👤 {contact['contact_person']}",
        f"     {contact['title']}",
        f"",
        f"  ☎️  Phone: {contact['phone']}",
    ]
    
    if contact.get("mobile"):
        lines.append(f"  📱 Mobile: {contact['mobile']}")
    
    lines.extend([
        f"  📧  Email: {contact['email']}",
    ])
    
    if contact.get("website"):
        lines.append(f"  🌐  Web: {contact['website']}")
    
    address = contact["address"]
    lines.extend([
        f"",
        f"  📍 {address['city']} ({address['postal_code']})",
        f"     {address['department']}, {address['region']}",
        f"",
        f"  ───────────────────────────────────────────",
        f"  🏆 {contact['qda_badge']}",
    ])
    
    if contact.get("qda_program"):
        lines.append(f"     Program: {contact['qda_program']}")
    
    lines.extend([
        f"",
        f"  💬 \"{contact['discount_message']}\"",
        f"═══════════════════════════════════════════════",
    ])
    
    return "\n".join(lines)
