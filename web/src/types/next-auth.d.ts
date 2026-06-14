import "next-auth";
import "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    /** Access token de Entra con audiencia del API (para el header Authorization: Bearer en /v1). */
    apiToken?: string;
    /** Expiración del access token (epoch en segundos). */
    apiTokenExp?: number;
    /** App roles del token (gating cosmético de UI; el gate real lo hace el API). */
    roles?: string[];
    /** True si el usuario trae el rol `admin`. */
    isAdmin?: boolean;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    apiToken?: string;
    apiTokenExp?: number;
    roles?: string[];
  }
}
