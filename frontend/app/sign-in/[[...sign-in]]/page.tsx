import { SignIn } from "@clerk/nextjs";

export const metadata = {
  title: "Giriş yap · SheetGen",
};

export default function SignInPage() {
  return (
    <div className="container flex min-h-[calc(100vh-3.5rem)] items-center justify-center py-10">
      <SignIn />
    </div>
  );
}
