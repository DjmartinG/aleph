/**
 * Cliente tipado del API de ALEPH (`aleph_api`, FastAPI). Solo LECTURA.
 * Contrato §5. La API NO recalcula nada en el cliente: el motor produce las cifras, aquí se consumen.
 *
 * Base URL: env `ALEPH_API_URL` (dev: http://localhost:8000 con la auth apagada).
 * En prod el `/v1` exige token Bearer de Entra — se cableará con NextAuth (fase posterior).
 */

export const API_BASE = process.env.ALEPH_API_URL ?? "http://localhost:8000";

/** Estados del ciclo de vida (deben coincidir con `aleph_engine.config.ESTADOS`). */
export type Estado = "prefactibilidad" | "aprobado" | "construccion" | "entregado";

/** Consolidado del portafolio (números CRUDOS, en miles COP; el cliente formatea). */
export interface PortfolioConsolidado {
  n: number;
  unidades: number;
  ventas: number;
  util_oper: number;
  udi: number;
  vpn: number;
  margen: number;
  tir_ref: number | null;
  tir_eq: number | null;
  credito_max: number;
}

export interface FunnelStage {
  estado: Estado | string;
  label: string;
  count: number;
}

/** Un proyecto en el pipeline/embudo (de `portfolio.pipeline`). */
export interface ProjectItem {
  slug: string;
  nombre: string;
  estado: Estado | string;
  tir: number | null;
  vpn: number | null;
  ventas: number | null;
  und: number;
  ubicacion: string;
  tipo: string;
}

export interface Portfolio {
  consolidado: PortfolioConsolidado;
  embudo: FunnelStage[];
  items: ProjectItem[];
}

/** GET /v1/portfolio. Sin caché (dato dinámico). Lanza Error con el status si la API falla. */
export async function getPortfolio(): Promise<Portfolio> {
  const res = await fetch(`${API_BASE}/v1/portfolio`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API respondió ${res.status} al pedir /v1/portfolio`);
  }
  return res.json() as Promise<Portfolio>;
}
