import { NextRequest, NextResponse } from "next/server";

const SITE_USERNAME = "ohdemo";

/**
 * Optional HTTP Basic Auth when SITE_PASSWORD is set (e.g. on Vercel Hobby).
 * Username is fixed to `ohdemo`; password comes from SITE_PASSWORD.
 * Leave SITE_PASSWORD unset locally so dev stays open.
 */
export function middleware(req: NextRequest) {
  const password = process.env.SITE_PASSWORD;
  if (!password) return NextResponse.next();

  const auth = req.headers.get("authorization");
  if (auth?.startsWith("Basic ")) {
    const encoded = auth.slice(6);
    try {
      const decoded = atob(encoded);
      const separator = decoded.indexOf(":");
      if (separator >= 0) {
        const user = decoded.slice(0, separator);
        const pass = decoded.slice(separator + 1);
        if (user === SITE_USERNAME && pass === password) {
          return NextResponse.next();
        }
      }
    } catch {
      // invalid base64
    }
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="OH AI Agent"' },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
