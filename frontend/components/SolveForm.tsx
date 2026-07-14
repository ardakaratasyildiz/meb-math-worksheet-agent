"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ArrowRight, CheckCircle2, ChevronDown, GraduationCap, Lightbulb, Loader2, Sparkles } from "lucide-react";
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

import { createQuiz, listKazanimlarByUnit, listUnits } from "@/lib/api";
import { getGradesLocal } from "@/lib/curriculum";
import { getKazanimlarByUnitLocal, getUnitsLocal } from "@/lib/units";
import { factsForSubject } from "@/lib/subjectFacts";
import {
  availableSubjects,
  hasMultipleSubjects,
  subjectMaxGrade,
  subjectMinGrade,
  subjectStyle,
} from "@/lib/subjects";
import type {
  Difficulty,
  DifficultyMode,
  GradeInfo,
  KazanimInfo,
  Subject,
  UnitInfo,
} from "@/lib/types";

// Çözülebilir 4 tip — dar union (QuestionType'tan türetmiyoruz; o genişletirdi).
type SolvableType =
  | "coktan_secmeli"
  | "dogru_yanlis"
  | "bosluk_doldurma"
  | "sozel_problem";

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
  { value: "sozel_problem", label: "Açık uçlu", hint: "Serbest cevap — kendin değerlendir" },
];

const KAZANIM_AUTO = "__AUTO__";

const ALL_TYPES_ON: Record<SolvableType, boolean> = {
  coktan_secmeli: true,
  dogru_yanlis: true,
  bosluk_doldurma: true,
  sozel_problem: true,
};

// Çözülebilir quiz üretim formu — /generate'in sade kardeşi. PDF/markalama/
// gelişmiş ayar YOK; çıktı PDF değil, çözülecek quiz. Dropdownlar lokal müfredat
// snapshot'ından anında dolar (backend cold-start'a bağımlı değil).
//
// mode: "solve" (öğrenci — üret ve doğrudan çöz) | "create" (öğretmen — üret + kaydet,
// sonra sınıfa ödev ata; ÇÖZMEYE sokmaz). Rol /practice/new sayfasında belirlenir.
export function SolveForm({ mode = "solve" }: { mode?: "solve" | "create" }) {
  const router = useRouter();
  const { userId } = useAuth();
  const [createdQuizId, setCreatedQuizId] = React.useState<string | null>(null);
  // "Bu kazanımda pratik yap" derin-linki: /practice/new?grade=&unit=&kazanim=&subject=
  const searchParams = useSearchParams();
  const initialGrade = Number(searchParams.get("grade")) || 5;
  const initialUnit = searchParams.get("unit") ?? "";
  const initialKazanim = searchParams.get("kazanim");

  // Ders seçimi — yalnız flag'i açık dersler. Deep-link ?subject= yalnız açık
  // dersi kabul eder; değilse matematik'e düşer.
  const multiSubject = hasMultipleSubjects();
  const subjects = availableSubjects();
  const spSubject = (searchParams.get("subject") ?? "").toLowerCase();
  const initialSubject: Subject = subjects.some((s) => s.value === spSubject)
    ? (spSubject as Subject)
    : "matematik";

  const [subject, setSubject] = React.useState<Subject>(initialSubject);
  const isMath = subject === "matematik";

  const [grade, setGrade] = React.useState(() =>
    Math.min(
      Math.max(initialGrade, subjectMinGrade(initialSubject)),
      subjectMaxGrade(initialSubject),
    ),
  );
  const [unitId, setUnitId] = React.useState(initialUnit);
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

  // Sınıflar dersin sınıf aralığına göre (lokal, anında — cold-start yok).
  const grades = React.useMemo<GradeInfo[]>(() => {
    const min = subjectMinGrade(subject);
    const max = subjectMaxGrade(subject);
    return getGradesLocal().filter((g) => g.id >= min && g.id <= max);
  }, [subject]);

  const [units, setUnits] = React.useState<UnitInfo[]>(() =>
    initialSubject === "matematik" ? getUnitsLocal(initialGrade) : [],
  );
  const [kazanimlar, setKazanimlar] = React.useState<KazanimInfo[]>([]);
  const [loadingUnits, setLoadingUnits] = React.useState(false);
  const [loadingKazanim, setLoadingKazanim] = React.useState(false);

  // Ünite yükleme: matematik lokal snapshot'tan (anında), diğer dersler API'den
  // (lokal snapshot yok). API yolu cold-start'a takılabilir → yükleniyor durumu.
  React.useEffect(() => {
    if (isMath) {
      setUnits(getUnitsLocal(grade));
      setLoadingUnits(false);
      return;
    }
    let cancelled = false;
    setLoadingUnits(true);
    listUnits(grade, subject)
      .then((u) => {
        if (!cancelled) setUnits(u);
      })
      .catch(() => {
        if (!cancelled) setUnits([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingUnits(false);
      });
    return () => {
      cancelled = true;
    };
  }, [grade, subject, isMath]);

  // unitId boş/geçersizse sınıfın ilk ünitesini otomatik seç → dropdown boş kalmaz.
  React.useEffect(() => {
    if (units.length === 0) return;
    if (!unitId || !units.some((u) => u.unit_id === unitId)) {
      setUnitId(units[0].unit_id);
      setKazanimKod(null);
    }
  }, [units, unitId]);

  React.useEffect(() => {
    if (!unitId) {
      setKazanimlar([]);
      return;
    }
    if (isMath) {
      setKazanimlar(getKazanimlarByUnitLocal(grade, unitId));
      setLoadingKazanim(false);
      return;
    }
    let cancelled = false;
    setLoadingKazanim(true);
    listKazanimlarByUnit(grade, unitId, subject)
      .then((k) => {
        if (!cancelled) setKazanimlar(k);
      })
      .catch(() => {
        if (!cancelled) setKazanimlar([]);
      })
      .finally(() => {
        if (!cancelled) setLoadingKazanim(false);
      });
    return () => {
      cancelled = true;
    };
  }, [grade, unitId, subject, isMath]);

  // Ders değişince sınıfı aralığa kıstır, ünite/kazanımı sıfırla.
  function onSubjectChange(v: Subject) {
    if (v === subject) return;
    setSubject(v);
    const min = subjectMinGrade(v);
    const max = subjectMaxGrade(v);
    setGrade((g) => Math.min(Math.max(g, min), max));
    setUnitId("");
    setKazanimKod(null);
  }

  async function onStart() {
    if (!unitId) {
      toast.error("Ünite seçin", { description: "Quiz için bir ünite seçmelisiniz." });
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
        unit_id: unitId,
        kazanim_kod: kazanimKod,
        difficulty,
        question_count: questionCount,
        tenant_id: userId,
        question_types,
        difficulty_mode: difficultyMode,
        // Matematik'te parametre eklenmez (geriye uyum); diğer derslerde gönderilir.
        ...(isMath ? {} : { subject }),
      });
      // Öğretmen: çözmeye SOKMA — "oluşturuldu, sınıfına ata" başarı ekranı.
      // Öğrenci: doğrudan çözmeye geç.
      if (mode === "create") {
        setCreatedQuizId(quiz.id);
        setSubmitting(false);
      } else {
        router.push(`/practice/quiz/${quiz.id}`);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Bilinmeyen hata";
      toast.error("Quiz üretilemedi", { description: msg });
      setSubmitting(false);
    }
  }

  // Öğretmen — quiz oluşturuldu: çözmeye sokmadan "sınıfa ata" yönlendirmesi.
  if (createdQuizId) {
    return (
      <div className="space-y-4">
        <div className="flex items-start gap-3 rounded-2xl border border-mint/40 bg-mint/10 p-5">
          <CheckCircle2 className="mt-0.5 h-6 w-6 flex-shrink-0 text-mint" />
          <div className="min-w-0">
            <p className="font-display text-lg font-bold">Quiz oluşturuldu 🎉</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Quiz &quot;Sınıflarım&quot;daki ödev listende hazır. Bir sınıfa gidip
              ödev olarak atayabilir, öğrencilerin çözünce sonuçlarını görebilirsin.
            </p>
          </div>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Button asChild size="lg" className="gap-2">
            <Link href="/practice/classes">
              <GraduationCap className="h-4 w-4" />
              Sınıfıma ödev ata
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => setCreatedQuizId(null)}
          >
            Başka quiz üret
          </Button>
          <Button asChild variant="ghost" size="lg">
            <Link href={`/practice/quiz/${createdQuizId}`}>Önce ben çözeyim</Link>
          </Button>
        </div>
      </div>
    );
  }

  // Üretim sürerken (~30 sn) "Bunu biliyor muydun?" bekleme ekranı göster.
  if (submitting) {
    return <QuizGeneratingState questionCount={questionCount} subject={subject} />;
  }

  return (
    <div className="space-y-6">
      {/* Ders seçici — yalnız matematik dışı ders açıkken görünür. Renk kodlaması
          ana sayfa vitriniyle ortak (lib/subjects → subjectStyle). */}
      {multiSubject ? (
        <div className="space-y-1.5">
          <Label>Ders</Label>
          <div className="flex flex-wrap gap-2">
            {subjects.map((s) => {
              const st = subjectStyle(s.value);
              const on = s.value === subject;
              return (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => onSubjectChange(s.value)}
                  aria-pressed={on}
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-sm font-semibold transition-colors ${
                    on
                      ? `${st.bg} ${st.text} ${st.border}`
                      : "border-border bg-background text-muted-foreground hover:bg-accent/40"
                  }`}
                >
                  <span aria-hidden>{st.emoji}</span>
                  {s.label}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="s-grade">Sınıf</Label>
          <Select
            value={String(grade)}
            onValueChange={(v) => {
              setGrade(Number(v));
              setUnitId("");
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
          <Label htmlFor="s-unit">Ünite</Label>
          <Select
            value={unitId}
            onValueChange={(v) => {
              setUnitId(v);
              setKazanimKod(null);
            }}
            disabled={units.length === 0 || loadingUnits}
          >
            <SelectTrigger id="s-unit">
              <SelectValue
                placeholder={loadingUnits ? "Yükleniyor…" : "Ünite seçin"}
              />
            </SelectTrigger>
            <SelectContent>
              {units.map((u) => (
                <SelectItem key={u.unit_id} value={u.unit_id}>
                  {u.no}. {u.name}
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
            disabled={kazanimlar.length === 0 || loadingKazanim}
          >
            <SelectTrigger id="s-kazanim">
              <SelectValue
                placeholder={loadingKazanim ? "Yükleniyor…" : "Kazanım seçin"}
              />
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
          {mode === "create"
            ? "Çözülebilir bir quiz üretilir ve sınıfına ödev atamak üzere kaydedilir (çözmeye sokmaz)."
            : "Çözülebilir tipler üretilir (çoktan seçmeli, doğru/yanlış, boşluk doldurma, açık uçlu). Üretim saniyeler içinde tamamlanır."}
        </p>
        <Button
          onClick={onStart}
          disabled={submitting || !unitId || enabledTypes.length === 0}
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
              {mode === "create" ? "Quiz oluştur" : "Quiz oluştur & çöz"}
            </>
          )}
        </Button>
      </div>
    </div>
  );
}

// ─── Quiz üretiliyor — "Bunu biliyor muydun?" bekleme ekranı ─────────────────
// /generate (PDF) akışındaki GeneratingState'in quiz karşılığı. Streaming yok;
// zaman-tabanlı faz/ilerleme + dönen matematik bilgisi (ortak @/lib/mathFacts).
function QuizGeneratingState({
  questionCount,
  subject,
}: {
  questionCount: number;
  subject: Subject;
}) {
  const facts = React.useMemo(() => factsForSubject(subject), [subject]);
  const [factIndex, setFactIndex] = React.useState(() =>
    Math.floor(Math.random() * facts.length),
  );
  const [elapsed, setElapsed] = React.useState(0);

  React.useEffect(() => {
    const factTimer = setInterval(() => {
      setFactIndex((i) => (i + 1) % facts.length);
    }, 11000);
    const tickTimer = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => {
      clearInterval(factTimer);
      clearInterval(tickTimer);
    };
  }, [facts]);

  const phase =
    elapsed < 8
      ? "Sorular üretiliyor"
      : elapsed < 18
        ? subject === "matematik"
          ? "Aritmetik denetimi yapılıyor"
          : "İçerik denetimi yapılıyor"
        : elapsed < 28
          ? "Kazanım uyumu denetleniyor"
          : "Quiz hazırlanıyor";
  const progress = Math.min(98, Math.round((1 - Math.exp(-elapsed / 14)) * 100));
  const eta = Math.max(0, 30 - elapsed);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
        <div className="flex-1">
          <p className="font-display text-base font-bold text-foreground">
            {phase}
          </p>
          <p className="text-xs text-muted-foreground">
            {questionCount} soruluk quiz hazırlanıyor
            {eta > 0 ? ` · ~${eta} sn` : " · birazdan..."}
          </p>
        </div>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary to-coral transition-all duration-1000 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="flex items-start gap-3 rounded-2xl border bg-accent/40 p-4">
        <Lightbulb className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
        <div className="min-w-0 flex-1">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-primary">
            Bunu biliyor muydun? 🤔
          </p>
          <p
            key={factIndex}
            className="animate-fade-in text-sm leading-relaxed text-foreground"
          >
            {facts[factIndex]}
          </p>
        </div>
      </div>
    </div>
  );
}
