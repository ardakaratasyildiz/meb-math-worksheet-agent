"use client";

import * as React from "react";
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

import {
  generateWorksheet,
  listGrades,
  listKazanimlar,
  listTopics,
} from "@/lib/api";
import { addHistory } from "@/lib/history";
import { useGenerateStore } from "@/lib/store";
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

export function GenerateForm() {
  const {
    grade,
    topicId,
    kazanimKod,
    difficulty,
    questionCount,
    status,
    setForm,
    startGenerate,
    setSuccess,
    setError,
  } = useGenerateStore();

  const [grades, setGrades] = React.useState<GradeInfo[]>([]);
  const [topics, setTopics] = React.useState<TopicInfo[]>([]);
  const [kazanimlar, setKazanimlar] = React.useState<KazanimInfo[]>([]);

  React.useEffect(() => {
    listGrades().then(setGrades).catch(() => setGrades([]));
  }, []);

  React.useEffect(() => {
    listTopics(grade).then(setTopics).catch(() => setTopics([]));
  }, [grade]);

  React.useEffect(() => {
    if (!topicId) return;
    listKazanimlar(grade, topicId)
      .then(setKazanimlar)
      .catch(() => setKazanimlar([]));
  }, [grade, topicId]);

  const isLoading = status === "loading";

  async function onGenerate() {
    startGenerate();
    try {
      const res = await generateWorksheet({
        grade,
        topic_id: topicId,
        kazanim_kod: kazanimKod || null,
        difficulty,
        question_count: questionCount,
      });
      setSuccess(res);
      addHistory(
        {
          grade,
          topic_id: topicId,
          kazanim_kod: kazanimKod,
          difficulty,
          question_count: questionCount,
        },
        res,
      );
      const trace = res.metadata.trace;
      if (trace?.cache_hit) {
        toast.success("Cache'ten anında geldi", {
          description: `${res.worksheet.questions.length} soru, 1 sn altında.`,
        });
      } else {
        toast.success("Çalışma kağıdı hazır", {
          description: `${res.worksheet.questions.length} soru üretildi.`,
        });
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Bilinmeyen hata";
      setError(msg);
      toast.error("Üretim başarısız", { description: msg });
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="grade">Sınıf</Label>
        <Select
          value={String(grade)}
          onValueChange={(v) =>
            setForm({ grade: Number(v), topicId: "", kazanimKod: null })
          }
        >
          <SelectTrigger id="grade">
            <SelectValue placeholder="Sınıf seç" />
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

      <div className="space-y-2">
        <Label htmlFor="topic">Konu</Label>
        <Select
          value={topicId}
          onValueChange={(v) => setForm({ topicId: v, kazanimKod: null })}
          disabled={topics.length === 0}
        >
          <SelectTrigger id="topic">
            <SelectValue placeholder="Konu seç" />
          </SelectTrigger>
          <SelectContent>
            {topics.map((t) => (
              <SelectItem key={t.id} value={t.id}>
                {t.name}{" "}
                <span className="text-xs text-muted-foreground">
                  · {t.kazanim_count} kazanım
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="kazanim">Kazanım</Label>
        <Select
          value={kazanimKod ?? KAZANIM_AUTO}
          onValueChange={(v) =>
            setForm({ kazanimKod: v === KAZANIM_AUTO ? null : v })
          }
          disabled={kazanimlar.length === 0}
        >
          <SelectTrigger id="kazanim">
            <SelectValue placeholder="Kazanım seç" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={KAZANIM_AUTO}>
              Otomatik (tüm kazanımlar)
            </SelectItem>
            {kazanimlar.map((k) => (
              <SelectItem key={k.kod} value={k.kod}>
                <span className="font-mono text-xs text-primary">{k.kod}</span>{" "}
                · {k.metin.slice(0, 60)}
                {k.metin.length > 60 ? "…" : ""}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Zorluk</Label>
        <div className="grid grid-cols-3 gap-2">
          {DIFFICULTIES.map((d) => (
            <Button
              key={d.value}
              type="button"
              variant={difficulty === d.value ? "default" : "outline"}
              onClick={() => setForm({ difficulty: d.value })}
            >
              {d.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="qcount">Soru sayısı</Label>
          <span className="text-sm font-medium tabular-nums">
            {questionCount}
          </span>
        </div>
        <Slider
          id="qcount"
          min={1}
          max={20}
          step={1}
          value={[questionCount]}
          onValueChange={([v]) => setForm({ questionCount: v ?? 10 })}
        />
      </div>

      <Button
        onClick={onGenerate}
        disabled={isLoading || !topicId}
        size="lg"
        className="w-full gap-2"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Üretiliyor…
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4" />
            Üret
          </>
        )}
      </Button>

      <p className="text-center text-xs text-muted-foreground">
        Cache hit'te ~1 sn · İlk üretim ~30 sn
      </p>
    </div>
  );
}
