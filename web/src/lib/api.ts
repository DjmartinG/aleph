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

// ---------- Ficha de proyecto + resultados ----------

export interface Meta {
  nombre: string;
  ubicacion?: string;
  zona?: string;
  tipo?: string;
  unidades?: number;
  moneda?: string;
  estado?: string;
  propietario?: string;
}

export interface KpisCabecera {
  ventas: number;
  util_oper: number;
  udi: number;
  margen_oper: number;
  tir_proyecto: number | null;
  tir_socio: number | null;
  vpn_proyecto: number | null;
}

export interface ProjectDetail {
  id: string;
  es_real: boolean;
  fuente: string;
  meta: Meta;
  estado: string;
  estado_label: string;
  kpis_cabecera: KpisCabecera;
}

export interface Indicadores {
  base_label: string;
  fiducia_real: boolean;
  tir_proyecto: number | null;
  tir_proyecto_label: string;
  tir_socio: number | null;
  tir_socio_label: string;
  tir_apalancada_ref: number | null;
  vpn_proyecto: number | null;
  vpn_label: string;
  wacc: number | null;
  tio: number | null;
  payback_mes: number | null;
  credito_max: number | null;
  credito_prom: number | null;
  intereses_total: number | null;
  max_necesidad_caja: number | null;
  valor_financiable: number | null;
  margen_oper: number | null;
}

export interface Pyg {
  ventas: number;
  recon_codensa: number;
  total_ingresos: number;
  directos: number;
  indirectos: number;
  honorarios: number;
  gastos_fijos: number;
  indirectos_otros: number;
  costo_lote: number;
  util_oper: number;
  margen_oper: number;
  udi: number;
  cg: number;
  socio: number;
  resultados: number;
}

export interface Check {
  clave: string;
  nombre: string;
  ok: boolean;
  detalle?: string;
}

/** Series mensuales del flujo apalancado (180 meses). */
export interface FlujoApalancado {
  operativo: number[];
  acumulado: number[];
  saldo_credito: number[];
  flujo_equity: number[];
  ingresos: number[];
  costos: number[];
  credito_max: number;
  max_necesidad_caja: number;
  aportes_total: number;
  payback_mes: number | null;
}

export interface Flujo {
  apalancado: FlujoApalancado;
  simple: Record<string, unknown>;
}

export interface Results {
  scenario_id: string;
  project_id: string;
  base_label: string;
  indicadores: Indicadores;
  pyg: Pyg;
  flujo: Flujo;
  checks: Check[];
}

/** GET /v1/projects/{slug}. null si no existe (404). */
export async function getProject(slug: string): Promise<ProjectDetail | null> {
  const res = await fetch(`${API_BASE}/v1/projects/${encodeURIComponent(slug)}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} en /v1/projects/${slug}`);
  return res.json() as Promise<ProjectDetail>;
}

/** GET /v1/scenarios/{slug}:base/results. null si no existe (404). */
export async function getResults(slug: string): Promise<Results | null> {
  const res = await fetch(
    `${API_BASE}/v1/scenarios/${encodeURIComponent(slug)}:base/results`,
    { cache: "no-store" },
  );
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} en results de ${slug}`);
  return res.json() as Promise<Results>;
}

// ---------- Sensibilidad (escenarios + tornado + heatmap) ----------

export interface EscenarioVals {
  ventas: number;
  util_oper: number;
  margen: number;
}

export interface Sensitivity {
  scenario_id: string;
  project_id: string;
  /** { Base | Optimista | Pesimista } → métricas. */
  escenarios: Record<string, EscenarioVals>;
  /** { "Precio -10%": Δutil, "Precio +10%": Δutil, ... } impacto sobre la utilidad. */
  tornado: Record<string, number>;
  matriz_2d: { pasos_precio: number[]; pasos_costo: number[]; margen_pct: number[][] };
}

/** GET /v1/scenarios/{slug}:base/sensitivity. null si no existe (404). */
export async function getSensitivity(slug: string): Promise<Sensitivity | null> {
  const res = await fetch(
    `${API_BASE}/v1/scenarios/${encodeURIComponent(slug)}:base/sensitivity`,
    { cache: "no-store" },
  );
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`API ${res.status} en sensitivity de ${slug}`);
  return res.json() as Promise<Sensitivity>;
}

// ---------- Monte Carlo (POST run) ----------

export interface MCStats {
  p10: number;
  p50: number;
  p90: number;
  media: number;
  std: number;
  n: number;
}

export interface MonteCarloResult {
  tir_proyecto: number[];
  tir_equity: number[];
  vpn_proyecto: number[];
  stats_tir: MCStats;
  stats_equity: MCStats;
  stats_vpn: MCStats;
  hurdle: number;
  prob_tir_hurdle: number;
  prob_vpn_pos: number;
  n: number;
  n_validas: number;
}

export interface MonteCarloParams {
  tipo?: "tir" | "margen";
  n?: number;
  seed?: number;
  rango_precio?: [number, number];
  rango_costo?: [number, number];
  rango_ventas?: [number, number];
}

/** POST /v1/scenarios/{slug}:base/run — Monte Carlo (único cálculo intensivo). */
export async function postRun(slug: string, params: MonteCarloParams): Promise<MonteCarloResult> {
  const res = await fetch(`${API_BASE}/v1/scenarios/${encodeURIComponent(slug)}:base/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${res.status} al correr Monte Carlo de ${slug}`);
  return res.json() as Promise<MonteCarloResult>;
}
