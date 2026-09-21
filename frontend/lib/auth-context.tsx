"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { getStoredUsername } from "@/lib/auth";

export type AuthMode = "login" | "register";

interface AuthContextValue {
  authenticated: boolean;
  username: string | null;
  modalOpen: boolean;
  modalMode: AuthMode;
  openAuth: (mode?: AuthMode) => void;
  closeAuth: () => void;
  setSession: (username: string) => void;
  clearSession: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<AuthMode>("login");

  // Hydrate auth state on the client only. Reading localStorage during the
  // initial render would make the first client render differ from the SSR
  // markup (server has no localStorage), causing a hydration mismatch.
  useEffect(() => {
    setUsername(getStoredUsername());
  }, []);

  const openAuth = useCallback((mode: AuthMode = "login") => {
    setModalMode(mode);
    setModalOpen(true);
  }, []);

  const closeAuth = useCallback(() => setModalOpen(false), []);

  const setSession = useCallback((user: string) => setUsername(user), []);
  const clearSession = useCallback(() => setUsername(null), []);

  return (
    <AuthContext.Provider
      value={{
        authenticated: Boolean(username),
        username,
        modalOpen,
        modalMode,
        openAuth,
        closeAuth,
        setSession,
        clearSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}