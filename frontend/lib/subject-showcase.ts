/**
 * Ana sayfa "ders vitrini" (sekmeli showroom) için ders başına temsilî örnek soru.
 *
 * Neden statik: ana sayfa hızlı ve backend cold-start'a bağımsız açılmalı; örnek
 * sorular pazarlama içeriği (üretim hattının GERÇEK çıktısını temsil eden, MEB
 * kazanımına hizalı, elle doğrulanmış küçük bir kesit). Canlıya ders açıldıkça
 * buradaki örnekleri pipeline çıktısıyla tazeleyebiliriz. Matematik zaten
 * lib/sample-questions.json'dan geniş havuz gösterir; bu dosya vitrindeki
 * ders-bazlı sekmeler içindir.
 */
import type { Subject } from "./types";

export interface ShowcaseQ {
  gradeLabel: string; // "8. sınıf · LGS"
  topic: string; // ünite / tema
  kazanim: string; // kazanım kodu (izlenebilirlik)
  question: string;
  options?: string[]; // çoktan seçmeli şıklar (varsa)
  answer: string; // doğru cevap (kısa)
}

export const SUBJECT_SHOWCASE: Record<Subject, ShowcaseQ> = {
  matematik: {
    gradeLabel: "8. sınıf · LGS",
    topic: "Cebirsel İfadeler",
    kazanim: "M.8.2.1",
    question:
      "Bir kenar uzunluğu (x + 3) cm olan bir karenin çevresi 32 cm olduğuna göre x kaçtır?",
    options: ["A) 3", "B) 5", "C) 7", "D) 9"],
    answer: "B) 5",
  },
  fen: {
    gradeLabel: "6. sınıf",
    topic: "Güneş, Dünya ve Ay",
    kazanim: "F.6.1.2",
    question:
      "Ay’ın Dünya etrafındaki dolanımı sırasında Dünya’dan görünen aydınlık yüzünün düzenli olarak değişmesine ne ad verilir?",
    options: ["A) Güneş tutulması", "B) Ay’ın evreleri", "C) Mevsimler", "D) Gel-git"],
    answer: "B) Ay’ın evreleri",
  },
  turkce: {
    gradeLabel: "7. sınıf",
    topic: "Yazım ve Noktalama",
    kazanim: "T.7.4.2",
    question: "Aşağıdaki cümlelerin hangisinde yazım yanlışı vardır?",
    options: [
      "A) Yarın erkenden yola çıkacağız.",
      "B) Herşey yolunda gidiyor.",
      "C) Kitabı masanın üstüne bıraktı.",
      "D) Bugün hava çok güzel.",
    ],
    answer: "B) Herşey yolunda gidiyor. (Doğrusu: “Her şey”)",
  },
  sosyal: {
    gradeLabel: "8. sınıf · İnkılap",
    topic: "Bir Kahraman Doğuyor",
    kazanim: "SB.8.2.1",
    question:
      "Osmanlı Devleti’ni I. Dünya Savaşı’ndan fiilen çekilmek zorunda bırakan Mondros Ateşkes Antlaşması hangi tarihte imzalanmıştır?",
    options: ["A) 30 Ekim 1918", "B) 22 Haziran 1919", "C) 23 Nisan 1920", "D) 24 Temmuz 1923"],
    answer: "A) 30 Ekim 1918",
  },
  ingilizce: {
    gradeLabel: "5. sınıf",
    topic: "Daily Routines",
    kazanim: "E5.3",
    question:
      "Choose the correct option: “My sister ___ to school at 8 o’clock every morning.”",
    options: ["A) go", "B) goes", "C) going", "D) is go"],
    answer: "B) goes",
  },
};
