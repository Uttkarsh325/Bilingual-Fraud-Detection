import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function GET(
  req: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const upstream = await fetch(`${BACKEND}/memory/${params.userId}`, {
      headers: { Authorization: req.headers.get("authorization") ?? "" },
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Backend unreachable";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}

export async function DELETE(
  req: NextRequest,
  { params }: { params: { userId: string } }
) {
  try {
    const upstream = await fetch(`${BACKEND}/memory/${params.userId}`, {
      method: "DELETE",
      headers: { Authorization: req.headers.get("authorization") ?? "" },
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Backend unreachable";
    return NextResponse.json({ detail: message }, { status: 502 });
  }
}
