// ─── Script-based language detection ─────────────────────────────────────────
// Deterministic, zero-latency check for Indic-script messages so that typing a
// Hindi (or Tamil/Bengali/etc.) message automatically produces a reply in that
// language — no separate detection service needed.

const SCRIPT_TESTS: Array<[RegExp, string]> = [
  [/[\u0900-\u097F]/, "hi-IN"], // Devanagari (Hindi, Marathi)
  [/[\u0980-\u09FF]/, "bn-IN"], // Bengali
  [/[\u0A00-\u0A7F]/, "pa-IN"], // Gurmukhi (Punjabi)
  [/[\u0A80-\u0AFF]/, "gu-IN"], // Gujarati
  [/[\u0B80-\u0BFF]/, "ta-IN"], // Tamil
  [/[\u0C00-\u0C7F]/, "te-IN"], // Telugu
  [/[\u0C80-\u0CFF]/, "kn-IN"], // Kannada
  [/[\u0D00-\u0D7F]/, "ml-IN"], // Malayalam
];

/**
 * Detect the language of a message from its script. Returns a BCP-47 code
 * (e.g. "hi-IN") or null when the text is Latin-script / undetectable.
 */
export function detectScriptLanguage(text: string): string | null {
  for (const [re, code] of SCRIPT_TESTS) {
    if (re.test(text)) return code;
  }
  return null;
}