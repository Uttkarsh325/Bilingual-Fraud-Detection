"use client";

import { useEffect, useRef } from "react";
import { Loader2, ShieldCheck } from "lucide-react";
import type { ChatMessage, SupportedLanguage } from "@/lib/types";
import MessageBubble from "./MessageBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  sessionId: string;
  language: SupportedLanguage;
}

export default function ChatWindow({
  messages,
  isLoading,
  sessionId,
  language,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      {isEmpty && !isLoading ? (
        /* Empty state */
        <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-6">
          <div className="w-16 h-16 rounded-2xl bg-brand-900/50 flex items-center justify-center">
            <ShieldCheck className="w-8 h-8 text-brand-400" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-slate-200 mb-2">
              Got a suspicious message?
            </h2>
            <p className="text-slate-400 text-sm max-w-sm">
              Paste it below or describe it in your own words — in{" "}
              <span className="text-brand-300">{language.nativeName}</span> or English. I&apos;ll
              analyse it against verified RBI &amp; NPCI advisories.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 mt-2">
            {[
              "Is this UPI request safe?",
              "I got a KYC update SMS",
              "Someone asked for my OTP",
            ].map((hint) => (
              <span
                key={hint}
                className="px-3 py-1.5 rounded-full bg-slate-800 text-slate-400 text-xs border border-slate-700"
              >
                {hint}
              </span>
            ))}
          </div>
        </div>
      ) : (
        <div className="max-w-3xl mx-auto flex flex-col gap-4">
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              sessionId={sessionId}
              languageCode={language.code}
            />
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center flex-shrink-0">
                <ShieldCheck className="w-4 h-4 text-white" />
              </div>
              <div className="bg-slate-800 border border-slate-700/50 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />
                <span className="text-slate-400 text-sm">Analysing…</span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}
