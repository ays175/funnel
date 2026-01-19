from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv

try:
    load_dotenv()
except PermissionError:
    # Fall back to existing environment variables if .env is unreadable.
    pass


def _req(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    openai_timeout_seconds: int

    app_env: str
    app_host: str
    app_port: int
    cors_origins: list[str]

    trace_db_url: str
    trace_retention_days: int

    enable_llm_facet_proposals: bool
    enable_retrieval: bool
    max_facet_questions: int
    max_refine_rounds: int

    require_user_confirm_before_final: bool
    allow_user_prompt_edit: bool


def load_settings() -> Settings:
    cors = os.getenv("CORS_ORIGINS", "")
    cors_list = [item.strip() for item in cors.split(",") if item.strip()]

    def _bool(name: str, default: str = "false") -> bool:
        return os.getenv(name, default).lower() in {"1", "true", "yes", "y"}

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "o3-mini-2025-01-31"),
        openai_timeout_seconds=int(os.getenv("OPENAI_TIMEOUT_SECONDS", "120")),
        app_env=os.getenv("APP_ENV", "dev"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        cors_origins=cors_list,
        trace_db_url=os.getenv("TRACE_DB_URL", "sqlite:///./trace.db"),
        trace_retention_days=int(os.getenv("TRACE_RETENTION_DAYS", "30")),
        enable_llm_facet_proposals=_bool("ENABLE_LLM_FACET_PROPOSALS", "true"),
        enable_retrieval=_bool("ENABLE_RETRIEVAL", "false"),
        max_facet_questions=int(os.getenv("MAX_FACET_QUESTIONS", "10")),
        max_refine_rounds=int(os.getenv("MAX_REFINE_ROUNDS", "2")),
        require_user_confirm_before_final=_bool(
            "REQUIRE_USER_CONFIRM_BEFORE_FINAL", "true"
        ),
        allow_user_prompt_edit=_bool("ALLOW_USER_PROMPT_EDIT", "true"),
    )
