"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import AuthForm from "./AuthForm";
import { useAuth } from "@/lib/auth-context";

/**
 * Full-screen login/register modal.
 * Blurs the page behind it with a dark, backdrop-blurred overlay.
 */
export default function AuthModal() {
  const { modalOpen, modalMode, closeAuth, setSession } = useAuth();

  useEffect(() => {
    if (!modalOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeAuth();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [modalOpen, closeAuth]);

  if (!modalOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
      {/* Blurred, dimmed backdrop */}
      <div
        className="absolute inset-0 bg-slate-950/70 backdrop-blur-md"
        onClick={closeAuth}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        className="relative w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={closeAuth}
          aria-label="Close"
          className="absolute top-4 right-4 z-10 p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
        <AuthForm
          mode={modalMode}
          embedded
          onSuccess={(username) => {
            setSession(username);
            closeAuth();
          }}
        />
      </div>
    </div>
  );
}