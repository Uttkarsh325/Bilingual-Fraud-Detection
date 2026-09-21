import type { Metadata } from "next";
import AuthForm from "@/components/auth/AuthForm";

export const metadata: Metadata = {
  title: "Sign In — FraudGuard AI",
  description: "Sign in to FraudGuard AI",
};

export default function LoginPage() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6 py-16">
      <AuthForm mode="login" />
    </div>
  );
}