"""Gemini prompt şablonları: system + few-shot + user katmanları."""
import re

from app.data.curriculum import Kazanim
from app.models.enums import Difficulty, QuestionType

# Few-shot örneklerindeki ham <svg> bloğu — model raw SVG çizmeyi TAKLİT ediyordu
# (D2b: gorsel_geometri drop'larının kaynağı). Örnekte nötrlenir → model görsel tipleri
# {{geo}}/{{chart}}/{{pattern}} direktifiyle üretmeye (system prompt yönergesine) döner.
_FEWSHOT_SVG_RE = re.compile(r"<svg\b.*?</svg>", flags=re.DOTALL | re.IGNORECASE)

SYSTEM_PROMPT = """Sen MEB (Milli Eğitim Bakanlığı) müfredatına uygun matematik soruları üreten bir eğitim asistanısın. Türkiye'deki ilkokul ve ortaokul matematik ders kitaplarını referans alıyorsun.

Kuralların:
1. Sorular MUTLAKA verilen kazanım metninin kapsamı dahilinde olmalı.
2. Kazanımın dışına çıkan, üst sınıf bilgisi gerektiren soru ÜRETME.
3. Sorular açık uçlu ve işlem tabanlı olmalı (çoktan seçmeli ASLA üretme).
4. Her sorunun kesin ve doğru bir cevabı olmalı; matematiksel olarak hatalı soru üretme.
5. Görsel ihtiyaçları (tablo/grafik/şekil) için RESİM ya da SVG üretme; bunun yerine SADECE METİN-TABANLI gösterimler kullan:
   - Tablolar için: markdown ELLE YAZMA → `{{table: Baş1 | Baş2 ;; s1h1 | s1h2 ;; s2h1 | s2h2}}`
     direktifini kullan (`;;` satır, `|` hücre, ilk satır başlık); sistem kusursuz tablo üretir.
   - Sütun/çubuk grafikleri için: kod bloğu içinde `█` veya `▇` karakterleriyle yatay/dikey çubuklar (her çubuğa etiket ve değer).
   - Geometrik şekiller için: kod bloğu içinde Unicode geometri karakterleri (△ □ ○ ◇ ▲ ●) + kenar/açı ölçüleri metin etiketi olarak.
   - Örüntüler için: Unicode sembol dizisi (♥ ♦ ♠ ★ ▲ ●) ya da emoji (🔴 🔵 🟢) — düzenli aralıklı.
   Tüm görsel bloklar `question` alanının İÇİNDE Markdown olarak gömülü olmalı. Soru kendi kendini açıklamalı; soru metni okunup görsel görüldüğünde net olmalı.
6. Zorluk seviyesi "Zorluk Kalibrasyonu" bölümünde somut olarak belirtilmiştir — sayısal aralık, adım sayısı ve bağlam karmaşıklığı bu kalibrasyona UYMALIDIR:
   - Kolay: tek adım, sınıf düzeyinin tabanında sayılar, bağlam yalın.
   - Orta: 2-3 adım, sınıf düzeyi sayılar, kısa günlük hayat bağlamı.
   - Zor: çok adımlı, sınıf üst sınırı sayılar, birden fazla kavram birleşik.
7. Soruları akıcı, sade ve doğru Türkçe ile, MEB ders kitabı tonunda yaz.
8. Her sorunun çözüm adımlarını mutlaka belirt.
9. İstenen soru tipi dağılımına TAM olarak uy. Tip-spesifik formatlar:
   - `salt_islem`: SADECE matematiksel ifade ve "= ?" — Türkçe açıklama ASLA olmasın. İfadeyi `$...$` (inline) veya `$$...$$` (display) sınırlayıcılarıyla LaTeX matematik notasyonunda yaz. Kesirler `\\frac{a}{b}`, kökler `\\sqrt{x}`, üs `^{n}`, alt indis `_{n}`. Çarpma `\\times`, bölme `\\div`, eşitsizlik `\\leq` `\\geq` `\\neq`. Çoktan basamak/değişken gerektiren ifadelerde display mode (`$$`) tercih edilir.
       Örnekler:
         - "$$\\frac{3}{4} + \\frac{1}{6} = ?$$"
         - "$$(12 + 8) \\times 3 \\div 5 = ?$$"
         - "$$\\sqrt{144} + 5^2 = ?$$"
         - "$$2x + 7 = 15 \\Rightarrow x = ?$$"
       UYARI: Kullanılan tüm semboller mathtext destekli olmalı (LaTeX standart subset). `\\begin{cases}`, `\\text{}` gibi karmaşık yapıları KULLANMA.
   - `tablo_sorusu`: Soru metni + tablo + tabloya dayalı hesap/yorum sorusu. Tabloyu
       **`{{table:...}}` DİREKTİFİYLE** ver (ham markdown `|---|` YAZMA):
       `{{table: Şehir | Nüfus (Okunuşu) ;; Şehir A | Sekiz milyon kırk bin iki yüz beş ;; Şehir B | Seksen milyon dört yüz bin yirmi beş ;; Şehir C | Sekiz yüz milyon kırk bin yirmi beş}}`
       En fazla ~6 satır / 5 sütun. `answer` tablodaki verilerle TUTARLI olmalı.
   - `gorsel_geometri`: Soru metni + GEOMETRİ DİREKTİFİ. **INLINE `<svg>` ÇİZME!** Şekli yalnızca
       aşağıdaki `{{geo:...}}` direktifiyle ver; sistem doğru orantılı, etiketleri çakışmayan,
       temiz SVG üretir (LLM'in elle çizdiği geometri şekilleri bozuk/etiketi kayık çıkıyordu).
       Değerler sayı veya `?` (bilinmeyen — ör. Pisagor'da hipotenüs); değere birim eklenebilir (`a=6 cm`):
       (a) Dik üçgen (Pisagor):  `{{geo:right_triangle|a=6|b=8|c=?}}`  (a taban, b dik kenar, c hipotenüs — dik açı işaretlenir)
       (b) Üçgen alan:  `{{geo:triangle|base=12|height=5}}`  (taban + kesikli yükseklik çizgisi)
           Genel üçgen:  `{{geo:triangle|a=5|b=6|c=7}}`  (a sol kenar, b sağ kenar, c taban)
       (c) Dikdörtgen:  `{{geo:rectangle|w=8|h=5}}`  ·  Kare:  `{{geo:square|s=6}}`
       (d) Çember:  `{{geo:circle|r=7}}`  (yarıçap çizgisi + etiket)
       (d2) Paralelkenar:  `{{geo:parallelogram|base=10|height=6}}`  ·  Yamuk:  `{{geo:trapezoid|a=6|b=12|h=5}}`  (a üst taban, b alt taban, h yükseklik — kesikli yükseklik çizgisi)
       (d3) Açı:  `{{geo:angle|deg=65}}`  (köşe + iki ışın + derece yayı; ölçme/açı soruları)
       (e) Direktifi soru metninin içine ilgili cümleden hemen sonra koy. Direktifteki ölçüler soru
           ve cevapla TUTARLI olmalı. `answer` sade sayı + birim (ör. "32 cm"); LaTeX ($) KULLANMA.
       (f) Bu 5 şekle (dik üçgen / üçgen / dikdörtgen / kare / çember) UYMAYAN özel bir figür
           gerekiyorsa o soruyu ÜRETME → metin-tabanlı başka bir tip seç. Direktif DIŞINDA ASLA
           `<svg>`, `<path>`, `<polygon>`, `<circle>` vb. YAZMA.
       TAM ÖRNEK (formatı öğren, sayıları kopyalama): question = "Bir dik üçgenin dik kenarları
       6 cm ve 8 cm uzunluğundadır. {{geo:right_triangle|a=6 cm|b=8 cm|c=?}} Bu üçgenin hipotenüs
       uzunluğu kaç cm'dir?" · answer = "10 cm" — DİKKAT: `<svg>` YOK, sadece `{{geo:...}}` direktifi.
   - `grafik_okuma`: Soru metni + grafiğe dayalı soru. **SVG ÇİZME!** Grafiği yalnızca
       aşağıdaki VERİ DİREKTİFİ ile belirt; sistem doğru orantılı, etiketleri çakışmayan
       grafiği otomatik üretir (LLM'in elle çizdiği grafikler bozuk çıkıyordu):
       (a) Pasta/daire grafiği:  `{{chart:pie|Etiket1=deger1|Etiket2=deger2|...}}`
           Örn: `{{chart:pie|Futbol=40|Basketbol=30|Voleybol=20|Tenis=10}}` (değerler yüzde veya sayı; sistem oranı hesaplar).
       (b) Sütun/çubuk grafiği:  `{{chart:bar|Etiket1=deger1|Etiket2=deger2|...}}`
           Örn: `{{chart:bar|Ocak=10|Şubat=14|Mart=8}}`
       (c) Direktifi soru metninin içine, ilgili cümleden hemen sonra koy. En fazla 8 kategori.
       (d) `answer` ve çözüm, direktifteki değerlerle TUTARLI olmalı (ör. basketbol oranı soruluyorsa cevap o değerin yüzdesi).
       (e) Direktif dışında ASLA `<svg>`, `<path>`, `<rect>` vb. YAZMA.
   - `oruntu_sekil`: Soru metni + örüntü. **SVG ÇİZME!** Örüntüyü yalnızca aşağıdaki
       VERİ DİREKTİFİ ile belirt; sistem şekilleri doğru, çakışmasız SVG olarak üretir
       (LLM'in elle çizdiği örüntüler bozuk çıkıyordu):
       (a) Şekil dizisi:  `{{pattern:şekil#renk, şekil#renk, ..., ?}}`
           Şekiller: `daire`, `kare`, `ucgen`, `yildiz`, `elmas`. Renkler: `kirmizi`,
           `mavi`, `yesil`, `sari`, `mor`, `turuncu`, `pembe` (veya `#ef4444` gibi hex).
           Eksik konum `?`. Örn: `{{pattern:daire#kirmizi, kare#mavi, ucgen#yesil, daire#kirmizi, kare#mavi, ?}}`
       (b) Büyüyen (sayısal) örüntü:  `{{pattern:grow|sayı1,sayı2,...,?}}` — her hücreye
           o kadar nokta çizilir. Örn: `{{pattern:grow|1,3,5,?}}` (cevap: 7).
       (c) Direktifi soru metninin içine, ilgili cümleden hemen sonra koy. En fazla ~8-10 öğe.
       (d) Örüntü kuralı (renk/şekil/sayı) MATEMATİKSEL tutarlı olmalı; `answer` kuralı
           uygulayarak bulunur (ör. yukarıda cevap "yeşil üçgen" veya "7").
       (e) Direktif dışında ASLA `<svg>`, `<circle>`, `<rect>` vb. YAZMA.
   - `coktan_secmeli`: Soru KÖKÜNÜ `question` alanına yaz — şıkları soru metnine GÖMME. 4 şıkkı `options` alanına, DÜZ METİN olarak (harf öneki "A)" vb. OLMADAN), doğru sırayla ver: `["12", "15", "18", "20"]`. Tam 4 şık; SADECE BİRİ doğru; çeldiriciler makul yanlışlar (yaygın hatalar) olsun. `answer` alanı SADECE doğru şıkkın harfi ("A", "B", "C" veya "D") — bu harf `options` dizisindeki konuma karşılık gelir (A=1., B=2., C=3., D=4.). Çözüm hangi şıkkın neden doğru olduğunu ve diğerlerinin neden yanlış olduğunu açıklar.
   - `bosluk_doldurma`: Soru cümlesi içinde bir veya birden fazla "_____" (en az 3 alt çizgi) boşluğu olsun. `answer` alanı boşluğa giren ifadeler — birden fazla boşluk varsa "; " ile ayrılır (örn. "12; 5"). Sıralama soldan sağa.
   - `dogru_yanlis`: Soru yerine TEK bir iddia/önerme cümlesi yaz (örn. "Bir karenin tüm kenarları eşittir."). Soru işareti olmasın. `answer` SADECE "Doğru" veya "Yanlış" olsun. Çözüm önermenin neden doğru/yanlış olduğunu kazanım çerçevesinde açıklar.
   - `eslestirme`: `question` = kısa yönerge + BOŞ SATIR + **2 kolonlu `{{table:...}}` direktifi** (ham markdown `|---|` YAZMA). Sol kolon numaralı öğeler (1,2,3…), sağ kolon KARIŞTIRILMIŞ harf karşılıkları (a,b,c…). Tipik 3-4 satır. `answer` = "1-c, 2-a, 3-b" eşleşmeleri.
     ⛔ **ZORUNLU: eşleştirilecek öğe+karşılık tablosunu `question` METNİNE MUTLAKA KOY. Yalnız "…eşleştiriniz." yönergesini yazıp tabloyu/öğeleri EKLEMEMEK KESİNLİKLE YASAK** — böyle bir soru cevaplanamaz ve OTOMATİK ELENİR (boşa üretim). Öğeler `answer`'da değil, GÖVDEDE olmalı.
     Örnek `question`: `Aşağıdaki kavramları tanımlarıyla eşleştiriniz.\n\n{{table: Kavram | Tanım ;; 1. İklim | a. Yeryüzünün yüksek ve engebeli bölümü ;; 2. Ova | b. Bir yerin uzun yıllar ortalama hava durumu ;; 3. Dağ | c. Alçak ve düz geniş arazi}}` · `answer`: `1-b, 2-c, 3-a`.
   - `siralama`: `question` = kısa yönerge + BOŞ SATIR + **sıralanacak KARIŞIK öğe listesi** (her öğe kendi satırında "I. …", "II. …" ya da "1. …", "2. …" ile numaralı). `answer` = doğru sıra " → " (boşluklu ok) ile.
     ⛔ **ZORUNLU: sıralanacak öğeleri `question` METNİNE MUTLAKA KOY. Yalnız "…sıralayınız." yönergesini yazıp öğeleri EKLEMEMEK KESİNLİKLE YASAK** — cevaplanamaz → OTOMATİK ELENİR. Öğeler `answer`'da değil, GÖVDEDE olmalı.
     Örnek `question`: `Aşağıdaki olayları oluş sırasına göre sıralayınız.\n\nI. Cumhuriyet ilan edildi.\nII. TBMM açıldı.\nIII. Kurtuluş Savaşı başladı.` · `answer`: `III → II → I`.
   - Diğer tipler (islem, sozel_problem, vs.): mevcut sözel/işlem formatında devam.
10. Verilen örnek soruların stilini ve seviyesini referans al, AMA aynı sayıları/bağlamları KOPYALAMA. GÖRSELLİ örneklerde (SVG/grafik/tablo): şekli OLDUĞU GİBİ KOPYALAMA — örnekteki görselin MANTIĞINI çöz (görsel neyi temsil ediyor, hangi veri şekilden okunuyor, soru şekil üzerinden neyi soruyor) ve bu mantığı KENDİ sorununa uygun FARKLI TASARIMDA yeni bir görselle uygula: farklı şekil türü, farklı düzen/yerleşim, farklı sayılar ve farklı gerçek yaşam bağlamı kullan. Örneğin bir "sayı doğrusu" örneğinden hareketle bir "kesir modeli", "geometrik şekil", "grafik" veya "tablo" da tasarlayabilirsin — yeter ki görsel soruyla matematiksel olarak TUTARLI olsun. Amaç örnekleri çoğaltmak değil, görsel kurma mantığını yeni ve özgün şekillerde üretebilmektir. Uygun olan HER konuda (sadece geometri değil; sayılar, kesir, cebir, veri, olasılık) görselli soru üretmekten çekinme.
11. Verilen örnekler hedef zorluğa yakın seçilmiştir; üretimlerini aynı zorlukta tut.
12. AÇILIŞ/KALIP ÇEŞİTLİLİĞİ (aynı kağıttaki sorular arası — ÖNEMLİ): soruların cümle
    İSKELETİNİ çeşitlendir; hepsi "Bir ..." ile BAŞLAMASIN. Farklı isim/bağlam seçmek
    YETMEZ (çiçekçi→otobüs→öğretmen hâlâ aynı kalıptır) — açılış YAPISINI değiştir. Karışık aç:
      • doğrudan soruyla ("Kaç ... eder?", "... kaçtır?")
      • birinci/ikinci kişi ("Elimde ... var", "... alışverişe çıktın")
      • diyalog/konuşma ("Ali, kardeşine ... dedi.")
      • zaman/durum kurgusu ("... yaparken", "Hafta sonu ...")
      • veri/tablo/görselle başlayan
      • soru-önce, bağlam-sonra
    Aynı açılış kalıbı bir kağıtta EN FAZLA 1-2 kez tekrarlansın; 5 soruda 5 farklı iskelet hedefle.
13. Çıktıyı MUTLAKA istenen JSON formatında üret; ek metin/açıklama EKLEME. `question` alanı Markdown içerebilir — newline (\\n), tablo, kod bloğu (```...```) serbesttir."""


# MEB TYMM ünite kazanımları kazanım-bazlı difficulty_hints taşımaz (yalnız kod+metin).
# Hint yoksa modelin zorluk kalibrasyonu tamamen kaybolmasın diye genel bir talimat
# uygulanır. Kazanım-özel hint (eski müfredat) varsa o tercih edilir.
_GENERIC_DIFFICULTY_HINT: dict[str, str] = {
    "kolay": "Tek adımlı, doğrudan işlem/tanıma; sade sayılar, kısa ifade.",
    "orta": "İki adımlı veya kısa bağlamlı problem; işlemi seçmeyi gerektirir.",
    "zor": "Çok adımlı muhakeme, ters/eksik bilgi veya birden çok kavramı birleştirme.",
}


def _format_kazanim_block(
    kazanimlar: list[Kazanim],
    difficulty: Difficulty,
    generic_hints: dict[str, str] | None = None,
) -> str:
    """`generic_hints`: DERSİN genel zorluk kalibrasyonu (ders modülünden gelir).

    Verilmezse matematiğin kalibrasyonu kullanılır. NEDEN AYRI (2026-08-24): MEB TYMM
    kazanımları kazanım-bazlı `difficulty_hints` TAŞIMAZ → sözel derslerde (Türkçe/
    Sosyal/İngilizce) her prompt'a matematiğin metni giriyordu ("sade sayılar",
    "işlemi seçmeyi gerektirir") ve modeli sayısal/işlem sorusuna itiyordu. Ders
    modülleri kendi `GENERIC_DIFFICULTY_HINT`'ini zaten tanımlıyordu ama HİÇBİR YERDE
    KULLANILMIYORDU (ölü kod) — bu parametre onu bağlar."""
    level = difficulty.value
    generic = (generic_hints or _GENERIC_DIFFICULTY_HINT).get(level, "")
    if len(kazanimlar) == 1:
        k = kazanimlar[0]
        hint = k.get("difficulty_hints", {}).get(level, "") or generic
        lines = [
            f"Hedef Kazanım Kodu: {k['kod']}",
            f"Hedef Kazanım Metni: {k['metin']}",
        ]
        if hint:
            lines.append(f"Zorluk Kalibrasyonu ({level}): {hint}")
        return "\n".join(lines)
    lines = ["Hedef Kazanımlar (soruları bu kazanımlar arasında dengeli dağıt):"]
    any_specific = any(k.get("difficulty_hints", {}).get(level) for k in kazanimlar)
    for k in kazanimlar:
        hint = k.get("difficulty_hints", {}).get(level, "")
        lines.append(f"  - {k['kod']}: {k['metin']}")
        if hint:
            lines.append(f"      Zorluk Kalibrasyonu ({level}): {hint}")
    if not any_specific and generic:
        lines.append(f"  Genel zorluk kalibrasyonu ({level}): {generic}")
    return "\n".join(lines)


def _format_distribution(distribution: dict[QuestionType, int]) -> str:
    lines = ["Soru Tipi Dağılımı (toplam soru sayısına eşit olmak ZORUNDA):"]
    for qt, n in distribution.items():
        lines.append(f"  - {qt.value}: {n} adet")
    # ÖLÇÜLDÜ (2026-07-29, canlı 7. sınıf Sosyal kağıtları): dağılım listelenmesine
    # rağmen model listede OLMAYAN tipler yazıyordu (sosyal soruya matematiğe özel
    # `salt_islem`). O tip MC sayılmadığı için 4-şık kapısı atlanıp soru ŞIKSIZ
    # teslim ediliyordu. Yasak açıkça yazılmadığı için modele bırakılmış bir boşluktu.
    lines.append(
        "  ⛔ YALNIZ yukarıda listelenen tipleri kullan. Listede olmayan bir "
        "`question_type` yazmak YASAK (soru elenir)."
    )
    return "\n".join(lines)


def _format_few_shot(
    examples: list[dict],
    target_difficulty: Difficulty,
    source: str = "static",
) -> str:
    if not examples:
        return ""
    header = (
        f"Hedef zorluk ({target_difficulty.value}) için MEB müfredat havuzundan seçilmiş örnek sorular "
        "(ASLA bu sayıları/bağlamları kopyalama; stil, seviye ve çeşitlilik referansı):"
    )
    if source == "rag":
        header = (
            f"Hedef zorluk ({target_difficulty.value}) için vector store'dan alınmış ilgili örnek sorular "
            "(MEB müfredatı + sentetik zengin corpus). Stil, seviye ve çeşitlilik referansı — "
            "sayıları/bağlamları KOPYALAMA."
        )
    lines = ["", header]
    for i, ex in enumerate(examples, start=1):
        qt = ex["type"]
        qt_value = qt.value if isinstance(qt, QuestionType) else str(qt)
        ex_diff = ex.get("difficulty", "orta")
        ex_src = ex.get("source")
        src_suffix = f" | Kaynak: {ex_src}" if ex_src else ""
        lines.append(f"\n[Örnek {i} — Tip: {qt_value} | Zorluk: {ex_diff}{src_suffix}]")
        ex_q = _FEWSHOT_SVG_RE.sub(
            "[görsel — SEN {{geo:...}} / {{chart:...}} direktifiyle üret]", ex["question"]
        )
        lines.append(f"Soru: {ex_q}")
        lines.append(f"Cevap: {ex['answer']}")
        lines.append(f"Çözüm: {ex['solution']}")
    return "\n".join(lines)


def _format_textbook_context(chunks: list[dict]) -> str:
    """MEB ders kitabından alınmış chunk'ları referans bağlam olarak biçimler."""
    if not chunks:
        return ""
    lines = [
        "",
        "MEB DERS KİTABINDAN İLGİLİ İÇERİK (referans olarak — KOPYALAMA, sadece stil/seviye/bağlam ipucu olarak kullan):",
    ]
    for i, c in enumerate(chunks, 1):
        page = c.get("page_start")
        page_str = f" sayfa {page}" if page is not None else ""
        header = c.get("header") or "kavram"
        ct = c.get("content_type") or ""
        ct_label = {
            "textbook_example": "Örnek",
            "textbook_activity": "Etkinlik",
            "textbook_problem": "Problem",
            "textbook_exercise": "Alıştırma",
            "textbook_concept": "Kavram",
            "curriculum_expansion": "Müfredat dışı bağlam",
        }.get(ct, ct)
        src = c.get("source") or ""
        text = (c.get("question") or "")[:700]
        lines.append(f"\n[Kaynak {i} — {ct_label} | {src}{page_str} | başlık: {header}]")
        lines.append(text)
    lines.append("")
    lines.append(
        "Yukarıdaki ders kitabı içerikleri SADECE bağlam ve seviye referansıdır. "
        "Aynı sayıları, isimleri veya senaryoları KOPYALAMA — kendi sorularını farklı bağlamlarla üret."
    )
    return "\n".join(lines)


def _format_exclusions(context_exclusions: list[str]) -> str:
    if not context_exclusions:
        return ""
    return (
        "\nKullanılmaması gereken bağlamlar (önceki üretimlerde geçti, "
        "sorularında BU kelimeleri kullanma; farklı bağlamlar seç):\n"
        + ", ".join(context_exclusions)
    )


def build_retry_prompt(
    original_user_prompt: str,
    already_generated_questions: list[str],
    missing_count: int,
    missing_distribution: dict[QuestionType, int] | None = None,
) -> str:
    """Eksik kalan sorular için yeniden üretim prompt'u.

    Orijinal talimat + kazanım + zorluk kriterleri korunur; üstüne
    daha önce üretilmiş soruların metinleri 'tekrar etme' uyarısıyla eklenir.

    `missing_distribution` verilirse hangi soru tipinden kaç tane üretilmesi
    gerektiği açıkça belirtilir — modelin tüm eksikleri ISLEM ile doldurmaması için.
    """
    already_block = "\n".join(
        f"  {i + 1}. {q}" for i, q in enumerate(already_generated_questions)
    )
    distribution_block = ""
    if missing_distribution:
        items = [
            f"  - {qt.value}: {n} adet"
            for qt, n in sorted(missing_distribution.items(), key=lambda x: -x[1])
            if n > 0
        ]
        if items:
            distribution_block = (
                "\n\nEKSİK KALAN SORU TİPLERİ — TAM olarak şu dağılımla üret "
                "(diğer tipleri tercih ETME, eksikleri kapat):\n"
                + "\n".join(items)
            )
    extension = (
        "\n\n─── YENİDEN ÜRETİM ───\n"
        "Aşağıdaki sorular daha önce üretildi. ASLA bu soruların aynısını, çok benzerini "
        "veya aynı sayıları/bağlamları kullanan başka bir versiyonunu üretme:\n"
        f"{already_block}\n\n"
        f"Yukarıdakilerden tamamen FARKLI, {missing_count} yeni soru üret."
        f"{distribution_block}\n\n"
        "Önceki talimatlar (kazanım, zorluk, JSON formatı) aynen geçerli."
    )
    return original_user_prompt + extension


_YENI_NESIL_BLOCK = """YENİ NESİL (HARMAN) MOD — bu kağıtta sorular KARIŞIK olsun: bir kısmı klasik hızlı pratik, bir kısmı yeni nesil/beceri temelli. Zorluktan BAĞIMSIZ olarak:
- `gunluk_hayat`, `sozel_problem`, `modelleme`, `akil_yurutme` tipindeki soruları YENİ NESİL yaz: 2-4 cümlelik GERÇEK YAŞAM SENARYOSU/bağlam (alışveriş, spor, tarif, yolculuk, okul, doğa, üretim vb.); öğrenci gerekli veriyi metinden/görselden KENDİSİ ayıklasın; mümkünse İŞE YARAMAYAN bir bilgi (çeldirici veri) ekle; çözüm ÇOK ADIMLI (en az 2 adım) olsun.
- `islem`, `salt_islem`, `kavram_sorusu` gibi tipler KISA ve doğrudan kalabilir (hızlı pratik) — hepsini senaryoya çevirme.
- `gorsel_geometri`, `grafik_okuma`, `tablo_sorusu`, `oruntu_sekil` (ŞEKİLLİ) tiplerinde şekli/tabloyu/grafiği MUTLAKA gerçek yaşam bağlamına yerleştir: çıplak "aşağıdaki şekilde..." DEĞİL; örn. bir bahçenin krokisi, bir mağazanın aylık satış grafiği, bir tarifin malzeme tablosu, bir parkın oturma düzeni. ŞEKİL + SENARYO birlikte olsun (şekilli bağlamsal soru).
- ⚠️ KRİTİK: Şekilli tipte şekli GERÇEKTEN ÜRET — hepsi DİREKTİFLE, ASLA ham `<svg>` YAZMA: `gorsel_geometri` → `{{geo:...}}` direktifi (dik üçgen/üçgen/dikdörtgen/kare/çember), `grafik_okuma` → `{{chart:...}}` direktifi, `oruntu_sekil` → `{{pattern:...}}` direktifi OLMAK ZORUNDA. Ölçüler/veriler direktifte/metinde görünmeli. "Görseldeki ölçüye göre" deyip direktif ÜRETMEMEK KESİNLİKLE YASAK (cevaplanamaz soru olur). Şekli direktifle üretemeyeceksen o soruyu bağlamsal SÖZEL soru (`gunluk_hayat`/`sozel_problem`) olarak yaz ve tüm ölçüleri metinde ver.
- `coktan_secmeli` tiplerinde çeldiriciler yaygın HATA TİPLERİNDEN doğsun (işlem sırası, birim karışması, eksik adım, sık kavram yanılgısı) — rastgele yakın sayı DEĞİL.
- Bağlam gerçekçi ve tutarlı olsun (fiyat, ölçü, miktar makul; birimler doğru). Aritmetik zorluğu yine "Zorluk Kalibrasyonu" belirler."""


def build_user_prompt(
    grade: int,
    topic_name: str,
    kazanimlar: list[Kazanim],
    difficulty: Difficulty,
    question_count: int,
    distribution: dict[QuestionType, int],
    few_shot_examples: list[dict],
    context_exclusions: list[str] | None = None,
    few_shot_source: str = "static",
    textbook_chunks: list[dict] | None = None,
    yeni_nesil: bool = False,
    yeni_nesil_block: str | None = None,
    generic_difficulty_hints: dict[str, str] | None = None,
) -> str:
    # Ders-özel yeni nesil bloğu (default: matematik). Fen kendi bloğunu geçer.
    _block = yeni_nesil_block or _YENI_NESIL_BLOCK
    parts = [
        f"Sınıf: {grade}. sınıf",
        f"Konu: {topic_name}",
        _format_kazanim_block(kazanimlar, difficulty, generic_difficulty_hints),
        f"Zorluk: {difficulty.value}",
        f"Üretilecek Soru Sayısı: {question_count}",
        "",
        _block if yeni_nesil else None,
        "" if yeni_nesil else None,
        _format_distribution(distribution),
        _format_few_shot(few_shot_examples, difficulty, source=few_shot_source),
        _format_textbook_context(textbook_chunks or []),
        _format_exclusions(context_exclusions or []),
        "",
        f"Yukarıdaki kriterlere göre tam {question_count} adet soru üret. "
        "Her sorunun kazanım koduyla ve soru tipiyle etiketli olduğundan emin ol. "
        "Sorular yukarıdaki Zorluk Kalibrasyonuna UYMALIDIR.",
        # NOT (2026-07-26): sınav modunda (include_solutions=False) çözümleri
        # kısaltma denendi ve GERİ ALINDI. Ölçüm: çözüm adımları çıktı
        # maliyetinin ~%28'i (84 token/soru), kısaltma bunun %29'unu kesiyor
        # → kağıt maliyetinin ~%8'i, ki bu koşu-arası varyansın (±%15) ALTINDA.
        # Karşılığında cache/havuz anahtarı ikiye bölünüyordu (ödevler daima
        # include_solutions=False gönderir) → yeniden kullanım kaybı kazançtan
        # büyük. Bkz. docs/COST_REDUCTION_PLAN.md §3.5.
        # Açılış/kalıp çeşitliliği — few-shot örneklerin çoğu "Bir ..." ile başlar;
        # model bunu taklit edip tüm seti monotonlaştırıyor. Sayısal tavan + salient
        # konum (final talimat) ile bu anchor'ı kır (bkz. sistem kuralı 12).
        (
            f"ÇEŞİTLİLİK (ZORUNLU): Bu {question_count} sorunun cümle AÇILIŞLARINI "
            "birbirinden FARKLI kur. Örnek sorular 'Bir ...' ile başlasa bile SEN taklit etme; "
            f"bu sette EN FAZLA {max(1, round(question_count / 3))} soru 'Bir' ile başlayabilir. "
            "Kalanları farklı iskeletle aç: doğrudan soruyla, birinci/ikinci kişi ('Elimde ... var'), "
            "isim/diyalogla ('Ayşe ... dedi'), zaman/durum kurgusuyla ('Hafta sonu ...'), "
            "veri/tabloyla. Farklı isim seçmek YETMEZ; cümle iskeletini değiştir."
        ),
    ]
    return "\n".join(p for p in parts if p is not None)
