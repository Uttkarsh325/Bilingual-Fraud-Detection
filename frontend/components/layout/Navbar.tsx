"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ShieldCheck, MessageSquare, Mic, Menu, X, LogIn, LogOut, User } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";
import { clearAuth } from "@/lib/auth";
import { useAuth } from "@/lib/auth-context";

const NAV_LINKS = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/voice", label: "Voice", icon: Mic },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const { username, openAuth, clearSession } = useAuth();

  const handleLogout = () => {
    clearAuth();
    clearSession();
    setMenuOpen(false);
    router.push("/");
    router.refresh();
  };

  return (
    <header className="h-16 sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50">
      <div className="max-w-6xl mx-auto px-6 h-full flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 font-bold text-lg text-slate-50">
          <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <span>FraudGuard AI</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden sm:flex items-center gap-1">
          {NAV_LINKS.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                pathname === href
                  ? "bg-brand-700/40 text-brand-300"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}

          {username ? (
            <div className="flex items-center gap-1 ml-2">
              <span className="flex items-center gap-1.5 px-3 py-2 text-sm text-slate-300">
                <User className="w-4 h-4 text-brand-400" />
                {username}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-slate-400 hover:text-danger-400 hover:bg-slate-800 transition-all"
                aria-label="Log out"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          ) : (
            <button
              onClick={() => openAuth("login")}
              className="ml-2 flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-brand-600 hover:bg-brand-700 text-white transition-all"
            >
              <LogIn className="w-4 h-4" />
              Login
            </button>
          )}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="sm:hidden p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="sm:hidden bg-slate-900 border-b border-slate-700/50 px-6 py-4 flex flex-col gap-2">
          {NAV_LINKS.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMenuOpen(false)}
              className={clsx(
                "flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all",
                pathname === href
                  ? "bg-brand-700/40 text-brand-300"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-800"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}

          <div className="border-t border-slate-700/50 pt-2 mt-2">
            {username ? (
              <>
                <div className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-300">
                  <User className="w-4 h-4 text-brand-400" />
                  {username}
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-danger-400 hover:bg-slate-800"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </>
            ) : (
              <button
                onClick={() => {
                  setMenuOpen(false);
                  openAuth("login");
                }}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-brand-400 hover:text-brand-300"
              >
                <LogIn className="w-4 h-4" />
                Login
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
