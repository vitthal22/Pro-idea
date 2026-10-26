"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AuthError, useRegister } from "@/hooks/queries/use-auth";

const registerSchema = z
  .object({
    name: z.string().min(1, "Name is required"),
    email: z.email("Enter a valid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type FieldName = "name" | "email" | "password" | "confirmPassword";

export function RegisterForm() {
  const router = useRouter();
  const register = useRegister();
  const [values, setValues] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<FieldName, string>>>(
    {},
  );
  const [submitError, setSubmitError] = useState<string | null>(null);

  function setField(field: FieldName, value: string) {
    setValues((v) => ({ ...v, [field]: value }));
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    const parsed = registerSchema.safeParse(values);
    if (!parsed.success) {
      const errors: Partial<Record<FieldName, string>> = {};
      for (const issue of parsed.error.issues) {
        const key = issue.path[0];
        if (
          key === "name" ||
          key === "email" ||
          key === "password" ||
          key === "confirmPassword"
        ) {
          errors[key] ??= issue.message;
        }
      }
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});

    try {
      await register.mutateAsync({
        name: parsed.data.name,
        email: parsed.data.email,
        password: parsed.data.password,
      });
      toast.success("Account created. Welcome!");
      router.push("/dashboard");
    } catch (error) {
      setSubmitError(
        error instanceof AuthError
          ? error.message
          : "Registration failed. Please try again.",
      );
    }
  }

  const fields: Array<{
    name: FieldName;
    label: string;
    type: string;
    autoComplete: string;
  }> = [
    { name: "name", label: "Name", type: "text", autoComplete: "name" },
    {
      name: "email",
      label: "Email",
      type: "email",
      autoComplete: "email",
    },
    {
      name: "password",
      label: "Password",
      type: "password",
      autoComplete: "new-password",
    },
    {
      name: "confirmPassword",
      label: "Confirm password",
      type: "password",
      autoComplete: "new-password",
    },
  ];

  return (
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-2xl">Create an account</CardTitle>
        <CardDescription>
          Sign up to start roasting your resume.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="grid gap-4" noValidate>
          {fields.map((field) => (
            <div key={field.name} className="grid gap-2">
              <Label htmlFor={field.name}>{field.label}</Label>
              <Input
                id={field.name}
                type={field.type}
                autoComplete={field.autoComplete}
                value={values[field.name]}
                onChange={(e) => setField(field.name, e.target.value)}
              />
              {fieldErrors[field.name] ? (
                <p className="text-sm text-destructive">
                  {fieldErrors[field.name]}
                </p>
              ) : null}
            </div>
          ))}
          {submitError ? (
            <p className="text-sm text-destructive">{submitError}</p>
          ) : null}
          <Button type="submit" disabled={register.isPending}>
            {register.isPending ? "Creating account..." : "Register"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="underline underline-offset-4">
            Log in
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
