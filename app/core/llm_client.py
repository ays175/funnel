from __future__ import annotations

from openai import OpenAI

from app.core.config import Settings


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to call the model.")
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)

    def generate(self, prompt_sections: list[tuple[str, str]]) -> tuple[str, str | None]:
        """
        Generate response from LLM.
        
        Returns:
            tuple: (answer, reasoning) where reasoning is the model's internal reasoning
                   (available for o-series models like o1, o3-mini) or None
        """
        prompt_text = "\n\n".join(
            f"{title}\n{content}" for title, content in prompt_sections
        ).strip()
        response = self.client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a precise assistant."},
                {"role": "user", "content": prompt_text},
            ],
        )
        
        message = response.choices[0].message
        answer = message.content or ""
        
        # For o-series models (o1, o3-mini, etc.), capture reasoning tokens
        reasoning = getattr(message, "reasoning_content", None)
        
        return answer, reasoning
