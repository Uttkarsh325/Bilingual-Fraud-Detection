import { NextRequest, NextResponse } from "next/server";

// Server-side only — never exposed to the browser
const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

/**
 * POST /api/voice
 * Proxies multipart audio to the backend /voice/transcribe endpoint.
 */
export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();

    const upstream = await fetch(`${BACKEND}/voice/transcribe`, {
      method: "POST",
      headers: {
        Authorization: req.headers.get("authorization") ?? "",
        // No Content-Type — let fetch set the correct multipart boundary automatically
      },
      body: formData,
    });

    const data = await upstream.json();

    if (!upstream.ok) {
      return NextResponse.json(data, { status: upstream.status });
    }

    return NextResponse.json(data);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Backend unreachable";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
