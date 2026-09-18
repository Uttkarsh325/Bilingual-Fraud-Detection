import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

/**
 * POST /api/chat
 * Thin proxy to the FastAPI backend's /chat endpoint.
 * Keeps the backend URL server-side so it is never exposed to the browser.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const upstream = await fetch(`${BACKEND}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: req.headers.get("authorization") ?? "",
      },
      body: JSON.stringify(body),
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
