import { apiClient } from "./client";
import type { ChatRequest, ChatResponse, VoiceTranscribeResponse } from "@/lib/types";

/**
 * Send a text message and receive an advisory response.
 */
export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  // Routes through Next.js proxy: /api/chat → backend /chat
  const { data } = await apiClient.post<ChatResponse>("/chat", payload);
  return data;
}

/**
 * Upload a recorded audio blob, get back a transcript + detected language.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  sessionId: string,
  userId: string,
  languageHint?: string
): Promise<VoiceTranscribeResponse> {
  const form = new FormData();
  form.append("audio", audioBlob, "recording.webm");
  form.append("session_id", sessionId);
  form.append("user_id", userId);
  if (languageHint) form.append("language_hint", languageHint);

  const { data } = await apiClient.post<VoiceTranscribeResponse>("/voice", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * Request TTS audio for a given text.
 * Returns a pre-signed S3 URL or a data URL.
 */
export async function synthesizeSpeech(
  text: string,
  languageCode: string,
  sessionId: string
): Promise<{ audio_url: string }> {
  // Routes through Next.js proxy: /api/voice/synthesize → backend /voice/synthesize
  const { data } = await apiClient.post<{ audio_url: string }>("/voice/synthesize", {
    text,
    language_code: languageCode,
    session_id: sessionId,
  });
  return data;
}

export async function getUserMemory(userId: string) {
  // Routes through Next.js proxy: /api/memory/:userId → backend /memory/:userId
  const { data } = await apiClient.get(`/memory/${userId}`);
  return data;
}

export async function clearUserMemory(userId: string) {
  const { data } = await apiClient.delete(`/memory/${userId}`);
  return data;
}

/**
 * Translate text into another language (default English).
 * Routes through the Next.js proxy: /api/translate → backend /translate.
 */
export async function translateText(
  text: string,
  target: string = "en-IN"
): Promise<string> {
  const { data } = await apiClient.post<{ translated_text: string }>("/translate", {
    text,
    target,
  });
  return data.translated_text;
}
