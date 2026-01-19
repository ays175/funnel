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
        
        # Build API parameters
        api_params = {
            "model": self.settings.openai_model,
        }
        
        # For o-series models, use different message format and reasoning_effort
        if self.settings.openai_model.startswith("o3") or self.settings.openai_model.startswith("o1"):
            api_params["messages"] = [
                {"role": "user", "content": prompt_text},
            ]
            api_params["reasoning_effort"] = "high"
        else:
            # For GPT-4 and other models, use standard format with system message
            api_params["messages"] = [
                {"role": "system", "content": "You are a precise assistant."},
                {"role": "user", "content": prompt_text},
            ]
        
        response = self.client.chat.completions.create(**api_params)
        
        message = response.choices[0].message
        answer = message.content or ""
        
        # For o-series models (o1, o3-mini, etc.), capture reasoning tokens
        # Try multiple possible attribute names
        reasoning = (
            getattr(message, "reasoning_content", None) or
            getattr(message, "reasoning", None) or
            (message.model_extra.get("reasoning_content") if hasattr(message, "model_extra") else None)
        )
        
        return answer, reasoning
