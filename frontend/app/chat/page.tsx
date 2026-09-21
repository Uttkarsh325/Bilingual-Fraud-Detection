"use client";

import { RotateCcw } from "lucide-react";
import { useConversation } from "@/lib/hooks/useConversation";
import ChatWindow from "@/components/chat/ChatWindow";
import ChatInput from "@/components/chat/ChatInput";
import LanguageSelector from "@/components/ui/LanguageSelector";
import RequireAuth from "@/components/auth/RequireAuth";
import SessionHistory from "@/components/sessions/SessionHistory";

export default function ChatPage() {
  return (
    <RequireAuth>
      <ChatContent />
    </RequireAuth>
  );
}

function ChatContent() {
  const {
    messages,
    isLoading,
    sessionId,
    selectedLanguage,
    sendMessage,
    sendAudio,
    setLanguage,
    resetConversation,
    loadSession,
  } = useConversation();

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Top bar */}
      <div className="flex items-center justify-between gap-4 px-4 py-3 border-b border-slate-700/50 bg-slate-900/60 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <LanguageSelector selected={selectedLanguage} onChange={setLanguage} />
          <span className="text-xs text-slate-500 hidden sm:block">
            Text or voice — I understand your language
          </span>
        </div>
        <div className="flex items-center gap-2">
          <SessionHistory
            activeSessionId={sessionId}
            onLoadSession={loadSession}
            onNewSession={resetConversation}
          />
          <button
            onClick={resetConversation}
            title="New conversation"
            className="btn-secondary text-xs py-1.5 px-3"
            aria-label="Start new conversation"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Chat</span>
          </button>
        </div>
      </div>

      {/* Chat messages */}
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        sessionId={sessionId}
        language={selectedLanguage}
      />

      {/* Input */}
      <ChatInput
        onSendText={sendMessage}
        onSendAudio={sendAudio}
        isLoading={isLoading}
        placeholder={`Ask in ${selectedLanguage.nativeName} or paste a suspicious message…`}
      />
    </div>
  );
}
