import { subjectLabel, subjectStyle } from "@/lib/subjects";
import type { Subject } from "@/lib/types";

/**
 * Ders rozeti — renk + emoji + ad. Ortak görsel dil (lib/subjects → subjectStyle).
 * İlerleme, geçmiş, quiz gibi ders bağlamı gösteren her yerde kullanılır.
 */
export function SubjectBadge({
  subject,
  size = "md",
}: {
  subject: Subject;
  size?: "sm" | "md";
}) {
  const st = subjectStyle(subject);
  const pad =
    size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${pad} ${st.bg} ${st.text} ${st.border}`}
    >
      <span aria-hidden>{st.emoji}</span>
      {subjectLabel(subject)}
    </span>
  );
}
