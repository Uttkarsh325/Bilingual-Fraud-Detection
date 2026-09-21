import { apiClient } from "./client";
import type { SessionDetail, SessionSummary } from "@/lib/types";

/** List the authenticated user's past sessions, most recent first. */
export async function listSessions(): Promise<SessionSummary[]> {
  const { data } = await apiClient.get<SessionSummary[]>("/sessions");
  return data;
}

/** Fetch the full transcript of one session. */
export async function getSession(sessionId: string): Promise<SessionDetail> {
  const { data } = await apiClient.get<SessionDetail>(`/sessions/${sessionId}`);
  return data;
}

/** Create an (empty) session, or return the existing one if it matches. */
export async function createSession(payload: {
  session_id: string;
  mode?: "chat" | "voice";
  language?: string;
}): Promise<SessionSummary> {
  const { data } = await apiClient.post<SessionSummary>("/sessions", payload);
  return data;
}

/** Delete a session and its transcript. */
export async function deleteSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/sessions/${sessionId}`);
}