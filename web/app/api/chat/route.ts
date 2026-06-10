import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: Request) {
  let message = "";
  try {
    const body = await req.json();
    message = (body?.message ?? "").toString();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      return NextResponse.json(
        { answer: "The research service is unavailable right now. Please try again shortly.", sources: [] },
        { status: 502 },
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { answer: "Couldn't reach the research service. Is the backend running?", sources: [] },
      { status: 502 },
    );
  }
}
