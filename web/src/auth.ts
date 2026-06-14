import NextAuth from "next-auth";
import MicrosoftEntraID from "next-auth/providers/microsoft-entra-id";

/**
 * Auth config-driven (espejo del API `aleph_api.auth`):
 * - SIN `AUTH_MICROSOFT_ENTRA_ID_ID` (dev local) → no hay provider y el proxy deja todo abierto;
 *   el /web habla con el API local que también tiene la auth apagada.
 * - CON las env de Entra (Vercel/prod) → se exige login Microsoft y, gracias al scope del API
 *   (`ALEPH_API_SCOPE` = api://<API_APP_ID>/access_as_user), el access token sale con la
 *   AUDIENCIA del API → se adjunta como Bearer a /v1.
 *
 * clientId / clientSecret / issuer los infiere Auth.js de AUTH_MICROSOFT_ENTRA_ID_{ID,SECRET,ISSUER}.
 */
const entraConfigured = !!process.env.AUTH_MICROSOFT_ENTRA_ID_ID;
const apiScope = process.env.ALEPH_API_SCOPE;

/**
 * Extrae el claim `roles` del access token de Entra (app roles del registro de la API). Se decodifica
 * SIN verificar firma: es solo para gating COSMÉTICO de la UI (mostrar/ocultar acciones de admin); la
 * compuerta REAL la hace el API, que sí valida el JWT y exige rol admin. El token viene de Entra.
 */
function rolesFromAccessToken(accessToken?: string): string[] {
  if (!accessToken) return [];
  try {
    const payload = accessToken.split(".")[1];
    if (!payload) return [];
    const b64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const claims = JSON.parse(Buffer.from(b64, "base64").toString("utf8"));
    return Array.isArray(claims.roles) ? claims.roles : [];
  } catch {
    return [];
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: entraConfigured
    ? [
        MicrosoftEntraID({
          authorization: {
            params: {
              scope: ["openid", "profile", "email", apiScope].filter(Boolean).join(" "),
            },
          },
        }),
      ]
    : [],
  callbacks: {
    async jwt({ token, account }) {
      // En el primer sign-in, captura el access token (audiencia del API), su expiración y los roles.
      if (account) {
        token.apiToken = account.access_token;
        token.apiTokenExp = account.expires_at;
        token.roles = rolesFromAccessToken(account.access_token);
      }
      return token;
    },
    async session({ session, token }) {
      session.apiToken = token.apiToken;
      session.apiTokenExp = token.apiTokenExp;
      session.roles = token.roles ?? [];
      session.isAdmin = (token.roles ?? []).some((r) => r.toLowerCase() === "admin");
      return session;
    },
  },
});
