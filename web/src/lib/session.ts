import "server-only";
import { auth } from "@/auth";

/** Auth encendida sólo si Entra está configurado (mismo gate que api.ts/proxy/provider). */
const AUTH_ON = !!process.env.AUTH_MICROSOFT_ENTRA_ID_ID;

/**
 * ¿El usuario actual es administrador? SERVER-ONLY. Gating de UI (mostrar/ocultar acciones de
 * escritura). NO es la compuerta de seguridad: el API revalida el JWT y exige rol admin en cada
 * mutación. En dev (auth apagada) → true, porque el API local está abierto y su principal de
 * desarrollo es admin (así las acciones se ven y se pueden probar en local).
 */
export async function isAdminUser(): Promise<boolean> {
  if (!AUTH_ON) return true;
  const session = await auth();
  return session?.isAdmin === true;
}
