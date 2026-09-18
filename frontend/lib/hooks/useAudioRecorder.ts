"use client";

import { useState, useRef, useCallback } from "react";

export type RecorderStatus = "idle" | "recording" | "stopped" | "error";

export interface UseAudioRecorderReturn {
  status: RecorderStatus;
  audioBlob: Blob | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  resetRecording: () => void;
  error: string | null;
}

/**
 * Hook that wraps the MediaRecorder API for in-browser audio capture.
 * Captures audio as WebM/Opus (supported in all modern browsers).
 */
export function useAudioRecorder(): UseAudioRecorderReturn {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const startRecording = useCallback(async () => {
    setError(null);
    setAudioBlob(null);
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        setStatus("stopped");
        // Stop all tracks to release the mic
        stream.getTracks().forEach((t) => t.stop());
      };

      recorder.onerror = () => {
        setError("Microphone recording failed.");
        setStatus("error");
      };

      recorder.start(250); // collect data every 250 ms
      setStatus("recording");
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message.includes("Permission")
            ? "Microphone access denied. Please allow microphone in browser settings."
            : err.message
          : "Could not start recording";
      setError(msg);
      setStatus("error");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const resetRecording = useCallback(() => {
    setStatus("idle");
    setAudioBlob(null);
    setError(null);
    chunksRef.current = [];
  }, []);

  return { status, audioBlob, startRecording, stopRecording, resetRecording, error };
}
