from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_fallback_models: str = "gemini-2.5-flash-lite,gemini-2.5-pro"
    gemini_embedding_model: str = "gemini-embedding-001"

    # Multi-provider fallback: Gemini ailesi tükenince Anthropic'e geç.
    enable_anthropic_fallback: bool = False
    anthropic_api_key: str = ""
    anthropic_fallback_model: str = "claude-sonnet-4-6"

    use_rag: bool = True
    chroma_db_path: str = "knowledge_base/chroma_db"
    chroma_collection: str = "meb_examples"

    enable_semantic_dedup: bool = True
    semantic_dedup_threshold: float = 0.88

    enable_critic: bool = True
    critic_model: str = "gemini-2.5-flash-lite"
    critic_min_confidence: float = 0.6

    enable_math_verifier: bool = True

    enable_history_persist: bool = True
    history_db_path: str = "knowledge_base/history.sqlite3"

    enable_hybrid_retrieval: bool = True
    hybrid_bm25_weight: float = 0.3  # RRF fusion'da BM25'in göreceli ağırlığı
    hybrid_rrf_k: int = 60  # standart Reciprocal Rank Fusion sabiti

    # Rate limit + API key
    api_keys: str = ""  # virgülle ayrılmış geçerli key'ler. Boşsa auth devre dışı.
    rate_limit_per_hour: int = 30
    rate_limit_per_minute: int = 5

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = True

    @property
    def fallback_model_list(self) -> list[str]:
        return [m.strip() for m in self.gemini_fallback_models.split(",") if m.strip()]


settings = Settings()
