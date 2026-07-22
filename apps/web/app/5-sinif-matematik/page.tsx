import { GradeMathHub, gradeMathMetadata } from "@/components/GradeMathHub";

export const metadata = gradeMathMetadata(5);

export default function Grade5MathHubPage() {
  return <GradeMathHub grade={5} />;
}
