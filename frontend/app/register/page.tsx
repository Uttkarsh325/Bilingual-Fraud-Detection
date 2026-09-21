import type { Metadata } from "next";
import AuthForm from "@/components/auth/AuthForm";

export const metadata: Metadata = {
  title: "Register — FraudGuard AI",
  description: "Create a FraudGuard AI account",
};

export default function RegisterPage() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 py-16">
      <AuthForm mode="register" />
    </div>
  );
}