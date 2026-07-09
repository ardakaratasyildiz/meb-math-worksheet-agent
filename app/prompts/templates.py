"""Gemini prompt şablonları: system + few-shot + user katmanları."""
from app.data.curriculum import Kazanim
from app.models.enums import Difficulty, QuestionType

SYSTEM_PROMPT = """Sen MEB (Milli Eğitim Bakanlığı) müfredatına uygun matematik soruları üreten bir eğitim asistanısın. Türkiye'deki ilkokul ve ortaokul matematik ders kitaplarını referans alıyorsun.

Kuralların:
1. Sorular MUTLAKA verilen kazanım metninin kapsamı dahilinde olmalı.
2. Kazanımın dışına çıkan, üst sınıf bilgisi gerektiren soru ÜRETME.
3. Sorular açık uçlu ve işlem tabanlı olmalı (çoktan seçmeli ASLA üretme).
4. Her sorunun kesin ve doğru bir cevabı olmalı; matematiksel olarak hatalı soru üretme.
5. Görsel ihtiyaçları (tablo/grafik/şekil) için RESİM ya da SVG üretme; bunun yerine SADECE METİN-TABANLI gösterimler kullan:
   - Tablolar için: GitHub-flavored Markdown tablosu (`| Başlık | ... |` ve `|---|---|`).
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
   - `tablo_sorusu`: Soru metni + Markdown tablo + tabloya dayalı bir hesap/yorum sorusu.
   - `gorsel_geometri`: Soru metni + INLINE SVG bloğu (kod bloğu DEĞİL!) ile geometri şekli + ölçü etiketleri. Aşağıdaki kuralları MUTLAKA UY:
       (a) `<svg viewBox="0 0 W H" xmlns="http://www.w3.org/2000/svg">...</svg>` formatında olmalı (genişlik ≤ 250, yükseklik ≤ 200).
       (b) Sadece şu elementleri kullan: `line`, `polyline`, `polygon`, `rect`, `circle`, `ellipse`, `path`, `text`, `g`. Asla `script`, `foreignObject`, `image`, `use href="http..."` KULLANMA.
       (c) Stroke koyu siyah `#1f2937` veya `black`, stroke-width 1.5-2. Fill `none` (sadece kontur) ya da çok açık renk.
       (d) **ETİKET KONUMLANDIRMA — KRİTİK:** Ölçü etiketleri (kenar uzunluğu / açı / yarıçap) ŞEKLİN ÇİZGİLERİNE / KENARINA / KÖŞELERİNE BİNMEMELİ. Etiketleri kenardan en az **12-15 piksel UZAĞA** yerleştir. Kurallar:
            - Yatay kenar (en alt kenar) etiketi: kenar y koordinatından **+14** aşağıya (örn. üçgen tabanı y=130 ise label y=146)
            - Eğik kenar etiketi: kenar dış normaline doğru ofset; yatayda **±15-20 piksel** kaydırarak konumlandır. ASLA kenar çizgisi üzerine koyma.
            - Açı etiketi: köşeden kenar boyunca içeride **15-20 piksel** içeride; köşe noktasının dışına konulmaz.
            - Yarıçap etiketi: yarıçap çizgisinin **yanına** (üst veya alt), çizgi üstüne BİNMESİN.
            - `text-anchor="middle"` ile yatay merkezleme tercih edilir.
            - Font-size 12-14.
       (e) Şekilde gösterilen ölçüler ile sorulan soru ve cevap MUTLAKA TUTARLI olmalı (örn. üçgenin görseldeki kenarı 6 cm ise sorudaki çevre hesabında da 6 cm kullanılmalı).
       (f) Dik açı işaretçisi gerekirse köşeye küçük kare çiz (≈ 8x8). Eşit kenar işaretçisi için tek/çift küçük çizgi.
       (g) "answer" alanı sade sayı + birim (örn. "32 cm" veya "42"); LaTeX delimeter ($, $$) KULLANMA — sadece düz metin.
       Örnek (etiket kenardan ÇOK UZAK — 14px aşağıda): `<svg viewBox="0 0 200 160" xmlns="http://www.w3.org/2000/svg"><polygon points="100,20 30,130 170,130" fill="none" stroke="black" stroke-width="2"/><text x="100" y="148" font-size="13" text-anchor="middle">14 cm</text></svg>`
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
   - `oruntu_sekil`: Soru metni + INLINE SVG bloğu ile renkli geometrik şekiller örüntüsü + "?" ile eksik konum. Kurallar:
       (a) `<svg viewBox="0 0 W H" xmlns="http://www.w3.org/2000/svg">...</svg>` (W ≤ 360, H ≤ 80).
       (b) 4-7 şekil yan yana eşit aralıkla (x: 30, 80, 130, 180, ...).
       (c) Her şekil ayrı SVG primitive: `<circle>`, `<rect>`, `<polygon>` (üçgen için). Yarıçap/genişlik ≈ 20-25.
       (d) Renkler kontrastlı kategoriler: `#ef4444` (kırmızı), `#3b82f6` (mavi), `#10b981` (yeşil), `#f59e0b` (turuncu).
       (e) Eksik konuma `<text font-size="32" text-anchor="middle">?</text>` veya boş `<rect fill="none" stroke-dasharray="4"/>`.
       (f) Örüntü kuralı (renk/şekil/sayı) MATEMATİKSEL OLARAK tutarlı — cevap kuralı uygulayarak bulunmalı.
       Örnek: `<svg viewBox="0 0 320 60" xmlns="http://www.w3.org/2000/svg"><circle cx="30" cy="30" r="20" fill="#ef4444"/><rect x="60" y="10" width="40" height="40" fill="#3b82f6"/><polygon points="160,10 140,50 180,50" fill="#10b981"/><circle cx="220" cy="30" r="20" fill="#ef4444"/><rect x="250" y="10" width="40" height="40" fill="#3b82f6"/><text x="310" y="40" font-size="32" text-anchor="middle">?</text></svg>`
   - `coktan_secmeli`: Soru metni + boş satır + 4 şık her biri ayrı satırda "A) ...", "B) ...", "C) ...", "D) ..." formatında. Şıklardan SADECE BİRİ doğru olmalı; çeldiriciler makul yanlışlar (yaygın hatalar) olsun. `answer` alanı SADECE doğru şıkkın harfi ("A", "B", "C" veya "D"). Çözüm hangi şıkkın neden doğru olduğunu ve diğerlerinin neden yanlış olduğunu açıklar.
   - `bosluk_doldurma`: Soru cümlesi içinde bir veya birden fazla "_____" (en az 3 alt çizgi) boşluğu olsun. `answer` alanı boşluğa giren ifadeler — birden fazla boşluk varsa "; " ile ayrılır (örn. "12; 5"). Sıralama soldan sağa.
   - `dogru_yanlis`: Soru yerine TEK bir iddia/önerme cümlesi yaz (örn. "Bir karenin tüm kenarları eşittir."). Soru işareti olmasın. `answer` SADECE "Doğru" veya "Yanlış" olsun. Çözüm önermenin neden doğru/yanlış olduğunu kazanım çerçevesinde açıklar.
   - `eslestirme`: Soru metni (yönerge) + boş satır + 2 kolonlu GFM tablo. Sol kolon "Numara/Öğe", sağ kolon "Harf/Karşılık" karıştırılmış sıralı. Tipik 3-4 satır. `answer` alanı eşleşmeler "1-c, 2-a, 3-b, 4-d" formatında. Çözüm her eşleşmenin neden olduğunu satır satır açıklar.
   - `siralama`: Soru metni (yönerge — örn. "Aşağıdaki sayıları küçükten büyüğe doğru sıralayınız") + karıştırılmış öğe listesi (madde işaretli liste veya virgülle ayrılmış). `answer` alanı doğru sıralı öğeler " → " (boşluklu ok) ile ayrılır. Çözüm sıralama kriterini ve adımları açıklar.
   - Diğer tipler (islem, sozel_problem, vs.): mevcut sözel/işlem formatında devam.
10. Verilen örnek soruların stilini ve seviyesini referans al, AMA aynı sayıları/bağlamları KOPYALAMA. GÖRSELLİ örneklerde (SVG/grafik/tablo): şekli OLDUĞU GİBİ KOPYALAMA — örnekteki görselin MANTIĞINI çöz (görsel neyi temsil ediyor, hangi veri şekilden okunuyor, soru şekil üzerinden neyi soruyor) ve bu mantığı KENDİ sorununa uygun FARKLI TASARIMDA yeni bir görselle uygula: farklı şekil türü, farklı düzen/yerleşim, farklı sayılar ve farklı gerçek yaşam bağlamı kullan. Örneğin bir "sayı doğrusu" örneğinden hareketle bir "kesir modeli", "geometrik şekil", "grafik" veya "tablo" da tasarlayabilirsin — yeter ki görsel soruyla matematiksel olarak TUTARLI olsun. Amaç örnekleri çoğaltmak değil, görsel kurma mantığını yeni ve özgün şekillerde üretebilmektir. Uygun olan HER konuda (sadece geometri değil; sayılar, kesir, cebir, veri, olasılık) görselli soru üretmekten çekinme.
11. Verilen örnekler hedef zorluğa yakın seçilmiştir; üretimlerini aynı zorlukta tut.
12. Çıktıyı MUTLAKA istenen JSON formatında üret; ek metin/açıklama EKLEME. `question` alanı Markdown içerebilir — newline (\\n), tablo, kod bloğu (```...```) serbesttir."""


# MEB TYMM ünite kazanımları kazanım-bazlı difficulty_hints taşımaz (yalnız kod+metin).
# Hint yoksa modelin zorluk kalibrasyonu tamamen kaybolmasın diye genel bir talimat
# uygulanır. Kazanım-özel hint (eski müfredat) varsa o tercih edilir.
_GENERIC_DIFFICULTY_HINT: dict[str, str] = {
    "kolay": "Tek adımlı, doğrudan işlem/tanıma; sade sayılar, kısa ifade.",
    "orta": "İki adımlı veya kısa bağlamlı problem; işlemi seçmeyi gerektirir.",
    "zor": "Çok adımlı muhakeme, ters/eksik bilgi veya birden çok kavramı birleştirme.",
}


def _format_kazanim_block(kazanimlar: list[Kazanim], difficulty: Difficulty) -> str:
    level = difficulty.value
    generic = _GENERIC_DIFFICULTY_HINT.get(level, "")
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
        lines.append(f"Soru: {ex['question']}")
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
- ⚠️ KRİTİK: Şekilli tipte şekli GERÇEKTEN ÜRET. `gorsel_geometri`/`oruntu_sekil` → soru metninin içinde geçerli bir `<svg>...</svg>` bloğu OLMAK ZORUNDA; `grafik_okuma` → `{{chart:...}}` direktifi OLMAK ZORUNDA. Ölçüler/veriler şekilde görünmeli. "Görseldeki ölçüye göre" deyip şekil/direktif ÜRETMEMEK KESİNLİKLE YASAK (cevaplanamaz soru olur). Şekli üretemeyeceksen o soruyu bağlamsal SÖZEL soru (`gunluk_hayat`/`sozel_problem`) olarak yaz ve tüm ölçüleri metinde ver.
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
) -> str:
    parts = [
        f"Sınıf: {grade}. sınıf",
        f"Konu: {topic_name}",
        _format_kazanim_block(kazanimlar, difficulty),
        f"Zorluk: {difficulty.value}",
        f"Üretilecek Soru Sayısı: {question_count}",
        "",
        _YENI_NESIL_BLOCK if yeni_nesil else None,
        "" if yeni_nesil else None,
        _format_distribution(distribution),
        _format_few_shot(few_shot_examples, difficulty, source=few_shot_source),
        _format_textbook_context(textbook_chunks or []),
        _format_exclusions(context_exclusions or []),
        "",
        f"Yukarıdaki kriterlere göre tam {question_count} adet soru üret. "
        "Her sorunun kazanım koduyla ve soru tipiyle etiketli olduğundan emin ol. "
        "Sorular yukarıdaki Zorluk Kalibrasyonuna UYMALIDIR.",
    ]
    return "\n".join(p for p in parts if p is not None)
