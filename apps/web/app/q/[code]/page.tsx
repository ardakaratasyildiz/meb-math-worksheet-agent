import { QuizSolver } from "@/components/QuizSolver";

// Public paylaşılan quiz çözme: /q/[code]. Misafir de çözebilir (login gerekmez).
export default async function SharedQuizPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const { code } = await params;
  return <QuizSolver shareCode={code} />;
}
