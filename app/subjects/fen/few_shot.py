"""Fen Bilimleri few-shot örnek havuzu — GERÇEK MEB LGS örnek soruları.

Kaynak: MEB ÖDSGM/EBA "8. Sınıf Fen Bilimleri Ünitelendirilmiş Örnek Sorular"
(knowledge_base/Fen/ornek_sorular/8.sinif/). Sorular metin çıkarımıyla alındı,
CEVAPLARI elle doğrulandı; çözümler burada elle yazıldı (kaynak çözüm içermiyor).
[[question-quality-fewshot-rootcause]]: matematik 1-7'nin sentetik few-shot
sorunundan kaçınmak için Fen few-shot'ı BAŞTAN gerçek sınav sorularına dayanır.

Yapı: matematik `EXAMPLES_BY_GRADE` deseni; sınıf → **kazanım kodu** → örnekler.
Kazanım etiketi ELLE yapıldı (EBA ünite no ≠ 2024 TYMM ünite no — crosswalk;
bkz. knowledge_base/Fen/SOURCES.md). Örnekler `coktan_secmeli` tipinde; şıklar
`question` metnine gömülü, `answer` = doğru şık harfi (matematik konvansiyonu).

⚠️ KAPSAM: Bu bir BAŞLANGIÇ ÇIPASIDIR — yalnız 8. sınıf, birkaç kazanım, yalnız
tam metin-tabanlı (görselsiz) sorular. Görselli sorular + 3-7. sınıf + tam kapsam,
ithal edilecek gerçek korpus çıkarımıyla (Faz 2-B; görsel gerektiren sorular için
vision) genişletilecek. Kalite kapısı (Faz 6) öncesi genişletme şart.

NOT: Henüz generation pipeline'ına BAĞLI DEĞİL (Faz 0b threading). Matematik
davranışı değişmez.
"""
from __future__ import annotations

from app.models.enums import QuestionType

_SRC = "MEB ÖDSGM/EBA 8. Sınıf Fen örnek soru"

# sınıf → kazanım kodu → örnek listesi
FEN_EXAMPLES: dict[int, dict[str, list[dict]]] = {
    8: {
        # ── Ünite 1: Mevsimler ve İklim — mevsim oluşumu (GÖRSELLİ/yeni nesil) ─
        # Dünya-Güneş diyagramı inline SVG olarak yeniden kuruldu (kaynak görselden).
        # ⚠️ Görselli few-shot: merge öncesi SVG render'ı gözle doğrulanmalı.
        "FB.8.1.1.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "zor",
                "source": _SRC + " (görselli/yeni nesil)",
                "question": (
                    "Aşağıdaki görselde 21 Haziran tarihinde Dünya’nın Güneş karşısındaki "
                    "durumu ile Kuzey yarım küredeki K ve Güney yarım küredeki G noktaları "
                    "gösterilmiştir.\n"
                    '<svg viewBox="0 0 340 200" xmlns="http://www.w3.org/2000/svg">'
                    '<circle cx="100" cy="100" r="55" fill="#cfe3f2" stroke="#1f2937" stroke-width="2"/>'
                    '<line x1="122" y1="50" x2="78" y2="150" stroke="#1f2937" stroke-width="1.2" stroke-dasharray="4 3"/>'
                    '<line x1="50" y1="78" x2="150" y2="72" stroke="#1f2937" stroke-width="1"/>'
                    '<line x1="46" y1="101" x2="154" y2="99" stroke="#1f2937" stroke-width="1"/>'
                    '<line x1="50" y1="124" x2="150" y2="128" stroke="#1f2937" stroke-width="1"/>'
                    '<text x="8" y="103" font-size="9">Ekvator</text>'
                    '<circle cx="112" cy="57" r="2.5" fill="#1f2937"/><text x="116" y="53" font-size="11">K</text>'
                    '<circle cx="88" cy="145" r="2.5" fill="#1f2937"/><text x="92" y="157" font-size="11">G</text>'
                    '<line x1="250" y1="58" x2="170" y2="58" stroke="#f59e0b" stroke-width="1.5"/>'
                    '<polygon points="168,58 175,54 175,62" fill="#f59e0b"/>'
                    '<line x1="250" y1="85" x2="170" y2="85" stroke="#f59e0b" stroke-width="1.5"/>'
                    '<polygon points="168,85 175,81 175,89" fill="#f59e0b"/>'
                    '<line x1="250" y1="112" x2="170" y2="112" stroke="#f59e0b" stroke-width="1.5"/>'
                    '<polygon points="168,112 175,108 175,116" fill="#f59e0b"/>'
                    '<line x1="250" y1="139" x2="170" y2="139" stroke="#f59e0b" stroke-width="1.5"/>'
                    '<polygon points="168,139 175,135 175,143" fill="#f59e0b"/>'
                    '<circle cx="292" cy="100" r="42" fill="#fde68a" stroke="#f59e0b" stroke-width="2"/>'
                    '<text x="292" y="104" font-size="12" text-anchor="middle">Güneş</text>'
                    "</svg>\n"
                    "Buna göre 21 Haziran’da;\n"
                    "I. Güney yarım kürede en uzun gece yaşanır.\n"
                    "II. Dünya üzerindeki tüm noktalarda gece-gündüz süreleri eşitlenir.\n"
                    "III. Kuzey yarım kürede sonbahar mevsimi sona erer, kış mevsimi başlar.\n"
                    "durumlarından hangileri yaşanır?\n\n"
                    "A) Yalnız I\nB) Yalnız II\nC) I ve III\nD) I, II ve III"
                ),
                "answer": "A",
                "solution": (
                    "21 Haziran’da Kuzey yarım küre Güneş’e dönüktür: kuzeyde yaz, en uzun "
                    "gündüz; güneyde kış, en uzun gece yaşanır → I doğru. Gece-gündüz süreleri "
                    "yalnızca ekinokslarda (21 Mart, 23 Eylül) tüm Dünya’da eşitlenir, 21 "
                    "Haziran’da değil → II yanlış. 21 Haziran kuzeyde YAZ başlangıcıdır, kış "
                    "değil → III yanlış. Doğru cevap A."
                ),
            },
        ],
        # ── Ünite 1: Mevsimler ve İklim — iklim/hava ayrımı, çıkarım ──────────
        "FB.8.1.2.1": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "“Karadeniz açıklarındaki kuru yük gemileri ve balıkçı tekneleri, "
                    "meteorolojinin şiddetli fırtına ve poyraz uyarısı ile İnebolu Limanı’na "
                    "sığındı. Balıkçılar, geçmiş yıllarda bu kadar kötü hava koşullarıyla "
                    "karşılaşmadıklarını, bu yıl şiddetli poyraz nedeniyle denize açılamadıklarını "
                    "belirttiler.”\n"
                    "Bu haber metnine göre hava durumu ile ilgili;\n"
                    "I. insanların yaşamsal faaliyetlerini etkilediği,\n"
                    "II. değişken olabileceği,\n"
                    "III. iklimin genel özellikleriyle ters düşmeyeceği\n"
                    "çıkarımlarından hangilerine ulaşılabilir?\n\n"
                    "A) I ve II\nB) I ve III\nC) II ve III\nD) I, II ve III"
                ),
                "answer": "A",
                "solution": (
                    "Metin, hava koşullarının balıkçıların denize açılmasını engellediğini "
                    "(I) ve bu yılki koşulların geçmiş yıllardan farklı/değişken olduğunu (II) "
                    "gösterir. Haber olağandışı bir hava olayını anlattığı için III (iklimle "
                    "ters düşmeme) desteklenmez. Doğru cevap A."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "“Hava durumu”, kısa zamanda dar bir alanda meydana gelen hava olayları; "
                    "“iklim” ise uzun zaman diliminde geniş bir alanda hava olaylarının ortalama "
                    "durumudur.\n"
                    "Buna göre aşağıdakilerden hangisi iklim şartlarına göre belirlenen insan "
                    "faaliyetlerine örnek OLAMAZ?\n\n"
                    "A) Çiftçilerin sonbahar ve ilkbahar donlarından etkilenmeyecek bitkileri ekmesi\n"
                    "B) Firmaların kışın ısıtma, yazın soğutma için enerji sistemleri kurması\n"
                    "C) Kar yağışının yıl boyu etkili olduğu bölgede evlerin çatısının dik yapılması\n"
                    "D) İnsanların yağışlı bir günde işe giderken yanına şemsiye alması"
                ),
                "answer": "D",
                "solution": (
                    "A, B ve C uzun süreli ortalama koşullara (iklim) göre alınan kararlardır. "
                    "D ise o günkü anlık hava durumuna verilen bir tepkidir, iklime göre değil. "
                    "Doğru cevap D."
                ),
            },
        ],
        # ── Ünite 3: Yaşamın Gizemi — kalıtım, tek karakter çaprazlaması ──────
        # (EBA'da eski müfredat "Ünite 2 / DNA ve Genetik Kod"; 2024 TYMM'de Ünite 3.)
        "FB.8.3.3.2": [
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "zor",
                "source": _SRC,
                "question": (
                    "Mendel, homozigot mor ve beyaz çiçekli bezelyeleri çaprazlamış; gelişen "
                    "yavru bezelyelerin TÜMÜNÜN mor çiçekli olduğunu gözlemlemiştir.\n"
                    "Buna göre bu bezelyeler ile ilgili;\n"
                    "I. Mor çiçek özelliği beyaz çiçek özelliğine baskındır.\n"
                    "II. Yavru bezelyelerin çiçek rengi bakımından genotipi heterozigottur.\n"
                    "III. Yavru bezelyeler kendi arasında çaprazlandığında beyaz çiçekli birey "
                    "oluşma ihtimali 3/4’tür.\n"
                    "yorumlarından hangileri YAPILAMAZ?\n\n"
                    "A) Yalnız I\nB) Yalnız III\nC) I ve II\nD) II ve III"
                ),
                "answer": "B",
                "solution": (
                    "Homozigot mor (MM) × beyaz (mm) → tüm yavrular Mm (heterozigot) ve mor: "
                    "bu I ve II'yi doğrular. Mm × Mm çaprazında beyaz (mm) oranı 1/4'tür, 3/4 "
                    "değil; dolayısıyla III yapılamaz. Doğru cevap B."
                ),
            },
            {
                "type": QuestionType.COKTAN_SECMELI,
                "difficulty": "orta",
                "source": _SRC,
                "question": (
                    "Bezelyelerde mor çiçeklilik baskın, beyaz çiçeklilik çekiniktir. Bir mor "
                    "çiçekli bezelye ile beyaz çiçekli bezelyenin çaprazlanması sonucu yavruların "
                    "bir kısmı beyaz çiçekli olmuştur.\n"
                    "Bu mor çiçekli bezelye, kendisiyle aynı genotipteki başka bir bezelye ile "
                    "çaprazlanırsa yeni kuşakta beyaz çiçekli birey oluşma olasılığı kaçtır?\n\n"
                    "A) %100\nB) %50\nC) %25\nD) %0"
                ),
                "answer": "C",
                "solution": (
                    "Beyaz (mm) yavru oluştuğu için mor ebeveyn çekinik alel taşır → genotipi "
                    "Mm'dir. Mm × Mm çaprazında yavruların 1/4'ü mm (beyaz) olur = %25. "
                    "Doğru cevap C."
                ),
            },
        ],
    },
}
