"use client";

import * as React from "react";
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

import {
  generateWorksheetStream,
  listGrades,
  listKazanimlar,
  listTopics,
} from "@/lib/api";
import { track } from "@/lib/analytics";
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

const DIFFICULTY_MODES: { value: DifficultyMode; label: string }[] = [
  { value: "single", label: "Tek seviye" },
  { value: "mixed", label: "Karışık" },
  { value: "progressive", label: "Progresyon" },
];

const DIFFICULTY_MODE_HINT: Record<DifficultyMode, string> = {
  single: "Yukarıdaki tekli zorluk değeri tüm sorulara uygulanır.",
  mixed: "Kolay/orta/zor (yaklaşık 30/40/30) karışık sırada üretilir.",
  progressive: "Aynı 30/40/30 dağılımı; sıralama kolay → orta → zor.",
};

const TYPE_GROUP_META: {
  key: TypeGroupKey;
  title: string;
  hint: string;
}[] = [
  {
    key: "open_ended",
    title: "Açık uçlu sözel",
    hint: "İşlem, sözel problem, kavram, akıl yürütme, modelleme, günlük hayat",
  },
  {
    key: "visual",
    title: "Görsel ve yapısal",
    hint: "Salt işlem, tablo, geometri, grafik, örüntü",
  },
  {
    key: "format",
    title: "Format çeşitliliği",
    hint: "Çoktan seçmeli, boşluk doldurma, doğru/yanlış, eşleştirme, sıralama",
  },
];

const KAZANIM_AUTO = "__AUTO__";

function flattenTypeGroups(
  groups: Record<TypeGroupKey, boolean>,
): QuestionType[] | null {
  const enabledKeys = (Object.keys(groups) as TypeGroupKey[]).filter(
    (k) => groups[k],
  );
  if (enabledKeys.length === 3) return null;
  return enabledKeys.flatMap((k) => QUESTION_TYPE_GROUPS[k] as QuestionType[]);
}

// Küçük yardımcı — section başlık + ince ayraç. Kart içinde gruplar arası
// görsel ritim kuruyor; ayrı bir komponente çıkarmaya değecek kadar tekrar
// ediyor (3 grup üst üste).
function SectionTitle({
  title,
  hint,
}: {
  title: string;
  hint?: string;
}) {
  return (
    <div className="space-y-1">
      <Label className="text-sm font-semibold">{title}</Label>
      {hint ? (
        <p className="text-[11px] leading-snug text-muted-foreground">{hint}</p>
      ) : null}
    </div>
  );
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
    setStreamedCount,
    setSuccess,
    setError,
  } = useGenerateStore();

  const { userId } = useAuth();

  const [grades, setGrades] = React.useState<GradeInfo[]>([]);
  const [topics, setTopics] = React.useState<TopicInfo[]>([]);
  const [kazanimlar, setKazanimlar] = React.useState<KazanimInfo[]>([]);
  // Progressive disclosure: gelişmiş ayarlar varsayılan kapalı. İlk kullanıcı
  // 5 alanlı (sınıf/konu/kazanım/zorluk/sayı) sade ekranla karşılaşır;
  // detay isteyen "▾ Gelişmiş ayarlar"ı açar.
  const [advancedOpen, setAdvancedOpen] = React.useState(false);

  // Default-dışı kaç ayar var? Kapalıyken kullanıcı bilsin diye badge'le göster.
  const advancedChangeCount = React.useMemo(() => {
    let n = 0;
    if (difficultyMode !== "single") n++;
    if (!typeGroups.open_ended || !typeGroups.visual || !typeGroups.format) n++;
    if (!includeAnswerKey) n++;
    if (!includeSolutions) n++;
    return n;
  }, [difficultyMode, typeGroups, includeAnswerKey, includeSolutions]);

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
  const anyTypeGroupOn =
    typeGroups.open_ended || typeGroups.visual || typeGroups.format;

  async function onGenerate() {
    if (!anyTypeGroupOn) {
      toast.error("Soru tipi seçimi", {
        description: "En az bir tip grubu açık olmalı.",
      });
      return;
    }
    // tenant_id (Clerk userId) hazır değilken üretme — aksi halde üretim
    // hesaba kaydedilmez ("geçmişte göremiyorum" sorununun kök sebebi).
    if (!userId) {
      toast.error("Oturum bilgisi henüz yüklenmedi", {
        description: "Birkaç saniye sonra tekrar deneyin.",
      });
      return;
    }
    startGenerate();
    // Funnel: aktivasyon adımının başlangıcı.
    track("worksheet_generate_start", {
      grade,
      topic_id: topicId,
      difficulty,
      difficulty_mode: difficultyMode,
      question_count: questionCount,
    });
    const t0 = performance.now();
    try {
      const question_types = flattenTypeGroups(typeGroups);
      // SSE streaming: bağlantı her soru event'iyle canlı kalır → uzun üretimde
      // proxy/tarayıcı idle-timeout'u tetiklenmez ("hata aldım ama geçmişte var"
      // sorununun kök sebebi). `complete` event'i bloklayan endpoint ile aynı
      // GenerateWorksheetResponse'u döner.
      const res = await generateWorksheetStream(
        {
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
        },
        { onQuestion: (_q, index) => setStreamedCount(index + 1) },
      );
      setSuccess(res);
      const trace = res.metadata.trace;
      // Aktivasyon başarısı + CACHE HIT ORANI ölçümü (kapasite/maliyet kritik).
      track("worksheet_generate_success", {
        grade,
        topic_id: topicId,
        difficulty_mode: difficultyMode,
        question_count: res.worksheet.questions.length,
        cache_hit: !!trace?.cache_hit,
        model: trace?.model_used ?? "unknown",
        provider: trace?.provider ?? "unknown",
        duration_ms: Math.round(performance.now() - t0),
      });
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
      track("worksheet_generate_error", {
        grade,
        topic_id: topicId,
        message: msg.slice(0, 120),
        duration_ms: Math.round(performance.now() - t0),
      });
      setError(msg);
      toast.error("Üretim başarısız", { description: msg });
    }
  }

  return (
    <div className="space-y-6">
      {/* ── Row 1: Sınıf / Konu / Kazanım ──────────────────────────────── */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-1.5">
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

        <div className="space-y-1.5">
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

        <div className="space-y-1.5">
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
                Tümü (otomatik dağılım)
              </SelectItem>
              {kazanimlar.map((k) => (
                <SelectItem key={k.kod} value={k.kod}>
                  <span className="font-mono text-xs text-primary">
                    {k.kod}
                  </span>{" "}
                  · {k.metin.slice(0, 50)}
                  {k.metin.length > 50 ? "…" : ""}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* ── Row 2: Zorluk + Soru sayısı ─────────────────────────────────
          Karışık/Progresyon modda Zorluk butonları GİZLENİR (disable yerine);
          Soru sayısı tek başına genişler. Mental model: "Karışık modda zorluk
          seçimi gerekmiyor" — disabled buton sorgulamasını silindi. */}
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
                  onClick={() => setForm({ difficulty: d.value })}
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
            <p className="text-[11px] text-amber-600 dark:text-amber-400">
              Karışık/progresyon için en az 5 soru önerilir.
            </p>
          ) : null}
        </div>
      </div>

      {/* ── Gelişmiş ayarlar (varsayılan kapalı) ──────────────────────
          Progressive disclosure — ilk kullanıcı sade form görür, detay
          isteyen açar. Default-dışı ayar varsa badge'le bildirir. */}
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
            Zorluk modu · Tip grupları · PDF içeriği
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
                    onClick={() => setForm({ difficultyMode: m.value })}
                    size="sm"
                  >
                    {m.label}
                  </Button>
                ))}
              </div>
              <p className="text-[11px] text-muted-foreground">
                {DIFFICULTY_MODE_HINT[difficultyMode]}
              </p>
            </div>

            {/* Soru tipi grupları */}
            <div className="space-y-2.5">
              <SectionTitle
                title="Soru tipi grupları"
                hint="Hangi tipler üretim havuzunda olsun? En az bir grup açık olmalı."
              />
              <div className="grid gap-3 md:grid-cols-3">
                {TYPE_GROUP_META.map((g) => (
                  <div
                    key={g.key}
                    role="presentation"
                    onClick={() =>
                      setForm({
                        typeGroups: {
                          ...typeGroups,
                          [g.key]: !typeGroups[g.key],
                        },
                      })
                    }
                    className={`flex w-full cursor-pointer items-start justify-between gap-3 rounded-md border bg-background p-3 text-left transition-colors hover:bg-accent/30 ${
                      typeGroups[g.key] ? "border-primary/40 bg-accent/20" : ""
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium leading-tight">
                        {g.title}
                      </p>
                      <p className="mt-0.5 line-clamp-2 text-[11px] leading-snug text-muted-foreground">
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
                <p className="text-[11px] text-destructive">
                  Üretim için en az bir grup açık olmalı.
                </p>
              ) : null}
            </div>

            {/* Çıktı içeriği */}
            <div className="space-y-2.5">
              <SectionTitle
                title="Çıktı (PDF) içeriği"
                hint="Sınav modu için cevap anahtarını ve çözüm sayfasını kapatabilirsiniz."
              />
              <div className="grid gap-3 md:grid-cols-2">
                <div
                  role="presentation"
                  onClick={() =>
                    setForm({ includeAnswerKey: !includeAnswerKey })
                  }
                  className={`flex w-full cursor-pointer items-start justify-between gap-3 rounded-md border bg-background p-3 text-left transition-colors hover:bg-accent/30 ${
                    includeAnswerKey ? "border-primary/40 bg-accent/20" : ""
                  }`}
                >
                  <div className="min-w-0 flex-1">
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
                <div
                  role="presentation"
                  onClick={() =>
                    setForm({ includeSolutions: !includeSolutions })
                  }
                  className={`flex w-full cursor-pointer items-start justify-between gap-3 rounded-md border bg-background p-3 text-left transition-colors hover:bg-accent/30 ${
                    includeSolutions ? "border-primary/40 bg-accent/20" : ""
                  }`}
                >
                  <div className="min-w-0 flex-1">
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
          </div>
        ) : null}
      </div>

      {/* ── Row 6: Üretim butonu — her zaman görünür ──────────────────── */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-[11px] text-muted-foreground">
          Üretim ~30 saniye sürer. Karışık/progresyon modunda 3 ayrı çağrı
          yapılır, süre ~60 sn&apos;ye çıkar.
        </p>
        <Button
          onClick={onGenerate}
          disabled={isLoading || !topicId || !anyTypeGroupOn}
          size="lg"
          className="gap-2 sm:min-w-[220px]"
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
      </div>
    </div>
  );
}
