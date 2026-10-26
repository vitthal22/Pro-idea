import { RegisterForm } from "@/components/auth/RegisterForm";

export const metadata = {
  title: "Register — Resume Roaster",
};

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <RegisterForm />
    </div>
  );
}
