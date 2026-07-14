# Haftalık Çalışma Programı Template'i (WS-6a)

AI destekli haftalık çalışma programının **pedagojik iskeleti**. Program üreten kod
(`app/services/study_plan.py`) bu template'i izler; LLM yalnızca her günün başlık/ipucu
metnini ve haftanın özetini yazar (yapıyı değil — yapı deterministik).

## Araştırma özeti (nasıl program hazırlanıyor)

Türkiye'deki LGS/ortaokul çalışma-programı kaynaklarının ortak ilkeleri:

- **İhtiyaç-odaklı:** program öğrencinin **eksiklerine** göre şekillenir; plansız çalışma
  = konu biriktirme + düzensiz tekrar.
- **Denge:** haftanın **~4 günü** konu çalışması + soru çözümü, **1 günü** tekrar + eksik
  tamamlama, **hafta sonu** deneme + analiz.
- **Aralıklı tekrar (spaced repetition):** öğrenilen konu ilk 24 saatte, sonra
  günlük/haftalık/aylık tekrar edilmezse unutulur → her haftaya **geçmiş konu tekrarı**
  konur.
- **Hata analizi:** hafta sonuna, o hafta yanlış/boş yapılan soruların gözden geçirildiği
  bir blok konur.
- **Seans + mola:** 40-50 dk çalışma + 10-15 dk mola; her derse haftada ≥2 gün.

Kaynaklar: [perabilim](https://www.perabilim.com/lgs-ders-calisma-programi/) ·
[ilerlet](https://ilerlet.com/ders-calisma-programi-nasil-hazirlanir2026-ogrenciler-icin-rehber) ·
[testdiyari](https://testdiyari.com/8-sinif-ders-calisma-programi/) ·
[superprof](https://www.superprof.com.tr/blog/calisma-programi-olusturma-rehberi/)

## Bizim template (7 gün · Pazartesi → Pazar)

Öncelik **eksik kazanımlar** (zayıf→güçlü sırada); hafta içi eksiklerle doldurulur,
hafta sonu tekrar + karışık denemeye ayrılır. Üç gün tipi:

| Gün | Tip | Amaç | İçerik kaynağı | Soru |
|-----|-----|------|----------------|------|
| Pazartesi | **odak** | En öncelikli eksik #1 | en zayıf kazanım | 10 |
| Salı | **odak** | Eksik #2 | sıradaki zayıf kazanım | 10 |
| Çarşamba | **odak** | Eksik #3 | sıradaki zayıf kazanım | 10 |
| Perşembe | **odak** | Eksik #4 | sıradaki zayıf kazanım | 10 |
| Cuma | **tekrar** | Aralıklı tekrar — unutmayı önle | çalışılmış (güçlü) konu | 8 |
| Cumartesi | **karışık** | Hata analizi / karışık deneme | farklı konulardan | 12 |
| Pazar | **karışık** | Genel deneme + analiz | farklı konulardan | 12 |

**Uyarlama kuralları (deterministik):**
- Eksik konu 4'ten azsa: kalan **odak** günleri otomatik **tekrar**a, tekrar havuzu da
  boşsa **karışık**a düşer → program **her zaman 7 gün** ve dolu.
- Hiç eksik yoksa (öğrenci güçlü): hafta **tekrar + karışık**a döner (pekiştirme).
- Hiç veri yoksa (çözüm yok): program üretilmez, önce quiz çözmeye teşvik edilir
  (eksik bilinmeden kişiselleştirme yapılamaz).
- **Karışık** günler tek kazanıma bağlı değildir → "Çalış" genel/karışık üretime gider.
- Soru sayısı tipe göre değişir (odak 10 · tekrar 8 · karışık 12) → çeşitlilik.

**LLM'in rolü:** her gün için türe uygun `title` (3-6 kelime) + somut `tip` (tek cümle) +
haftalık `summary`. Yapıyı, dersi, kazanımı, linki LLM belirlemez (uydurma riski yok);
sıkı timeout + fail-open ile deterministik metne düşülür.
