import { GradeMathHub, gradeMathMetadata } from "@/components/GradeMathHub";

export const metadata = gradeMathMetadata(7);

export default function Grade7MathHubPage() {
  return <GradeMathHub grade={7} />;
}
