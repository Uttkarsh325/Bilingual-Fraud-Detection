"use client";

import { useState, useRef, useEffect, type KeyboardEvent } from "react";
import { Send, Mic, MicOff, Loader2, Square } from "lucide-react";
import clsx from "clsx";
import { useAudioRecorder } from "@/lib/hooks/useAudioRecorder";

interface ChatInputProps {
  onSendText: (text: string) => void;
  onSendAudio: (blob: Blob) => void;
  isLoading: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export default function ChatInput({
  onSendText,
  onSendAudio,
  isLoading,
  disabled = false,
  placeholder = "Describe a suspicious message, or paste it here…",
}: ChatInputProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { status, audioBlob, startRecording, stopRecording, resetRecording } =
    useAudioRecorder();

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [text]);

  // When recording stops and blob is ready, send it
  useEffect(() => {
    if (status === "stopped" && audioBlob) {
      onSendAudio(audioBlob);
      resetRecording();
    }
  }, [status, audioBlob, onSendAudio, resetRecording]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSendText(trimmed);
    setText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isRecording = status === "recording";
  const canSend = text.trim().length > 0 && !isLoading && !disabled;

  return (
    <div className="flex items-end gap-2 p-4 bg-slate-900 border-t border-slate-700/50">
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={disabled || isLoading || isRecording}
          className={clsx(
            "input-field resize-none pr-12 min-h-[44px] max-h-40",
            (disabled || isRecording) && "opacity-50 cursor-not-allowed"
          )}
          aria-label="Chat message input"
        />
      </div>

      {/* Voice record button */}
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled || isLoading}
        title={isRecording ? "Stop recording" : "Record voice message"}
        aria-label={isRecording ? "Stop recording" : "Record voice message"}
        className={clsx(
          "flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all",
          isRecording
            ? "bg-red-600 hover:bg-red-700 text-white animate-pulse-slow"
            : "bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-slate-100",
          (disabled || isLoading) && "opacity-50 cursor-not-allowed"
        )}
      >
        {isRecording ? <Square className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
      </button>

      {/* Send button */}
      <button
        onClick={handleSend}
        disabled={!canSend}
        title="Send message"
        aria-label="Send message"
        className={clsx(
          "flex-shrink-0 w-11 h-11 rounded-xl flex items-center justify-center transition-all",
          canSend
            ? "bg-brand-600 hover:bg-brand-700 text-white"
            : "bg-slate-700 text-slate-500 cursor-not-allowed"
        )}
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Send className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}
