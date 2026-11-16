import { NextRequest, NextResponse } from "next/server";

const encoder = new TextEncoder();

async function sha256(value: string): Promise<Uint8Array> {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(value)));
}

async function safeEqual(a: string, b: string): Promise<boolean> {
  const [ha, hb] = await Promise.all([sha256(a), sha256(b)]);
  let diff = 0;
  for (let i = 0; i < ha.length; i++) diff |= ha[i] ^ hb[i];
  return diff === 0;
}

function unauthorized(): NextResponse {
  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Secure Area"' },
  });
}

function parseCredentials(raw: string): { user: string; pass: string } | null {
  const sep = raw.indexOf(":");
  if (sep <= 0) return null;
  return { user: raw.slice(0, sep), pass: raw.slice(sep + 1) };
}

function decodeBasicHeader(header: string): { user: string; pass: string } | null {
  const match = /^basic +(\S+)$/i.exec(header.trim());
  if (!match) return null;
  let decoded: string;
  try {
    const bytes = Uint8Array.from(atob(match[1]), (c) => c.charCodeAt(0));
    decoded = new TextDecoder().decode(bytes);
  } catch {
    return null;
  }
  return parseCredentials(decoded);
}

export async function middleware(req: NextRequest) {
  const raw = process.env.BASIC_AUTH_CREDENTIALS?.trim();

  // Without credentials, only Vercel previews (synthetic data) and `next dev` are served.
  // Any other host, including self-hosted `next start`, refuses all requests.
  if (!raw) {
    if (process.env.VERCEL_ENV === "preview" || process.env.NODE_ENV === "development") {
      return NextResponse.next();
    }
    console.error("BASIC_AUTH_CREDENTIALS is missing or malformed; refusing all requests");
    return new NextResponse("Service unavailable", { status: 503 });
  }

  const valid = parseCredentials(raw);
  if (!valid || !valid.pass) {
    console.error("BASIC_AUTH_CREDENTIALS is missing or malformed; refusing all requests");
    return new NextResponse("Service unavailable", { status: 503 });
  }

  const header = req.headers.get("authorization");
  const given = header ? decodeBasicHeader(header) : null;
  if (!given) return unauthorized();

  const [userOk, passOk] = await Promise.all([
    safeEqual(given.user, valid.user),
    safeEqual(given.pass, valid.pass),
  ]);
  if (userOk && passOk) return NextResponse.next();

  return unauthorized();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
