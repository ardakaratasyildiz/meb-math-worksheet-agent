import Link from "next/link";
import { ArrowRight, ListChecks } from "lucide-react";

import { Button } from "@/components/ui/button";
import sampleData from "@/lib/sample-questions.json";

/**
 * Login'siz ÖRNEK SORU önizlemesi (server component).
 *
 * Landing page'ler build-time statik render edildiği için örnekler de statik
 * veriden gelir (scripts/gen_samples.py üretir, commit edilir). Gerçek soru
 * metni server-render edilen HTML'de bulunur → Googlebot boş kabuk yerine
 * içerik indeksler (bounce ↓, dönüşüm ↑). Cevaplar <details> ile açılır —
 * client JS gerektirmez ve içerik yine indekslenebilir.
 *
 * Slug için örnek yoksa (henüz üretilmemiş yeni konu) sessizce gizlenir.
 */
interface SampleQuestion {
  question: string;
  answer: string;
  question_type: string;
  kazanim_kod: string;
}
interface SampleEntry {
  grade: number;
  topic_id: string;
  difficulty: string;
  questions: SampleQuestion[];
}

const DATA = sampleData as unknown as Record<string, SampleEntry>;

export function SampleQuestions({
  slug,
  grade,
  topicId,
  topicName,
}: {
  slug: string;
  grade: number;
  topicId: string;
  topicName: string;
}) {
  const entry = DATA[slug];
  if (!entry || !entry.questions?.length) return null;

  // Önizleme temizliği: LaTeX ($, \) içeren veya aşırı uzun (görsel/tablo)
  // soruları ele — düz-metin, kısa, indekslenebilir örnekler kalsın. En çok 3.
  const questions = entry.questions
    .filter((q) => !/[$\\]/.test(q.question) && q.question.length <= 400)
    .slice(0, 3);
  if (!questions.length) return null;

  const generateHref = `/generate?grade=${grade}&topic=${topicId}`;

  return (
    <section className="py-16">
      <div className="container max-w-3xl">
        <div className="mb-6 flex items-center gap-2">
          <ListChecks className="h-5 w-5 text-primary" />
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Örnek sorular
          </h2>
        </div>
        <p className="mb-8 text-muted-foreground">
          {grade}. sınıf {topicName.toLowerCase()} konusundan örnek sorular —
          sistemin ürettiği sorulardan bir kesit. Kendi çalışma kağıdını
          üretmek için soru sayısını, zorluğu ve tipi sen seçersin.
        </p>

        <ol className="space-y-4">
          {questions.map((q, i) => (
            <li key={i} className="rounded-lg border bg-card p-5">
              <p className="font-medium leading-relaxed text-foreground">
                <span className="mr-2 text-primary">{i + 1}.</span>
                {q.question}
              </p>
              <details className="mt-3 group">
                <summary className="cursor-pointer list-none text-sm font-medium text-primary hover:underline">
                  Cevabı göster
                </summary>
                <p className="mt-2 rounded-md bg-accent/40 p-3 text-sm text-foreground">
                  {q.answer}
                </p>
              </details>
            </li>
          ))}
        </ol>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Button asChild size="lg" className="gap-2">
            <Link href={generateHref}>
              Bunun gibi kağıt üret <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <span className="text-sm text-muted-foreground">
            Hesap açmak için yalnızca e-posta yeterli.
          </span>
        </div>
      </div>
    </section>
  );
}
