"""Gemini prompt şablonları: system + few-shot + user katmanları."""
from app.data.curriculum import Kazanim
from app.models.enums import Difficulty, QuestionType

SYSTEM_PROMPT = """Sen MEB (Milli Eğitim Bakanlığı) müfredatına uygun matematik soruları üreten bir eğitim asistanısın. Türkiye'deki ilkokul ve ortaokul matematik ders kitaplarını referans alıyorsun.

Kuralların:
1. Sorular MUTLAKA verilen kazanım metninin kapsamı dahilinde olmalı.
2. Kazanımın dışına çıkan, üst sınıf bilgisi gerektiren soru ÜRETME.
3. Sorular açık uçlu ve işlem tabanlı olmalı (çoktan seçmeli ASLA üretme).
4. Her sorunun kesin ve doğru bir cevabı olmalı; matematiksel olarak hatalı soru üretme.
5. Görsel/şekil/resim gerektiren sorular üretme; geometri sorularını sözel olarak ifade et (kenar uzunlukları, açı ölçüleri vb. metinde verilsin).
6. Zorluk seviyesi "Zorluk Kalibrasyonu" bölümünde somut olarak belirtilmiştir — sayısal aralık, adım sayısı ve bağlam karmaşıklığı bu kalibrasyona UYMALIDIR:
   - Kolay: tek adım, sınıf düzeyinin tabanında sayılar, bağlam yalın.
   - Orta: 2-3 adım, sınıf düzeyi sayılar, kısa günlük hayat bağlamı.
   - Zor: çok adımlı, sınıf üst sınırı sayılar, birden fazla kavram birleşik.
7. Soruları akıcı, sade ve doğru Türkçe ile, MEB ders kitabı tonunda yaz.
8. Her sorunun çözüm adımlarını mutlaka belirt.
9. İstenen soru tipi dağılımına TAM olarak uy.
10. Verilen örnek soruların stilini ve seviyesini referans al, AMA aynı sayıları/bağlamları KOPYALAMA.
11. Verilen örnekler hedef zorluğa yakın seçilmiştir; üretimlerini aynı zorlukta tut.
12. Çıktıyı MUTLAKA istenen JSON formatında üret; ek metin/açıklama EKLEME."""


def _format_kazanim_block(kazanimlar: list[Kazanim], difficulty: Difficulty) -> str:
    level = difficulty.value
    if len(kazanimlar) == 1:
        k = kazanimlar[0]
        hint = k.get("difficulty_hints", {}).get(level, "")
        lines = [
            f"Hedef Kazanım Kodu: {k['kod']}",
            f"Hedef Kazanım Metni: {k['metin']}",
        ]
        if hint:
            lines.append(f"Zorluk Kalibrasyonu ({level}): {hint}")
        return "\n".join(lines)
    lines = ["Hedef Kazanımlar (soruları bu kazanımlar arasında dengeli dağıt):"]
    for k in kazanimlar:
        hint = k.get("difficulty_hints", {}).get(level, "")
        lines.append(f"  - {k['kod']}: {k['metin']}")
        if hint:
            lines.append(f"      Zorluk Kalibrasyonu ({level}): {hint}")
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
) -> str:
    """Eksik kalan sorular için yeniden üretim prompt'u.

    Orijinal talimat + kazanım + zorluk kriterleri korunur; üstüne
    daha önce üretilmiş soruların metinleri 'tekrar etme' uyarısıyla eklenir.
    """
    already_block = "\n".join(
        f"  {i + 1}. {q}" for i, q in enumerate(already_generated_questions)
    )
    extension = (
        "\n\n─── YENİDEN ÜRETİM ───\n"
        "Aşağıdaki sorular daha önce üretildi. ASLA bu soruların aynısını, çok benzerini "
        "veya aynı sayıları/bağlamları kullanan başka bir versiyonunu üretme:\n"
        f"{already_block}\n\n"
        f"Yukarıdakilerden tamamen FARKLI, {missing_count} yeni soru üret. "
        "Önceki talimatlar (kazanım, zorluk, soru tipi dağılımı, JSON formatı) aynen geçerli."
    )
    return original_user_prompt + extension


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
) -> str:
    parts = [
        f"Sınıf: {grade}. sınıf",
        f"Konu: {topic_name}",
        _format_kazanim_block(kazanimlar, difficulty),
        f"Zorluk: {difficulty.value}",
        f"Üretilecek Soru Sayısı: {question_count}",
        "",
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
