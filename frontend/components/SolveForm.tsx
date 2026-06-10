"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";

import { createQuiz } from "@/lib/api";
import {
  getGradesLocal,
  getKazanimlarLocal,
  getTopicsLocal,
} from "@/lib/curriculum";
import type {
  Difficulty,
  GradeInfo,
  KazanimInfo,
  TopicInfo,
} from "@/lib/types";

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: "kolay", label: "Kolay" },
  { value: "orta", label: "Orta" },
  { value: "zor", label: "Zor" },
];

const KAZANIM_AUTO = "__AUTO__";

// Çözülebilir quiz üretim formu — /generate'in sade kardeşi. PDF/markalama/
// gelişmiş ayar YOK; çıktı PDF değil, çözülecek quiz. Dropdownlar lokal müfredat
// snapshot'ından anında dolar (backend cold-start'a bağımlı değil).
export function SolveForm() {
  const router = useRouter();
  const { userId } = useAuth();
  // "Bu kazanımda pratik yap" derin-linki: /coz/yeni?grade=&topic=&kazanim=
  const searchParams = useSearchParams();
  const initialGrade = Number(searchParams.get("grade")) || 5;
  const initialTopic = searchParams.get("topic") ?? "";
  const initialKazanim = searchParams.get("kazanim");

  const [grade, setGrade] = React.useState(initialGrade);
  const [topicId, setTopicId] = React.useState(initialTopic);
  const [kazanimKod, setKazanimKod] = React.useState<string | null>(
    initialKazanim,
  );
  const [difficulty, setDifficulty] = React.useState<Difficulty>("orta");
  const [questionCount, setQuestionCount] = React.useState(10);
  const [submitting, setSubmitting] = React.useState(false);

  const [grades] = React.useState<GradeInfo[]>(getGradesLocal);
  const [topics, setTopics] = React.useState<TopicInfo[]>(() =>
    getTopicsLocal(initialGrade),
  );
  const [kazanimlar, setKazanimlar] = React.useState<KazanimInfo[]>([]);

  React.useEffect(() => {
    setTopics(getTopicsLocal(grade));
  }, [grade]);

  React.useEffect(() => {
    setKazanimlar(topicId ? getKazanimlarLocal(grade, topicId) : []);
  }, [grade, topicId]);

  async function onStart() {
    if (!topicId) {
      toast.error("Konu seçin", { description: "Quiz için bir konu seçmelisiniz." });
      return;
    }
    if (!userId) {
      toast.error("Oturum bilgisi henüz yüklenmedi", {
        description: "Birkaç saniye sonra tekrar deneyin.",
      });
      return;
    }
    setSubmitting(true);
    try {
      const quiz = await createQuiz({
        grade,
        topic_id: topicId,
        kazanim_kod: kazanimKod,
        difficulty,
        question_count: questionCount,
        tenant_id: userId,
      });
      router.push(`/coz/quiz/${quiz.id}`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Bilinmeyen hata";
      toast.error("Quiz üretilemedi", { description: msg });
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="s-grade">Sınıf</Label>
          <Select
            value={String(grade)}
            onValueChange={(v) => {
              setGrade(Number(v));
              setTopicId("");
              setKazanimKod(null);
            }}
          >
            <SelectTrigger id="s-grade">
              <SelectValue placeholder="Sınıf seçin" />
            </SelectTrigger>
            <SelectContent>
              {grades.map((g) => (
                <SelectItem key={g.id} value={String(g.id)}>
                  {g.name} · {g.level}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="s-topic">Konu</Label>
          <Select
            value={topicId}
            onValueChange={(v) => {
              setTopicId(v);
              setKazanimKod(null);
            }}
            disabled={topics.length === 0}
          >
            <SelectTrigger id="s-topic">
              <SelectValue placeholder="Konu seçin" />
            </SelectTrigger>
            <SelectContent>
              {topics.map((t) => (
                <SelectItem key={t.id} value={t.id}>
                  {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="s-kazanim">Kazanım kodu</Label>
          <Select
            value={kazanimKod ?? KAZANIM_AUTO}
            onValueChange={(v) =>
              setKazanimKod(v === KAZANIM_AUTO ? null : v)
            }
            disabled={kazanimlar.length === 0}
          >
            <SelectTrigger id="s-kazanim">
              <SelectValue placeholder="Kazanım seçin" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={KAZANIM_AUTO}>Tümü (otomatik)</SelectItem>
              {kazanimlar.map((k) => (
                <SelectItem key={k.kod} value={k.kod}>
                  <span className="font-mono text-xs text-primary">{k.kod}</span>{" "}
                  · {k.metin.slice(0, 40)}
                  {k.metin.length > 40 ? "…" : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-1.5">
          <Label>Zorluk</Label>
          <div className="grid grid-cols-3 gap-2">
            {DIFFICULTIES.map((d) => (
              <Button
                key={d.value}
                type="button"
                variant={difficulty === d.value ? "default" : "outline"}
                onClick={() => setDifficulty(d.value)}
                size="sm"
              >
                {d.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="s-count">Soru sayısı</Label>
            <span className="text-sm font-medium tabular-nums">
              {questionCount}
            </span>
          </div>
          <Slider
            id="s-count"
            min={1}
            max={20}
            step={1}
            value={[questionCount]}
            onValueChange={([v]) => setQuestionCount(v ?? 10)}
          />
        </div>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-[11px] text-muted-foreground">
          Çözülebilir tipler üretilir (çoktan seçmeli, doğru/yanlış, boşluk
          doldurma, işlem). Üretim ~30 saniye sürer.
        </p>
        <Button
          onClick={onStart}
          disabled={submitting || !topicId}
          size="lg"
          className="gap-2 sm:min-w-[200px]"
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Hazırlanıyor…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Quiz oluştur & çöz
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
