from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_models: str = "gemini-2.5-flash-lite,gemini-2.5-pro"
    gemini_embedding_model: str = "gemini-embedding-001"

    use_rag: bool = True
    chroma_db_path: str = "knowledge_base/chroma_db"
    chroma_collection: str = "meb_examples"

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = True

    @property
    def fallback_model_list(self) -> list[str]:
        return [m.strip() for m in self.gemini_fallback_models.split(",") if m.strip()]


settings = Settings()
