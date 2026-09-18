"use client";

import { useState, useCallback, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import toast from "react-hot-toast";
import { sendChatMessage, transcribeAudio } from "@/lib/api/chat";
import type { ChatMessage, ConversationState, SupportedLanguage } from "@/lib/types";
import { SUPPORTED_LANGUAGES } from "@/lib/types";

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

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      // Add the user bubble immediately
      addMessage({ role: "user", content: text });
      setState((s) => ({ ...s, isLoading: true, error: null }));

      try {
        const response = await sendChatMessage({
          session_id: sessionId.current,
          user_id: userId.current,
          message: text,
          language: state.selectedLanguage.code,
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
    [state.selectedLanguage.code, addMessage]
  );

  const sendAudio = useCallback(
    async (blob: Blob) => {
      setState((s) => ({ ...s, isLoading: true, error: null }));
      try {
        const transcription = await transcribeAudio(
          blob,
          sessionId.current,
          userId.current,
          state.selectedLanguage.code
        );
        await sendMessage(transcription.transcript);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Audio processing failed";
        setState((s) => ({ ...s, error: message }));
        toast.error(message);
      } finally {
        setState((s) => ({ ...s, isLoading: false }));
      }
    },
    [state.selectedLanguage.code, sendMessage]
  );

  const setLanguage = useCallback((lang: SupportedLanguage) => {
    setState((s) => ({ ...s, selectedLanguage: lang }));
  }, []);

  const resetConversation = useCallback(() => {
    sessionId.current = uuidv4();
    setState((s) => ({
      ...s,
      sessionId: sessionId.current,
      messages: [],
      error: null,
    }));
  }, []);

  return {
    ...state,
    sendMessage,
    sendAudio,
    setLanguage,
    resetConversation,
  };
}
