"use client";

import { useCallback, useEffect, useState } from "react";
import { v4 as uuidv4 } from "uuid";
import { deleteSession, getSession, listSessions } from "@/lib/api/sessions";
import type {
  ChatMessage,
  SessionMessageRecord,
  SessionSummary,
} from "@/lib/types";

function toChatMessage(record: SessionMessageRecord): ChatMessage {
  return {
    id: uuidv4(),
    role: record.role,
    content: record.content,
    timestamp: new Date(record.created_at),
    metadata: record.metadata ?? undefined,
  };
}

/**
 * Loads and manages the authenticated user's saved sessions.
 * Sessions are scoped to the user server-side, so no user id is needed here.
 */
export function useSessionHistory() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const list = await listSessions();
      setSessions(list);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const fetchSession = useCallback(
    async (sessionId: string): Promise<ChatMessage[]> => {
      const detail = await getSession(sessionId);
      return detail.messages.map(toChatMessage);
    },
    []
  );

  const remove = useCallback(async (sessionId: string) => {
    await deleteSession(sessionId);
    setSessions((s) => s.filter((x) => x.session_id !== sessionId));
  }, []);

  return { sessions, loading, error, refresh, fetchSession, remove };
}