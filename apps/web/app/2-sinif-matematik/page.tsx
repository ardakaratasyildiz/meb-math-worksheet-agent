import { GradeMathHub, gradeMathMetadata } from "@/components/GradeMathHub";

export const metadata = gradeMathMetadata(2);

export default function Grade2MathHubPage() {
  return <GradeMathHub grade={2} />;
}
