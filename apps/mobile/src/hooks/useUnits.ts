import type { SubjectSlug, UnitInfo } from "@soruatolyesi/shared";
import { useEffect, useState } from "react";

import { listUnits } from "@/lib/api";

/** Ders + sınıf değiştikçe MEB ünitelerini yükler. */
export function useUnits(grade: number, subject: SubjectSlug) {
  const [units, setUnits] = useState<UnitInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setUnits([]);
    setError(null);
    listUnits(grade, subject)
      .then((u) => {
        if (!cancelled) setUnits(u);
      })
      .catch((e) => {
        if (!cancelled) setError((e as Error).message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [grade, subject]);

  return { units, loading, error };
}
