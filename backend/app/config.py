from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    orca_base_url: str = "https://api.orcarouter.ai/v1/chat/completions"
    orca_api_key: str = ""
    orca_model: str = "z-ai/glm-5.3-flash-free"
    orca_fallback_models: str = ""
    orca_timeout: float = 60.0
    orca_max_retries: int = 3
    ai_provider: str = "orcarouter"
    local_model_path: str = ""
    database_url: str = "sqlite:///./interlingo.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
