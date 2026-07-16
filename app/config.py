from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # Yeni nesil (kalite/premium) yolu için daha güçlü model. Kodlama-optimize →
    # geometri SVG gibi yapısal çıktıda daha güvenilir; şekilli+bağlamsal soru için.
    # A/B (2026-07): 3.5-flash şekilli oranı ~2x, Pro'dan hızlı (48s vs 63s).
    gemini_model_yeni_nesil: str = "gemini-3.5-flash"
    # Sınıf-bazlı model seçimi: 1-4. sınıf soruları basit → hafif/ucuz flash 2.5
    # yeterli; 5-8. sınıf bağlamsal/şekilli kalite için güçlü Gemini 3 flash.
    # Seçim app.services.agent.model_for_grade() üzerinden uygulanır; yeni_nesil
    # (premium) bayrağından bağımsızdır — o yalnız prompt+dağılımı etkiler.
    gemini_model_grade_1_4: str = "gemini-2.5-flash"
    gemini_model_grade_5_8: str = "gemini-3.5-flash"
    gemini_fallback_models: str = "gemini-2.5-flash-lite,gemini-2.5-pro"
    gemini_embedding_model: str = "gemini-embedding-001"
    # Embedding boyutu: 3072 (varsayılan) yerine 768 → ChromaDB dosyaları GitHub
    # 100MB limitinin altında kalır (LFS gerekmez). Cosine retrieval kalitesi ~korunur.
    # DİKKAT: ingest ve query aynı boyutu kullanmalı (ikisi de GeminiEmbedder).
    embedding_dimensions: int = 768

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
    # Latency: mixed/progressive modda kolay/orta/zor bucket'larını paralel koş
    # (ardışık yerine). Her bucket bağımsız → ~3× hızlanma.
    parallel_difficulty_buckets: bool = True

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

    # --- Clerk oturum JWT doğrulama (P0 — billing ön koşulu) ---
    # Bugün backend, istekteki tenant_id'ye (Clerk userId) DOĞRULAMADAN güveniyor.
    # Premium/abonelik tenant_id'ye bağlanınca, kullanıcı bu değeri değiştirip bedava
    # premium olabilir. app/services/clerk_auth.py Clerk JWKS'inden oturum token'ının
    # RS256 imzasını doğrular → `sub` claim'inden DOĞRULANMIŞ tenant_id üretir.
    #
    # Kademeli açılış (docs/IYZICO_ENTEGRASYON_PLANI.md §11):
    #   1. clerk_issuer boş → doğrulama DEVRE DIŞI (bugünkü davranış; hiçbir şey kırılmaz).
    #   2. clerk_issuer set + frontend Bearer token gönderir → doğrulama devreye girer.
    # clerk_issuer: Clerk instance issuer URL'i (token'daki `iss` ile birebir eşleşmeli),
    #   ör. https://clerk.soruatolyesi.com veya https://<slug>.clerk.accounts.dev
    # clerk_jwks_url: normalde issuer'dan türetilir (/.well-known/jwks.json); yalnız
    #   özel bir dağıtımda override gerekiyorsa doldur.
    clerk_issuer: str = ""
    clerk_jwks_url: str = ""
    # JWKS anahtarları bellekte bu kadar saniye cache'lenir (imza doğrulama her istekte
    # ağ çağrısı yapmasın). Bilinmeyen kid görülürse süreden bağımsız bir kez yenilenir.
    clerk_jwks_cache_ttl: int = 3600

    # Premium yetkilendirme (entitlement) — "yeni nesil" GİZLİ kalite kaldıracı.
    # Gerçek billing/abonelik henüz yok; bu ayarlar app/services/entitlements.py
    # üzerinden okunur ve ileride Clerk publicMetadata / billing'e bağlanır.
    #   - premium_yeni_nesil: yeni nesil (harman) mod açık mı (özellik anahtarı)
    #   - premium_all: herkesi premium say → herkes yeni nesil alır
    #   - premium_tenant_ids: premium Clerk userId'leri (virgülle) allowlist
    # Karar HER ZAMAN sunucuda verilir; client bir bayrak gönderemez.
    # ŞİMDİLİK premium_all=True → ücretsiz dahil herkes yeni nesil (harman) alıyor.
    # Abonelik/billing canlı olunca: premium_all=False yap + premium_tenant_ids doldur
    # → o an ücretsiz=normal, premium=yeni nesil FARKI devreye girer.
    premium_yeni_nesil: bool = True
    premium_all: bool = True
    premium_tenant_ids: str = ""

    # Ders (subject) ekseni — çok-ders geçişi (docs/FEN_BILIMLERI_PLAN.md).
    # KALİTE KAPISI feature-flag'leri. Kalite paritesi doğrulandıktan sonra
    # (2026-07-10 go-live) hepsi VARSAYILAN AÇIK: env ile (FEN_ENABLED=false vb.)
    # istenirse tekrar kapatılabilir. Frontend tarafı NEXT_PUBLIC_ENABLED_SUBJECTS
    # ile eşlenir (ikisi birlikte açık olmalı, yoksa üretim 403).
    fen_enabled: bool = True
    turkce_enabled: bool = True
    sosyal_enabled: bool = True
    ingilizce_enabled: bool = True

    @property
    def premium_tenant_id_set(self) -> set[str]:
        return {t.strip() for t in self.premium_tenant_ids.split(",") if t.strip()}

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        items = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return items or ["*"]

    @property
    def clerk_auth_enabled(self) -> bool:
        """Clerk JWT doğrulaması yapılandırıldı mı? (issuer set ise açık)"""
        return bool(self.clerk_issuer.strip())

    @property
    def clerk_jwks_url_resolved(self) -> str:
        """JWKS endpoint: açık override varsa onu, yoksa issuer'dan türetir."""
        if self.clerk_jwks_url.strip():
            return self.clerk_jwks_url.strip()
        issuer = self.clerk_issuer.strip().rstrip("/")
        return f"{issuer}/.well-known/jwks.json" if issuer else ""

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_reload: bool = True

    @property
    def fallback_model_list(self) -> list[str]:
        return [m.strip() for m in self.gemini_fallback_models.split(",") if m.strip()]


settings = Settings()
