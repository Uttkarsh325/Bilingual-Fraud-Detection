"use client";

import { useState, useCallback, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import toast from "react-hot-toast";
import { sendChatMessage, transcribeAudio } from "@/lib/api/chat";
import type { ChatMessage, ConversationState, SupportedLanguage } from "@/lib/types";
import { SUPPORTED_LANGUAGES } from "@/lib/types";
import { detectScriptLanguage } from "@/lib/language";

function getOrCreateUserId(): string {
  if (typeof window === "undefined") return "anon";
  let uid = localStorage.getItem("fg_user_id");
  if (!uid) {
    uid = uuidv4();
    localStorage.setItem("fg_user_id", uid);
  }
  return uid;
}

export function useConversation() {
  const sessionId = useRef<string>(uuidv4());
  const userId = useRef<string>(getOrCreateUserId());

  const [state, setState] = useState<ConversationState>({
    sessionId: sessionId.current,
    userId: userId.current,
    messages: [],
    isLoading: false,
    isRecording: false,
    isSpeaking: false,
    selectedLanguage: SUPPORTED_LANGUAGES[0], // English default
    error: null,
  });

  const addMessage = useCallback((msg: Omit<ChatMessage, "id" | "timestamp">) => {
    const full: ChatMessage = { ...msg, id: uuidv4(), timestamp: new Date() };
    setState((s) => ({ ...s, messages: [...s.messages, full] }));
    return full;
  }, []);

  const setLanguage = useCallback((lang: SupportedLanguage) => {
    setState((s) => ({ ...s, selectedLanguage: lang }));
  }, []);

  const sendMessage = useCallback(
    async (text: string, mode: "chat" | "voice" = "chat", language?: string) => {
      if (!text.trim()) return;

      // Mirror the message's language when one is explicitly given (voice flow)
      // or infer it from the script (e.g. Hindi typing → Hindi reply).
      const scriptLang = detectScriptLanguage(text);
      let effectiveLanguage = language ?? state.selectedLanguage.code;
      if (!language && scriptLang) effectiveLanguage = scriptLang;
      if (scriptLang) {
        const matched = SUPPORTED_LANGUAGES.find((l) => l.code === scriptLang);
        if (matched) setLanguage(matched);
      }

      // Add the user bubble immediately
      addMessage({ role: "user", content: text });
      setState((s) => ({ ...s, isLoading: true, error: null }));

      try {
        const response = await sendChatMessage({
          session_id: sessionId.current,
          user_id: userId.current,
          message: text,
          language: effectiveLanguage,
          mode,
        });

        addMessage({
          role: "assistant",
          content: response.reply,
          metadata: response.metadata,
        });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Something went wrong";
        setState((s) => ({ ...s, error: message }));
        toast.error(message);
      } finally {
        setState((s) => ({ ...s, isLoading: false }));
      }
    },
    [state.selectedLanguage.code, addMessage, setLanguage]
  );

  const sendAudio = useCallback(
    async (blob: Blob) => {
      setState((s) => ({ ...s, isLoading: true, error: null }));
      try {
        // No language hint → Sarvam auto-detects Hindi / any other language.
        const transcription = await transcribeAudio(
          blob,
          sessionId.current,
          userId.current
        );

        const detectedLang = SUPPORTED_LANGUAGES.find(
          (l) =>
            l.code.toLowerCase() ===
            (transcription.language_detected || "").toLowerCase()
        );

        // Reflect the spoken language in the UI (selector, TTS)…
        if (detectedLang) setLanguage(detectedLang);

        // …and force the analysis to run/reply in that language.
        await sendMessage(
          transcription.transcript,
          "voice",
          detectedLang ? detectedLang.code : state.selectedLanguage.code
        );
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Audio processing failed";
        setState((s) => ({ ...s, error: message }));
        toast.error(message);
      } finally {
        setState((s) => ({ ...s, isLoading: false }));
      }
    },
    [state.selectedLanguage.code, sendMessage, setLanguage]
  );

  const resetConversation = useCallback(() => {
    sessionId.current = uuidv4();
    setState((s) => ({
      ...s,
      sessionId: sessionId.current,
      messages: [],
      error: null,
    }));
  }, []);

  // Resume a saved session: switch the active id and hydrate the transcript.
  const loadSession = useCallback((id: string, history: ChatMessage[]) => {
    sessionId.current = id;
    setState((s) => ({
      ...s,
      sessionId: id,
      messages: history,
      error: null,
      isLoading: false,
    }));
  }, []);

  return {
    ...state,
    sendMessage,
    sendAudio,
    setLanguage,
    resetConversation,
    loadSession,
  };
}
