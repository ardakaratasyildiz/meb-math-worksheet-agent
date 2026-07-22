import { GradeMathHub, gradeMathMetadata } from "@/components/GradeMathHub";

export const metadata = gradeMathMetadata(3);

export default function Grade3MathHubPage() {
  return <GradeMathHub grade={3} />;
}
