import { QuizSolver } from "@/components/QuizSolver";

export default async function CozQuizPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <QuizSolver quizId={id} />;
}
