"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ChevronDown, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
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
import { Switch } from "@/components/ui/switch";

import { createQuiz } from "@/lib/api";
import {
  getGradesLocal,
  getKazanimlarLocal,
  getTopicsLocal,
} from "@/lib/curriculum";
import type {
  Difficulty,
  DifficultyMode,
  GradeInfo,
  KazanimInfo,
  TopicInfo,
} from "@/lib/types";

// Çözülebilir 4 tip — dar union (QuestionType'tan türetmiyoruz; o genişletirdi).
type SolvableType =
  | "coktan_secmeli"
  | "dogru_yanlis"
  | "bosluk_doldurma"
  | "salt_islem";

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: "kolay", label: "Kolay" },
  { value: "orta", label: "Orta" },
  { value: "zor", label: "Zor" },
];

const DIFFICULTY_MODES: { value: DifficultyMode; label: string }[] = [
  { value: "single", label: "Tek seviye" },
  { value: "mixed", label: "Karışık" },
  { value: "progressive", label: "Progresyon" },
];

// Çözülebilir 4 tip — gelişmiş panelde tek tek açılıp kapatılır.
const SOLVABLE_TYPES: { value: SolvableType; label: string; hint: string }[] = [
  { value: "coktan_secmeli", label: "Çoktan seçmeli", hint: "4 şıklı, tek doğru" },
  { value: "dogru_yanlis", label: "Doğru / Yanlış", hint: "Tek önerme" },
  { value: "bosluk_doldurma", label: "Boşluk doldurma", hint: "____ ile boşluk" },
  { value: "salt_islem", label: "İşlem", hint: "Sayısal sonuç" },
];

const KAZANIM_AUTO = "__AUTO__";

const ALL_TYPES_ON: Record<SolvableType, boolean> = {
  coktan_secmeli: true,
  dogru_yanlis: true,
  bosluk_doldurma: true,
  salt_islem: true,
};

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

  // Gelişmiş (varsayılan kapalı): tip seçimi + zorluk modu.
  const [advancedOpen, setAdvancedOpen] = React.useState(false);
  const [types, setTypes] = React.useState<Record<SolvableType, boolean>>(
    ALL_TYPES_ON,
  );
  const [difficultyMode, setDifficultyMode] =
    React.useState<DifficultyMode>("single");

  const enabledTypes = SOLVABLE_TYPES.filter((t) => types[t.value]);
  const advancedChangeCount =
    (difficultyMode !== "single" ? 1 : 0) +
    (enabledTypes.length !== SOLVABLE_TYPES.length ? 1 : 0);

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
    if (enabledTypes.length === 0) {
      toast.error("Soru tipi seçimi", {
        description: "En az bir çözülebilir tip açık olmalı.",
      });
      return;
    }
    setSubmitting(true);
    try {
      // Tümü açıksa null (sunucu varsayılanı = 4 tip); alt küme ise listeyi gönder.
      const question_types =
        enabledTypes.length === SOLVABLE_TYPES.length
          ? null
          : enabledTypes.map((t) => t.value);
      const quiz = await createQuiz({
        grade,
        topic_id: topicId,
        kazanim_kod: kazanimKod,
        difficulty,
        question_count: questionCount,
        tenant_id: userId,
        question_types,
        difficulty_mode: difficultyMode,
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

      {/* Zorluk butonları yalnız tek-seviye modda; karışık/progresyonda gizlenir
          (zorluk seçimi anlamsız), soru sayısı tek başına genişler. */}
      <div
        className={`grid gap-4 ${
          difficultyMode === "single" ? "md:grid-cols-2" : "md:grid-cols-1"
        }`}
      >
        {difficultyMode === "single" ? (
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
        ) : null}

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

      {/* ── Gelişmiş ayarlar (varsayılan kapalı) ───────────────────────── */}
      <div className="space-y-3">
        <button
          type="button"
          onClick={() => setAdvancedOpen((v) => !v)}
          aria-expanded={advancedOpen}
          className="flex w-full items-center justify-between gap-3 rounded-md border bg-background px-4 py-3 text-sm transition-colors hover:bg-accent/30"
        >
          <span className="flex items-center gap-2 font-medium">
            <ChevronDown
              className={`h-4 w-4 transition-transform ${
                advancedOpen ? "rotate-180" : ""
              }`}
            />
            Gelişmiş ayarlar
            {advancedChangeCount > 0 ? (
              <Badge variant="secondary" className="ml-1 text-[10px]">
                {advancedChangeCount} değişiklik
              </Badge>
            ) : null}
          </span>
          <span className="hidden text-[11px] text-muted-foreground sm:inline">
            Soru tipleri · Zorluk modu
          </span>
        </button>

        {advancedOpen ? (
          <div className="space-y-6 rounded-md border bg-accent/10 p-4">
            {/* Zorluk modu */}
            <div className="space-y-1.5">
              <Label>Zorluk modu</Label>
              <div className="grid grid-cols-3 gap-2">
                {DIFFICULTY_MODES.map((m) => (
                  <Button
                    key={m.value}
                    type="button"
                    variant={difficultyMode === m.value ? "default" : "outline"}
                    onClick={() => setDifficultyMode(m.value)}
                    size="sm"
                  >
                    {m.label}
                  </Button>
                ))}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Karışık/progresyon kolay-orta-zor dağıtır; en az 5 soru önerilir.
              </p>
            </div>

            {/* Soru tipleri */}
            <div className="space-y-2.5">
              <div className="space-y-1">
                <Label className="text-sm font-semibold">Soru tipleri</Label>
                <p className="text-[11px] text-muted-foreground">
                  Hangi çözülebilir tipler üretilsin? En az bir tip açık olmalı.
                </p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {SOLVABLE_TYPES.map((t) => (
                  <div
                    key={t.value}
                    role="presentation"
                    onClick={() =>
                      setTypes((prev) => ({
                        ...prev,
                        [t.value]: !prev[t.value],
                      }))
                    }
                    className={`flex w-full cursor-pointer items-start justify-between gap-3 rounded-md border bg-background p-3 text-left transition-colors hover:bg-accent/30 ${
                      types[t.value] ? "border-primary/40 bg-accent/20" : ""
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium leading-tight">
                        {t.label}
                      </p>
                      <p className="mt-0.5 text-[11px] text-muted-foreground">
                        {t.hint}
                      </p>
                    </div>
                    <Switch
                      checked={types[t.value]}
                      onCheckedChange={(v) =>
                        setTypes((prev) => ({ ...prev, [t.value]: v }))
                      }
                      aria-label={t.label}
                    />
                  </div>
                ))}
              </div>
              {enabledTypes.length === 0 ? (
                <p className="text-[11px] text-destructive">
                  Üretim için en az bir tip açık olmalı.
                </p>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-[11px] text-muted-foreground">
          Çözülebilir tipler üretilir (çoktan seçmeli, doğru/yanlış, boşluk
          doldurma, işlem). Üretim ~30 saniye sürer.
        </p>
        <Button
          onClick={onStart}
          disabled={submitting || !topicId || enabledTypes.length === 0}
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
