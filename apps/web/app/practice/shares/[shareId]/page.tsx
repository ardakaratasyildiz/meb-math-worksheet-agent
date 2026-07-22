import { ShareResultsView } from "@/components/ShareResultsView";

export default async function ShareResultsPage({
  params,
}: {
  params: Promise<{ shareId: string }>;
}) {
  const { shareId } = await params;
  return <ShareResultsView shareId={shareId} />;
}
