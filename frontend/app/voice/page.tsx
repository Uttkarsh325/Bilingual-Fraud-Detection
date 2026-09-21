"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { RotateCcw, ShieldCheck, TriangleAlert } from "lucide-react";
import { useConversation } from "@/lib/hooks/useConversation";
import { useAudioRecorder } from "@/lib/hooks/useAudioRecorder";
import VoiceOrb, { type VoiceOrbState } from "@/components/voice/VoiceOrb";
import MessageBubble from "@/components/chat/MessageBubble";
import LanguageSelector from "@/components/ui/LanguageSelector";
import ChatInput from "@/components/chat/ChatInput";
import RequireAuth from "@/components/auth/RequireAuth";
import SessionHistory from "@/components/sessions/SessionHistory";

export default function VoicePage() {
  return (
    <RequireAuth>
      <VoiceContent />
    </RequireAuth>
  );
}

function VoiceContent() {
  const {
    messages,
    isLoading,
    sessionId,
    selectedLanguage,
    sendMessage,
    sendAudio,
    setLanguage,
    resetConversation,
    error,
    loadSession,
  } = useConversation();

  const { status: recStatus, audioBlob, startRecording, stopRecording, resetRecording } =
    useAudioRecorder();

  const [orbState, setOrbState] = useState<VoiceOrbState>("idle");

  // Map recorder + conversation state → orb visual state
  useEffect(() => {
    if (recStatus === "recording") {
      setOrbState("recording");
    } else if (isLoading) {
      setOrbState("processing");
    } else {
      setOrbState("idle");
    }
  }, [recStatus, isLoading]);

  // When recording stops, forward blob to conversation hook
  useEffect(() => {
    if (recStatus === "stopped" && audioBlob) {
      sendAudio(audioBlob);
      resetRecording();
    }
  }, [recStatus, audioBlob, sendAudio, resetRecording]);

  // Last exchange: the most recent spoken (user) message + its assistant reply.
  // The reply must come AFTER the user message, otherwise an earlier assistant
  // message from a prior turn would be paired with the latest one.
  const lastUserIndex = messages.reduce(
    (acc, m, i) => (m.role === "user" ? i : acc),
    -1
  );
  const lastUserMessage = lastUserIndex >= 0 ? messages[lastUserIndex] : null;
  const repliesAfter = lastUserIndex >= 0
    ? messages.slice(lastUserIndex + 1).filter((m) => m.role === "assistant")
    : [];
  const lastAssistantMessage =
    repliesAfter.length > 0 ? repliesAfter[repliesAfter.length - 1] : null;

  const awaitingReply = Boolean(lastUserMessage) && !lastAssistantMessage && isLoading;
  const replyFailed = Boolean(lastUserMessage) && !lastAssistantMessage && !isLoading;

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Top bar */}
      <div className="flex items-center justify-between gap-4 px-4 py-3 border-b border-slate-700/50">
        <LanguageSelector selected={selectedLanguage} onChange={setLanguage} />
        <div className="flex items-center gap-2">
          <SessionHistory
            activeSessionId={sessionId}
            onLoadSession={loadSession}
            onNewSession={resetConversation}
          />
          <button
            onClick={resetConversation}
            className="btn-secondary text-xs py-1.5 px-3"
            aria-label="New conversation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Session</span>
          </button>
        </div>
      </div>

      {/* Voice orb + last reply */}
      <div className="flex flex-col items-center justify-center flex-1 gap-10 px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4 }}
        >
          <VoiceOrb
            state={orbState}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
          />
        </motion.div>

        {/* Spoken message first, then the analysis */}
        {lastUserMessage && (
          <div className="w-full max-w-xl flex flex-col gap-3">
            <MessageBubble
              message={lastUserMessage}
              sessionId={sessionId}
              languageCode={selectedLanguage.code}
            />
            {lastAssistantMessage ? (
              <MessageBubble
                message={lastAssistantMessage}
                sessionId={sessionId}
                languageCode={selectedLanguage.code}
              />
            ) : awaitingReply ? (
              <div className="flex gap-3 justify-start">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-700 flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4 text-white" />
                </div>
                <div className="inline-flex items-center gap-2 rounded-2xl rounded-bl-md bg-slate-800 border border-slate-700/50 px-4 py-3 text-sm text-slate-400">
                  <span className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" />
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce [animation-delay:150ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce [animation-delay:300ms]" />
                  </span>
                  Analysing your message…
                </div>
              </div>
            ) : replyFailed ? (
              <div className="flex gap-3 justify-start">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-900/70 flex items-center justify-center">
                  <TriangleAlert className="w-4 h-4 text-red-300" />
                </div>
                <div className="rounded-2xl rounded-bl-md bg-slate-800 border border-red-700/40 px-4 py-3 text-sm text-red-200">
                  The analysis didn&apos;t come through - {error ?? "please try again."}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Fallback text input */}
      <ChatInput
        onSendText={sendMessage}
        onSendAudio={sendAudio}
        isLoading={isLoading}
        placeholder={`Or type in ${selectedLanguage.nativeName}…`}
      />
    </div>
  );
}
