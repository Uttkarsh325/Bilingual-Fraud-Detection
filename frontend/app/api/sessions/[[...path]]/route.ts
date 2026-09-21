import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

/**
 * /api/sessions/[[...path]]
 * Thin proxy to the backend's /sessions endpoints (list/get/create/update/delete
 * and message append). Forwards the caller's Authorization header so sessions
 * are always scoped to the authenticated user.
 */
async function handler(
  req: NextRequest,
  { params }: { params: { path?: string[] } }
) {
  const path = params.path?.join("/") ?? "";
  const method = req.method;

  try {
    const hasBody = method === "POST" || method === "PUT";
    const body = hasBody ? await req.json() : undefined;

    const upstream = await fetch(`${BACKEND}/sessions/${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: req.headers.get("authorization") ?? "",
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    });

    const data = await upstream.json().catch(() => null);
    return NextResponse.json(data, { status: upstream.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Backend unreachable";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}

export { handler as GET, handler as POST, handler as PUT, handler as DELETE };