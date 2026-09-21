"use client";

import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import clsx from "clsx";
import toast from "react-hot-toast";
import { Languages, ShieldCheck, User, Volume2 } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import ScamBadge from "@/components/ui/ScamBadge";
import SourceCitations from "@/components/ui/SourceCitations";
import { synthesizeSpeech, translateText } from "@/lib/api/chat";
import { useState } from "react";

interface MessageBubbleProps {
  message: ChatMessage;
  sessionId: string;
  languageCode: string;
}

// Indic script ranges for the languages we support — used to decide whether a
// response is worth offering to translate (e.g. Devanagari for Hindi/Marathi).
function isNonEnglish(text: string): boolean {
  return /[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF\u0B80-\u0BFF\u0C00-\u0C7F\u0C80-\u0CFF\u0D00-\u0D7F]/.test(
    text
  );
}

export default function MessageBubble({ message, sessionId, languageCode }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [translated, setTranslated] = useState<string | null>(null);
  const [translating, setTranslating] = useState(false);

  const handleSpeak = async () => {
    if (isSpeaking) return;
    setIsSpeaking(true);
    try {
      const { audio_url } = await synthesizeSpeech(
        message.content,
        languageCode,
        sessionId
      );
      const audio = new Audio(audio_url);
      audio.onended = () => setIsSpeaking(false);
      audio.onerror = () => setIsSpeaking(false);
      await audio.play();
    } catch {
      setIsSpeaking(false);
    }
  };

  const handleTranslate = async () => {
    if (translated) {
      setTranslated(null); // toggle back to original
      return;
    }
    setTranslating(true);
    try {
      const result = await translateText(message.content);
      setTranslated(result);
    } catch (err: unknown) {
      const detail =
        err instanceof Error ? err.message : "Translation failed";
      toast.error(detail);
    } finally {
      setTranslating(false);
    }
  };

  const showTranslate = !isUser && isNonEnglish(message.content);
  const displayContent = translated ?? message.content;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={clsx("flex gap-3", isUser ? "justify-end" : "justify-start")}
    >
      {/* Avatar — assistant only */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center">
          <ShieldCheck className="w-4 h-4 text-white" />
        </div>
      )}

      <div
        className={clsx(
          "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "bg-brand-700 text-white rounded-br-md"
            : "bg-slate-800 text-slate-100 rounded-bl-md border border-slate-700/50"
        )}
      >
        {/* Content */}
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose prose-invert prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
          </div>
        )}

        {/* Scam classification badge (assistant only) */}
        {!isUser && message.metadata?.scam_classification && (
          <ScamBadge classification={message.metadata.scam_classification} />
        )}

        {/* Source citations (assistant only) */}
        {!isUser &&
          message.metadata?.retrieved_sources &&
          message.metadata.retrieved_sources.length > 0 && (
            <SourceCitations sources={message.metadata.retrieved_sources} />
          )}

        {/* Footer row */}
        <div
          className={clsx(
            "flex items-center justify-between mt-2 gap-4",
            isUser ? "text-brand-200" : "text-slate-500"
          )}
        >
          <span className="text-xs">
            {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>

          {/* Translate toggle — Hindi/Indic responses → English */}
          <div className="flex items-center gap-3">
            {showTranslate && (
              <button
                onClick={handleTranslate}
                disabled={translating}
                title={translated ? "Show original" : "Translate to English"}
                aria-label={translated ? "Show original response" : "Translate to English"}
                className={clsx(
                  "flex items-center text-slate-500 hover:text-slate-300 transition-colors",
                  translated && "text-brand-400"
                )}
              >
                <Languages className={clsx("w-3.5 h-3.5", translating && "animate-pulse")} />
                <span className="ml-1 text-xs">
                  {translating ? "Translating…" : translated ? "Original" : "English"}
                </span>
              </button>
            )}

            {/* TTS play button — assistant only */}
            {!isUser && (
              <button
                onClick={handleSpeak}
                disabled={isSpeaking}
                title="Play response aloud"
                className={clsx(
                  "text-slate-500 hover:text-slate-300 transition-colors",
                  isSpeaking && "text-brand-400 animate-pulse"
                )}
                aria-label="Play response as audio"
              >
                <Volume2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Avatar — user only */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
          <User className="w-4 h-4 text-slate-300" />
        </div>
      )}
    </motion.div>
  );
}
