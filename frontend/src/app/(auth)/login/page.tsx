import { LoginForm } from "@/components/auth/LoginForm";

export const metadata = {
  title: "Log in — Resume Roaster",
};

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <LoginForm />
    </div>
  );
}
