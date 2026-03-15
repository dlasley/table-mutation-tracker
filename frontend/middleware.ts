import { NextRequest, NextResponse } from "next/server";

export function middleware(req: NextRequest) {
  const credentials = process.env.BASIC_AUTH_CREDENTIALS;

  // Skip auth if not configured
  if (!credentials) {
    return NextResponse.next();
  }

  const sep = credentials.indexOf(":");
  if (sep <= 0) {
    return NextResponse.next();
  }

  const validUser = credentials.slice(0, sep);
  const validPass = credentials.slice(sep + 1);

  const auth = req.headers.get("authorization");
  if (auth) {
    const [scheme, encoded] = auth.split(" ");
    if (scheme === "Basic" && encoded) {
      const decoded = atob(encoded);
      const dSep = decoded.indexOf(":");
      if (dSep > 0) {
        const u = decoded.slice(0, dSep);
        const p = decoded.slice(dSep + 1);
        if (u === validUser && p === validPass) {
          return NextResponse.next();
        }
      }
    }
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Secure Area"' },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
