import { Flame } from "lucide-react";
import Link from "next/link";

import { LoginForm } from "@/components/auth/LoginForm";

export const metadata = {
  title: "Log in — Resume Roaster",
};

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <div
        className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-24 mx-auto h-96 max-w-3xl"
        aria-hidden
      />
      <Link
        href="/"
        className="relative mb-8 flex items-center gap-2.5 text-lg font-semibold"
      >
        <span className="flex size-9 items-center justify-center rounded-xl bg-primary/15 text-primary">
          <Flame className="size-5" />
        </span>
        Resume Roaster
      </Link>
      <div className="glass-card relative mx-auto w-full max-w-sm rounded-2xl p-1">
        <LoginForm />
      </div>
    </div>
  );
}
