import { Flame } from "lucide-react";
import Link from "next/link";

import { RegisterForm } from "@/components/auth/RegisterForm";

export const metadata = {
  title: "Register — Resume Roaster",
};

export default function RegisterPage() {
  return (
    <div className="relative flex min-h-screen flex-col items-center px-4 pt-16 pb-12">
      <div
        className="bg-glow-ember pointer-events-none absolute inset-x-0 -top-24 mx-auto h-96 max-w-3xl"
        aria-hidden
      />
      <Link
        href="/"
        className="relative mb-6 flex items-center gap-2.5 font-heading text-lg font-bold tracking-tight"
      >
        <span className="flex size-9 items-center justify-center rounded-xl bg-primary/15 text-primary">
          <Flame className="size-5" />
        </span>
        Resume Roaster
      </Link>
      <div className="relative mx-auto w-full max-w-sm">
        <RegisterForm />
      </div>
    </div>
  );
}
