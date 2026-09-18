"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { RotateCcw } from "lucide-react";
import { useConversation } from "@/lib/hooks/useConversation";
import { useAudioRecorder } from "@/lib/hooks/useAudioRecorder";
import VoiceOrb, { type VoiceOrbState } from "@/components/voice/VoiceOrb";
import MessageBubble from "@/components/chat/MessageBubble";
import LanguageSelector from "@/components/ui/LanguageSelector";
import ChatInput from "@/components/chat/ChatInput";

export default function VoicePage() {
  const {
    messages,
    isLoading,
    sessionId,
    selectedLanguage,
    sendMessage,
    sendAudio,
    setLanguage,
    resetConversation,
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

  const lastAssistantMessage = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Top bar */}
      <div className="flex items-center justify-between gap-4 px-4 py-3 border-b border-slate-700/50">
        <LanguageSelector selected={selectedLanguage} onChange={setLanguage} />
        <button
          onClick={resetConversation}
          className="btn-secondary text-xs py-1.5 px-3"
          aria-label="New conversation"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Session</span>
        </button>
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

        {/* Show the last assistant message */}
        {lastAssistantMessage && (
          <div className="w-full max-w-xl">
            <MessageBubble
              message={lastAssistantMessage}
              sessionId={sessionId}
              languageCode={selectedLanguage.code}
            />
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
