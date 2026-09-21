"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import { History, Mic, MessageSquare, Plus, RefreshCw, Trash2, X } from "lucide-react";
import { useSessionHistory } from "@/lib/hooks/useSessionHistory";
import type { ChatMessage, SessionSummary } from "@/lib/types";

interface SessionHistoryProps {
  activeSessionId: string;
  onLoadSession: (sessionId: string, messages: ChatMessage[]) => void;
  onNewSession: () => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function SessionHistory({
  activeSessionId,
  onLoadSession,
  onNewSession,
}: SessionHistoryProps) {
  const { sessions, loading, error, refresh, fetchSession, remove } = useSessionHistory();
  const [open, setOpen] = useState(false);
  const [removing, setRemoving] = useState<string | null>(null);

  const openDrawer = () => {
    refresh();
    setOpen(true);
  };

  const handleSelect = async (s: SessionSummary) => {
    try {
      const history = await fetchSession(s.session_id);
      onLoadSession(s.session_id, history);
      setOpen(false);
    } catch {
      setOpen(false);
    }
  };

  const handleDelete = async (s: SessionSummary) => {
    setRemoving(s.session_id);
    try {
      await remove(s.session_id);
    } finally {
      setRemoving(null);
    }
  };

  return (
    <>
      <button
        onClick={openDrawer}
        title="Saved conversations"
        className="btn-secondary text-xs py-1.5 px-3"
        aria-label="Open session history"
      >
        <History className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">History</span>
      </button>

      {open && typeof document !== "undefined"
        ? createPortal(
            <motion.div
              className="fixed inset-0 z-[90]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
            {/* Blurred backdrop */}
            <div
              className="absolute inset-0 bg-slate-950/70 backdrop-blur-md"
              onClick={() => setOpen(false)}
              aria-hidden="true"
            />

            {/* Drawer */}
            <motion.aside
              role="dialog"
              aria-label="Session history"
              initial={{ x: 320 }}
              animate={{ x: 0 }}
              transition={{ type: "tween", duration: 0.2 }}
              className="absolute right-0 top-0 bottom-0 w-80 max-w-[85vw] bg-slate-900 border-l border-slate-700/50 flex flex-col"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700/50">
                <h2 className="text-sm font-semibold text-slate-200">Saved conversations</h2>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => {
                      onNewSession();
                      setOpen(false);
                    }}
                    title="Start a new conversation"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
                    aria-label="New conversation"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                  <button
                    onClick={refresh}
                    title="Refresh"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
                    aria-label="Refresh history"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setOpen(false)}
                    title="Close"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
                    aria-label="Close history"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto p-3">
                {loading ? (
                  <div className="flex items-center justify-center h-24">
                    <RefreshCw className="w-5 h-5 text-brand-400 animate-spin" />
                  </div>
                ) : error ? (
                  <p className="text-sm text-red-300 text-center px-4 py-6">{error}</p>
                ) : sessions.length === 0 ? (
                  <div className="text-center px-4 py-10">
                    <History className="w-8 h-8 mx-auto text-slate-600 mb-3" />
                    <p className="text-sm text-slate-400">
                      No saved conversations yet. Start chatting and your history will
                      appear here.
                    </p>
                  </div>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {sessions.map((s) => {
                      const active = s.session_id === activeSessionId;
                      return (
                        <li key={s.session_id}>
                          <div
                            className={`relative rounded-xl border transition-colors ${
                              active
                                ? "bg-brand-900/40 border-brand-700/60"
                                : "bg-slate-800/50 border-slate-700/50 hover:bg-slate-800"
                            }`}
                          >
                            <button
                              onClick={() => handleSelect(s)}
                              className="w-full text-left px-3 py-2.5 pr-10"
                            >
                              <span className="flex items-center gap-1.5 text-slate-400">
                                {s.mode === "voice" ? (
                                  <Mic className="w-3.5 h-3.5" />
                                ) : (
                                  <MessageSquare className="w-3.5 h-3.5" />
                                )}
                                <span className="text-xs">{formatDate(s.updated_at)}</span>
                              </span>
                              <span className="block text-sm text-slate-200 truncate mt-1">
                                {s.title}
                              </span>
                            </button>
                            <button
                              onClick={() => handleDelete(s)}
                              title="Delete session"
                              className="absolute top-2 right-2 p-1 rounded-md text-slate-500 hover:text-red-300 hover:bg-slate-700/50 transition-colors"
                            >
                              {removing === s.session_id ? (
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Trash2 className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </motion.aside>
            </motion.div>,
            document.body
          )
        : null}
    </>
  );
}