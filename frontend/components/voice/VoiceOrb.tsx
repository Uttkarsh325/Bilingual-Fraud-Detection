"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Loader2, Volume2, ShieldCheck } from "lucide-react";
import clsx from "clsx";

export type VoiceOrbState = "idle" | "recording" | "processing" | "speaking";

interface VoiceOrbProps {
  state: VoiceOrbState;
  onStartRecording: () => void;
  onStopRecording: () => void;
}

const STATE_CONFIG: Record<
  VoiceOrbState,
  { label: string; sublabel: string; color: string; pulseColor: string }
> = {
  idle: {
    label: "Tap to speak",
    sublabel: "or type your message below",
    color: "bg-brand-600 hover:bg-brand-700",
    pulseColor: "bg-brand-500",
  },
  recording: {
    label: "Listening…",
    sublabel: "Tap again to stop",
    color: "bg-red-600",
    pulseColor: "bg-red-500",
  },
  processing: {
    label: "Analysing…",
    sublabel: "Please wait",
    color: "bg-amber-600",
    pulseColor: "bg-amber-500",
  },
  speaking: {
    label: "Speaking…",
    sublabel: "AI is responding",
    color: "bg-green-600",
    pulseColor: "bg-green-500",
  },
};

export default function VoiceOrb({ state, onStartRecording, onStopRecording }: VoiceOrbProps) {
  const config = STATE_CONFIG[state];

  const handleClick = () => {
    if (state === "idle") onStartRecording();
    else if (state === "recording") onStopRecording();
  };

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Orb */}
      <div className="relative flex items-center justify-center">
        {/* Pulse rings */}
        {(state === "recording" || state === "speaking") && (
          <>
            <span
              className={clsx(
                "absolute w-36 h-36 rounded-full opacity-20 animate-ping",
                config.pulseColor
              )}
            />
            <span
              className={clsx(
                "absolute w-28 h-28 rounded-full opacity-30 animate-ping",
                config.pulseColor
              )}
              style={{ animationDelay: "0.3s" }}
            />
          </>
        )}

        <button
          onClick={handleClick}
          disabled={state === "processing" || state === "speaking"}
          aria-label={state === "recording" ? "Stop recording" : "Start recording"}
          className={clsx(
            "relative w-24 h-24 rounded-full flex items-center justify-center",
            "text-white shadow-2xl transition-all duration-300 focus:outline-none",
            "focus:ring-4 focus:ring-brand-500/50",
            config.color,
            (state === "processing" || state === "speaking") && "cursor-default opacity-80"
          )}
        >
          <AnimatePresence mode="wait">
            {state === "idle" && (
              <motion.div key="mic" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                <Mic className="w-9 h-9" />
              </motion.div>
            )}
            {state === "recording" && (
              <motion.div key="stop" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                <Square className="w-9 h-9" />
              </motion.div>
            )}
            {state === "processing" && (
              <motion.div key="loader" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                <Loader2 className="w-9 h-9 animate-spin" />
              </motion.div>
            )}
            {state === "speaking" && (
              <motion.div key="speaker" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
                <Volume2 className="w-9 h-9" />
              </motion.div>
            )}
          </AnimatePresence>
        </button>
      </div>

      {/* Waveform bars (visible only while recording) */}
      {state === "recording" && (
        <div className="flex items-center gap-1 h-8">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="voice-bar h-6" />
          ))}
        </div>
      )}

      {/* Label */}
      <div className="text-center">
        <p className="text-lg font-semibold text-slate-100">{config.label}</p>
        <p className="text-sm text-slate-400">{config.sublabel}</p>
      </div>
    </div>
  );
}
