# Aşama D — Müfredat Genişletmesi (MEB 2024)

> **Durum:** Tamamlandı (2026-04-25). `curriculum.py`'a 16 yeni kazanım eklendi, mevcut tagged chunk'lar yeni kazanımlara yeniden bağlandı, few-shot örnekleri eklendi, end-to-end üretim doğrulandı.

---

## TL;DR

- **16 yeni kazanım** eklendi (5/6/7. sınıf), **2 yeni öğrenme alanı** açıldı (Veri İşleme ve İstatistik, Olasılık).
- **167 textbook chunk** yeniden etiketlenip yeni kazanımlara bağlandı (önceden `curriculum_expansion` olarak gizliydi).
- **Aşama A+B+D toplam ek maliyet: ~$1.80** (Aşama D katkısı $0.30 — re-tagging Gemini Flash).
- ChromaDB'de embedding'ler aynı kaldı (text değişmedi); sadece metadata güncellendi.
- Yeni kazanımlar için few-shot pool zenginleştirildi (her kazanıma 2 örnek).
- End-to-end test: 3 yeni kazanım (Olasılık, Merkezi Eğilim, Çarpan/Asal) için 3'er soru üretildi, kalite yüksek.

---

## Eklenen Kazanımlar

### 5. sınıf (3 yeni)

| Kazanım | Konu | Alan |
|---------|------|------|
| M.5.2.5 | Yüzdeyi tanır, basit yüzde hesapları | Kesirler |
| M.5.3.5 | Temel geometrik kavramlar (nokta, doğru, ışın, paralel, dik) | Geometri |
| M.5.6.1 | Veri toplama, sıklık tablosu, sütun grafiği | **Veri İşleme** (yeni) |

### 6. sınıf (10 yeni)

| Kazanım | Konu | Alan |
|---------|------|------|
| M.6.1.5 | Çarpan, kat, asal sayı kavramları | Doğal Sayılar |
| M.6.1.6 | OBEB ve OKEK | Doğal Sayılar |
| M.6.1.7 | Bölünebilme kuralları (2, 3, 4, 5, 6, 9, 10) | Doğal Sayılar |
| M.6.2.5 | Yüzde problemleri (indirim, KDV, kâr-zarar) | Kesirler |
| M.6.3.4 | Açılar (tümler, bütünler, komşu, ters) | Geometri |
| M.6.3.5 | Çember ve dairenin temel elemanları | Geometri |
| M.6.5.4 | Algoritma ve akış şemaları | Cebir |
| M.6.6.1 | Sütun ve çizgi grafikleri | **Veri İşleme** (yeni) |
| M.6.6.2 | Aritmetik ortalama, ortanca, tepe değer | **Veri İşleme** (yeni) |
| M.6.7.1 | Olası, kesin, imkansız durumlar; basit olasılık | **Olasılık** (yeni) |

### 7. sınıf (3 yeni)

| Kazanım | Konu | Alan |
|---------|------|------|
| M.7.6.1 | Daire grafiği oluşturma ve yorumlama | **Veri İşleme** (yeni) |
| M.7.6.2 | Aritmetik ortalama, ortanca, tepe değeri ileri yorum | **Veri İşleme** (yeni) |
| M.7.7.1 | Olasılık hesabı (kesir, ondalık, yüzde) | **Olasılık** (yeni) |

**Toplam: 16 yeni kazanım, kazanım sayısı 107 → 123 (%+15)**

---

## Re-tagging Sonuçları

Mevcut tagged JSON'larda `kazanim_kod_llm=null` + `confidence ∈ {high, medium}` chunk'lar Gemini'ye yeniden gönderildi (genişletilmiş kazanım listesi ile).

| Sınıf | Re-tag Aday | Yeni Eşleşme | Hala Unmapped |
|-------|-------------|--------------|---------------|
| 1 | 14 | 2 (M.1.5.x fallback) | 12 |
| 2 | 33 | 13 (M.2.1.x, M.2.4.x fallback) | 20 |
| 5 | 76 | **50** (M.5.6.1: 39, M.5.2.5: 5, M.5.3.5: 4, fallback: 2) | 24 |
| 6 | 98 | **79** (M.6.1.5: 21, M.6.6.2: 13, M.6.7.1: 13, M.6.6.1: 10, M.6.1.6: 7, M.6.1.7: 7, M.6.2.5: 6, M.6.3.4: 1, M.6.3.5: 1) | 18 |
| 7 | 39 | 23 (M.7.6.1: 11, M.7.6.2: 7, fallback: 4, M.7.7.1: 0*) | 16 |
| **TOPLAM** | **260** | **167** | **90** |

\* M.7.7.1 (Olasılık) için textbook chunk eşleşmesi olmadı çünkü 7. sınıf "test/kavrama kitabı" Olasılık konusunu sınırlı işliyor. Few-shot ile destek devreye girdi.

### Eşleşme oranı: %64 (167/260)

Hala unmapped olan 90 chunk:
- "Diğer / Sözlük / Coğrafya / Ders Kitabı Yönergeleri" gibi gerçekten matematik dışı içerikler
- 6. sınıf'ta birkaç "üslü ifadeler" chunk'ı (kazanım eklemedim — düşük yoğunluk)
- 7. sınıf'ta "tam sayıların kuvvetleri" detayları (mevcut M.7.1.4 ile zayıf eşleştirilebiliyor)

---

## ChromaDB Güncelleme

**Strateji:** Embedding'ler aynı (chunk metni değişmedi) — `collection.update(ids, metadatas)` ile sadece metadata güncellendi. Hızlı, idempotent, embedding maliyeti yok.

| Metrik | Değer |
|--------|-------|
| Update edilen chunk | 167 |
| Insert edilen | 0 (hepsi mevcuttu) |
| Toplam koleksiyon (değişmedi) | 2.861 |
| Embedding maliyeti (Aşama D) | $0 |
| Re-tagging maliyeti (Aşama D) | ~$0.30 |
| Re-tagging süresi | ~10 dk (paralel) |

---

## Few-shot Genişlemesi

Her yeni kazanım için 2 manuel few-shot örneği eklendi (`app/data/few_shot/grade_{5,6,7}.py`):
- 5. sınıfa 6 yeni örnek (3 kazanım × 2)
- 6. sınıfa 20 yeni örnek (10 kazanım × 2)
- 7. sınıfa 6 yeni örnek (3 kazanım × 2)
- **Toplam: 32 yeni few-shot örneği**

Few-shot örnekleri henüz ChromaDB'ye ingest edilmedi (yeni `ingest_to_chroma.py --rebuild` çalıştırılırsa girer). Şu an statik fallback ile kullanılıyor — agent zaten doğru davranıyor (sentetik+textbook ChromaDB'den + manuel pool'dan birleşik).

---

## End-to-End Doğrulama

3 yeni kazanım için 3'er soru üretildi (`include_textbook=True`, gerçek üretim akışı):

### M.6.7.1 — Olasılık ✅
> "Bir kutuda 8 kırmızı, 6 mavi ve 10 sarı kalem bulunmaktadır. Kutudan rastgele çekilen bir kalemin mavi olmama olasılığını kesir olarak ifade ediniz." → **3/4** ✅
>
> "Bir torbaya 1'den 24'e kadar numaralandırılmış eş büyüklükte kartlar konuluyor. Torbadan rastgele çekilen bir kartın tek sayı veya çift sayı olma olasılıklarını ayrı ayrı kesir olarak ifade ediniz..." (eş olasılık kavramı) ✅

### M.6.6.2 — Aritmetik Ortalama, Ortanca, Tepe Değer ✅
> "Bir sınıftaki 7 öğrencinin bir sınavdan aldığı puanlar 60, 70, 75, 80, 85, 90, 20. Bu veri grubunu en iyi temsil eden merkezi eğilim ölçüsü hangisidir?" → "Ortanca; çünkü 20 puanı gibi bir aykırı değer aritmetik ortalamayı etkilerken, ortanca veri grubunun genelini daha iyi yansıtır." ✅

### M.6.1.5 — Çarpan/Asal Sayılar ✅
> "108 sayısını asal çarpanlarının çarpımı şeklinde yazınız." → **108 = 2² × 3³** ✅
>
> "91 sayısı asal bir sayı mıdır? ... 91 sayısının çarpanları 1, 7, 13 ve 91'dir. Asal sayılar sadece 1'e ve kendisine kalansız bölünebilen ... 91 sayısının başka çarpanları olduğu için asal değildir." ✅

**Streamlit dropdown:** Yeni `Veri İşleme` ve `Olasılık` topic'leri otomatik göründü (CURRICULUM dict üzerinden tarandığı için).

---

## Aşama A + B + D Toplam Görünüm

| Metrik | Aşama A | Aşama B | Aşama D | Toplam |
|--------|---------|---------|---------|--------|
| Çıkarılan chunk | 378 | 1.378 | — | 1.756 |
| ChromaDB'ye eklenen | 231 | 811 | 0 (sadece update) | 1.042 |
| Mapped (kazanıma bağlı) | 155 | 628 | +167 | **950** |
| Curriculum_expansion (gizli) | 76 | 874 | −167 | 783 |
| Eklenen kazanım | 0 | 0 | +16 | 123 |
| Maliyet | $0.30 | $1.20 | $0.30 | **$1.80** |
| Süre | ~25 dk | ~25 dk | ~15 dk | ~65 dk |

**Eşleşme oranı:** Aşama A+B sonrası %46 (783/1.733), Aşama D sonrası **%55 (950/1.733)** ✅

---

## Üretilen Dosyalar (Aşama D)

- `app/models/enums.py` — `VERI_ISLEME`, `OLASILIK` TopicId değerleri
- `app/data/curriculum.py` — 16 yeni kazanım + difficulty_hints
- `app/data/few_shot/grade_5.py`, `grade_6.py`, `grade_7.py` — 32 yeni few-shot örneği
- `scripts/retag_unmapped.py` — Re-tagging script (yeni)
- `scripts/reingest_retagged.py` — Metadata güncelleme script (yeni)
- `knowledge_base/processed/retag_run_grade{1,2,5,6,7}.log` — Re-tagging logları
- `knowledge_base/processed/textbook_chunks_grade{1,2,5,6,7}_tagged.json` — `retagged: True` flag eklendi

---

## Sonraki Adım Seçenekleri

### Seçenek 1: Sentetik corpus üretimi (yeni kazanımlar için) — önerim
**Süre:** 1-2 saat | **Maliyet:** $3-5
**Etki:** Her yeni kazanım için 5×3 zorluk = 15 sentetik soru üretilir → ChromaDB'ye ingest. Few-shot zenginliği artar.

### Seçenek 2: Aşama C — 3-4. sınıf OCR (Gemini Vision)
**Süre:** yarım gün | **Maliyet:** $10-15
**Etki:** Bu iki sınıf için textbook chunks aktif olur (sentetik corpus zaten kapsamlı).

### Seçenek 3: A/B test (Aşama D etkisi)
**Süre:** 30 dk | **Maliyet:** ~$0.30
**Etki:** Yeni kazanımlar için sentetik-only vs sentetik+textbook karşılaştır; Aşama D'nin sayısal etkisini ölç.

### Seçenek 4: Production hazırlığı
- Streamlit'i polish et (yeni topic'ler için ikon/açıklama)
- Test coverage ekle
- Logging/monitoring
- Rate limit ve quota yönetimi
