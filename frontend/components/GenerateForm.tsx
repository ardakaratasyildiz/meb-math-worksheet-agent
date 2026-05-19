"use client";

import * as React from "react";
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
import { Switch } from "@/components/ui/switch";

import {
  generateWorksheet,
  listGrades,
  listKazanimlar,
  listTopics,
} from "@/lib/api";
import { addHistory } from "@/lib/history";
import { useGenerateStore, type TypeGroupKey } from "@/lib/store";
import {
  QUESTION_TYPE_GROUPS,
  type Difficulty,
  type DifficultyMode,
  type GradeInfo,
  type KazanimInfo,
  type QuestionType,
  type TopicInfo,
} from "@/lib/types";

const DIFFICULTIES: { value: Difficulty; label: string }[] = [
  { value: "kolay", label: "Kolay" },
  { value: "orta", label: "Orta" },
  { value: "zor", label: "Zor" },
];

const DIFFICULTY_MODES: { value: DifficultyMode; label: string; hint: string }[] = [
  { value: "single", label: "Tek seviye", hint: "Yukarıda seçilen zorluk" },
  { value: "mixed", label: "Karışık", hint: "Kolay + orta + zor karışık" },
  { value: "progressive", label: "Progresyon", hint: "Kolay → orta → zor sıralı" },
];

const TYPE_GROUP_META: {
  key: TypeGroupKey;
  title: string;
  hint: string;
}[] = [
  {
    key: "open_ended",
    title: "Açık uçlu sözel",
    hint: "İşlem · Sözel problem · Kavram · Akıl yürütme · Modelleme · Günlük hayat",
  },
  {
    key: "visual",
    title: "Görsel ve yapısal",
    hint: "Salt işlem · Tablo · Geometri · Grafik · Örüntü",
  },
  {
    key: "format",
    title: "Format çeşitliliği",
    hint: "Çoktan seçmeli · Boşluk doldurma · Doğru/Yanlış · Eşleştirme · Sıralama",
  },
];

const KAZANIM_AUTO = "__AUTO__";

function flattenTypeGroups(
  groups: Record<TypeGroupKey, boolean>,
): QuestionType[] | null {
  const enabledKeys = (Object.keys(groups) as TypeGroupKey[]).filter(
    (k) => groups[k],
  );
  if (enabledKeys.length === 3) return null; // hepsi açık → backend default
  return enabledKeys.flatMap((k) => QUESTION_TYPE_GROUPS[k] as QuestionType[]);
}

export function GenerateForm() {
  const {
    grade,
    topicId,
    kazanimKod,
    difficulty,
    questionCount,
    typeGroups,
    difficultyMode,
    includeAnswerKey,
    includeSolutions,
    status,
    setForm,
    startGenerate,
    setSuccess,
    setError,
  } = useGenerateStore();

  // Clerk userId — backend cache/history kullanıcı izolasyonu için tenant_id olarak gider.
  const { userId } = useAuth();

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

  // En az 1 grup açık olmalı — aksi halde üretim engellenir.
  const anyTypeGroupOn =
    typeGroups.open_ended || typeGroups.visual || typeGroups.format;

  async function onGenerate() {
    if (!anyTypeGroupOn) {
      toast.error("Soru tipi seçimi", {
        description: "En az bir tip grubu açık olmalı.",
      });
      return;
    }
    startGenerate();
    try {
      const question_types = flattenTypeGroups(typeGroups);
      const res = await generateWorksheet({
        grade,
        topic_id: topicId,
        kazanim_kod: kazanimKod || null,
        difficulty,
        question_count: questionCount,
        tenant_id: userId ?? null,
        question_types,
        difficulty_mode: difficultyMode,
        include_answer_key: includeAnswerKey,
        include_solutions: includeSolutions,
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
        toast.success("Önbellekten getirildi", {
          description: `${res.worksheet.questions.length} soru — aynı parametrelerle daha önce üretilmişti.`,
        });
      } else {
        toast.success("Üretim tamamlandı", {
          description: `${res.worksheet.questions.length} soru üretildi ve denetimden geçti.`,
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

      <div className="space-y-2">
        <Label htmlFor="topic">Konu</Label>
        <Select
          value={topicId}
          onValueChange={(v) => setForm({ topicId: v, kazanimKod: null })}
          disabled={topics.length === 0}
        >
          <SelectTrigger id="topic">
            <SelectValue placeholder="Konu seçin" />
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
        <Label htmlFor="kazanim">Kazanım kodu</Label>
        <Select
          value={kazanimKod ?? KAZANIM_AUTO}
          onValueChange={(v) =>
            setForm({ kazanimKod: v === KAZANIM_AUTO ? null : v })
          }
          disabled={kazanimlar.length === 0}
        >
          <SelectTrigger id="kazanim">
            <SelectValue placeholder="Kazanım kodu seçin" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={KAZANIM_AUTO}>
              Tümü (konunun tüm kazanımlarından)
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
              disabled={difficultyMode !== "single"}
            >
              {d.label}
            </Button>
          ))}
        </div>
        {difficultyMode !== "single" ? (
          <p className="text-xs text-muted-foreground">
            Karışık veya progresyon modda yukarıdaki tekli seçim kullanılmaz —
            zorluk dağıtımı otomatik (yaklaşık %30 kolay, %40 orta, %30 zor).
          </p>
        ) : null}
      </div>

      {/* Sprint 12-A: Zorluk modu */}
      <div className="space-y-2">
        <Label>Zorluk modu</Label>
        <div className="grid grid-cols-3 gap-2">
          {DIFFICULTY_MODES.map((m) => (
            <Button
              key={m.value}
              type="button"
              variant={difficultyMode === m.value ? "default" : "outline"}
              onClick={() => setForm({ difficultyMode: m.value })}
              className="flex h-auto flex-col items-center justify-center gap-0.5 py-2"
            >
              <span className="text-sm font-medium">{m.label}</span>
              <span className="text-[10px] font-normal opacity-80">
                {m.hint}
              </span>
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
        {difficultyMode !== "single" && questionCount < 5 ? (
          <p className="text-xs text-amber-600 dark:text-amber-400">
            Karışık/progresyon modu için en az 5 soru önerilir; aksi halde tek
            seviye davranışına düşer.
          </p>
        ) : null}
      </div>

      {/* Sprint 12-A: Soru tipi grupları */}
      <div className="space-y-3 rounded-lg border bg-card p-4">
        <div>
          <Label>Soru tipi grupları</Label>
          <p className="mt-1 text-xs text-muted-foreground">
            Hangi tipler üretim havuzunda olsun? En az bir grup açık olmalı.
          </p>
        </div>
        <div className="space-y-3">
          {TYPE_GROUP_META.map((g) => (
            <div
              key={g.key}
              className="flex items-start justify-between gap-3 rounded-md border bg-background p-3"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium leading-tight">{g.title}</p>
                <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">
                  {g.hint}
                </p>
              </div>
              <Switch
                checked={typeGroups[g.key]}
                onCheckedChange={(v) =>
                  setForm({
                    typeGroups: { ...typeGroups, [g.key]: v },
                  })
                }
                aria-label={g.title}
              />
            </div>
          ))}
        </div>
        {!anyTypeGroupOn ? (
          <p className="text-xs text-destructive">
            Üretim için en az bir grup açık olmalı.
          </p>
        ) : null}
      </div>

      {/* Sprint 12-A: Çıktı kontrolü */}
      <div className="space-y-3 rounded-lg border bg-card p-4">
        <div>
          <Label>Çıktı (PDF) içeriği</Label>
          <p className="mt-1 text-xs text-muted-foreground">
            Sınav modu için cevap anahtarını ve çözüm sayfasını kapatabilirsiniz.
          </p>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 rounded-md border bg-background p-3">
            <div className="flex-1">
              <p className="text-sm font-medium">Cevap anahtarı sayfası</p>
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                PDF sonunda numara ↔ doğru cevap tablosu.
              </p>
            </div>
            <Switch
              checked={includeAnswerKey}
              onCheckedChange={(v) => setForm({ includeAnswerKey: v })}
              aria-label="Cevap anahtarı sayfası"
            />
          </div>
          <div className="flex items-center justify-between gap-3 rounded-md border bg-background p-3">
            <div className="flex-1">
              <p className="text-sm font-medium">Çözüm adımları sayfası</p>
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                Her sorunun adım adım çözümü ayrı sayfada.
              </p>
            </div>
            <Switch
              checked={includeSolutions}
              onCheckedChange={(v) => setForm({ includeSolutions: v })}
              aria-label="Çözüm adımları sayfası"
            />
          </div>
        </div>
      </div>

      <Button
        onClick={onGenerate}
        disabled={isLoading || !topicId || !anyTypeGroupOn}
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
            Üretimi başlat
          </>
        )}
      </Button>

      <p className="text-center text-xs text-muted-foreground">
        Ortalama üretim süresi 30 saniyedir. Karışık/progresyon modunda 3 ayrı
        çağrı yapılır, süre ~60 saniyeye çıkar.
      </p>
    </div>
  );
}
