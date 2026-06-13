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
      // En el primer sign-in, captura el access token (audiencia del API) y su expiración.
      if (account) {
        token.apiToken = account.access_token;
        token.apiTokenExp = account.expires_at;
      }
      return token;
    },
    async session({ session, token }) {
      session.apiToken = token.apiToken;
      session.apiTokenExp = token.apiTokenExp;
      return session;
    },
  },
});
