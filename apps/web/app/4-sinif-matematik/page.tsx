import { GradeMathHub, gradeMathMetadata } from "@/components/GradeMathHub";

export const metadata = gradeMathMetadata(4);

export default function Grade4MathHubPage() {
  return <GradeMathHub grade={4} />;
}
