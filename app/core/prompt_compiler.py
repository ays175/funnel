from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptSection:
    title: str
    content: str


class PromptCompiler:
    def compile(
        self,
        raw_query: str,
        selections: dict[str, str | None],
        user_overrides: dict | None,
        proceed_defaults: dict[str, str],
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

        base_instructions = "Answer clearly and concisely."
        if user_overrides and user_overrides.get("instructions"):
            base_instructions = str(user_overrides["instructions"]).strip()

        extra_instructions: list[str] = []
        deliverable = str(selections.get("deliverable_type", "") or "")
        if "memo" in deliverable.lower():
            extra_instructions.append(
                "Use a legal memo format with clear headings: Issue, Background/Assumptions, "
                "Applicable Law, Analysis, Risks, and Recommended Next Steps."
            )

        instructions = "\n".join(
            line for line in [base_instructions, *extra_instructions] if line
        )

        sections = [
            PromptSection(title="User Query", content=raw_query.strip()),
            PromptSection(title="Selected Facets", content="\n".join(selection_lines) or "None"),
        ]

        client_answers = selections.get("client_answers")
        if client_answers:
            sections.append(
                PromptSection(title="Client Answers", content=str(client_answers).strip())
            )

        sections.append(PromptSection(title="Instructions", content=instructions))
        return sections
