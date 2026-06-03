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

    # Latency: ilk üretim batch'ini hedeften fazla iste ki math/critic elemeleri
    # seri post-filter top-up turu açmadan absorbe edilsin. 1.0 = kapalı (eski
    # davranış). ~1.3 → ilk çağrı %30 fazla soru ister, sonda hedefe kırpılır.
    generation_overshoot_ratio: float = 1.3

    enable_history_persist: bool = True
    history_db_path: str = "knowledge_base/history.sqlite3"

    # Kullanıcı (tenant) bazlı çalışma kağıdı geçmişi — /api/worksheets/history
    enable_worksheet_history: bool = True
    worksheet_history_max_per_tenant: int = 50

    enable_hybrid_retrieval: bool = True
    hybrid_bm25_weight: float = 0.3  # RRF fusion'da BM25'in göreceli ağırlığı
    hybrid_rrf_k: int = 60  # standart Reciprocal Rank Fusion sabiti

    # Generation cache (Sprint 6) — aynı tuple için cached set döndürür, LLM call atlar
    enable_generation_cache: bool = True
    generation_cache_max_per_key: int = 10

    # Sentry error tracking (Sprint 6) — DSN boşsa Sentry off
    sentry_dsn: str = ""
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.1  # %10 performance sample
    sentry_release: str | None = None

    # Rate limit + API key
    api_keys: str = ""  # virgülle ayrılmış geçerli key'ler. Boşsa auth devre dışı.
    admin_api_key: str = ""  # /admin endpoint'leri için ayrı key. Boşsa admin devre dışı.
    rate_limit_per_hour: int = 30
    rate_limit_per_minute: int = 5

    # CORS — frontend domain'leri (virgülle). Boşsa "*" (yalnızca dev için).
    cors_origins: str = ""

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        items = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return items or ["*"]

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = True

    @property
    def fallback_model_list(self) -> list[str]:
        return [m.strip() for m in self.gemini_fallback_models.split(",") if m.strip()]


settings = Settings()
