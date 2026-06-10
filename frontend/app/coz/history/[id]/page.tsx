import { AttemptDetailView } from "@/components/AttemptDetailView";

export default async function CozHistoryDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <AttemptDetailView attemptId={id} />;
}
