"use server";

import { revalidatePath } from "next/cache";
import {
  approveScenario,
  createProject,
  postRun,
  WriteError,
  type MonteCarloParams,
  type MonteCarloResult,
} from "@/lib/api";

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

// ---------- Escritura (Fase 5): crear + aprobar un proyecto ----------
// El token de Entra y la URL del API quedan SERVER-SIDE; el API revalida el JWT y exige rol admin
// (defensa real). Esta acción es delgada: arma la secuencia crear→aprobar y traduce el resultado a
// algo que el formulario (client) pueda mostrar SIN volcar excepciones crudas al usuario.

export interface CrearProyectoInput {
  par: Record<string, unknown>;
  slug?: string;
  nombre?: string;
  es_real?: boolean;
}

export type CrearProyectoResult =
  | { ok: true; slug: string; scenario_id: string; tir_proyecto: number | null; checks_ok: boolean }
  | { ok: false; status: number; message: string };

/**
 * Crea un proyecto (escenario v1 borrador) y lo APRUEBA en un paso → queda visible en el portafolio
 * (que lee baseline/approved). Devuelve la TIR proyecto y el estado de los cuadres para feedback.
 * Errores del API (422 validación, 403 sin rol, 409 slug duplicado, 503 sin Supabase) vuelven como
 * `{ok:false, message}` con el `detail` del motor/servidor; el `redirect` de 401 se deja propagar.
 */
export async function crearYAprobarProyecto(
  input: CrearProyectoInput,
): Promise<CrearProyectoResult> {
  // Paso 1: crear (valida `par` con el motor ANTES de persistir → un 422/409 aquí no deja rastro).
  let created;
  try {
    created = await createProject(input.par, {
      slug: input.slug,
      nombre: input.nombre,
      es_real: input.es_real,
    });
  } catch (e) {
    if (e instanceof WriteError) return { ok: false, status: e.status, message: e.message };
    throw e; // p.ej. el control-flow de redirect() (401) DEBE propagarse
  }

  // Paso 2: aprobar (recalcula con el motor). Si falla aquí, el borrador YA quedó guardado → el
  // mensaje lo dice para que el usuario no reintente con el mismo nombre y choque con un 409.
  try {
    const approved = await approveScenario(created.scenario_id);
    revalidatePath("/");
    revalidatePath(`/proyectos/${created.slug}`);
    return {
      ok: true,
      slug: created.slug,
      scenario_id: created.scenario_id,
      tir_proyecto: approved.tir_proyecto,
      checks_ok: approved.checks_ok,
    };
  } catch (e) {
    if (e instanceof WriteError) {
      return {
        ok: false,
        status: e.status,
        message: `El proyecto se guardó como borrador, pero no se pudo aprobar: ${e.message}`,
      };
    }
    throw e;
  }
}
