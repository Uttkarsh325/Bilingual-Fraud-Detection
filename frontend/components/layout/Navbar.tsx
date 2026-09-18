"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ShieldCheck, MessageSquare, Mic, Menu, X } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

const NAV_LINKS = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/voice", label: "Voice", icon: Mic },
];

export default function Navbar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

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
        </div>
      )}
    </header>
  );
}
