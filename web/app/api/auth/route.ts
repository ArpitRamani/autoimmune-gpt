import { NextResponse } from "next/server";

const PASSCODE = process.env.APP_PASSCODE ?? "";

export async function POST(req: Request) {
  // Returns { required, ok }. If no passcode is configured, access is open.
  if (!PASSCODE) return NextResponse.json({ required: false, ok: true });
  let code = "";
  try {
    code = ((await req.json())?.code ?? "").toString();
  } catch {
    /* ignore */
  }
  return NextResponse.json({ required: true, ok: code === PASSCODE });
}
