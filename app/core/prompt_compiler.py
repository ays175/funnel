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
        fact_answers: list[str] | None = None,
        client_answers: list[str] | None = None,
        fact_questions: list[str] | None = None,
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

        memo_instructions = (
            "You are drafting an internal legal memo from a junior associate to a senior partner. "
            "Tone: neutral, predictive, risk-aware. Use headings: Question Presented, Brief Answer, "
            "Facts, Assumptions & Unknowns, Applicable Law, Analysis (with counterarguments), Risks, "
            "and Next Steps. Use fact answers as Facts. Missing information must appear in "
            "Assumptions & Unknowns and be reflected in Next Steps. Use a bulleted list under "
            "Assumptions & Unknowns."
        )
        base_instructions = memo_instructions
        if user_overrides and user_overrides.get("instructions"):
            base_instructions = "\n".join(
                [memo_instructions, str(user_overrides["instructions"]).strip()]
            )

        instructions = base_instructions

        sections = [
            PromptSection(title="User Query", content=raw_query.strip()),
            PromptSection(title="Selected Facets", content="\n".join(selection_lines) or "None"),
        ]

        if fact_questions:
            sections.append(
                PromptSection(
                    title="Fact Questions",
                    content="\n".join(f"- {item}" for item in fact_questions if str(item).strip()),
                )
            )

        if fact_answers:
            sections.append(
                PromptSection(
                    title="Fact Answers",
                    content="\n".join(f"- {item}" for item in fact_answers if str(item).strip()),
                )
            )

        if fact_questions:
            answered_questions = {
                str(item).split(":", 1)[0].strip() for item in (fact_answers or []) if ":" in str(item)
            }
            unanswered = [
                question for question in fact_questions if question and question not in answered_questions
            ]
            if unanswered:
                sections.append(
                    PromptSection(
                        title="Unanswered Fact Questions",
                        content="\n".join(f"- {item}" for item in unanswered if str(item).strip()),
                    )
                )

        if client_answers:
            sections.append(
                PromptSection(
                    title="Client Answers",
                    content="\n".join(
                        f"- {item}" for item in client_answers if str(item).strip()
                    ),
                )
            )

        sections.append(PromptSection(title="Instructions", content=instructions))
        return sections
