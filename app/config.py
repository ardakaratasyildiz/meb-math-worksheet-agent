from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: str = ""
    # Gemini trafiğini temiz-IP'li bir proxy (ör. Cloudflare Worker) üzerinden geçir.
    # Render free-tier paylaşımlı çıkış IP'si Google tarafından 403 ile bloklanınca
    # (bkz. 2026-07 incident) devreye alınır. BOŞ → doğrudan Google'a (bugünkü davranış).
    # Proxy, generativelanguage.googleapis.com'a birebir forward eder; genai SDK'nın
    # base_url'i buna çevrilir. gemini_proxy_secret → proxy'nin x-proxy-secret kapısı
    # (açık-proxy + key sızıntısı koruması). Hem generation hem embedding kapsanır.
    gemini_base_url: str = ""
    gemini_proxy_secret: str = ""
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
    # Fallback zinciri — KUYRUK MALİYETİ RİSKİ: `gemini-2.5-pro` çıkarıldı
    # (2026-07-26). Şema-drop gibi KALICI hatada zincir pro'ya düşüyordu:
    # çıktı $10/1M (2.5-flash'ın 4×'i) ve pro düşünmeyi KAPATAMIYOR (min 128) →
    # tek talihsiz istek kağıt maliyetini katlıyordu. flash-lite fallback olarak
    # yeterli; gerçekten güçlü modele ihtiyaç varsa `model_for()` politikası
    # zaten baştan 3.5-flash seçiyor.
    gemini_fallback_models: str = "gemini-2.5-flash-lite"
    # ── Model seçimi = model_for(grade, geometri?, zorluk, premium?) ─────────────
    # İki kutup: ucuz (grade_1_4=2.5-flash) ve güçlü (grade_5_8=3.5-flash). Politika
    # (A/B + Cloud Monitoring 2026-07 ile kalibre — 3.5 maliyetin %86'sıydı):
    #   1-4              → ucuz
    #   geometri teması  → güçlü (A/B: 2.5 geometri SVG'de zorlanıyor)
    #   8 + premium      → güçlü (komple)
    #   5-7 + premium + ZOR bucket → güçlü (kalan bucket'lar ucuz; ekstra çağrı yok)
    #   diğer her şey    → ucuz (ücretsiz 5-8 geometri-dışı dahil)
    # Premium = GERÇEK abonelik/trial (billing_store), premium_all dark-launch DEĞİL
    # → ödeyen yokken herkes ucuz model (max tasarruf). Bkz. entitlements.is_premium_for_model.
    #
    # Thinking (düşünme) token bütçesi — ÇIKTI fiyatından faturalanır (maliyet sürücüsü).
    #   0 = kapalı · -1 = dinamik · N>0 = sabit bütçe.
    # 1-4 → 0 (A/B: kalite korundu, ~%50-76 tasarruf). 5-7 → 512 (A/B: teslim 5/5,
    # g7'de %41 tasarruf; kapalı riskliydi). 8 → -1 (en zor+LGS, dokunma). Güçlü model
    # (3.5, geometri/premium) → -1 (kaliteyi koru). gemini-2.5-pro 0'ı kapatamaz →
    # provider 0'ı pro'da dinamiğe çevirir.
    gemini_thinking_budget_grade_1_4: int = 0
    gemini_thinking_budget_grade_5_7: int = 512
    gemini_thinking_budget_grade_8: int = -1
    gemini_thinking_budget_strong: int = -1  # güçlü model (3.5) için dinamik
    gemini_embedding_model: str = "gemini-embedding-001"
    # Cloud Monitoring maliyet MUTABAKATI (admin panel): SA ile Google'ın KENDİ token
    # sayaçlarını okur → gerçek maliyet (tüm generate + embedding + başarısız çağrılar)
    # vs defter (tahmin). Render'da SA key JSON'ı _sa_json env'ine yapıştırılır; lokalde
    # _sa_file dosya yolu. İkisi de boşsa özellik kapalı (endpoint available=False döner).
    # SA yalnız roles/monitoring.viewer ister (salt-okunur).
    gemini_monitoring_sa_json: str = ""
    gemini_monitoring_sa_file: str = ""
    # Panelde $ yanında ~TL göstermek için kur (yaklaşık, redeploy'suz tune edilebilir).
    usd_try_rate: float = 38.0
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
    # A/B (2026-07-23, scripts/eval/thinking_ab.py): 0.6→0.75. Düşük-güvenli (conf~0.70)
    # tartışmalı redler soruyu düşürüp gereksiz top-up turu (pahalı yeniden üretim)
    # tetikliyordu; 0.75 yalnız yüksek-güvenli redleri düşürür → cebir/fen kağıt maliyeti
    # ~%50 azaldı, critic geçiş oranı korundu/iyileşti (0.96→1.00). Bkz. overshoot.
    critic_min_confidence: float = 0.75
    # Critic parçalama (2026-07-26 ölçümü): 30+ soruyu tek çağrıda denetlerken
    # flash-lite yanıtı yozlaşıp 64K çıktı tavanına dayanıyor → kesik JSON →
    # fail-open (filtreleme YOK) + ~65K token/148 sn israf. 10'luk gruplar
    # hem maliyeti hem yozlaşmayı keser, denetim gerçekten çalışır.
    critic_batch_size: int = 10
    # Çözüm adımları critic girdisinin baskın kalemi (~500 karakter/soru);
    # doğrulama için ilk adımlar yeterli.
    critic_max_solution_chars: int = 400

    enable_math_verifier: bool = True

    # Latency: ilk üretim batch'ini hedeften fazla iste ki math/critic elemeleri
    # seri post-filter top-up turu açmadan absorbe edilsin. 1.0 = kapalı (eski
    # davranış). A/B (2026-07-23): 1.3→1.8. Grade 8'de format/critic drop'ları 1.3
    # buffer'ını aşıp 2 top-up turu (her biri ~48k prompt'u YENİDEN gönderir) tetikliyordu;
    # 1.8 drop'ları ilk çağrıda absorbe eder → top-up ~kaybolur, maliyet düşer.
    generation_overshoot_ratio: float = 1.8
    # Yedek soru havuzu (spare pool): overshoot'un KIRPILAN fazlaları çöpe gitmek
    # yerine soru-bazlı envantere yazılır ve sonraki isteklerde LLM top-up'ı
    # YERİNE kullanılır (2026-07-26 ölçümü: 20 soruluk kağıt için 36 soru
    # üretiliyor, ~12'si atılıyordu; top-up çağrıları 19-24K çıktı token'ı).
    enable_spare_pool: bool = True
    # 60 → 300 (Opus denetimi 2026-07-28, MUST-FIX): 60, havuzun yalnız post-filter
    # yedeği olduğu Faz 1 için yeterliydi. Faz 2'de depo BİRİNCİL servis yolu
    # olunca kova başına 60 çok az kalır (20 soruluk 3 kağıt tek kullanıcıyı
    # tüketir → çeşitlilik biter, aynı sorular hızla tekrar sıraya girer).
    # 300 × ~700 kova (ders×sınıf×ünite×kazanım×tip×zorluk, bkz. plan §0b) ×
    # ~2KB/soru ≈ 400MB tavan — Turso free-tier 9GB'ın altında, ve pratikte
    # yalnız GERÇEKTEN aktif kovalar dolar (tavana hiç yaklaşmayan yüzlerce
    # kova boş/az kalır). Trim artık `used_count`'a göre DEĞİL damga durumuna
    # göre çalışıyor (bkz. llm_cache.SpareQuestionPool.add_many) — kapasite
    # büyüklüğü artık "hangi soru silinir" kararını bozmuyor, yalnızca ne kadar
    # çeşitlilik biriktirebileceğimizi belirliyor.
    spare_pool_max_per_key: int = 300
    # Depoyu BİRİNCİL servis yolu yapar (Faz 2, §3b, docs/COST_QUALITY_V2_PLAN.md):
    # eskiden akış `cache → LLM üret → filtre → (yedek/havuz) → top-up` idi — havuz
    # yalnız post-filter EKSİĞİNİ kapatıyordu, LLM her zaman baştan çağrılıyordu.
    # True iken akış `cache → DEPO (istenen sayının TAMAMI) → yalnız EKSİK kadar LLM`
    # olur: depo isteneni tam karşılarsa LLM'e (few-shot/textbook retrieval dahil)
    # HİÇ gidilmez. Tek kısıt aynı kullanıcıya tekrar (history exclude_norms);
    # çapraz-kullanıcı tekrar kullanıcı kararıyla SERBEST (doluluk eşiği yok).
    # False → bugünkü davranış birebir (LLM her zaman önce çağrılır, havuz yalnız
    # eksik kapatma/top-up alternatifi olarak devrede kalır) — redeploy'suz geri
    # alma: env `ENABLE_POOL_FIRST_SERVING=false`.
    enable_pool_first_serving: bool = True
    # Tip-farkında pool-first (Opus denetimi 2026-07-28, SHOULD-FIX): açıkken
    # pool-first hedef soru TİPİ dağılımını (`distribute_question_types`) da
    # gözetir — kovada baskın olan tek tip (ör. yalnız `islem`) kağıdın tamamını
    # ele geçiremez, her tip yalnız KENDİ kotası kadar depodan çekilir, kalanı
    # LLM'in hedefine (tip-bazlı eksik) devredilir. Kapalıysa (eski/basit
    # davranış) pool-first yalnız TOPLAM sayıya bakar, tip karışımı tesadüfe
    # kalır — redeploy'suz geri alma: env `POOL_FIRST_RESPECT_TYPE_MIX=false`.
    pool_first_respect_type_mix: bool = True
    # ÜRETİM ÇIKTI TAVANI — "format-drop" israfının panzehiri (2026-07-26 ölçümü):
    # üretici modelin çıktı tavanı yoktu; g5 kağıdında 2.5-flash YOZLAŞIP 65.012
    # token/237 sn yazdı, 64K tavanına dayandı, JSON kesildi ("şemaya uymadı"),
    # zincir flash-lite'a düştü, o da 34.366 token yaktı → tek istekte ~99K çıktı
    # token'ı (~6.3 TL) HİÇBİR ŞEY için harcandı.
    # Tavan = soru_sayısı × per_question + thinking payı. Ölçülen normal tüketim
    # ~420-450 token/soru → 900 iki kat pay bırakır. DİKKAT: Gemini 2.5+'ta
    # thinking token'ları da max_output_tokens'a sayılır → dinamik thinking (-1)
    # için ayrı pay eklenmeli, aksi halde meşru üretim kesilir.
    generation_output_cap_per_question: int = 900
    generation_output_cap_thinking_allowance: int = 20000
    # Latency: mixed/progressive modda kolay/orta/zor bucket'larını paralel koş
    # (ardışık yerine). Her bucket bağımsız → ~3× hızlanma.
    parallel_difficulty_buckets: bool = True

    enable_history_persist: bool = True
    history_db_path: str = "knowledge_base/history.sqlite3"
    # Kalıcı görülmüş-set (Soru deposu Faz 1, §3a): `seen_questions()` eskiden
    # `deque(maxlen=30)`'a dayanıyordu → 3. kağıtta 1. kağıdın soruları "hiç
    # görülmemiş" sayılıp TEKRAR gelebiliyordu (kullanıcının "aynı soruyu
    # görmesin" beklentisi bu yüzden çalışmıyordu). True → dışlama kümesi
    # anahtar başına DB'den tembel yüklenir ve TAVANSIZ tutulur (yalnız
    # normalize metin, ucuz). `context_exclusions`/`seen_embeddings` bilinçli
    # olarak SINIRLI KALIR (prompt token'ı / RAM-CPU maliyeti). False → eski
    # 30'luk pencere davranışına döner (redeploy'suz geri alma).
    history_seen_unbounded: bool = True

    # Kullanıcı (tenant) bazlı çalışma kağıdı geçmişi — /api/worksheets/history
    enable_worksheet_history: bool = True
    worksheet_history_max_per_tenant: int = 50

    enable_hybrid_retrieval: bool = True
    hybrid_bm25_weight: float = 0.3  # RRF fusion'da BM25'in göreceli ağırlığı
    hybrid_rrf_k: int = 60  # standart Reciprocal Rank Fusion sabiti

    # Generation cache (Sprint 6) — aynı tuple için cached set döndürür, LLM call atlar
    enable_generation_cache: bool = True
    # 10→30 (2026-07-23): aynı anahtarda kullanıcının geçmişi tükenmeden daha çok
    # bedava çeşitlilik → cache hit oranı artar, taze (pahalı) üretim azalır.
    generation_cache_max_per_key: int = 30

    # --- Anonim çeşitlilik kovası (2026-07-29 ölçümü) --------------------------
    # ÖLÇÜLDÜ: anonim üretimlerin TAMAMI tek `__shared__` history kovasını
    # paylaşıyordu. Teslim edilen her soru o kovaya "görülmüş" olarak yazılıyor ve
    # `GenerationCache.get()` bir cached set'te TEK BİR görülmüş soru bulursa seti
    # tamamen atlıyor → anonim trafikte cache yazılıyor ama BİR DAHA ASLA
    # okunamıyordu (canlı: 97 üretimde 3 isabet). `history_seen_unbounded`
    # bunu kalıcı hale getirdi.
    #
    # True → anonim istekler istemci IP'sinden türetilen kovaya ayrılır: aynı
    # ziyaretçi çeşitlilik görmeye devam eder, FARKLI ziyaretçiler birbirinin
    # cache'inden okuyabilir. False → eski `__shared__` davranışı (redeploy'suz
    # geri alma). Giriş yapmış kullanıcı ETKİLENMEZ (tenant_id her zaman kazanır).
    anon_variation_bucket: bool = True
    # IP hash tuzu. Ham IP HİÇBİR YERE yazılmaz, yalnız HMAC'in 12 hex'i kovada
    # görünür. Tuzu değiştirmek tüm anonim kovaları sıfırlar (zararsız: yalnız
    # çeşitlilik penceresi resetlenir). Boş → aşağıdaki sabit varsayılan; çok
    # örnekli (multi-instance) kurulumda AYNI değer olmalı, yoksa kovalar ayrışır.
    anon_variation_salt: str = ""

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
    # Clerk Backend API sırrı — sunucu-tarafı ROL kontrolü için (publicMetadata.role'ü
    # Clerk'ten çeker; app/services/clerk_roles.py). BOŞ → rol enforcement DEVRE DIŞI
    # (fail-open; bugünkü davranış). Frontend'deki CLERK_SECRET_KEY ile aynı olabilir.
    clerk_secret_key: str = ""
    # Çekilen rolün bellek cache TTL'i (rol artık kalıcı → uzun tutulabilir).
    clerk_role_cache_ttl: int = 3600

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
    # yeni_nesil TEASER (ücretsiz): premium full yeni_nesil alır; ücretsiz yalnız
    # BİR zorluk bucket'ında yeni_nesil görür (tadımlık, fiyatlandırma kaldıracı).
    # Soru-başına bölme YOK → mevcut zorluk bucket'ına biner (ekstra çağrı yok).
    # Dark-launch'ta premium_all herkesi premium yapar → teaser dormant; billing
    # canlı olunca (premium_all=False) ücretsiz kullanıcılarda otomatik devreye girer.
    free_yeni_nesil_enabled: bool = True
    free_yeni_nesil_bucket: str = "orta"

    # --- Abonelik / kota (billing) — MONETIZATION_PLAN §2 (2026-07-16 modeli) ---
    # Kademeler: free (100 soru/ay) · pro (1000 soru/ay) · pro-plus (fair-use sınırsız)
    # · trial (7g kartsız tam-Pro). Kota birimi = soru/ay, aylık reset (Türkiye ayı),
    # cache-hit üretimler sayılmaz, anonim üretim kotasız. Karar HER ZAMAN sunucuda.
    #   billing_enabled: ödeme/kota enforcement feature flag (kademeli açılış §11).
    #     False iken kota uygulanmaz (bugünkü davranış); billing canlı olunca True.
    free_monthly_questions: int = 100
    pro_monthly_questions: int = 1000
    # pro-plus "sınırsız" ama suistimale karşı arka plan makul tavan (soru/ay).
    pro_plus_fair_use_questions: int = 10000
    # KESİN model (2026-07-24, MONETIZATION_PLAN §2): kota birimi = ÇALIŞMA KAĞIDI (soru değil).
    # Açık sayı (gizli maliyet-tavanı YOK — şeffaflık). quota_limit BUNLARI kullanır;
    # yukarıdaki *_questions artık atıl (geriye-uyum için bırakıldı).
    free_monthly_worksheets: int = 10
    pro_monthly_worksheets: int = 50
    pro_plus_monthly_worksheets: int = 120
    # Ücretsiz kademede GÜNLÜK tavan (kağıt/gün, Türkiye günü). Aylık 10 hakkın ilk iki
    # günde tüketilip kullanıcının 28 gün boş kalmasını engeller; aynı zamanda ücretsiz
    # trafiğin günlük maliyet tavanını belirler. 0 → günlük tavan kapalı.
    free_daily_worksheets: int = 2
    # 7g reverse trial süresi (gün) + trial kotası (kağıt).
    # Trial Pro+ KALİTESİ verir (yeni_nesil vb.) ama ADEDİ ayrıdır: 120 kağıtlık Pro+
    # tavanı denemede ~180 TL üretim maliyeti demekti — bir aylık Pro gelirinden fazla.
    # Değer göstermeye 20 kağıt yeter (KARAR 2026-08-12).
    trial_days: int = 7
    trial_worksheets: int = 20
    billing_enabled: bool = False
    # Ek kağıt paketi (top-up) — tüketilebilir IAP; abonelik üstü, süreli (MONETIZATION_PLAN §2).
    topup_expiry_days: int = 30
    # RevenueCat consumable product id → eklenecek kağıt sayısı. Webhook consumable olayında
    # TOP_UP_STORE'a bu haritadan kredi eklenir (ürünler 28 Tem sonrası mağazada tanımlanır).
    topup_products: str = "com.soruatolyesi.app.topup_25:25,com.soruatolyesi.app.topup_75:75"

    # --- RevenueCat (mobil IAP webhook → subscriptions senkronu) ---
    # Mobil uygulama IAP'yi RevenueCat üzerinden yapar; RevenueCat bize webhook
    # gönderir → billing_store.subscriptions güncellenir (iyzico ile ORTAK depo).
    # app_user_id = Clerk userId (mobil RevenueCat'i böyle konfigüre eder) = tenant_id.
    #   revenuecat_webhook_auth: RevenueCat panosunda ayarlanan Authorization header
    #     değeri (paylaşımlı sır). SET ise header birebir eşleşmeli (aksi 401). BOŞ ise
    #     doğrulama atlanır + uyarı loglanır (yalnız sandbox/dev; PROD'da MUTLAKA set et).
    #   revenuecat_product_map: "product_id:plan_code" çiftleri (virgülle). Eşleşme
    #     yoksa ürün/entitlement adında "plus" geçerse pro-plus, aksi halde pro (fallback).
    #   revenuecat_allow_sandbox: sandbox (test) satın almaları GERÇEK abonelik/kredi
    #     sayılsın mı. RevenueCat sandbox olayları için de webhook gönderir ve olay
    #     `environment: SANDBOX` taşır. Test döneminde True olmalı (uçtan uca doğrulama:
    #     satın al → webhook → /api/me/entitlements). CANLIYA ÇIKARKEN Render'da
    #     REVENUECAT_ALLOW_SANDBOX=false yap — aksi halde davet ettiğin sandbox/lisans
    #     test hesapları bedavaya Pro yazdırmaya devam eder. Reddedilen olay yine
    #     billing_events'e kaydedilir (iz kalsın), yalnız abonelik/krediye işlenmez.
    revenuecat_webhook_auth: str = ""
    revenuecat_product_map: str = ""
    revenuecat_allow_sandbox: bool = True

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
    def revenuecat_product_dict(self) -> dict[str, str]:
        """product_id → plan_code eşlemesi (revenuecat_product_map'ten parse)."""
        out: dict[str, str] = {}
        for pair in self.revenuecat_product_map.split(","):
            pair = pair.strip()
            if ":" in pair:
                k, v = pair.split(":", 1)
                if k.strip() and v.strip():
                    out[k.strip()] = v.strip()
        return out

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

    @property
    def topup_product_credits(self) -> dict[str, int]:
        """RevenueCat consumable product id → kağıt sayısı ('com.soruatolyesi.app.topup_25:25,com.soruatolyesi.app.topup_75:75')."""
        out: dict[str, int] = {}
        for part in self.topup_products.split(","):
            part = part.strip()
            if ":" not in part:
                continue
            pid, _, val = part.partition(":")
            pid = pid.strip()
            try:
                n = int(val.strip())
            except ValueError:
                continue
            if pid and n > 0:
                out[pid] = n
        return out


settings = Settings()
