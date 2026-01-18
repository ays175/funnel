from __future__ import annotations

from groq import Groq

from app.core.config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required to call the model.")
        self.settings = settings
        self.client = Groq(api_key=settings.groq_api_key, timeout=settings.groq_timeout_seconds)

    def generate(self, prompt_sections: list[tuple[str, str]]) -> str:
        prompt_text = "\n\n".join(
            f"{title}\n{content}" for title, content in prompt_sections
        ).strip()
        response = self.client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a precise assistant."},
                {"role": "user", "content": prompt_text},
            ],
        )
        return response.choices[0].message.content or ""
