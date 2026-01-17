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

        instructions = "Answer clearly and concisely."
        if user_overrides and user_overrides.get("instructions"):
            instructions = str(user_overrides["instructions"]).strip()

        return [
            PromptSection(title="User Query", content=raw_query.strip()),
            PromptSection(title="Selected Facets", content="\n".join(selection_lines) or "None"),
            PromptSection(title="Instructions", content=instructions),
        ]
