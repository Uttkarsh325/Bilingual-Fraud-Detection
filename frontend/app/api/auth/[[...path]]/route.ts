import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

/**
 * Catch-all auth proxy: /api/auth/{register|login|me} → backend /auth/{register|login|me}
 * Keeps the backend URL server-side and forwards the Authorization header.
 */
async function proxy(req: NextRequest, path: string[]) {
  try {
    const isPost = req.method === "POST";
    const body = isPost ? await req.json() : undefined;
    const search = new URL(req.url).search;

    const upstream = await fetch(`${BACKEND}/auth/${path.join("/")}${search}`, {
      method: req.method,
      headers: {
        "Content-Type": "application/json",
        Authorization: req.headers.get("authorization") ?? "",
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Backend unreachable";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}

export async function POST(req: NextRequest, ctx: { params: { path?: string[] } }) {
  return proxy(req, ctx.params.path ?? []);
}

export async function GET(req: NextRequest, ctx: { params: { path?: string[] } }) {
  return proxy(req, ctx.params.path ?? []);
}