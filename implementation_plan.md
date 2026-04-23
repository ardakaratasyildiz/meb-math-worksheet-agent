# 📐 MEB Matematik Çalışma Kağıdı Üretici Agent

MEB müfredatına uygun, 1-7. sınıf arası matematik soruları üreten bir Gemini-tabanlı agent mikroservisi.

## Genel Bakış

| Özellik | Detay |
|---------|-------|
| **Teknoloji** | Python + FastAPI |
| **LLM** | Google Gemini |
| **Sınıflar** | 1. - 7. sınıf |
| **Zorluk** | Kolay / Orta / Zor |
| **Soru Tipi** | Klasik, açık uçlu, işlem tabanlı |
| **Çıktı** | JSON (sorular + cevap anahtarı), PDF (sonraki aşama) |
| **Müfredat** | MEB hardcoded konu ağacı + kazanım kodları |
| **Konu Sayısı** | 5 ana öğrenme alanı (sınıfa göre alt konular + kazanımlar) |
| **Çeşitlilik** | Few-shot örnek havuzu + soru tipi rotasyonu + tekrar önleme |

---

## MEB Müfredat Konu Ağacı (Hardcoded)

Agent'ın temel bilgi kaynağı olan 5 öğrenme alanı ve sınıflara göre alt konuları.

> **Kazanım Kodları:** Her konu, MEB resmi müfredatındaki **kazanım kodları** (örn. `M.5.1.2.3`) ve kazanım metinleriyle birlikte hardcoded olarak tanımlanır. Bu, soru üretiminde "konu" gibi soyut bir hedef yerine, müfredat dokümanındaki spesifik kazanım metnini Gemini'ye verme imkânı sağlar.

Aşağıdaki tablo üst düzey kapsamı gösterir; gerçek `curriculum.py` dosyasında her sınıf-konu çifti altında kazanım kodu listesi bulunacaktır.

### 1. 📊 Doğal Sayılar ve İşlemler
| Sınıf | Kapsam |
|-------|--------|
| 1 | 100'e kadar sayılar, toplama-çıkarma |
| 2 | 1000'e kadar sayılar, toplama-çıkarma, çarpmaya giriş |
| 3 | 10.000'e kadar sayılar, dört işlem |
| 4 | Büyük doğal sayılar, dört işlem, bölme |
| 5 | Doğal sayılarla işlemler, işlem önceliği |
| 6 | Tam sayılar, mutlak değer, toplama-çıkarma |
| 7 | Tam sayılarla çarpma-bölme, işlem önceliği |

### 2. 🔢 Kesirler ve Ondalık Sayılar
| Sınıf | Kapsam |
|-------|--------|
| 1 | — (bu alan 1. sınıfta yok) |
| 2 | — (bu alan 2. sınıfta yok) |
| 3 | Kesirlere giriş: yarım, çeyrek, bütün-parça |
| 4 | Kesir türleri, ondalık gösterim, sıralama |
| 5 | Kesirlerle toplama-çıkarma |
| 6 | Kesirlerle dört işlem |
| 7 | Rasyonel sayılar, rasyonel sayılarla işlemler |

### 3. 📐 Geometri
| Sınıf | Kapsam |
|-------|--------|
| 1 | Temel geometrik şekilleri tanıma (kare, üçgen, daire) |
| 2 | Kenar ve köşe kavramı, şekil özellikleri |
| 3 | Çevre hesaplama, simetri |
| 4 | Açılar (dar, dik, geniş), çevre-alan |
| 5 | Üçgen ve dörtgenlerin çevre-alan hesabı |
| 6 | Alan hesaplamaları (paralelkenar, üçgen, yamuk) |
| 7 | Çember ve dairede uzunluk-alan, merkez açı |

### 4. 📏 Ölçme
| Sınıf | Kapsam |
|-------|--------|
| 1 | Uzunluk karşılaştırma, standart olmayan birimler |
| 2 | cm-m, saat okuma, tartma |
| 3 | Birim dönüşümleri (km-m-cm-mm), zaman |
| 4 | Birim dönüşümleri, alan-çevre birimleri |
| 5 | Hacim ölçme, litre-mililitre |
| 6 | Sıvı ölçüleri, hacim hesaplama |
| 7 | Prizmaların hacmi ve yüzey alanı |

### 5. 🧮 Cebir ve Denklemler
| Sınıf | Kapsam |
|-------|--------|
| 1 | Basit sayı örüntüleri (2, 4, 6, ?) |
| 2 | Sayı ve şekil örüntüleri |
| 3 | Örüntülerde kural bulma |
| 4 | Örüntü ve ilişkilerde genelleme |
| 5 | Basit denklemler (x + 3 = 7) |
| 6 | Cebirsel ifadeler, birinci dereceden denklemler |
| 7 | Eşitsizlikler, doğrusal denklemler, oran-orantı |

> [!IMPORTANT]
> 1-2. sınıflarda "Kesirler" alanı mevcut olmadığından, bu sınıflar için bu konu seçimi engellenecek.
> Geometri soruları görsel gerektirmeden, sözel/hesaplamalı olarak üretilecek.

### Kazanım Veri Yapısı (Örnek)

```python
# curriculum.py içinde her konu için:
{
    "topic_id": "kesirler",
    "grade": 5,
    "name": "Kesirler ve Ondalık Sayılar",
    "kazanimlar": [
        {
            "kod": "M.5.1.4.1",
            "metin": "Birim kesirleri sayı doğrusunda gösterir ve sıralar."
        },
        {
            "kod": "M.5.1.4.2",
            "metin": "Tam sayılı kesrin bileşik kesir, bileşik kesrin tam sayılı kesir biçiminde yazılabileceğini anlar."
        },
        {
            "kod": "M.5.1.5.1",
            "metin": "Paydaları eşit ve eşit olmayan en çok iki kesrin toplama-çıkarma işlemini yapar."
        }
    ]
}
```

Üretim sırasında: ya kullanıcı belirli bir kazanım seçer, ya da konu seçilirse o konuya ait kazanımlar arasından otomatik dağıtım yapılır.

---

## Mimari Yapı

```
Sheet Generator/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI uygulama başlangıcı
│   ├── config.py               # Ayarlar (.env, API keys)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py          # Pydantic modelleri (request/response)
│   │   └── enums.py            # Difficulty, QuestionType enum'ları
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── curriculum.py       # Hardcoded MEB müfredat + kazanım kodları
│   │   └── few_shot/           # Kazanım kodu bazlı örnek soru havuzu
│   │       ├── __init__.py
│   │       ├── grade_1.py
│   │       ├── grade_2.py
│   │       ├── ...
│   │       └── grade_7.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent.py            # Gemini agent servisi
│   │   ├── diversity.py        # Soru tipi rotasyonu + tekrar önleme
│   │   └── examples.py         # Few-shot örnek seçici
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── worksheets.py       # Soru üretim endpoint'leri
│   │   └── curriculum.py       # Müfredat listeleme endpoint'leri
│   │
│   └── prompts/
│       ├── __init__.py
│       └── templates.py        # Gemini prompt şablonları (system + user + few-shot)
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## API Tasarımı

### Endpoint'ler

#### 1. `GET /api/curriculum/grades`
Mevcut sınıfları listeler.

**Response:**
```json
{
  "grades": [
    {"id": 1, "name": "1. Sınıf", "level": "İlkokul"},
    {"id": 2, "name": "2. Sınıf", "level": "İlkokul"},
    {"id": 3, "name": "3. Sınıf", "level": "İlkokul"},
    {"id": 4, "name": "4. Sınıf", "level": "İlkokul"},
    {"id": 5, "name": "5. Sınıf", "level": "Ortaokul"},
    {"id": 6, "name": "6. Sınıf", "level": "Ortaokul"},
    {"id": 7, "name": "7. Sınıf", "level": "Ortaokul"}
  ]
}
```

#### 2. `GET /api/curriculum/grades/{grade_id}/topics`
Seçilen sınıfın konularını listeler.

**Response (örnek: 5. sınıf):**
```json
{
  "grade": 5,
  "topics": [
    {"id": "dogal_sayilar", "name": "Doğal Sayılar ve İşlemler", "description": "Doğal sayılarla işlemler, işlem önceliği"},
    {"id": "kesirler", "name": "Kesirler ve Ondalık Sayılar", "description": "Kesirlerle toplama-çıkarma"},
    {"id": "geometri", "name": "Geometri", "description": "Üçgen ve dörtgenlerin çevre-alan hesabı"},
    {"id": "olcme", "name": "Ölçme", "description": "Hacim ölçme, litre-mililitre"},
    {"id": "cebir", "name": "Cebir ve Denklemler", "description": "Basit denklemler (x + 3 = 7)"}
  ]
}
```

#### 3. `POST /api/worksheets/generate`
Çalışma kağıdı üretir.

**Request:**
```json
{
  "grade": 5,
  "topic_id": "cebir",
  "difficulty": "orta",
  "question_count": 10
}
```

**Response:**
```json
{
  "worksheet": {
    "title": "5. Sınıf - Cebir ve Denklemler Çalışma Kağıdı",
    "grade": 5,
    "topic": "Cebir ve Denklemler",
    "difficulty": "Orta",
    "question_count": 10,
    "questions": [
      {
        "number": 1,
        "question": "x + 12 = 25 denkleminde x kaçtır?",
        "answer": "x = 13"
      },
      {
        "number": 2,
        "question": "3 × y = 36 denkleminde y kaçtır?",
        "answer": "y = 12"
      }
    ],
    "answer_key": [
      {"number": 1, "answer": "x = 13"},
      {"number": 2, "answer": "y = 12"}
    ]
  },
  "metadata": {
    "generated_at": "2026-04-19T14:52:00Z",
    "model": "gemini-2.0-flash",
    "curriculum": "MEB 2024"
  }
}
```

---

## Gemini Prompt Stratejisi

Agent'ın doğru ve müfredata uygun soru üretmesi için **katmanlı prompt** yaklaşımı kullanılacak. Prompt 3 bölümden oluşur: **System (sabit kurallar)** + **Few-shot (örnek sorular)** + **User (dinamik kazanım + dağılım talebi)**.

### System Prompt (Sabit)
```
Sen MEB (Milli Eğitim Bakanlığı) müfredatına uygun matematik soruları üreten 
bir eğitim asistanısın. Türkiye'deki ilkokul ve ortaokul matematik ders 
kitaplarını referans alıyorsun.

Kuralların:
1. Sorular MUTLAKA verilen kazanım metninin kapsamı dahilinde olmalı
2. Kazanımın dışına çıkan, üst sınıf bilgisi gerektiren soru ÜRETME
3. Sorular açık uçlu ve işlem tabanlı olmalı (çoktan seçmeli değil)
4. Her sorunun kesin ve doğru bir cevabı olmalı
5. Görsel/şekil gerektiren sorular üretme; geometri sorularını sözel anlat
6. Zorluk seviyesine göre: 
   - Kolay: Temel kavramlar, tek adımlı işlemler
   - Orta: Birden fazla adım gerektiren işlemler
   - Zor: Karmaşık problem çözme, birden fazla kavramı birleştiren sorular
7. Soruları Türkçe üret, dilbilgisi MEB ders kitabı tonunda olsun
8. Her sorunun çözüm adımlarını da belirt
9. İstenen soru tipi dağılımına UYUN (işlem/problem/kavram/akıl yürütme)
10. Verilen örnek soruların stilini ve formatını referans al, KOPYALAMA
```

### Few-Shot Örnek Bloğu (Dinamik)
Seçilen kazanım kodu için `data/few_shot/` havuzundan 2-3 örnek soru prompt'a enjekte edilir:

```
İşte hedef kazanım için MEB ders kitabı tarzında örnek sorular:

[Örnek 1 - Tip: islem]
Soru: 3/4 + 2/4 işleminin sonucu kaçtır?
Cevap: 5/4
Çözüm: Paydalar eşit olduğundan paylar toplanır: 3+2=5. Sonuç: 5/4

[Örnek 2 - Tip: sozel_problem]
Soru: Bir pastanın 2/8'ini Ayşe, 3/8'ini Burak yedi. Toplam ne kadar pasta yenildi?
Cevap: 5/8
Çözüm: 2/8 + 3/8 = 5/8

Bu örnekler stil ve seviye referansıdır; aynı sayıları/bağlamı KULLANMA.
```

### User Prompt (Dinamik)
```
Sınıf: {grade}. sınıf
Konu: {topic_name}
Hedef Kazanım Kodu: {kazanim_kod}
Hedef Kazanım Metni: {kazanim_metin}
Zorluk: {difficulty}
Soru Sayısı: {question_count}

Soru Tipi Dağılımı (toplam {question_count}):
- İşlem sorusu: {n_islem} adet
- Sözel problem: {n_problem} adet
- Kavram sorusu: {n_kavram} adet
- Akıl yürütme: {n_akil} adet

Üretilmemesi gereken bağlamlar (önceki sorularda kullanıldı):
{exclusion_list}

Yukarıdaki kriterlere göre {question_count} adet matematik sorusu üret.
```

### Response Format
Gemini'den **structured JSON output** istenecek (`response_mime_type: application/json`). Her soru objesi: `number`, `question`, `answer`, `solution_steps`, `kazanim_kod`, `question_type`.

---

## Validasyon Kuralları

| Parametre | Kural |
|-----------|-------|
| `grade` | 1-7 arası tam sayı |
| `topic_id` | Seçilen sınıfta mevcut olan konu |
| `kazanim_kod` | (opsiyonel) Seçilen konuya ait geçerli kazanım kodu |
| `difficulty` | `kolay`, `orta`, `zor` |
| `question_count` | 1-20 arası (aşırı yüklemeyi önlemek için) |
| 1-2. sınıf + kesirler | ❌ Engellenir (müfredatta yok) |

---

## Soru Çeşitliliği Mekanizması

Gemini'nin tek bir prompt'tan gelen sorularda tekrara düşmesini ve sınırlı bir alt-örüntüye sıkışmasını önlemek için 3 katmanlı kontrol uygulanır:

### 1. Soru Tipi Taksonomisi

Her üretim talebi, soru tipi dağılımına göre planlanır:

| Tip | Açıklama | Örnek |
|-----|----------|-------|
| `islem` | Saf işlem sorusu, bağlamsız | `3/4 + 2/4 = ?` |
| `sozel_problem` | Günlük hayat bağlamlı problem | "Ali'nin 12 elması var, 4'ünü..." |
| `kavram_sorusu` | Tanım/özellik sorusu | "Bileşik kesir nedir? Bir örnek ver" |
| `akil_yurutme` | Çok adımlı, akıl yürütme | "Hangi sayı 3'ün katı, çift ve 20'den küçük?" |
| `modelleme` | Görselsiz modelleme/temsil | "Sayı doğrusunda 5/4 nereye düşer? Sözel anlat" |
| `gunluk_hayat` | Pratik uygulama | "1 litre süt 32 TL ise 250 ml kaç TL?" |

`services/diversity.py` zorluk + soru sayısına göre dağılım üretir (örn. zorluk=orta, n=10 → 3 işlem + 4 problem + 2 kavram + 1 akıl yürütme).

### 2. Few-Shot Örnek Havuzu

`data/few_shot/grade_X.py` her kazanım kodu için **el yazımı 3-5 örnek** içerir. Bu örnekler:
- MEB ders kitaplarındaki soru tarzını birebir yansıtır
- Her tip için en az bir örnek bulundurur
- Üretim sırasında kazanım koduna göre ilgili olanlar prompt'a enjekte edilir

```python
# data/few_shot/grade_5.py (örnek)
FEW_SHOT_EXAMPLES = {
    "M.5.1.5.1": [
        {
            "type": "islem",
            "question": "3/8 + 2/8 işleminin sonucu kaçtır?",
            "answer": "5/8",
            "solution": "Paydalar eşit, paylar toplanır: 3+2=5"
        },
        {
            "type": "sozel_problem",
            "question": "Bir pastanın 1/6'sını Ayşe, 2/6'sını Burak yedi. Toplam ne kadar pasta yenildi?",
            "answer": "3/6 (veya 1/2)",
            "solution": "1/6 + 2/6 = 3/6"
        },
        # ... diğer tipler
    ],
}
```

### 3. Tekrar Önleme (Hafif)

RAG'sız, basit ve maliyetsiz bir yaklaşım:

- **Normalize hash:** Her üretilen sorunun sayıları/bağlamı normalize edilip (örn. küçük harf, sayı yer tutucusu) hash'i in-memory bir set'te tutulur. Aynı batch içinde duplikat çıkarsa atılır.
- **Bağlam dışlama listesi:** Üretilen sorulardaki tekrar eden bağlamlar (`pasta`, `elma`, `Ali`) prompt'taki `exclusion_list`'e eklenip bir sonraki üretimde "bu bağlamları kullanma" denilir.
- **Stochastic ayarlar:** `temperature=0.8`, her batch'te farklı `seed`. 

> **Not:** Embedding tabanlı semantik benzerlik kontrolü RAG aşamasına bırakıldı. MVP'de string-level kontrol yeterli kalite veriyorsa devam edilir.

---

## Kullanılacak Kütüphaneler

```
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.0.0
google-genai>=1.0.0
python-dotenv>=1.0.0
```

---

## Geliştirme Aşamaları

### Aşama 1: Temel Yapı ✏️
1. Proje iskeletini oluştur
2. MEB müfredat verisini **kazanım kodlarıyla birlikte** hardcode et (`data/curriculum.py`)
3. Pydantic modellerini tanımla (`schemas.py`) — kazanım, soru tipi alanlarıyla
4. FastAPI uygulamasını kur

### Aşama 2: Few-Shot Havuzu 📚
1. Soru tipi enum'ını tanımla (`models/enums.py`)
2. Her sınıf için `data/few_shot/grade_X.py` dosyalarını oluştur
3. Her kazanım kodu için en az 3-5 el yazımı örnek soru ekle
4. Örnek seçici servisini yaz (`services/examples.py`)

### Aşama 3: Gemini Agent 🤖
1. Gemini client yapılandırması
2. Katmanlı prompt şablonlarını oluştur (system + few-shot + user)
3. Soru üretim servisini implement et
4. JSON response parsing ve validasyon

### Aşama 4: Çeşitlilik Mekanizması 🎲
1. Soru tipi dağılım hesaplayıcı (`services/diversity.py`)
2. Normalize hash ile in-batch duplikat kontrolü
3. Bağlam dışlama listesi yönetimi
4. Temperature/seed parametre yönetimi

### Aşama 5: API Endpoint'leri 🌐
1. Müfredat listeleme endpoint'leri (kazanımları da döndür)
2. Soru üretim endpoint'i
3. Hata yönetimi ve validasyon
4. Swagger dökümantasyonu

### Aşama 6: Test & Doğrulama ✅
1. Her sınıf-konu-zorluk kombinasyonu için test
2. Gemini çıktı kalitesi kontrolü
3. Aynı parametrelerle çoklu üretim → çeşitlilik denetimi
4. Edge case'lerin yönetimi

---

## Doğrulama Planı

### Otomatik Testler
- API endpoint'lerinin çalıştığını doğrulamak için Swagger UI üzerinden test
- `curl` ile her endpoint'i test etme
- Geçersiz parametre kombinasyonlarının doğru hata döndürmesi

### Manuel Doğrulama
- Farklı sınıf ve konularda soru üretip MEB müfredatına uygunluğunu kontrol etme
- Cevap anahtarının doğruluğunu matematiksel olarak doğrulama
- Zorluk seviyelerinin gerçekten farklılaşıp farklılaşmadığını değerlendirme

---

## 🗄️ Saklı Plan: RAG Tabanlı Genişletme (Sonraki İterasyon)

MVP'nin çıktı kalitesi yetersiz kalırsa veya soru çeşitliliği darboğaz oluşturursa devreye alınacak **opsiyonel mimari**. MVP tamamlanmadan başlanmaz.

### Motivasyon
- Few-shot örnekler manuel hazırlandığı için ölçeklenmesi zor
- MEB'in tüm kaynaklarını (ders kitapları, ÖBA, EBA, kazanım açıklamaları) kapsamak için otomatik bir bilgi tabanı gerekli
- Semantik benzerlik (sadece string değil) ile gerçek çeşitlilik kontrolü

### Eklenecek Bileşenler

```
Sheet Generator/
├── knowledge_base/                # YENİ
│   ├── raw/                       # MEB PDF'leri (ders kitabı, müfredat dokümanı)
│   ├── processed/                 # Parse edilmiş chunk'lar
│   └── index/                     # Vector store (chroma/faiss)
│
├── app/
│   ├── services/
│   │   ├── retriever.py           # YENİ — kazanım koduna göre ilgili pasajları çek
│   │   ├── embedder.py            # YENİ — embedding üretimi
│   │   └── ingestion.py           # YENİ — PDF parse + chunk + embed pipeline
```

### Veri Kaynakları (MEB Resmi)
| Kaynak | URL Kalıbı | İçerik |
|--------|-----------|--------|
| Resmi müfredat | `mufredat.meb.gov.tr` | Kazanım dokümanları, açıklamalar |
| Ders kitapları | EBA / `meb.gov.tr` | Konu anlatımları, örnek sorular |
| ÖBA materyalleri | `ogmmateryal.eba.gov.tr` | Etkinlik ve örnekler |
| EBA içerikleri | `eba.gov.tr` | Video transkriptleri, sorular |

### Akış
1. **Ingestion (offline, bir kere):** PDF'leri indir → metin çıkar → kazanım koduna göre etiketle → chunk → embed → vector store
2. **Retrieval (üretim sırasında):** Hedef kazanım kodu için top-K ilgili pasaj + örnek soru çek
3. **Augmented prompt:** Few-shot bloğunu RAG'dan gelen gerçek MEB içerikleriyle ZENGİNLEŞTİR (manuel few-shot'ı tamamen değiştirmek yerine)
4. **Semantic dedup:** Üretilen sorunun embedding'i alınır; cosine similarity > 0.85 olanlar reddedilir

### MVP'den Geçiş Kriterleri
RAG'a geçmeden önce şunlar gözlemlenirse haklı sebep oluşur:
- Kullanıcı geri bildirimi: "Sorular tek tip" / "MEB ders kitabıyla örtüşmüyor"
- Aynı kazanımda 50+ üretim sonrası benzersiz soru oranı < %60
- Manuel few-shot bakımı sürdürülemez hale gelir (kazanım sayısı × 5 örnek = yüzlerce kayıt)

### Maliyet/Karmaşıklık
- Embedding API maliyeti (Gemini embedding veya open-source)
- Vector DB (chroma yerelde basit, prod'da pinecone/qdrant)
- PDF parsing pipeline (pypdf2 / pdfplumber)
- Hukuki kontrol: MEB içeriklerinin yeniden dağıtımı vs. yalnızca dahili kullanım

---

## Diğer Gelecek Aşamalar (Kapsam Dışı)
- 📄 PDF çıktı desteği
- 🎨 Web frontend
- 📚 8-12. sınıf desteği
- 🖼️ Geometri görselleri
- 📊 Çoktan seçmeli soru tipi
- 💾 Veritabanı (üretilen soruların kalıcı kaydı, kullanım analitiği)
