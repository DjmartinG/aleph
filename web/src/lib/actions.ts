"use server";

import { postRun, type MonteCarloParams, type MonteCarloResult } from "@/lib/api";

/**
 * Server Action: corre el Monte Carlo en el motor (vía la API), del lado del servidor.
 * Así la URL/token del API quedan server-side (preparado para el login de Entra en /web).
 */
export async function runMonteCarlo(
  slug: string,
  params: MonteCarloParams,
): Promise<MonteCarloResult> {
  return postRun(slug, params);
}
