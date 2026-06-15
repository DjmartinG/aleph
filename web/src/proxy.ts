import { NextResponse, type NextRequest } from "next/server";

/**
 * Proxy de Next 16 (antes "middleware"). Protege TODAS las rutas con un chequeo OPTIMISTA de la
 * cookie de sesión de Auth.js (la validación real del token la hace `auth()` server-side, y el API
 * revalida el JWT de Entra). Patrón recomendado por la guía de auth de Next 16.
 *
 * Config-driven: sin `AUTH_MICROSOFT_ENTRA_ID_ID` (dev local) deja pasar todo (auth apagada).
 */
const AUTH_ON = !!process.env.AUTH_MICROSOFT_ENTRA_ID_ID;
const SESSION_COOKIES = ["authjs.session-token", "__Secure-authjs.session-token"];

export function proxy(req: NextRequest) {
  if (!AUTH_ON) return NextResponse.next();

  const hasSession = SESSION_COOKIES.some((c) => req.cookies.has(c));
  const { pathname } = req.nextUrl;

  if (!hasSession && pathname !== "/login") {
    const url = new URL("/login", req.nextUrl);
    url.searchParams.set("callbackUrl", pathname + req.nextUrl.search);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  // Corre en todo MENOS: rutas de auth (/api/*), assets, favicon, y el lanzador público de Teams
  // (teams.html — debe cargar SIN login dentro del iframe de Teams; abre la app en el navegador).
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico|icon.svg|teams.html).*)"],
};
