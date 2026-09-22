from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_fallback_models: str = ""
    openrouter_timeout: float = 60.0
    openrouter_max_retries: int = 3
    ai_provider: str = "openrouter"
    local_model_path: str = ""
    database_url: str = "sqlite:///./interlingo.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
