import { GradeMathHub, gradeMathMetadata } from "@/components/GradeMathHub";

export const metadata = gradeMathMetadata(1);

export default function Grade1MathHubPage() {
  return <GradeMathHub grade={1} />;
}
