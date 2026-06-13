import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    /** Access token de Entra con audiencia del API (para el header Authorization: Bearer en /v1). */
    apiToken?: string;
    /** Expiración del access token (epoch en segundos). */
    apiTokenExp?: number;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    apiToken?: string;
    apiTokenExp?: number;
  }
}
