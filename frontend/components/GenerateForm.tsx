"use client";

import * as React from "react";
import { useAuth } from "@clerk/nextjs";
import { ChevronDown, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  QuotaExceededError,
  StreamIncompleteError,
  generateWorksheetStream,
  listGrades,
  listKazanimlarByUnit,
  listUnits,
  listWorksheetHistory,
} from "@/lib/api";
import type { QuotaInfo } from "@/lib/api";
import { Paywall } from "@/components/Paywall";
import { getGradesLocal } from "@/lib/curriculum";
import { getKazanimlarByUnitLocal, getUnitsLocal } from "@/lib/units";
import { track } from "@/lib/analytics";
import { addHistory, type HistoryItem } from "@/lib/history";
import { useGenerateStore, type FormState, type TypeGroupKey } from "@/lib/store";
import {
  QUESTION_TYPE_GROUPS,
  filterTypesForSubject,
  type Difficulty,
  type DifficultyMode,
  type GenerateWorksheetResponse,
  type GradeInfo,
  type KazanimInfo,
  type QuestionType,
  type Subject,
  type UnitInfo,
} from "@/lib/types";
import {
  availableSubjects,
  hasMultipleSubjects,
  isSubjectEnabled,
  subjectMinGrade,
} from "@/lib/subjects";

// Akış kesildiğinde (mobil/uygulama-içi tarayıcı timeout'u) backend üretimi
// thread'de bitirip geçmişe kaydetmiş olabilir. Kısa süre geçmişi yoklayıp aynı
// parametrelerle yeni kaydı bul → kağıdı kurtar. Böylece "akış kesildi" hatası
// çoğu durumda sessizce başarıya döner.
async function recoverFromHistory(
  tenantId: string,
  req: {
    grade: number;
    unit_id: string | null;
    difficulty: Difficulty;
    question_count: number;
  },
): Promise<GenerateWorksheetResponse | null> {
  for (let i = 0; i < 8; i++) {
    await new Promise((r) => setTimeout(r, 4000));
    let items: HistoryItem[];
    try {
      items = await listWorksheetHistory(tenantId);
    } catch {
      continue;
    }
    const now = Date.now();
    const match = items.find((it) => {
      const r = it.request;
      return (
        r?.grade === req.grade &&
        r?.unit_id === req.unit_id &&
        r?.difficulty === req.difficulty &&
        r?.question_count === req.question_count &&
        now - new Date(it.saved_at).getTime() < 180000 // son ~3 dk
      );
    });
    if (match?.response) return match.response;
  }
  return null;
}

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

// "Görsel ve yapısal" grubu UI'dan KALDIRILDI: görselli sorular (geometri, tablo,
// grafik, örüntü) artık sunucu tarafında konuya göre belirli bir oranda otomatik
// üretiliyor (TOPIC_VISUAL_BIAS). Kullanıcıya görsel seçtirmek kafa karışıklığı
// yaratıyordu. Kullanıcı yalnızca sözel ve format gruplarını yönetir; görsel her
// zaman havuzda (flattenTypeGroups içinde visual:true zorlanır).
const TYPE_GROUP_META: {
  key: TypeGroupKey;
  title: string;
  hint: string;
}[] = [
  {
    key: "open_ended",
    title: "Açık uçlu sorular",
    hint: "İşlem, sözel problem, kavram, akıl yürütme, modelleme, günlük hayat",
  },
  {
    key: "multiple_choice",
    title: "Çoktan seçmeli sorular",
    hint: "Şıklı test soruları (A/B/C/D)",
  },
  {
    key: "other_format",
    title: "Diğer soru tipleri",
    hint: "Boşluk doldurma, doğru/yanlış, eşleştirme, sıralama",
  },
];

const KAZANIM_AUTO = "__AUTO__";

function flattenTypeGroups(
  groups: Record<TypeGroupKey, boolean>,
  subject: string = "matematik",
): QuestionType[] | null {
  // Görsel tipler (salt_islem/tablo/grafik/örüntü) cevap formatı olarak AÇIK UÇLUDUR,
  // şıkları yoktur. Eskiden `visual: true` sabitti → "Çoktan seçmeli" seçen kullanıcıya
  // şıksız sorular geliyordu (canlı ölçüm: 6 sorunun 3'ü şıksız). Artık görsel havuz
  // yalnız açık uçlu da isteniyorsa açılıyor; kullanıcı yine doğrudan seçemiyor.
  const effective: Record<TypeGroupKey, boolean> = { ...groups, visual: groups.open_ended };
  const enabledKeys = (Object.keys(effective) as TypeGroupKey[]).filter(
    (k) => effective[k],
  );
  // Tüm gruplar açıksa (görsel dahil) kısıtlama yok → null (backend tüm tipleri kullanır).
  if (enabledKeys.length === Object.keys(QUESTION_TYPE_GROUPS).length)
    return null;
  // Ders süzgeci: gruplar matematik tiplerinden oluşuyor; başka bir derste
  // desteklenmeyenler düşer (hepsi düşerse null = dersin varsayılan dağılımı).
  return filterTypesForSubject(
    subject,
    enabledKeys.flatMap((k) => QUESTION_TYPE_GROUPS[k] as QuestionType[]),
  );
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

export function GenerateForm({
  initialGrade,
  initialUnitId,
  initialKazanim,
  initialSubject,
}: {
  initialGrade?: number;
  initialUnitId?: string;
  initialKazanim?: string;
  initialSubject?: Subject;
} = {}) {
  const {
    subject,
    grade,
    unitId,
    kazanimKod,
    difficulty,
    questionCount,
    typeGroups,
    difficultyMode,
    includeAnswerKey,
    includeSolutions,
    brandName,
    brandSubtitle,
    brandLogo,
    status,
    setForm,
    startGenerate,
    setStreamedCount,
    setSuccess,
    setError,
  } = useGenerateStore();

  const { userId } = useAuth();
  // Kota aşımı (402) → paywall. billing_enabled kapalıyken hiç tetiklenmez.
  const [paywall, setPaywall] = React.useState<QuotaInfo | null>(null);

  // SEO deep-link hidrasyonu (?grade=&topic=&kazanim=) — bir kez, mount'ta.
  // URL niyeti, localStorage'a persist edilmiş son seçimi EZER (kullanıcı SEO'dan
  // belirli bir sınıf/konu için geldi). Ayrıca huni ölçümü için form'a varış
  // event'i atılır → cta_generate_click ile arası = auth-duvarı kaybı.
  const hydratedRef = React.useRef(false);
  React.useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;
    const patch: Partial<FormState> = {};
    if (initialGrade) patch.grade = initialGrade;
    if (initialUnitId) patch.unitId = initialUnitId;
    if (initialKazanim) patch.kazanimKod = initialKazanim;
    // Ders: deep-link fen (flag açıksa) uygula; flag kapalıyken persist edilmiş
    // fen'i matematik'e düşür (güvenlik). Fen sınıf aralığı 3-8 → geçersiz sınıfı düzelt.
    // Deep-link ders (flag açıksa uygula); flag kapalı/geçersiz persist → matematik.
    if (initialSubject && isSubjectEnabled(initialSubject)) patch.subject = initialSubject;
    if (!patch.subject && !isSubjectEnabled(subject)) patch.subject = "matematik";
    // Ders sınıf aralığı → geçersiz sınıfı geçerli varsayılana (5, tümünde geçerli) çek.
    const effSubject = patch.subject ?? subject;
    const effGrade = patch.grade ?? grade;
    if (effGrade < subjectMinGrade(effSubject)) patch.grade = 5;
    const fromDeeplink = Object.keys(patch).length > 0;
    if (fromDeeplink) setForm(patch);
    track("generate_page_view", {
      grade: patch.grade ?? grade,
      unit_id: patch.unitId ?? unitId,
      subject: patch.subject ?? subject,
      deeplink: fromDeeplink,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Dropdown verisi lokal müfredat snapshot'ından başlatılır → seçenekler ilk
  // render'da hazır gelir, Render backend'inin cold-start'ını beklemez (eski
  // "30-40 sn boş kalıyor" sorununun kök sebebi). Backend yine arka planda
  // yoklanıp olası drift'i düzeltir (aşağıdaki effect'ler).
  // Lokal snapshot yalnız matematik için var (JSON'lar math). Fen'de seçenekler
  // backend'den gelir (flag arkasında; cold-start'ta kısa boş kalabilir — kabul).
  const [grades, setGrades] = React.useState<GradeInfo[]>(() =>
    subject === "matematik" ? getGradesLocal() : [],
  );
  const [units, setUnits] = React.useState<UnitInfo[]>(() =>
    subject === "matematik" ? getUnitsLocal(grade) : [],
  );
  const [kazanimlar, setKazanimlar] = React.useState<KazanimInfo[]>(() =>
    subject === "matematik" && unitId
      ? getKazanimlarByUnitLocal(grade, unitId)
      : [],
  );
  // Progressive disclosure: gelişmiş ayarlar varsayılan kapalı. İlk kullanıcı
  // 5 alanlı (sınıf/konu/kazanım/zorluk/sayı) sade ekranla karşılaşır;
  // detay isteyen "▾ Gelişmiş ayarlar"ı açar.
  const [advancedOpen, setAdvancedOpen] = React.useState(false);

  // Default-dışı kaç ayar var? Kapalıyken kullanıcı bilsin diye badge'le göster.
  const advancedChangeCount = React.useMemo(() => {
    let n = 0;
    if (difficultyMode !== "single") n++;
    if (
      !typeGroups.open_ended ||
      !typeGroups.multiple_choice ||
      !typeGroups.other_format
    )
      n++;
    if (!includeAnswerKey) n++;
    if (!includeSolutions) n++;
    if (brandName.trim() || brandSubtitle.trim() || brandLogo) n++;
    return n;
  }, [
    difficultyMode,
    typeGroups,
    includeAnswerKey,
    includeSolutions,
    brandName,
    brandSubtitle,
    brandLogo,
  ]);

  // Aşağıdaki üç effect lokal listeyi backend'le senkronlar. Backend boş/hatalı
  // dönerse (ör. cold-start sırasında) lokal snapshot korunur — seçenekler asla
  // boşalmaz. Yalnız dolu bir yanıt geldiğinde üzerine yazılır.
  React.useEffect(() => {
    setGrades(subject === "matematik" ? getGradesLocal() : []);
    listGrades(subject)
      .then((g) => {
        if (g.length) setGrades(g);
      })
      .catch(() => {});
  }, [subject]);

  React.useEffect(() => {
    setUnits(subject === "matematik" ? getUnitsLocal(grade) : []);
    listUnits(grade, subject)
      .then((u) => {
        if (u.length) setUnits(u);
      })
      .catch(() => {});
  }, [grade, subject]);

  // unitId boş/geçersizse (ilk açılış, sınıf değişimi, eski persist) sınıfın ilk
  // ünitesini otomatik seç → dropdown asla boş kalmaz, üretim hep geçerli çalışır.
  React.useEffect(() => {
    if (units.length === 0) return;
    if (!unitId || !units.some((u) => u.unit_id === unitId)) {
      setForm({ unitId: units[0].unit_id, kazanimKod: null });
    }
  }, [units, unitId, setForm]);

  React.useEffect(() => {
    if (!unitId) {
      setKazanimlar([]);
      return;
    }
    setKazanimlar(
      subject === "matematik" ? getKazanimlarByUnitLocal(grade, unitId) : [],
    );
    listKazanimlarByUnit(grade, unitId, subject)
      .then((k) => {
        if (k.length) setKazanimlar(k);
      })
      .catch(() => {});
  }, [grade, unitId, subject]);

  const isLoading = status === "loading";
  // Görsel grubu artık kullanıcı seçimi değil (sunucu oranı); kullanıcıya görünen
  // gruplardan (açık uçlu / çoktan seçmeli / diğer) en az biri açık olmalı.
  const anyTypeGroupOn =
    typeGroups.open_ended ||
    typeGroups.multiple_choice ||
    typeGroups.other_format;

  const logoInputRef = React.useRef<HTMLInputElement>(null);

  function onLogoChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // aynı dosya tekrar seçilebilsin
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      toast.error("Geçersiz dosya", {
        description: "Lütfen bir görsel (PNG/JPG) seçin.",
      });
      return;
    }
    if (file.size > 500 * 1024) {
      toast.error("Logo çok büyük", {
        description: "En fazla 500 KB. Daha küçük bir görsel seçin.",
      });
      return;
    }
    const reader = new FileReader();
    reader.onload = () =>
      setForm({
        brandLogo: typeof reader.result === "string" ? reader.result : "",
      });
    reader.onerror = () => toast.error("Logo okunamadı");
    reader.readAsDataURL(file);
  }

  // Ders değişiminde sınıf/ünite/kazanım sıfırlanır. Fen 3-8 → matematik'ten
  // fen'e geçerken sınıf 3'ün altındaysa geçerli bir varsayılana (5) çek.
  function onSubjectChange(next: Subject) {
    const nextGrade = grade < subjectMinGrade(next) ? 5 : grade;
    setForm({
      subject: next,
      grade: nextGrade,
      unitId: null,
      kazanimKod: null,
    });
  }

  async function onGenerate() {
    if (!anyTypeGroupOn) {
      toast.error("Soru tipi seçimi", {
        description: "En az bir tip grubu açık olmalı.",
      });
      return;
    }
    // Anonim üretime izin verilir (tenant_id null → backend history'ye yazmaz,
    // rate-limit IP bazlı). Giriş yapıldıysa tenant_id = userId → üretim hesaba
    // kaydedilir ve geçmişte görünür. PDF indirme anonimde üyelik kapısında
    // (QuestionPreview).
    startGenerate();
    // Funnel: aktivasyon adımının başlangıcı.
    track("worksheet_generate_start", {
      grade,
      unit_id: unitId,
      difficulty,
      difficulty_mode: difficultyMode,
      question_count: questionCount,
    });
    const t0 = performance.now();
    try {
      const question_types = flattenTypeGroups(typeGroups, subject);
      // SSE streaming: bağlantı her soru event'iyle canlı kalır → uzun üretimde
      // proxy/tarayıcı idle-timeout'u tetiklenmez ("hata aldım ama geçmişte var"
      // sorununun kök sebebi). `complete` event'i bloklayan endpoint ile aynı
      // GenerateWorksheetResponse'u döner.
      const res = await generateWorksheetStream(
        {
          grade,
          subject,
          unit_id: unitId,
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
        unit_id: unitId,
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
          unit_id: unitId,
          kazanim_kod: kazanimKod,
          difficulty,
          question_count: questionCount,
        },
        res,
      );
      // Cache durumu kullanıcıya gösterilmez — yanıltıcı olabiliyordu (kısmi
      // cache hit'te yine de uzun bekleyip "Önbellekten" görmek hoş değil).
      // cache_hit yalnız GA4'e (kapasite ölçümü) gider.
      toast.success("Üretim tamamlandı", {
        description: `${res.worksheet.questions.length} soru üretildi ve denetimden geçti.`,
      });
    } catch (e: unknown) {
      // Kota aşımı (402) → jenerik hata yerine paywall göster (güven-önce).
      if (e instanceof QuotaExceededError) {
        setPaywall(e.info);
        track("worksheet_generate_paywall", {
          grade,
          unit_id: unitId,
          plan: e.info.plan ?? "free",
        });
        return;
      }
      // Akış kesildiyse (bağlantı/timeout — özellikle mobil/uygulama-içi tarayıcı):
      // backend üretimi bitirip geçmişe kaydetmiş olabilir → loading'de kalıp
      // geçmişten kurtarmayı dene. Başarısızsa gerçek hata göster.
      if (e instanceof StreamIncompleteError && userId) {
        const recovered = await recoverFromHistory(userId, {
          grade,
          unit_id: unitId,
          difficulty,
          question_count: questionCount,
        });
        if (recovered) {
          setSuccess(recovered);
          addHistory(
            { grade, unit_id: unitId, kazanim_kod: kazanimKod, difficulty, question_count: questionCount },
            recovered,
          );
          track("worksheet_generate_recovered", {
            grade,
            unit_id: unitId,
            duration_ms: Math.round(performance.now() - t0),
          });
          toast.success("Üretim tamamlandı", {
            description: `Bağlantı bir an koptu ama ${recovered.worksheet.questions.length} soruluk çalışma kağıdın hazır.`,
          });
          return;
        }
      }
      const msg = e instanceof Error ? e.message : "Bilinmeyen hata";
      track("worksheet_generate_error", {
        grade,
        unit_id: unitId,
        message: msg.slice(0, 120),
        duration_ms: Math.round(performance.now() - t0),
      });
      setError(msg);
      toast.error("Üretim başarısız", {
        description:
          e instanceof StreamIncompleteError
            ? "Bağlantı koptu ve kağıt bulunamadı. Geçmiş sayfanı kontrol et veya tekrar dene."
            : msg,
      });
    }
  }

  return (
    <div className="space-y-6">
      <Paywall
        open={paywall !== null}
        onOpenChange={(o) => !o && setPaywall(null)}
        info={paywall}
      />
      {/* ── Ders seçici (yalnız birden çok ders açıksa görünür) ─────────── */}
      {hasMultipleSubjects() ? (
        <div className="space-y-1.5">
          <Label htmlFor="subject">Ders</Label>
          <Select
            value={subject}
            onValueChange={(v) => onSubjectChange(v as Subject)}
          >
            <SelectTrigger id="subject" className="md:max-w-xs">
              <SelectValue placeholder="Ders seçin" />
            </SelectTrigger>
            <SelectContent>
              {availableSubjects().map((s) => (
                <SelectItem key={s.value} value={s.value}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ) : null}

      {/* ── Row 1: Sınıf / Konu / Kazanım ──────────────────────────────── */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="grade">Sınıf</Label>
          <Select
            value={String(grade)}
            onValueChange={(v) =>
              setForm({ grade: Number(v), unitId: null, kazanimKod: null })
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
          <Label htmlFor="unit">Ünite</Label>
          <Select
            value={unitId ?? ""}
            onValueChange={(v) => setForm({ unitId: v, kazanimKod: null })}
            disabled={units.length === 0}
          >
            <SelectTrigger id="unit">
              <SelectValue placeholder="Ünite seçin" />
            </SelectTrigger>
            <SelectContent>
              {units.map((u) => (
                <SelectItem key={u.unit_id} value={u.unit_id}>
                  {u.no}. {u.name}{" "}
                  <span className="text-xs text-muted-foreground">
                    · {u.kazanim_count} kazanım
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
                hint="Hangi tipler üretim havuzunda olsun? En az bir grup açık olmalı. (Görselli sorular konuya göre otomatik eklenir.)"
              />
              <div className="grid gap-3 md:grid-cols-2">
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

            {/* PDF markalama (white-label) */}
            <div className="space-y-2.5">
              <SectionTitle
                title="PDF markalama (kurum/öğretmen)"
                hint="PDF'in üst bilgisine kurum veya öğretmen adı eklenir. Bir kez girince kaydedilir."
              />
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="brandName">Kurum / öğretmen adı</Label>
                  <Input
                    id="brandName"
                    value={brandName}
                    maxLength={80}
                    placeholder="ör. Atatürk Ortaokulu"
                    onChange={(e) => setForm({ brandName: e.target.value })}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="brandSubtitle">Alt satır (opsiyonel)</Label>
                  <Input
                    id="brandSubtitle"
                    value={brandSubtitle}
                    maxLength={60}
                    placeholder="ör. 5-A Sınıfı · Ahmet Öğretmen"
                    onChange={(e) => setForm({ brandSubtitle: e.target.value })}
                  />
                </div>
              </div>

              {/* Logo (opsiyonel) — PDF üst bilgisinde adın yanında görünür. */}
              <div className="space-y-1.5">
                <Label>Logo (opsiyonel)</Label>
                <div className="flex flex-wrap items-center gap-3">
                  {brandLogo ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={brandLogo}
                      alt="Logo önizleme"
                      className="h-10 w-auto max-w-[120px] rounded border bg-white object-contain p-1"
                    />
                  ) : null}
                  <input
                    ref={logoInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    className="hidden"
                    onChange={onLogoChange}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => logoInputRef.current?.click()}
                  >
                    {brandLogo ? "Logoyu değiştir" : "Logo seç"}
                  </Button>
                  {brandLogo ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => setForm({ brandLogo: "" })}
                    >
                      Kaldır
                    </Button>
                  ) : null}
                </div>
                <p className="text-[11px] text-muted-foreground">
                  PNG/JPG, en fazla 500 KB. Cihazında saklanır, her PDF&apos;e
                  basılır.
                </p>
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
          disabled={isLoading || !unitId || !anyTypeGroupOn}
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
