import { QuizSolver } from "@/components/QuizSolver";

// Ödev çözme: /practice/assignments/[id]. Login zorunlu (middleware /practice).
export default async function AssignmentSolvePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <QuizSolver assignmentId={id} />;
}
