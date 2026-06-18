import { GradeMathHub, gradeMathMetadata } from "@/components/GradeMathHub";

export const metadata = gradeMathMetadata(6);

export default function Grade6MathHubPage() {
  return <GradeMathHub grade={6} />;
}
