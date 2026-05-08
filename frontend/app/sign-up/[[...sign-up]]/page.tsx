import { SignUp } from "@clerk/nextjs";

export const metadata = {
  title: "Kayıt ol · SheetGen",
};

export default function SignUpPage() {
  return (
    <div className="container flex min-h-[calc(100vh-3.5rem)] items-center justify-center py-10">
      <SignUp />
    </div>
  );
}
