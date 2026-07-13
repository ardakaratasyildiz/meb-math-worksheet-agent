/**
 * Ana sayfa "ders vitrini" (sekmeli showroom) için ders başına TEMSİLÎ örnek sorular.
 *
 * Neden statik: ana sayfa hızlı ve backend cold-start'a bağımsız açılmalı; örnek
 * sorular pazarlama içeriği (üretim hattının GERÇEK çıktısını temsil eden, MEB
 * kazanımına hizalı, elle doğrulanmış küçük bir kesit). Ders başına birden çok örnek
 * → vitrinde "başka örnek" ile çeşitlilik. Matematik zaten lib/sample-questions.json'dan
 * geniş havuz gösterir; bu dosya vitrindeki ders-bazlı sekmeler içindir.
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

export const SUBJECT_SHOWCASE: Record<Subject, ShowcaseQ[]> = {
  matematik: [
    {
      gradeLabel: "8. sınıf · LGS",
      topic: "Cebirsel İfadeler",
      kazanim: "M.8.2.1",
      question:
        "Bir kenar uzunluğu (x + 3) cm olan bir karenin çevresi 32 cm olduğuna göre x kaçtır?",
      options: ["A) 3", "B) 5", "C) 7", "D) 9"],
      answer: "B) 5",
    },
    {
      gradeLabel: "5. sınıf",
      topic: "Doğal Sayılar",
      kazanim: "M.5.1.1",
      question:
        "324.067 sayısının binler bölüğündeki rakamların basamak değerleri toplamı kaçtır?",
      options: ["A) 24.000", "B) 4.000", "C) 24.067", "D) 320.000"],
      answer: "A) 24.000",
    },
    {
      gradeLabel: "7. sınıf",
      topic: "Oran ve Orantı",
      kazanim: "M.7.1.3",
      question:
        "Bir haritada 2 cm, gerçekte 50 km'yi gösteriyorsa; haritadaki 6 cm gerçekte kaç km'dir?",
      options: ["A) 100 km", "B) 120 km", "C) 150 km", "D) 300 km"],
      answer: "C) 150 km",
    },
  ],
  fen: [
    {
      gradeLabel: "6. sınıf",
      topic: "Güneş, Dünya ve Ay",
      kazanim: "F.6.1.2",
      question:
        "Ay’ın Dünya etrafındaki dolanımı sırasında Dünya’dan görünen aydınlık yüzünün düzenli olarak değişmesine ne ad verilir?",
      options: ["A) Güneş tutulması", "B) Ay’ın evreleri", "C) Mevsimler", "D) Gel-git"],
      answer: "B) Ay’ın evreleri",
    },
    {
      gradeLabel: "6. sınıf",
      topic: "Hücre",
      kazanim: "F.6.1.1",
      question: "Hücre duvarı aşağıdaki hücrelerden hangisinde BULUNMAZ?",
      options: ["A) Bitki hücresi", "B) Bakteri hücresi", "C) Mantar hücresi", "D) Hayvan hücresi"],
      answer: "D) Hayvan hücresi",
    },
    {
      gradeLabel: "8. sınıf · LGS",
      topic: "Madde ve Endüstri",
      kazanim: "F.8.4.2",
      question:
        "Aşağıdaki olaylardan hangisi kimyasal değişime örnektir?",
      options: [
        "A) Buzun erimesi",
        "B) Şekerin suda çözünmesi",
        "C) Demirin paslanması",
        "D) Camın kırılması",
      ],
      answer: "C) Demirin paslanması",
    },
  ],
  turkce: [
    {
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
    {
      gradeLabel: "6. sınıf",
      topic: "Sözcükte Anlam",
      kazanim: "T.6.3.5",
      question:
        "“Sınıfın en çalışkan öğrencisi olarak herkese örnek oluyordu.” cümlesindeki “örnek olmak” sözü aşağıdakilerden hangisiyle açıklanır?",
      options: [
        "A) Kopya vermek",
        "B) Model/rehber davranış sergilemek",
        "C) Yardım istemek",
        "D) Ödül kazanmak",
      ],
      answer: "B) Model/rehber davranış sergilemek",
    },
    {
      gradeLabel: "8. sınıf · LGS",
      topic: "Cümlenin Ögeleri",
      kazanim: "T.8.3.4",
      question:
        "“Öğretmen, sınavdan sonra ödevleri dikkatlice inceledi.” cümlesinin öznesi hangisidir?",
      options: ["A) Öğretmen", "B) Ödevleri", "C) Dikkatlice", "D) Sınavdan sonra"],
      answer: "A) Öğretmen",
    },
  ],
  sosyal: [
    {
      gradeLabel: "8. sınıf · İnkılap",
      topic: "Bir Kahraman Doğuyor",
      kazanim: "SB.8.2.1",
      question:
        "Osmanlı Devleti’ni I. Dünya Savaşı’ndan fiilen çekilmek zorunda bırakan Mondros Ateşkes Antlaşması hangi tarihte imzalanmıştır?",
      options: ["A) 30 Ekim 1918", "B) 22 Haziran 1919", "C) 23 Nisan 1920", "D) 24 Temmuz 1923"],
      answer: "A) 30 Ekim 1918",
    },
    {
      gradeLabel: "8. sınıf · İnkılap",
      topic: "Millî Bir Destan",
      kazanim: "SB.8.3.2",
      question: "Türkiye Büyük Millet Meclisi (TBMM) hangi tarihte açılmıştır?",
      options: ["A) 19 Mayıs 1919", "B) 23 Nisan 1920", "C) 29 Ekim 1923", "D) 30 Ağustos 1922"],
      answer: "B) 23 Nisan 1920",
    },
    {
      gradeLabel: "6. sınıf",
      topic: "Yeryüzünde Yaşam",
      kazanim: "SB.6.3.1",
      question:
        "Bir yerin ekvatora olan uzaklığı arttıkça, o yerin yıllık ortalama sıcaklığı genellikle nasıl değişir?",
      options: ["A) Artar", "B) Azalır", "C) Değişmez", "D) Önce artar sonra azalır"],
      answer: "B) Azalır",
    },
  ],
  ingilizce: [
    {
      gradeLabel: "5. sınıf",
      topic: "Daily Routines",
      kazanim: "E5.3",
      question:
        "Choose the correct option: “My sister ___ to school at 8 o’clock every morning.”",
      options: ["A) go", "B) goes", "C) going", "D) is go"],
      answer: "B) goes",
    },
    {
      gradeLabel: "7. sınıf",
      topic: "Present Continuous",
      kazanim: "E7.2",
      question: "Choose the correct option: “Look! The children ___ football in the garden.”",
      options: ["A) play", "B) plays", "C) are playing", "D) played"],
      answer: "C) are playing",
    },
    {
      gradeLabel: "8. sınıf · LGS",
      topic: "Friendship",
      kazanim: "E8.1",
      question:
        "Choose the option that best completes the sentence: “A good friend is someone you can ___ with your secrets.”",
      options: ["A) trust", "B) borrow", "C) refuse", "D) argue"],
      answer: "A) trust",
    },
  ],
};
