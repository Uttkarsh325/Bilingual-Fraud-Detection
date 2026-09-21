"use client";

import { useState } from "react";
import Link from "next/link";
import { LogIn, UserPlus, ShieldCheck } from "lucide-react";
import toast from "react-hot-toast";
import { login, registerUser } from "@/lib/api/auth";
import { storeAuth } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

interface AuthFormProps {
  mode: "login" | "register";
  embedded?: boolean;
  onSuccess?: (username: string) => void;
}

export default function AuthForm({ mode, embedded = false, onSuccess }: AuthFormProps) {
  const { openAuth } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const isLogin = mode === "login";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;

    setSubmitting(true);
    try {
      const result = isLogin
        ? await login(username.trim(), password)
        : await registerUser(username.trim(), password);

      storeAuth(result.access_token, result.username);
      toast.success(`Welcome${isLogin ? " back" : ""}, ${result.username}!`);

      if (embedded && onSuccess) {
        onSuccess(result.username);
        return;
      }

      window.location.href = "/chat";
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      toast.error(message);
      setSubmitting(false);
    }
  };

  const switchMode = (next: "login" | "register") => {
    if (embedded) {
      openAuth(next);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="glass-card p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-brand-600 flex items-center justify-center mb-4">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-slate-50">
            {isLogin ? "Welcome back" : "Create your account"}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            {isLogin
              ? "Sign in to analyse messages and get fraud advisories."
              : "Free account — your conversations stay private."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="username" className="text-sm text-slate-300 font-medium">
              Username
            </label>
            <input
              id="username"
              type="text"
              required
              minLength={3}
              maxLength={50}
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field"
              placeholder="e.g. rahul_99"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-sm text-slate-300 font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={6}
              maxLength={128}
              autoComplete={isLogin ? "current-password" : "new-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field"
              placeholder="At least 6 characters"
            />
          </div>

          <button type="submit" disabled={submitting} className="btn-primary w-full justify-center mt-2 text-base py-2.5">
            {isLogin ? <LogIn className="w-5 h-5" /> : <UserPlus className="w-5 h-5" />}
            {submitting ? "Please wait…" : isLogin ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p className="text-sm text-slate-400 text-center mt-6">
          {isLogin ? (
            <>
              Don&apos;t have an account?{" "}
              {embedded ? (
                <button type="button" onClick={() => switchMode("register")} className="text-brand-400 hover:text-brand-300 font-medium">
                  Register
                </button>
              ) : (
                <Link href="/register" className="text-brand-400 hover:text-brand-300 font-medium">
                  Register
                </Link>
              )}
            </>
          ) : (
            <>
              Already have an account?{" "}
              {embedded ? (
                <button type="button" onClick={() => switchMode("login")} className="text-brand-400 hover:text-brand-300 font-medium">
                  Sign in
                </button>
              ) : (
                <Link href="/login" className="text-brand-400 hover:text-brand-300 font-medium">
                  Sign in
                </Link>
              )}
            </>
          )}
        </p>
      </div>
    </div>
  );
}