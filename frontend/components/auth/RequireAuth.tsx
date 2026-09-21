"use client";

import { useEffect } from "react";
import { useAuth } from "@/lib/auth-context";

/**
 * Guards client pages — opens the login modal when no user is authenticated.
 * Renders children only once the user is signed in.
 */
export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { authenticated, openAuth } = useAuth();

  useEffect(() => {
    if (!authenticated) {
      openAuth("login");
    }
  }, [authenticated, openAuth]);

  if (!authenticated) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="w-8 h-8 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  return <>{children}</>;
}