"use client";

import * as React from "react";
import { CheckCircle2 } from "lucide-react";

import { availableSubjects, subjectStyle } from "@/lib/subjects";
import { SUBJECT_SHOWCASE } from "@/lib/subject-showcase";

/**
 * Hero (ana sayfa) sağ görseli — ders kartı "fanı".
 *
 * Çok-ders açıkken (page.tsx `multi`) hero'da tek statik matematik kartı yerine
 * mevcut derslerin örnek soru kartları yelpaze gibi dizilir; öndeki otomatik döner,
 * tıklanınca öne gelir. Renk kodu tüm uygulamayla ortak (lib/subjects → subjectStyle),
 * örnekler subject-showcase.ts'ten (gerçek üretime hizalı, elle doğrulanmış kesit).
 *
 * Tasarım kararı (demo "B + A metni"): kartlar kompakt — başlık + soru + cevap
 * satırı (şıklar hero'da gösterilmez, yer için). Maskot (🦊) üstte zıplar.
 */
export function HeroSubjectFan() {
  const subjects = React.useMemo(() => availableSubjects(), []);
  const n = subjects.length;
  const [active, setActive] = React.useState(0);

  // Öndeki kartı ~2.8sn'de bir döndür (reduced-motion'da durdur).
  React.useEffect(() => {
    if (n <= 1) return;
    const prefersReduced =
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (prefersReduced) return;
    const t = setInterval(() => setActive((a) => (a + 1) % n), 2800);
    return () => clearInterval(t);
  }, [n]);

  return (
    <div className="relative mx-auto h-[380px] max-w-[460px]">
      {/* Maskot */}
      <div
        aria-hidden
        className="absolute -left-3 -top-7 z-30 animate-bob text-5xl drop-shadow-md"
      >
        🦊
      </div>

      {subjects.map((s, idx) => {
        const st = subjectStyle(s.value);
        const q = (SUBJECT_SHOWCASE[s.value] ?? [])[0];
        if (!q) return null;

        // Simetrik ofset: aktif kart merkezde (0), diğerleri iki yana yelpaze.
        let off = idx - active;
        if (off > n / 2) off -= n;
        if (off < -n / 2) off += n;
        const abs = Math.abs(off);

        return (
          <button
            key={s.value}
            type="button"
            onClick={() => setActive(idx)}
            aria-label={`${s.label} örnek sorusu`}
            className="absolute left-1/2 top-5 w-[340px] -ml-[170px] rounded-2xl border border-border bg-card p-5 text-left shadow-pop transition-all duration-500 ease-out"
            style={{
              borderTop: `5px solid ${st.hex}`,
              transform: `rotate(${off * 5}deg) translateY(${abs * 8}px) scale(${1 - abs * 0.04})`,
              transformOrigin: "bottom center",
              opacity: 1 - abs * 0.28,
              zIndex: 20 - abs,
            }}
          >
            <div className="flex items-center gap-2 text-xs font-bold">
              <span
                className="inline-flex items-center gap-1.5"
                style={{ color: st.hex }}
              >
                <span aria-hidden className="text-sm">
                  {st.emoji}
                </span>
                {q.gradeLabel}
              </span>
              <span
                className="ml-auto rounded-full px-2.5 py-1 font-mono text-[10px]"
                style={{ background: `${st.hex}1f`, color: st.hex }}
              >
                {q.kazanim}
              </span>
            </div>

            <p className="mt-3 line-clamp-3 text-sm font-medium leading-relaxed text-foreground">
              {q.question}
            </p>

            <div
              className="mt-4 flex items-center gap-1.5 border-t border-dashed pt-3 text-[11px] font-bold"
              style={{ color: st.hex }}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              Cevap anahtarı · adım adım çözüm
            </div>
          </button>
        );
      })}
    </div>
  );
}
