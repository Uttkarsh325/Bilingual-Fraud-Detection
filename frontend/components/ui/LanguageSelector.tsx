"use client";

import { Globe } from "lucide-react";
import { SUPPORTED_LANGUAGES, type SupportedLanguage } from "@/lib/types";

interface LanguageSelectorProps {
  selected: SupportedLanguage;
  onChange: (lang: SupportedLanguage) => void;
}

export default function LanguageSelector({ selected, onChange }: LanguageSelectorProps) {
  return (
    <div className="relative">
      <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
        <Globe className="w-4 h-4 text-slate-400" />
      </div>
      <select
        value={selected.code}
        onChange={(e) => {
          const lang = SUPPORTED_LANGUAGES.find((l) => l.code === e.target.value);
          if (lang) onChange(lang);
        }}
        className="pl-9 pr-8 py-2 bg-slate-800 border border-slate-700 rounded-xl text-sm
                   text-slate-100 focus:outline-none focus:ring-2 focus:ring-brand-500
                   appearance-none cursor-pointer"
        aria-label="Select language"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.nativeName} ({lang.name})
          </option>
        ))}
      </select>
    </div>
  );
}
