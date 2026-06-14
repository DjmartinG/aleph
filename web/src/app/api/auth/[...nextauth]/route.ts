import type { NextRequest } from "next/server";
import { handlers } from "@/auth";

const { GET: baseGET, POST } = handlers;

/**
 * Sanea la respuesta de `GET /api/auth/session`: NextAuth v5 devuelve al navegador el objeto `session`
 * tal como lo arma el callback `session()` — que incluye `apiToken`/`apiTokenExp` (el access token de
 * Entra con audiencia del API). Ese Bearer debe usarse SOLO server-side (`api.ts` lo adjunta vía
 * `auth()`, que decodifica la cookie directamente y NO pasa por esta ruta), así que lo retiramos de la
 * respuesta HTTP para que ningún JS del cliente (ni un XSS/extensión) lo pueda exfiltrar. `roles`/
 * `isAdmin` se dejan (no son secretos; solo nombres de rol para gating cosmético de UI).
 */
export async function GET(req: NextRequest): Promise<Response> {
  const res = await baseGET(req);
  const isSession = new URL(req.url).pathname.endsWith("/session");
  const isJson = res.headers.get("content-type")?.includes("application/json");
  if (!isSession || !isJson) return res;

  const data = await res.json();
  if (data && typeof data === "object") {
    delete (data as Record<string, unknown>).apiToken;
    delete (data as Record<string, unknown>).apiTokenExp;
  }
  const headers = new Headers(res.headers);
  headers.delete("content-length"); // lo recalcula la plataforma con el cuerpo saneado
  return new Response(JSON.stringify(data), { status: res.status, headers });
}

export { POST };
